"""Datenmodelle des Kategorie-Checks.

Gespeichert werden nur Zuschauerzahlen der live gesendeten Kanäle einer Kategorie –
keine Kanalnamen, Titel oder Nutzerdaten.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SNAPSHOT_FORMAT = "sge-category-snapshot"
MAX_VIEWERS_PER_SNAPSHOT = 2000
Verdict = Literal["good", "ok", "hard", "low_demand"]


class CategorySnapshot(BaseModel):
    """Eine Messung: Zuschauerzahlen aller Live-Kanäle einer Kategorie in einer Sprache."""

    model_config = ConfigDict(extra="ignore")

    format: Literal["sge-category-snapshot"] = SNAPSHOT_FORMAT
    version: Literal[1] = 1
    taken_at: float = Field(gt=1_500_000_000, description="Zeitpunkt der Messung, Unix-Sekunden (UTC)")
    category_id: str = Field(pattern=r"^\d{1,20}$")
    category: str = Field(min_length=1, max_length=120)
    alias: str | None = Field(default=None, max_length=120,
                              description="Eingegebene Schreibweise, z. B. „CS2“ für Counter-Strike")
    language: str = Field(pattern=r"^([a-z]{2}|any)$", description="ISO-639-1 oder 'any'")
    complete: bool = Field(description="False: Seitenlimit erreicht, es gibt noch mehr Kanäle")
    viewers: list[int] = Field(default_factory=list, max_length=MAX_VIEWERS_PER_SNAPSHOT)

    @field_validator("viewers")
    @classmethod
    def _sorted(cls, values: list[int]) -> list[int]:
        if any(value < 0 or value > 10_000_000 for value in values):
            raise ValueError("viewer counts must be between 0 and 10,000,000")
        return sorted(values, reverse=True)

    @field_validator("category")
    @classmethod
    def _strip(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("category must not be blank")
        return value

    @field_validator("alias")
    @classmethod
    def _strip_alias(cls, value: str | None) -> str | None:
        value = " ".join(value.split()) if value else ""
        return value or None

    @property
    def channels(self) -> int:
        return len(self.viewers)


class SlotInfo(BaseModel):
    weekday: int = Field(ge=0, le=6, description="0 = Montag")
    hour: int = Field(ge=0, le=22, description="Beginn des Zwei-Stunden-Blocks (Ortszeit)")
    label: str
    measurements: int = Field(ge=1)
    median_rank: int = Field(ge=1)
    rank_is_lower_bound: bool
    median_total_viewers: int = Field(ge=0)


class CategorySummary(BaseModel):
    category: str
    category_id: str
    language: str
    measurements: int = Field(ge=1)
    median_channels: int = Field(ge=0)
    channels_is_lower_bound: bool
    median_total_viewers: int = Field(ge=0)
    median_viewers_per_channel: float = Field(ge=0)
    top3_share: float = Field(ge=0, le=1, description="Anteil der drei größten Kanäle an allen Zuschauern")
    median_rank: int = Field(ge=1, description="Platz im Verzeichnis mit deinen Zuschauern")
    rank_is_lower_bound: bool
    verdict: Verdict
    verdict_text: str
    best_slots: list[SlotInfo] = Field(default_factory=list, max_length=3)
    aliases: list[str] = Field(default_factory=list,
                               description="Schreibweisen, unter denen gemessen wurde, z. B. CS2")
    gambling: bool = Field(default=False, description="Glücksspiel-Kategorie (wird nicht empfohlen)")


class CategoryCheckResult(BaseModel):
    version: Literal["category-check-v1"] = "category-check-v1"
    own_viewers: int
    language: Literal["de", "en"]
    measurements: int = Field(ge=0)
    categories: list[CategorySummary]
    notes: list[str]


class CategoryCheckRequest(BaseModel):
    """API: gespeicherte Messungen auswerten (die API selbst fragt Twitch nicht an)."""

    snapshots: list[CategorySnapshot] = Field(min_length=1, max_length=500)
    own_viewers: int = Field(default=2, ge=0, le=100_000)
    utc_offset_minutes: int = Field(default=60, ge=-720, le=840,
                                    description="Für die Zeitfenster, z. B. 60 = MEZ, 120 = MESZ")
    language: Literal["de", "en"] = "de"
    window: str | None = Field(default=None, pattern=r"^\d{1,2}-\d{1,2}$",
                               description="Uhrzeiten für „beste Zeiten“, z. B. 16-24")
    include_gambling: bool = Field(default=False,
                                   description="Glücksspiel-Kategorien (Slots, Casino …) zeigen")

    @model_validator(mode="after")
    def _limit_total(self):
        if sum(len(item.viewers) for item in self.snapshots) > 200_000:
            raise ValueError("too many viewer values in total (max 200,000)")
        return self
