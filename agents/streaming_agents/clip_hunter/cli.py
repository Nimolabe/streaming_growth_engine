"""Kommandozeile des Clip Hunter.

Beispiele:
  python -m streaming_agents.clip_hunter record-chat meinkanal --out chat.jsonl
  python -m streaming_agents.clip_hunter analyze --video vod.mp4 --chat chat.jsonl \
      --twitch-video 2345678901 --report bericht.html --export-dir clips --vertical
  python -m streaming_agents.clip_hunter viewer-clips --twitch-video 2345678901 --out clips.json
  python -m streaming_agents.clip_hunter evaluate --result ergebnis.json --viewer-clips clips.json
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from .audio_signal import MediaError
from .chat_log import ChatLogError, ChatLogWriter, read_chat_log
from .evaluation import EvaluationReport, evaluate_against_viewer_clips
from .export import export_candidates
from .fusion import CATEGORY_LABELS, format_hms
from .hunter import hunt
from .models import ChatLogHeader, HuntResult, HuntSettings
from .report import render_report
from .twitch_api import HelixClient, TwitchApiError, VideoInfo, ViewerClip, parse_video_id
from .twitch_irc import ChannelNameError, TwitchChatRecorder, normalize_channel

_CLIPS = TypeAdapter(list[ViewerClip])


class CliError(Exception):
    pass


def _new_file(path: str, overwrite: bool) -> Path:
    target = Path(path).expanduser()
    if target.exists() and not overwrite:
        raise CliError(f"{target} existiert bereits (mit --overwrite ersetzen).")
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def _parse_vod_start(value: str) -> float:
    try:
        moment = datetime.fromisoformat(value.strip())
    except ValueError as exc:
        raise CliError("--vod-start erwartet z. B. 2026-11-14T18:00:05+01:00") from exc
    if moment.tzinfo is None:
        moment = moment.astimezone()  # ohne Zeitzone: lokale Zeit des Rechners
    return moment.timestamp()


def _print(text: str = "") -> None:
    print(text, flush=True)


def cmd_record_chat(args: argparse.Namespace) -> int:
    channel = normalize_channel(args.channel)
    target = _new_file(args.out, args.overwrite)
    bots = [name.strip() for name in (args.bots or "").split(",") if name.strip()]
    header = ChatLogHeader(channel=channel, started_at=time.time())
    with ChatLogWriter(target, header, overwrite=True) as writer:
        _print(f"Schneide den Chat von #{channel} mit → {target}")
        _print("Beenden mit Strg+C. Die Datei wird laufend gespeichert.")
        recorder = TwitchChatRecorder(
            channel, writer, extra_bot_names=bots,
            max_seconds=args.minutes * 60 if args.minutes else None, log=_print)
        stats = recorder.run()
    _print(f"Fertig ({stats.stopped_by or 'beendet'}): {stats.messages} Nachrichten, "
           f"{stats.events} Ereignisse (Subs, Raids, Bits), {stats.reconnects} Neuverbindungen.")
    return 0


def _settings(args: argparse.Namespace) -> HuntSettings:
    values = {"language": args.lang, "max_candidates": args.max,
              "chat_offset_seconds": args.chat_offset}
    if args.pre_roll is not None:
        values["pre_roll_seconds"] = args.pre_roll
    if args.post_roll is not None:
        values["post_roll_seconds"] = args.post_roll
    return HuntSettings(**values)


def _load_clips(path: str) -> list[ViewerClip]:
    try:
        return _CLIPS.validate_json(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValidationError) as exc:
        raise CliError(f"Zuschauer-Clips aus {path} konnten nicht gelesen werden.") from exc


def _summary(result: HuntResult) -> None:
    labels = CATEGORY_LABELS[result.language]
    _print(f"\nModus: {result.mode} · Chat-Momente: {result.chat_moments_found} · "
           f"Audio-Spitzen: {result.audio_spikes_found}")
    if result.alignment_note:
        _print(f"Hinweis: {result.alignment_note}")
    if not result.candidates:
        _print("Keine Kandidaten gefunden.")
        return
    _print(f"{'#':>3}  {'von':>8}  {'bis':>8}  {'Art':<10} {'Wert':>4}  Sicherheit")
    for item in result.candidates:
        _print(f"{item.rank:>3}  {format_hms(item.start_seconds):>8}  "
               f"{format_hms(item.end_seconds):>8}  {labels[item.category]:<10} "
               f"{item.score:>4}  {item.confidence}")


def cmd_analyze(args: argparse.Namespace) -> int:
    if not args.video and not args.chat:
        raise CliError("Bitte --video und/oder --chat angeben.")
    if args.vertical and not args.export_dir:
        raise CliError("--vertical gilt nur zusammen mit --export-dir.")
    if args.export_dir and not args.video:
        raise CliError("Für --export-dir wird --video benötigt.")
    if args.compare and not args.twitch_video:
        raise CliError("--compare braucht --twitch-video.")
    if args.compare and args.viewer_clips:
        raise CliError("Entweder --compare oder --viewer-clips angeben, nicht beides.")
    out = _new_file(args.out, args.overwrite) if args.out else None
    report_path = _new_file(args.report, args.overwrite) if args.report else None
    settings = _settings(args)
    chat_log = read_chat_log(args.chat) if args.chat else None
    if chat_log and chat_log.skipped_lines:
        _print(f"Hinweis: {chat_log.skipped_lines} unlesbare Zeilen im Chat-Mitschnitt übersprungen.")

    video_id = None
    vod_start = _parse_vod_start(args.vod_start) if args.vod_start else None
    video: VideoInfo | None = None
    if args.twitch_video:
        video_id = parse_video_id(args.twitch_video)
        # Twitch nur fragen, wenn es nötig ist: Startzeit für den Chat oder Zuschauer-Clips.
        if (chat_log is not None and vod_start is None) or args.compare:
            video = HelixClient.from_env().get_video(video_id)
            if vod_start is None:
                vod_start = video.started_at
                _print(f"VOD-Start laut Twitch: {video.created_at.isoformat()}")

    _print("Analysiere … (lange VODs brauchen einige Minuten)")
    result = hunt(recording=args.video, chat_log=chat_log, vod_start=vod_start,
                  settings=settings, twitch_video_id=video_id)
    _summary(result)

    evaluation: EvaluationReport | None = None
    clips: list[ViewerClip] | None = None
    if args.viewer_clips:
        clips = _load_clips(args.viewer_clips)
    elif args.compare and video is not None:
        clips = HelixClient.from_env().get_viewer_clips(video)
    if clips is not None:
        evaluation = evaluate_against_viewer_clips(result.candidates, clips,
                                                   top_n=min(10, settings.max_candidates),
                                                   language=settings.language)
        _print(f"\nAbgleich mit {evaluation.viewer_clips} Zuschauer-Clips "
               f"({evaluation.community_moments} Momente): Abdeckung "
               f"{_pct(evaluation.coverage)}, Trefferquote Top {evaluation.top_n} "
               f"{_pct(evaluation.precision_at_n)}")

    exported: dict[int, Path] = {}
    if args.export_dir:
        files = export_candidates(args.video, result.candidates, args.export_dir,
                                  vertical=args.vertical)
        exported = {item.rank: path for item, path in zip(result.candidates, files)}
        _print(f"{len(files)} Clips gespeichert in {Path(args.export_dir).resolve()}")

    payload = {"result": json.loads(result.model_dump_json())}
    if evaluation:
        payload["evaluation"] = json.loads(evaluation.model_dump_json())
    if out:
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _print(f"Ergebnis gespeichert: {out}")
    if report_path:
        report_path.write_text(render_report(result, evaluation=evaluation, exported=exported,
                                             report_path=report_path.resolve()),
                               encoding="utf-8")
        _print(f"Bericht gespeichert: {report_path} (im Browser öffnen)")
    if not out and not report_path:
        _print("\n" + json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _pct(value: float | None) -> str:
    return "–" if value is None else f"{round(value * 100)} %"


def cmd_viewer_clips(args: argparse.Namespace) -> int:
    target = _new_file(args.out, args.overwrite)
    client = HelixClient.from_env()
    video = client.get_video(args.twitch_video)
    clips = client.get_viewer_clips(video)
    target.write_text(_CLIPS.dump_json(clips, indent=2).decode() + "\n", encoding="utf-8")
    _print(f"{len(clips)} Zuschauer-Clips mit VOD-Position gespeichert: {target}")
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    try:
        raw = json.loads(Path(args.result).read_text(encoding="utf-8"))
        result = HuntResult.model_validate(raw.get("result", raw))
    except (OSError, json.JSONDecodeError, ValidationError, AttributeError) as exc:
        raise CliError(f"{args.result} ist kein Clip-Hunter-Ergebnis.") from exc
    evaluation = evaluate_against_viewer_clips(result.candidates, _load_clips(args.viewer_clips),
                                               top_n=args.top, language=result.language)
    _print(f"Community-Momente: {evaluation.community_moments} · Abdeckung "
           f"{_pct(evaluation.coverage)} (nach Aufrufen {_pct(evaluation.view_weighted_coverage)})"
           f" · Trefferquote Top {evaluation.top_n}: {_pct(evaluation.precision_at_n)}")
    _print(evaluation.note)
    if args.report:
        target = _new_file(args.report, args.overwrite)
        target.write_text(render_report(result, evaluation=evaluation), encoding="utf-8")
        _print(f"Bericht gespeichert: {target}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m streaming_agents.clip_hunter",
        description="Clip Hunter: findet Clip-Momente über Chat-Reaktionen und Audio-Spitzen.")
    sub = parser.add_subparsers(dest="command", required=True)

    record = sub.add_parser("record-chat", help="Twitch-Chat live mitschneiden (anonym, nur lesen)")
    record.add_argument("channel", help="Kanalname oder Link, z. B. meinkanal")
    record.add_argument("--out", required=True, help="Zieldatei, z. B. chat.jsonl")
    record.add_argument("--minutes", type=float, help="Nach so vielen Minuten automatisch stoppen")
    record.add_argument("--bots", help="Weitere Bot-Namen, kommagetrennt")
    record.add_argument("--overwrite", action="store_true")
    record.set_defaults(handler=cmd_record_chat)

    analyze = sub.add_parser("analyze", help="VOD und/oder Chat auswerten")
    analyze.add_argument("--video", help="Eigene Aufnahme/VOD-Datei (mp4, mkv, …) oder Audiodatei")
    analyze.add_argument("--chat", help="Chat-Mitschnitt (.jsonl) von record-chat")
    analyze.add_argument("--twitch-video", help="Twitch-VOD-ID oder -Link (für Startzeit und Links)")
    analyze.add_argument("--vod-start", help="Startzeit des VODs, z. B. 2026-11-14T18:00:05+01:00")
    analyze.add_argument("--chat-offset", type=float, default=0.0,
                         help="Chat um so viele Sekunden verschieben (positiv = später)")
    analyze.add_argument("--max", type=int, default=15, help="Höchstzahl Kandidaten (1–50)")
    analyze.add_argument("--pre-roll", type=float, help="Sekunden vor dem Höhepunkt (Standard 20)")
    analyze.add_argument("--post-roll", type=float, help="Sekunden nach dem Höhepunkt (Standard 10)")
    analyze.add_argument("--lang", choices=["de", "en"], default="de")
    analyze.add_argument("--out", help="Ergebnis als JSON speichern")
    analyze.add_argument("--report", help="HTML-Bericht speichern")
    analyze.add_argument("--export-dir", help="Kandidaten als MP4 in diesen Ordner schneiden")
    analyze.add_argument("--vertical", action="store_true", help="Export im Hochformat 9:16")
    analyze.add_argument("--viewer-clips", help="Zuschauer-Clips (.json) zum Abgleich")
    analyze.add_argument("--compare", action="store_true",
                         help="Zuschauer-Clips direkt von Twitch holen und abgleichen")
    analyze.add_argument("--overwrite", action="store_true")
    analyze.set_defaults(handler=cmd_analyze)

    clips = sub.add_parser("viewer-clips", help="Zuschauer-Clips eines VODs von Twitch laden")
    clips.add_argument("--twitch-video", required=True, help="Twitch-VOD-ID oder -Link")
    clips.add_argument("--out", required=True)
    clips.add_argument("--overwrite", action="store_true")
    clips.set_defaults(handler=cmd_viewer_clips)

    evaluate = sub.add_parser("evaluate", help="Gespeichertes Ergebnis mit Zuschauer-Clips messen")
    evaluate.add_argument("--result", required=True)
    evaluate.add_argument("--viewer-clips", required=True)
    evaluate.add_argument("--top", type=int, default=10)
    evaluate.add_argument("--report")
    evaluate.add_argument("--overwrite", action="store_true")
    evaluate.set_defaults(handler=cmd_evaluate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (CliError, ChatLogError, MediaError, TwitchApiError, ChannelNameError,
            ValidationError, ValueError) as exc:
        message = str(exc).splitlines()[0] if str(exc) else type(exc).__name__
        if isinstance(exc, ValidationError):
            message = "Ungültige Einstellung: " + "; ".join(
                f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in exc.errors())
        print(f"Clip Hunter: {message}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Abgebrochen.", file=sys.stderr)
        return 130
