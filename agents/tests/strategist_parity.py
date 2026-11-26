"""Paritäts-Fixtures Python ↔ JavaScript für den Content Strategist.

Python erzeugt für feste Profile die erwarteten Ergebnisse (``build_plan(..., surface="web")``)
und speichert sie in ``tests/fixtures/strategist-parity.json`` (Repo-Wurzel). Die Tests
``agents/tests/test_strategist_web.py`` (Node) und ``tests/web/test_strategist_parity.py``
(Chromium) führen ``js/strategist-core.js`` mit denselben Eingaben aus und verlangen identische
Ergebnisse.

Neu erzeugen (nach jeder Änderung an Inhalten oder Planer), aus ``agents/``:
    python -m streaming_agents.content_strategist export-web --out ../data/content-strategist.json
    python tests/strategist_parity.py
"""
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from streaming_agents.content_strategist.models import StrategyRequest
from streaming_agents.content_strategist.planner import PlanError, build_plan
from streaming_agents.content_strategist.web_export import checksum, content

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_content_strategist as cs  # Profile der bestehenden Tests wiederverwenden

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "strategist-parity.json"


def window(text: str) -> dict:
    """„Mo 18-22“ → Rohform wie im API-Body (Wochentag und Uhrzeit als Text, ungeparst)."""
    day, span = text.replace("–", "-").split()
    start, end = span.split("-", 1)
    return {"day": day, "start": start, "end": end}


def base(games, windows=cs.WINDOWS, **extra) -> dict:
    raw = {"games": list(games), "windows": [window(item) for item in windows],
           "hours_per_week": 8, "streams_per_week": 3}
    raw.update(extra)
    return raw


def cases() -> list[dict]:
    result: list[dict] = []

    def add(name: str, raw: dict) -> None:
        result.append({"name": name, "request": raw})

    # 1. Beispielprofile: 9 Genres × 3 Zuschauer-Profile × DE/EN (54)
    for genre, game in cs.EXAMPLE_GAMES.items():
        for profile, values in cs.PROFILES.items():
            for language in ("de", "en"):
                add(f"beispiel-{genre}-{profile}-{language}",
                    base((game,), language=language, **values))

    # 2. Regressionsprofile der Simulation mit 100 Test-Streamern (#31, 30 Stück)
    for (games, streams, hours, viewers, chatters, goal, experience, first_time, language,
         windows, week, collab, mood, commands) in cs.SIMULATION:
        add("simulation-" + "+".join(games) + f"-{streams}x{hours}h",
            base(games, windows, streams_per_week=streams, hours_per_week=hours,
                 average_viewers=viewers, active_chatters=chatters, goal=goal,
                 experience=experience, first_time=first_time, language=language,
                 week_number=week, collab_partner=collab, mood=mood, commands=list(commands)))

    # 3. Grenzfälle
    add("mitternacht-fr-sa-so", base(("Valorant",), ["Fr 22-2", "Sa 23:30-3", "So 22-1"],
                                     streams_per_week=3, hours_per_week=10))
    add("mitternacht-so-mo-verschmilzt", base(("Minecraft",), ["So 20-24", "Mo 0-2", "Mi 18-22"],
                                              streams_per_week=2, hours_per_week=8))
    # Vorbereitung vor Mo 0:15 liegt am Sonntag davor (negative Wochenminute → Modulo).
    add("montag-kurz-nach-mitternacht", base(("Valorant",), ["Mo 0:15-3"], streams_per_week=1,
                                             hours_per_week=4))
    add("ganzer-tag", base(("Just Chatting",), ["Mi 0-24"], streams_per_week=1, hours_per_week=6))
    add("ueberlappende-fenster", base(("Fortnite",), ["Mo 18-21", "Mo 20-23", "Di 19:15-20:30"],
                                      streams_per_week=2, hours_per_week=6))
    for hours, name in ((6, "rueckblick-gekuerzt"), (5, "clips-gekuerzt"), (4, "vorbereitung"),
                        (3, "zu-wenig-zeit")):
        add(f"knapp-{name}", base(("Stardew Valley",), streams_per_week=2, hours_per_week=hours))
    add("knapp-en", base(("Stardew Valley",), streams_per_week=3, hours_per_week=4, language="en"))
    add("zu-wenige-fenster", base(("Valorant",), ["Mo 18-19:30", "Di 18-18:45"],
                                  streams_per_week=2))
    add("zu-wenige-fenster-en", base(("Valorant",), ["Mo 18-19"], streams_per_week=2,
                                     language="en"))
    add("sieben-streams-kein-freier-tag", base(("Minecraft",), cs.W_ALL, streams_per_week=7,
                                               hours_per_week=30, active_chatters=9,
                                               goal="community"))
    add("unbekannte-spiele", base(("Tetris Effect", "Schach", "Starfield"),
                                  hours_per_week=12, streams_per_week=4, first_time=True))
    add("unbekannt-en-woche-3", base(("Balatro",), language="en", week_number=3))
    add("gluecksspiel-allein", base(("Slots",)))
    add("gluecksspiel-allein-en", base(("virtual casino", "Poker"), language="en"))
    add("gluecksspiel-gemischt", base(("Slots", "Valorant")))
    add("gluecksspiel-gemischt-en", base(("Valorant", "BLACKJACK", "Minecraft"), language="en"))
    for mood in ("chill", "ambitious", "funny", "chillig", "ehrgeizig", "lustig", "Entspannt"):
        add(f"stimmung-{mood}", base(("Valorant", "Stardew Valley"), mood=mood,
                                     streams_per_week=4, hours_per_week=12))
    add("stimmung-funny-en", base(("Phasmophobia",), mood="funny", language="en"))
    add("rang-ziel", base(("Valorant",), rank_goal="Platin", streams_per_week=4,
                          hours_per_week=12))
    add("rang-reise", base(("League of Legends",), rank_goal="Diamant 2",
                           current_rank="Gold", streams_per_week=3, week_number=2))
    add("rang-reise-en", base(("Rocket League",), rank_goal="Champion", current_rank="Diamond",
                              language="en", mood="ambitious"))
    add("befehle", base(("Fortnite",), commands=["!discord", "!insta", "!discord"]))
    add("befehle-lange-namen", base(("Warhammer 40,000: Darktide – Ultimate Edition Deluxe",),
                                    commands=["!discord", "!youtube_kanal", "!merch"],
                                    first_time=True))
    add("koop-coach", base(("Valorant", "Phasmophobia"), collab_partner=True, active_chatters=12,
                           experience="advanced", goal="community", streams_per_week=4,
                           hours_per_week=14))
    add("plattform-youtube", base(("Minecraft",), platform="youtube", language="en"))
    add("sonderzeichen-namen", base(("Pokémon Legenden: Z-A", "STRASSE der Ehre",
                                     "Baldur's Gate 3"), streams_per_week=3))
    add("eszett-und-emoji", base(("Fußball Manager ⚽", "Cozy Grove"), language="de"))
    add("doppelte-spiele", base(("Minecraft", "minecraft", " Minecraft  ")))
    # casefold: „Straße“ und „STRASSE“ sind dasselbe Spiel (toLowerCase allein sähe das nicht).
    add("eszett-doppelt", base(("Straße", "STRASSE", "Fußball"), streams_per_week=2))
    # Emojis an der 140-Zeichen-Grenze: in Codepoints passen die Befehle noch (135 + Befehle),
    # in UTF-16-Einheiten (JS .length) wären es 141 – dann fielen sie fälschlich weg.
    add("emoji-grenze-befehle", base(("Fest " + "🎉" * 5 + " " + "x" * 59,),
                                     ["Mo 18-22"], commands=["!discord", "!insta"],
                                     streams_per_week=1, hours_per_week=4))
    add("emoji-grenze-befehle-2", base(("Fest " + "🎉" * 6 + " " + "x" * 58,),
                                       ["Mo 18-22", "Do 19-23"], commands=["!discord", "!insta"],
                                       streams_per_week=2, hours_per_week=8))
    add("geschweifte-klammern", base(("{n} Game {rank}",), language="en"))
    add("zahlen-als-uhrzeit", {"games": ["Valorant"], "windows": [
        {"day": 0, "start": 18, "end": 22}, {"day": "sa.", "start": "14:00", "end": 20.0}],
        "hours_per_week": "6", "streams_per_week": 2})
    add("vollbreite-ziffern", {"games": ["Minecraft"], "windows": [
        {"day": "Freitag", "start": "１８", "end": "２２:３０"}],
        "hours_per_week": 5, "streams_per_week": 1})

    # 4. Ungültige Eingaben (Meldungen wie models.py / pydantic)
    invalid = {
        "uhrzeit-zu-gross": {"windows": [{"day": "Mo", "start": 1080, "end": 22}]},
        "uhrzeit-minuten": {"windows": [{"day": "Mo", "start": "18:75", "end": "20"}]},
        "uhrzeit-bruch": {"windows": [{"day": "Mo", "start": 18.5, "end": 20}]},
        "uhrzeit-text": {"windows": [{"day": "Mo", "start": "abends", "end": "22"}]},
        "uhrzeit-25": {"windows": [{"day": "Mo", "start": "25", "end": "26"}]},
        "fenster-ohne-dauer": {"windows": [{"day": "Mo", "start": "18", "end": "18"}]},
        "beginn-24": {"windows": [{"day": "Mo", "start": "24", "end": "2"}]},
        "wochentag-unbekannt": {"windows": [{"day": "Xy", "start": "18", "end": "22"}]},
        "wochentag-zahl": {"windows": [{"day": 9, "start": "18", "end": "22"}]},
        "fenster-als-text": {"windows": ["Fr 20-23"]},
        "keine-fenster": {"windows": []},
        "spielname-zu-kurz": {"games": ["X"]},
        "keine-spiele": {"games": []},
        "zu-viele-spiele": {"games": ["A1", "B2", "C3", "D4", "E5", "F6"]},
        "befehl-ungueltig": {"commands": ["discord"]},
        "befehl-gross": {"commands": ["!Discord"]},
        "zu-viele-befehle": {"commands": ["!a", "!b", "!c", "!d"]},
        "rang-ungueltig": {"rank_goal": "Gold_3"},
        "rang-zu-lang": {"rank_goal": "Ein sehr langes Rangziel"},
        "stunden-zu-wenig": {"hours_per_week": 1},
        "stunden-zu-viel": {"hours_per_week": 61},
        "streams-null": {"streams_per_week": 0},
        "ziel-unbekannt": {"goal": "fame"},
        "sprache-unbekannt": {"language": "fr"},
        "stimmung-unbekannt": {"mood": "wütend"},
        "stunden-fehlen": {"hours_per_week": None},
    }
    for name, change in invalid.items():
        raw = base(("Valorant",))
        raw.update(change)
        if raw.get("hours_per_week", 0) is None:
            del raw["hours_per_week"]
        add(f"ungueltig-{name}", raw)
    return result


def expected(raw: dict) -> dict:
    try:
        request = StrategyRequest.model_validate(raw)
    except ValidationError as exc:
        error = exc.errors()[0]
        return {"error": {"type": "validation",
                          "loc": ".".join(str(part) for part in error["loc"]),
                          "message": error["msg"].removeprefix("Value error, ")}}
    try:
        return {"plan": build_plan(request, surface="web").model_dump(mode="json")}
    except PlanError as exc:
        return {"error": {"type": "plan", "message": str(exc)}}


CASEFOLD_SAMPLES = ["Straße", "STRASSE", "ẞ", "ΣΊΣΥΦΟΣ", "ﬁnal", "µ", "İstanbul", "Ǆemal",
                    "Ⅻ", "Café", "ŉ"]


def build() -> dict:
    items = [{"name": case["name"], "request": case["request"],
              "expected": expected(case["request"])} for case in cases()]
    return {
        "about": "Erwartete Ergebnisse aus Python für js/strategist-core.js "
                 "(neu erzeugen: python tests/strategist_parity.py in agents/).",
        "data_sha256": checksum(content()),
        "casefold": [[text, text.casefold()] for text in CASEFOLD_SAMPLES],
        "cases": items,
    }


def render() -> str:
    """Ein Fall pro Zeile: klein genug fürs Repo und trotzdem gut im Diff zu lesen."""
    data = build()
    dump = lambda value: json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    head = {key: value for key, value in data.items() if key != "cases"}
    lines = [dump(head)[:-1] + ',"cases":[']
    lines += [dump(case) + ("," if index < len(data["cases"]) - 1 else "")
              for index, case in enumerate(data["cases"])]
    return "\n".join(lines) + "\n]}\n"


if __name__ == "__main__":
    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE_PATH.write_text(render(), encoding="utf-8")
    data = build()
    plans = sum(1 for item in data["cases"] if "plan" in item["expected"])
    print(f"{FIXTURE_PATH}: {len(data['cases'])} Fälle ({plans} Pläne, "
          f"{len(data['cases']) - plans} Fehler), {FIXTURE_PATH.stat().st_size / 1024:.0f} KB")
