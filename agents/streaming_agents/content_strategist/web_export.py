"""Export der Inhalte des Content Strategist für die Website (``data/content-strategist.json``).

Entscheidung des Nutzers („Weg A“): Der Planer läuft als JavaScript im Browser
(``js/strategist-core.js``), die INHALTE kommen aus Python. Inhalte werden nur hier in Python
gepflegt; danach ``python -m streaming_agents.content_strategist export-web`` ausführen und die
Paritäts-Fixtures neu erzeugen (``python tests/strategist_parity.py`` in ``agents/``).

Enthalten: Genres mit Aliassen, alle Formate, alle Titel (inkl. Stimmungs- und Rang-Titel),
Emoji-Regeln, Twitch-Grenzen, Eingabe-Regeln, Planer-Konstanten und die Glücksspiel-Liste
(Fallstrick 15: Glücksspiel wird nie geplant). NICHT enthalten: der Kategorie-Check – er braucht
das Twitch-Secret und darf nie im Browser laufen.

Die Datei ist deterministisch (sortierte Schlüssel wo die Reihenfolge egal ist, feste
Reihenfolge wo sie zählt) und trägt eine SHA-256-Prüfsumme über den Inhalt.
"""
import hashlib
import json
from pathlib import Path

from ..category_check.aliases import CATEGORY_ALIASES
from ..category_check.gambling import GAMBLING_NAMES, rejection
from . import planner
from .formats import FORMATS
from .genres import _ALIAS_TABLE, GAME_ALIASES, GENRE_LABELS, UNKNOWN_LABEL
from .models import _DAY_ALIASES, CLOCK_HELP, DAY_LABELS, VERSION
from .titles import (
    CLIP_TITLES,
    COMMAND_RE,
    DAYPARTS,
    FILLS,
    GENRE_MOOD,
    MAX_COMMANDS,
    MOOD_TITLES,
    RANK_GOAL,
    RANK_JOURNEY,
    RANKED_GENRES,
    RANKED_GOAL_MOOD,
    RANKED_MOOD,
    SEPARATOR,
    STREAM_TITLES,
    TITLE_TARGET_CHARS,
)
from .twitch_limits import SOURCE_DATE, SOURCE_URL, TAG_MAX_CHARS, TAGS_MAX_COUNT, TITLE_MAX_CHARS

EXPORT_FORMAT = 1
DEFAULT_PATH = Path("data") / "content-strategist.json"
# Schlüssel für „kein Genre erkannt“ (in Python ``None``), weil JSON-Schlüssel Texte sind.
GENERAL = "_general"


def _key(genre: str | None) -> str:
    return GENERAL if genre is None else genre


def _pair(text: tuple[str, str] | None) -> list[str] | None:
    return None if text is None else [text[0], text[1]]


def _formats() -> list[dict]:
    return [{
        "id": item.id, "genre": item.genre, "needs_chat": item.needs_chat,
        "goals": list(item.goals), "name": _pair(item.name),
        "steps": [_pair(step) for step in item.steps],
        "prep": [_pair(step) for step in item.prep],
        "hook": _pair(item.hook), "clip": _pair(item.clip), "metric": _pair(item.metric),
        "tags": [_pair(tag) for tag in item.tags], "needs_collab": item.needs_collab,
        "expert": item.expert, "series": [_pair(step) for step in item.series],
        "week_end": item.week_end, "first_time_only": item.first_time_only,
        "needs_history": item.needs_history,
    } for item in FORMATS]  # Katalogreihenfolge zählt (Rangliste bei gleicher Punktzahl)


def content() -> dict:
    """Alles, was ``js/strategist-core.js`` braucht – ohne Prüfsumme."""
    return {
        "format": EXPORT_FORMAT,
        "version": VERSION,
        "genres": {
            "labels": {genre: _pair(pair) for genre, pair in GENRE_LABELS.items()},
            "unknown_label": _pair(UNKNOWN_LABEL),
            "aliases": {genre: list(aliases) for genre, aliases in GAME_ALIASES.items()},
            # Fertig normalisiert und sortiert (längster Alias zuerst) – so muss JavaScript
            # weder normalisieren noch sortieren, und die Reihenfolge ist garantiert gleich.
            "alias_table": [[alias, genre] for alias, genre in _ALIAS_TABLE],
        },
        "formats": _formats(),
        "titles": {
            "separator": SEPARATOR,
            "target_chars": TITLE_TARGET_CHARS,
            "max_commands": MAX_COMMANDS,
            "command_pattern": COMMAND_RE.pattern,
            "genre_mood": {_key(genre): mood for genre, mood in GENRE_MOOD.items()},
            "ranked_genres": sorted(RANKED_GENRES),
            "dayparts": [list(part) for part in DAYPARTS],
            "mood_titles": {_key(genre): {mood: _pair(text) for mood, text in moods.items()}
                            for genre, moods in MOOD_TITLES.items()},
            "ranked_mood": _pair(RANKED_MOOD),
            "ranked_goal_mood": _pair(RANKED_GOAL_MOOD),
            "rank_goal": _pair(RANK_GOAL),
            "rank_journey": _pair(RANK_JOURNEY),
            "fills": {fid: {key: _pair(text) for key, text in fills.items()}
                      for fid, fills in FILLS.items()},
            "stream_titles": {fid: {"goal": _pair(item.goal), "invite": _pair(item.invite),
                                    "first": _pair(item.first), "ranked": item.ranked,
                                    "mood": item.mood}
                              for fid, item in STREAM_TITLES.items()},
            "clip_titles": {fid: [_pair(text) for text in pair]
                            for fid, pair in CLIP_TITLES.items()},
        },
        "emoji": {
            "rule": "Genau ein Emoji am Anfang jedes Titels; es steht im Text selbst.",
            "unicode_categories": ["So", "Sk", "Mn", "Cf"],
            "extra_codepoints": ["️"],
        },
        "twitch_limits": {
            "title_max_chars": TITLE_MAX_CHARS, "tags_max_count": TAGS_MAX_COUNT,
            "tag_max_chars": TAG_MAX_CHARS, "source_url": SOURCE_URL, "source_date": SOURCE_DATE,
        },
        "input": {
            "day_labels": {lang: list(labels) for lang, labels in DAY_LABELS.items()},
            "day_aliases": dict(sorted(_DAY_ALIASES.items())),
            "clock_help": CLOCK_HELP,
        },
        "planner": {
            "prep_minutes": planner.PREP_MINUTES, "min_prep_minutes": planner.MIN_PREP_MINUTES,
            "prep_gap": planner.PREP_GAP, "clip_minutes": planner.CLIP_MINUTES,
            "review_minutes": planner.REVIEW_MINUTES, "min_stream": planner.MIN_STREAM,
            "max_stream": planner.MAX_STREAM, "step": planner.STEP,
            "chat_order": planner.CHAT_ORDER,
            "genre_tag": {genre: _pair(pair) for genre, pair in planner.GENRE_TAG.items()},
            "goal_label": {goal: _pair(pair) for goal, pair in planner.GOAL_LABEL.items()},
            "no_measurements_note": _pair(planner.WEB_NO_MEASUREMENTS),
        },
        # Fallstrick 15: Glücksspiel wird nie geplant. Namen in normalisierter Form
        # (``category_check.aliases.normalize``), dazu die Kurzformen des Kategorie-Checks,
        # damit eine Kurzform auf eine Glücksspiel-Kategorie ebenso abgelehnt wird.
        "gambling": {
            "names": sorted(GAMBLING_NAMES),
            "rejection": {lang: rejection("{name}", lang) for lang in ("de", "en")},
        },
        "category_aliases": dict(sorted(CATEGORY_ALIASES.items())),
    }


def checksum(data: dict) -> str:
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def export() -> dict:
    data = content()
    return {"sha256": checksum(data), **data}


def render() -> str:
    """Der Dateiinhalt: kompaktes JSON (eine Zeile pro Hauptschlüssel wäre kaum lesbarer)."""
    return json.dumps(export(), ensure_ascii=False, separators=(",", ":")) + "\n"


def write(path: str | Path) -> Path:
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(), encoding="utf-8")
    return target
