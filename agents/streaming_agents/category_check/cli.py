"""Kommandozeile des Kategorie-Checks.

Beispiele:
  python -m streaming_agents.category_check measure "Minecraft" "Stardew Valley" --out messungen.jsonl
  python -m streaming_agents.category_check suggest --top 30 --out messungen.jsonl
  python -m streaming_agents.category_check watch "Minecraft" "Stardew Valley" --every 60 --hours 72 \
      --out messungen.jsonl
  python -m streaming_agents.category_check report messungen.jsonl --viewers 2 --window 16-24 \
      --html bericht.html

Benötigt TWITCH_CLIENT_ID und TWITCH_CLIENT_SECRET (kostenlose App unter dev.twitch.tv/console).
"""
import argparse
import sys
import time
from collections.abc import Callable
from pathlib import Path

from ..clip_hunter.twitch_api import HelixClient, TwitchApiError
from .aliases import alias_label
from .analysis import analyze, parse_window
from .collect import (
    DEFAULT_PAGES,
    MAX_PAGES,
    Category,
    CategoryNotFound,
    measure_many,
    resolve_category,
    suggestion_categories,
)
from .gambling import GamblingNotSupported, rejection
from .models import CategoryCheckResult
from .report import render_report
from .store import StoreError, append_snapshots, load_snapshots

LABELS = {
    "de": {"good": "gute Chance", "ok": "machbar", "hard": "schwer", "low_demand": "wenig Publikum"},
    "en": {"good": "good chance", "ok": "doable", "hard": "hard", "low_demand": "small audience"},
}


class CliError(Exception):
    pass


def _print(text: str = "") -> None:
    print(text, flush=True)


def _language(value: str) -> str:
    value = value.strip().casefold()
    if value != "any" and not (len(value) == 2 and value.isascii() and value.isalpha()):
        raise argparse.ArgumentTypeError("Sprache als Kürzel angeben, z. B. de, en oder any")
    return value


def _new_file(path: str, overwrite: bool) -> Path:
    target = Path(path).expanduser()
    if target.exists() and not overwrite:
        raise CliError(f"{target} existiert bereits (mit --overwrite ersetzen).")
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def print_table(result: CategoryCheckResult) -> None:
    labels = LABELS[result.language]
    de = result.language == "de"
    if not result.categories:
        _print("Keine Messungen." if de else "No measurements.")
        return
    width = min(34, max(len(item.category) for item in result.categories))
    head = ("Kategorie", "Kanäle", "Zuschauer", "dein Platz", "Einschätzung") if de else \
           ("Category", "Channels", "Viewers", "your rank", "verdict")
    _print(f"{head[0]:<{width}}  {head[1]:>7}  {head[2]:>9}  {head[3]:>11}  {head[4]}")
    for item in result.categories:
        name = item.category if len(item.category) <= width else item.category[:width - 1] + "…"
        plus = "+" if item.channels_is_lower_bound else ""
        rank = f">{item.median_rank - 1}" if item.rank_is_lower_bound else str(item.median_rank)
        _print(f"{name:<{width}}  {str(item.median_channels) + plus:>7}  "
               f"{str(item.median_total_viewers) + plus:>9}  {rank:>11}  {labels[item.verdict]}")
    best = [item for item in result.categories if item.best_slots]
    if best:
        _print("\nBeste Zeiten:" if de else "\nBest times:")
        for item in best[:5]:
            _print(f"  {item.category}: " + ", ".join(slot.label for slot in item.best_slots))
    _print("")
    for note in result.notes:
        _print(f"• {note}")


def _resolve_all(client: HelixClient, names: list[str], ui: str = "de") -> list[Category]:
    """Kategorien auflösen. Glücksspiel wird freundlich abgelehnt und nicht gemessen; kommt
    nur Glücksspiel vor, bricht der Befehl ab (Exit-Code 2)."""
    categories: list[Category] = []
    rejected = 0
    for name in names:
        try:
            category = resolve_category(client, name)
        except GamblingNotSupported as exc:
            _print(rejection(exc.name, ui))
            rejected += 1
            continue
        if category.alias:
            _print(alias_label(category.alias, category.name))
        if all(existing.id != category.id for existing in categories):
            categories.append(category)
    if not categories:
        raise CliError("Keine unterstützte Kategorie zum Messen." if ui == "de" else
                       "No supported category to measure.")
    return categories


def _round(client: HelixClient, categories: list[Category], args: argparse.Namespace) -> int:
    result = measure_many(client, categories, args.lang, max_pages=args.pages)
    for error in result.errors:
        _print(f"Fehler: {error}")
    if result.snapshots:
        append_snapshots(args.out, result.snapshots)
    return len(result.snapshots)


def cmd_measure(args: argparse.Namespace) -> int:
    client = HelixClient.from_env()
    categories = _resolve_all(client, args.categories, args.ui)
    _print(f"Messe {len(categories)} Kategorien (Sprache: {args.lang}) …")
    result = measure_many(client, categories, args.lang, max_pages=args.pages)
    for error in result.errors:
        _print(f"Fehler: {error}")
    if not result.snapshots:
        raise CliError("Keine Messung erfolgreich.")
    append_snapshots(args.out, result.snapshots)
    _print(f"{len(result.snapshots)} Messungen ergänzt in {Path(args.out).expanduser()}\n")
    print_table(analyze(result.snapshots, own_viewers=args.viewers, language=args.ui))
    return 0 if not result.errors else 1


def cmd_suggest(args: argparse.Namespace) -> int:
    client = HelixClient.from_env()
    chosen = suggestion_categories(client, args.top)
    categories = chosen.categories
    _print(f"Messe die {len(categories)} meistgesehenen Kategorien (Sprache: {args.lang}) …")
    result = measure_many(client, categories, args.lang, max_pages=args.pages)
    for error in result.errors:
        _print(f"Fehler: {error}")
    if not result.snapshots:
        raise CliError("Keine Messung erfolgreich.")
    append_snapshots(args.out, result.snapshots)
    _print(f"{len(result.snapshots)} Messungen ergänzt in {Path(args.out).expanduser()}\n")
    print_table(analyze(result.snapshots, own_viewers=args.viewers, language=args.ui,
                        skipped_gambling=chosen.skipped_gambling))
    return 0 if not result.errors else 1


def cmd_watch(args: argparse.Namespace, sleep: Callable[[float], None] = time.sleep,
              clock: Callable[[], float] = time.monotonic) -> int:
    client = HelixClient.from_env()
    categories = _resolve_all(client, args.categories, args.ui)
    rounds = max(1, int(args.hours * 60 // args.every) + 1)
    _print(f"Messe {len(categories)} Kategorien alle {args.every:g} Minuten, insgesamt "
           f"{rounds} Runden → {Path(args.out).expanduser()}")
    _print("Beenden mit Strg+C; bisherige Messungen bleiben gespeichert.")
    for number in range(1, rounds + 1):
        started = clock()
        saved = _round(client, categories, args)
        _print(f"Runde {number}/{rounds}: {saved} Messungen gespeichert "
               f"({time.strftime('%a %H:%M')})")
        if number < rounds:
            sleep(max(0.0, args.every * 60 - (clock() - started)))
    _print("Fertig. Auswerten mit: python -m streaming_agents.category_check report "
           f"{args.out}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    loaded = load_snapshots(*args.files)
    if loaded.skipped_lines:
        _print(f"Hinweis: {loaded.skipped_lines} unlesbare Zeilen übersprungen.")
    window = parse_window(args.window) if args.window else None
    result = analyze(loaded.snapshots, own_viewers=args.viewers, language=args.ui, window=window)
    print_table(result)
    if args.html:
        target = _new_file(args.html, args.overwrite)
        target.write_text(render_report(result), encoding="utf-8")
        _print(f"\nBericht gespeichert: {target} (im Browser öffnen)")
    if args.json:
        target = _new_file(args.json, args.overwrite)
        target.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
        _print(f"Ergebnis gespeichert: {target}")
    return 0


def _common(parser: argparse.ArgumentParser, *, out: bool = True) -> None:
    parser.add_argument("--lang", type=_language, default="de",
                        help="Sprache der Streams: de, en, … oder any (Standard: de)")
    parser.add_argument("--pages", type=int, default=DEFAULT_PAGES,
                        help=f"Höchstens so viele Seiten à 100 Kanäle (1–{MAX_PAGES}; "
                             "bei suggest Standard 3)")
    parser.add_argument("--viewers", type=int, default=2,
                        help="Deine durchschnittlichen Zuschauer (Standard 2)")
    parser.add_argument("--ui", choices=["de", "en"], default="de", help="Sprache der Ausgabe")
    if out:
        parser.add_argument("--out", required=True, help="Messdatei (.jsonl), wird ergänzt")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m streaming_agents.category_check",
        description="Kategorie-Check: In welcher Twitch-Kategorie und wann wirst du gesehen?")
    sub = parser.add_subparsers(dest="command", required=True)

    measure = sub.add_parser("measure", help="Kategorien jetzt einmal messen")
    measure.add_argument("categories", nargs="+", help="Exakte Kategorienamen, z. B. \"Minecraft\"")
    _common(measure)
    measure.set_defaults(handler=cmd_measure)

    suggest = sub.add_parser("suggest", help="Die meistgesehenen Kategorien messen und vergleichen")
    suggest.add_argument("--top", type=int, default=30, help="Anzahl Kategorien (1–100)")
    _common(suggest)
    suggest.set_defaults(handler=cmd_suggest)

    watch = sub.add_parser("watch", help="Regelmäßig messen, um die besten Zeiten zu finden")
    watch.add_argument("categories", nargs="+")
    watch.add_argument("--every", type=float, default=60, help="Minuten zwischen Messungen (≥ 10)")
    watch.add_argument("--hours", type=float, default=24, help="Gesamtdauer in Stunden (≤ 336)")
    _common(watch)
    watch.set_defaults(handler=cmd_watch)

    report = sub.add_parser("report", help="Gespeicherte Messungen auswerten")
    report.add_argument("files", nargs="+", help="Eine oder mehrere Messdateien (.jsonl)")
    report.add_argument("--viewers", type=int, default=2, help="Deine durchschnittlichen Zuschauer")
    report.add_argument("--ui", choices=["de", "en"], default="de")
    report.add_argument("--window", help="Nur diese Uhrzeiten für „beste Zeiten“, z. B. 16-24 oder 20-2")
    report.add_argument("--html", help="HTML-Bericht speichern")
    report.add_argument("--json", help="Ergebnis als JSON speichern")
    report.add_argument("--overwrite", action="store_true")
    report.set_defaults(handler=cmd_report)
    return parser


def _check(args: argparse.Namespace, argv: list[str] | None) -> None:
    if getattr(args, "viewers", 0) < 0 or getattr(args, "viewers", 0) > 100_000:
        raise CliError("--viewers muss zwischen 0 und 100000 liegen.")
    if hasattr(args, "pages"):
        given = argv is not None and any(item.startswith("--pages") for item in argv)
        if args.command == "suggest" and not given:
            args.pages = 3  # viele Kategorien: weniger Seiten, damit es schnell bleibt
        if not 1 <= args.pages <= MAX_PAGES:
            raise CliError(f"--pages muss zwischen 1 und {MAX_PAGES} liegen.")
    if args.command == "suggest" and not 1 <= args.top <= 100:
        raise CliError("--top muss zwischen 1 und 100 liegen.")
    if args.command == "watch":
        if args.every < 10:
            raise CliError("--every muss mindestens 10 Minuten sein.")
        if not 0 < args.hours <= 336:
            raise CliError("--hours muss zwischen 0 und 336 (zwei Wochen) liegen.")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        _check(args, argv)
        return args.handler(args)
    except (CliError, CategoryNotFound, TwitchApiError, StoreError, ValueError) as exc:
        message = str(exc).splitlines()[0] if str(exc) else type(exc).__name__
        print(f"Kategorie-Check: {message}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Abgebrochen. Bisherige Messungen sind gespeichert.", file=sys.stderr)
        return 130
