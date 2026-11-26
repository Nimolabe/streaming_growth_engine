"""Kommandozeile des Content Strategist.

Beispiele:
  python -m streaming_agents.content_strategist plan --game "Stardew Valley" \
      --window "Mo 18-22" --window "Mi 18-22" --window "Sa 14-20" \
      --hours 8 --streams 3 --viewers 3 --chatters 1 --html plan.html

  # Mit Messungen aus dem Kategorie-Check (Uhrzeiten nach Publikum pro Platz):
  python -m streaming_agents.content_strategist plan --game "Minecraft" --window "Fr 18-23" \
      --window "Sa 12-22" --hours 6 --streams 2 --viewers 3 --measurements messungen.jsonl

  # Inhalte für die Website exportieren (aus der Repo-Wurzel; die Datei wird committet):
  python -m streaming_agents.content_strategist export-web --out data/content-strategist.json

Alles läuft lokal, ohne Sprachmodell und ohne Kosten.
"""
import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from ..category_check.store import StoreError, load_snapshots
from .models import StrategyRequest, TimeWindow
from .planner import PlanError, build_plan
from .report import render_html, render_text
from .web_export import DEFAULT_PATH, write


class CliError(Exception):
    pass


def _new_file(path: str, overwrite: bool) -> Path:
    target = Path(path).expanduser()
    if target.exists() and not overwrite:
        raise CliError(f"{target} existiert bereits (mit --overwrite ersetzen).")
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def _window(text: str) -> TimeWindow:
    try:
        return TimeWindow.parse(text)
    except (ValueError, ValidationError) as exc:
        raise argparse.ArgumentTypeError(_first_error(exc)) from exc


def _first_error(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return exc.errors()[0]["msg"].removeprefix("Value error, ")
    return str(exc).splitlines()[0]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m streaming_agents.content_strategist",
        description="Content Strategist: Wochenplan mit Spiel, Uhrzeit, Format, Titel und Tags.")
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan", help="Wochenplan erstellen")
    plan.add_argument("--game", action="append", required=True,
                      help="Spiel bzw. Twitch-Kategorie (1–5×), z. B. --game \"Stardew Valley\"")
    plan.add_argument("--window", action="append", required=True, type=_window,
                      help="Zeitfenster in Ortszeit, z. B. \"Mo 18-22\", \"Sa 14:00-20:30\", "
                           "\"Fr 22-2\" (über Mitternacht)")
    plan.add_argument("--hours", type=int, required=True,
                      help="GESAMTE Zeit pro Woche in Stunden: Streams plus Vorbereitung, Clips und "
                           "Wochenrückblick. Ist sie knapp, kürzt der Plan diese Zusatzaufgaben "
                           "und sagt es in den Hinweisen")
    plan.add_argument("--streams", type=int, required=True, help="Streams pro Woche (1–7)")
    plan.add_argument("--viewers", type=int, default=0, help="Durchschnittliche Zuschauer")
    plan.add_argument("--chatters", type=int, default=0, help="Aktive Chatter pro Stream")
    plan.add_argument("--goal", choices=["discovery", "community", "consistency"],
                      default="discovery", help="Ziel: neue Zuschauer, Community oder Regelmäßigkeit")
    plan.add_argument("--experience", choices=["beginner", "intermediate", "advanced"],
                      default="beginner")
    plan.add_argument("--lang", choices=["de", "en"], default="de", help="Sprache von Plan und Titeln")
    plan.add_argument("--platform", choices=["twitch", "youtube", "kick", "tiktok", "other"],
                      default="twitch")
    plan.add_argument("--rank-goal", help="Rang-Ziel für die Titel, z. B. \"Platin\"")
    plan.add_argument("--current-rank", help="Aktueller Rang, z. B. \"Silber\" (mit --rank-goal)")
    plan.add_argument("--commands", nargs="+", default=[],
                      help="Bis zu 3 eigene Chat-Befehle für die Titel, z. B. '!discord' '!insta'")
    plan.add_argument("--mood", choices=["chill", "ambitious", "funny", "chillig", "ehrgeizig",
                                         "lustig"],
                      help="Stimmung der Titel (Standard: passend zu Genre und Format)")
    plan.add_argument("--first-time", action="store_true",
                      help="Zum ersten Mal / blind: Titel „Zum ersten Mal …“, bei unbekannten "
                           "Genres das Format „Erste Eindrücke“")
    plan.add_argument("--week", type=int, default=1,
                      help="Wievielte Woche du planst (Standard 1) – Zähler in Titeln laufen weiter")
    plan.add_argument("--collab", action="store_true",
                      help="Mitspieler oder Gast verfügbar (Koop- und Coach-Formate)")
    plan.add_argument("--measurements", nargs="+",
                      help="Messdatei(en) aus dem Kategorie-Check (.jsonl)")
    plan.add_argument("--utc-offset", type=int,
                      help="Zeitzone der Messungen in Minuten (Standard: Ortszeit des Rechners)")
    plan.add_argument("--json", help="Plan als JSON speichern")
    plan.add_argument("--html", help="HTML-Bericht speichern")
    plan.add_argument("--overwrite", action="store_true")
    plan.set_defaults(handler=cmd_plan)

    export = sub.add_parser("export-web",
                            help="Inhalte (Genres, Formate, Titel) als JSON für die Website")
    export.add_argument("--out", default=str(DEFAULT_PATH),
                        help=f"Zieldatei (Standard: {DEFAULT_PATH}, relativ zum aktuellen Ordner)")
    export.set_defaults(handler=cmd_export_web)
    return parser


def cmd_export_web(args: argparse.Namespace) -> int:
    target = write(args.out)
    size = target.stat().st_size
    print(f"Export gespeichert: {target} ({size / 1024:.1f} KB). Danach die Paritäts-Fixtures "
          "neu erzeugen: python tests/strategist_parity.py (in agents/)", flush=True)
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    measurements = []
    if args.measurements:
        loaded = load_snapshots(*args.measurements)
        measurements = loaded.snapshots
        if loaded.skipped_lines:
            print(f"Hinweis: {loaded.skipped_lines} unlesbare Zeilen übersprungen.", flush=True)
    request = StrategyRequest(
        games=args.game, windows=args.window, hours_per_week=args.hours,
        streams_per_week=args.streams, average_viewers=args.viewers,
        active_chatters=args.chatters, goal=args.goal, experience=args.experience,
        language=args.lang, platform=args.platform, collab_partner=args.collab,
        week_number=args.week, rank_goal=args.rank_goal, current_rank=args.current_rank,
        commands=args.commands, mood=args.mood,
        first_time=args.first_time,
        measurements=measurements, utc_offset_minutes=args.utc_offset,
    )
    plan = build_plan(request)
    print(render_text(plan), flush=True)
    if args.html:
        target = _new_file(args.html, args.overwrite)
        target.write_text(render_html(plan), encoding="utf-8")
        print(f"\nBericht gespeichert: {target} (im Browser öffnen)", flush=True)
    if args.json:
        target = _new_file(args.json, args.overwrite)
        target.write_text(plan.model_dump_json(indent=2) + "\n", encoding="utf-8")
        print(f"Plan gespeichert: {target}", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (CliError, PlanError, StoreError, ValidationError, ValueError) as exc:
        print(f"Content Strategist: {_first_error(exc)}", file=sys.stderr)
        return 2
