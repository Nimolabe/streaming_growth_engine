"""Eingaben und Ausgaben des Content Strategist (Variante A: lokal, regelbasiert)."""
import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from ..category_check.models import CategorySnapshot

VERSION = "content-strategist-a1"
DAYS = ("mo", "tu", "we", "th", "fr", "sa", "su")
DAY_LABELS = {"de": ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"),
              "en": ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")}
_DAY_ALIASES = {
    "mo": 0, "mon": 0, "montag": 0, "monday": 0,
    "di": 1, "tu": 1, "tue": 1, "dienstag": 1, "tuesday": 1,
    "mi": 2, "we": 2, "wed": 2, "mittwoch": 2, "wednesday": 2,
    "do": 3, "th": 3, "thu": 3, "donnerstag": 3, "thursday": 3,
    "fr": 4, "fri": 4, "freitag": 4, "friday": 4,
    "sa": 5, "sat": 5, "samstag": 5, "saturday": 5,
    "so": 6, "su": 6, "sun": 6, "sonntag": 6, "sunday": 6,
}
_TIME_RE = re.compile(r"^(\d{1,2})(?::(\d{2}))?$")


def parse_day(value: str | int) -> int:
    if isinstance(value, int):
        if 0 <= value <= 6:
            return value
        raise ValueError("Wochentag 0–6 (0 = Montag) / weekday 0–6 (0 = Monday)")
    key = value.strip().casefold().rstrip(".")
    if key in _DAY_ALIASES:
        return _DAY_ALIASES[key]
    raise ValueError(f"Unbekannter Wochentag / unknown weekday: {value!r}")


def parse_clock(value: str | int) -> int:
    """„18“, „18:30“, „24:00“ → Minuten seit Mitternacht (0–1440)."""
    match = _TIME_RE.match(str(value).strip())
    if not match:
        raise ValueError(f"Uhrzeit als HH oder HH:MM angeben / time as HH or HH:MM: {value!r}")
    hours, minutes = int(match.group(1)), int(match.group(2) or 0)
    total = hours * 60 + minutes
    if minutes >= 60 or total > 24 * 60:
        raise ValueError(f"Ungültige Uhrzeit / invalid time: {value!r}")
    return total


class TimeWindow(BaseModel):
    """Zeitfenster an einem Wochentag in Ortszeit. Ende ≤ Beginn: geht über Mitternacht."""

    day: int = Field(description="0 = Montag … 6 = Sonntag (auch „Mo“, „Sa“, „Sunday“)")
    start: int = Field(description="Minuten seit Mitternacht (auch „18“ oder „18:30“)")
    end: int = Field(description="Minuten seit Mitternacht; kleiner als start = über Mitternacht")

    @field_validator("day", mode="before")
    @classmethod
    def _day(cls, value):
        return parse_day(value)

    @field_validator("start", "end", mode="before")
    @classmethod
    def _clock(cls, value):
        return parse_clock(value)

    @model_validator(mode="after")
    def _not_empty(self):
        if (self.end - self.start) % 1440 == 0 and not (self.start == 0 and self.end == 1440):
            raise ValueError("Zeitfenster ohne Dauer / window has no duration")
        if self.start == 1440:
            raise ValueError("Beginn 24:00 → stattdessen 0:00 am Folgetag / use 0:00 next day")
        return self

    @property
    def minutes(self) -> int:
        return (self.end - self.start) % 1440 or 1440

    @property
    def week_start(self) -> int:
        """Minute in der Woche (Mo 0:00 = 0)."""
        return self.day * 1440 + self.start

    @classmethod
    def parse(cls, text: str) -> "TimeWindow":
        """„Mo 18-22“, „Sa 14:00–20:30“, „Fr 22-2“ (über Mitternacht)."""
        parts = text.replace("–", "-").split()
        if len(parts) != 2 or "-" not in parts[1]:
            raise ValueError(f"Zeitfenster wie „Mo 18-22“ angeben / window like 'Mon 18-22': {text!r}")
        start, end = parts[1].split("-", 1)
        return cls(day=parts[0], start=start, end=end)


class StrategyRequest(BaseModel):
    games: list[str] = Field(min_length=1, max_length=5,
                             description="1–5 Spiele bzw. Twitch-Kategorien")
    windows: list[TimeWindow] = Field(min_length=1, max_length=21,
                                      description="Verfügbare Zeitfenster pro Wochentag (Ortszeit)")
    hours_per_week: int = Field(ge=2, le=60,
                                description="Gesamtzeit pro Woche inkl. Vorbereitung, Clip, Rückblick")
    streams_per_week: int = Field(ge=1, le=7)
    average_viewers: int = Field(default=0, ge=0, le=1_000_000)
    active_chatters: int = Field(default=0, ge=0, le=1_000_000)
    goal: Literal["discovery", "community", "consistency"] = "discovery"
    experience: Literal["beginner", "intermediate", "advanced"] = "beginner"
    language: Literal["de", "en"] = "de"
    platform: Literal["twitch", "youtube", "kick", "tiktok", "other"] = "twitch"
    week_number: int = Field(default=1, ge=1, le=520,
                             description="Woche der Planung; Zähler in Titeln („Tag 3“) laufen weiter")
    collab_partner: bool = Field(default=False,
                                 description="Mitspieler oder Gast verfügbar (Koop-/Coach-Formate)")
    measurements: list[CategorySnapshot] = Field(
        default_factory=list, max_length=5000,
        description="Optional: Messungen aus dem Kategorie-Check (JSONL-Zeilen)")
    utc_offset_minutes: int | None = Field(
        default=None, ge=-720, le=840,
        description="Zeitzone der Messungen; leer = Ortszeit des Rechners")

    @field_validator("games")
    @classmethod
    def _games(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            text = " ".join(value.split())
            if not 2 <= len(text) <= 80:
                raise ValueError("Spielname 2–80 Zeichen / game name 2–80 characters")
            if text.casefold() not in {item.casefold() for item in cleaned}:
                cleaned.append(text)
        return cleaned


# ------------------------------------------------------------------ Ausgabe
class GameInfo(BaseModel):
    name: str
    genre: str | None
    genre_label: str
    genre_recognized: bool
    category_check: str | None = None


class Session(BaseModel):
    day: int
    label: str
    start: str
    end: str
    minutes: int


class StreamPlan(BaseModel):
    number: int
    stream: Session
    game: str
    genre_label: str
    format_id: str
    format_name: str
    needs_chat: Literal["none", "low", "active"]
    needs_collab: bool
    title: str
    title_alternatives: list[str]
    tags: list[str]
    run_of_show: list[str]
    break_note: str | None
    preparation: Session
    prep_steps: list[str]
    hook: str
    clip_idea: str
    clip_day: str
    measurement: str
    why: str
    timing_reason: str


class SeriesPlan(BaseModel):
    format_name: str
    game: str
    episodes: list[str]


class Budget(BaseModel):
    weekly_minutes: int
    stream_minutes: int
    preparation_minutes: int
    clip_minutes: int
    review_minutes: int
    unplanned_minutes: int


class WeeklyReview(BaseModel):
    day: str
    minutes: int
    questions: list[str]


class ContentPlan(BaseModel):
    version: str = VERSION
    prototype: bool = True
    model_used: bool = False
    language: Literal["de", "en"]
    platform: str
    chat_level: Literal["none", "low", "active"]
    timing_source: Literal["measurements", "windows_only"]
    games: list[GameInfo]
    streams: list[StreamPlan]
    review: WeeklyReview
    series: SeriesPlan | None
    budget: Budget
    twitch_limits: str
    notes: list[str]
    limitations: list[str]
