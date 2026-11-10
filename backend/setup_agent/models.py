"""Datenmodelle A–F des Setup Intelligence Agent (Pydantic v2).

Beschreibung der Felder: docs/setup-agent/DATENMODELL.md
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, computed_field, field_validator, model_validator

from . import identity

# Kleine Toleranz für Uhrabweichungen zwischen Rechnern
_CLOCK_SKEW = timedelta(minutes=5)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware_past(value: datetime | None, field: str) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        raise ValueError(f"{field}: Zeitstempel braucht eine Zeitzone.")
    value = value.astimezone(timezone.utc)
    if value > utcnow() + _CLOCK_SKEW:
        raise ValueError(f"{field}: Zeitpunkt liegt in der Zukunft.")
    return value


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, validate_assignment=True)

    @model_validator(mode="before")
    @classmethod
    def _drop_computed(cls, data: Any) -> Any:
        """Gespeicherte Daten enthalten abgeleitete Felder (id, slot, match_key, …) für Abfragen.
        Beim Einlesen werden sie verworfen und neu berechnet, damit sie nie veraltet sein können."""
        if isinstance(data, dict):
            computed = cls.model_computed_fields
            if computed and any(k in data for k in computed):
                data = {k: v for k, v in data.items() if k not in computed}
        return data


# ---------------------------------------------------------------- Aufzählungen


class Platform(StrEnum):
    TWITCH = "twitch"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    KICK = "kick"
    OTHER = "other"


class StreamCategory(StrEnum):
    GAMING = "gaming"
    CHATTING = "chatting"
    IRL = "irl"
    MUSIC = "music"
    CREATIVE = "creative"


class ProductCategory(StrEnum):
    MIKROFON = "mikrofon"
    MIKROFONARM = "mikrofonarm"
    AUDIO_INTERFACE = "audio_interface"
    KAMERA = "kamera"
    OBJEKTIV = "objektiv"
    LICHT = "licht"
    HEADSET = "headset"
    MAUS = "maus"
    TASTATUR = "tastatur"
    BILDSCHIRM = "bildschirm"
    CPU = "cpu"
    GPU = "gpu"
    RAM = "ram"
    MAINBOARD = "mainboard"
    PC = "pc"
    CAPTURE = "capture"
    STREAMDECK = "streamdeck"
    GREENSCREEN = "greenscreen"
    STUHL = "stuhl"
    SCHREIBTISCH = "schreibtisch"
    ZUBEHOER = "zubehoer"
    SOFTWARE_STREAMING = "software_streaming"
    SOFTWARE_AUDIO = "software_audio"
    SOFTWARE_PLUGIN = "software_plugin"
    SONSTIGES = "sonstiges"


class SourceType(StrEnum):
    OFFICIAL_STATEMENT = "official_statement"
    OWN_SETUP_PAGE = "own_setup_page"
    VIDEO_STATEMENT = "video_statement"
    MANUFACTURER = "manufacturer"
    VIDEO_VISUAL = "video_visual"
    THIRD_PARTY = "third_party"


PRIMARY_SOURCE_TYPES = frozenset(
    {SourceType.OFFICIAL_STATEMENT, SourceType.OWN_SETUP_PAGE, SourceType.VIDEO_STATEMENT, SourceType.MANUFACTURER}
)


class VerificationStatus(StrEnum):
    CONFIRMED = "confirmed"
    PROBABLE = "probable"
    OUTDATED = "outdated"
    CONFLICTING = "conflicting"
    UNKNOWN = "unknown"


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class Availability(StrEnum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"
    UNKNOWN = "unknown"


class AccessMethod(StrEnum):
    MANUAL = "manual"
    OFFICIAL_API = "official_api"
    RSS = "rss"
    HTTP_ALLOWED = "http_allowed"


class ProposalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class Operation(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    RETIRE = "retire"


class AuditAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    RETIRE = "retire"
    APPROVE = "approve"
    REJECT = "reject"
    CHECK_FAILED = "check_failed"


class ActorType(StrEnum):
    ADMIN = "admin"
    AGENT = "agent"
    SYSTEM = "system"


# ---------------------------------------------------------------- Bausteine


class Actor(_Model):
    type: ActorType
    id: str = Field(min_length=1, max_length=128)


class Money(_Model):
    amount_minor: int = Field(ge=0, description="Betrag in kleinster Einheit (Cent)")
    currency: str = Field(pattern=r"^[A-Z]{3}$", description="ISO 4217, z. B. EUR")


class _Versioned(_Model):
    version: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @field_validator("created_at", "updated_at")
    @classmethod
    def _check_times(cls, v: datetime, info: Any) -> datetime:
        return _aware_past(v, info.field_name)


# ---------------------------------------------------------------- A. Streamer und Setup


class PlatformAccount(_Model):
    platform: Platform
    handle: str = Field(min_length=1, max_length=64)
    url: HttpUrl


class Streamer(_Versioned):
    id: str = Field(pattern=r"^[a-z]+-[a-z0-9-]+$")
    display_name: str = Field(min_length=1, max_length=60)
    platforms: list[PlatformAccount] = Field(min_length=1)
    primary_language: str | None = Field(default=None, pattern=r"^[a-z]{2}$")
    categories: list[StreamCategory] = Field(min_length=1)
    profile_links: list[HttpUrl] = Field(default_factory=list)
    active: bool = True

    @staticmethod
    def make_id(platform: Platform, handle: str) -> str:
        return f"{platform.value}-{identity.slugify(handle)}"


class Evidence(_Model):
    source_url: HttpUrl
    source_type: SourceType
    observed_at: datetime
    retrieved_at: datetime
    media_timestamp: str | None = Field(default=None, pattern=r"^\d{1,2}:\d{2}(:\d{2})?$")
    note: str | None = Field(default=None, max_length=280)

    @field_validator("observed_at", "retrieved_at")
    @classmethod
    def _check_times(cls, v: datetime, info: Any) -> datetime:
        return _aware_past(v, info.field_name)

    @model_validator(mode="after")
    def _retrieved_after_observed(self) -> Evidence:
        if self.retrieved_at < self.observed_at:
            raise ValueError("retrieved_at darf nicht vor observed_at liegen.")
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def source_id(self) -> str:
        return identity.source_id(str(self.source_url))

    @property
    def domain(self) -> str:
        return identity.url_domain(str(self.source_url))

    @property
    def is_primary(self) -> bool:
        return self.source_type in PRIMARY_SOURCE_TYPES


class SetupClaim(_Versioned):
    streamer_id: str = Field(min_length=1)
    category: ProductCategory
    role: str = Field(default="primary", pattern=r"^[a-z][a-z0-9_]{0,31}$")
    product_id: str | None = None
    raw_name: str = Field(min_length=1, max_length=200)
    evidence: list[Evidence] = Field(min_length=1, description="Ohne Beleg keine Angabe")
    status: VerificationStatus = VerificationStatus.UNKNOWN
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel = ConfidenceLevel.NONE
    reason: str = Field(default="Noch nicht bewertet.", min_length=1)
    last_verified_at: datetime | None = None
    published: bool = False

    @field_validator("last_verified_at")
    @classmethod
    def _check_verified(cls, v: datetime | None) -> datetime | None:
        return _aware_past(v, "last_verified_at")

    @model_validator(mode="after")
    def _unique_sources(self) -> SetupClaim:
        ids = [e.source_id for e in self.evidence]
        if len(ids) != len(set(ids)):
            raise ValueError("Dieselbe Quelle ist mehrfach als Beleg eingetragen.")
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def slot(self) -> str:
        return f"{self.category.value}:{self.role}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def id(self) -> str:
        return identity.claim_id(self.streamer_id, self.slot, self.product_id, self.raw_name)


# ---------------------------------------------------------------- B. Produktkatalog


class Product(_Versioned):
    manufacturer: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=120)
    category: ProductCategory
    variant: str | None = Field(default=None, max_length=80)
    aliases: list[str] = Field(default_factory=list)
    gtin: str | None = None
    specs: dict[str, str | int | float | bool] = Field(default_factory=dict)
    discontinued: bool | None = None

    @field_validator("gtin")
    @classmethod
    def _check_gtin(cls, v: str | None) -> str | None:
        if v is not None and not identity.gtin_is_valid(v):
            raise ValueError("GTIN/EAN ist ungültig (Prüfziffer).")
        return v

    @computed_field  # type: ignore[prop-decorator]
    @property
    def id(self) -> str:
        return identity.product_id(self.manufacturer, self.model)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def match_key(self) -> str:
        return identity.product_match_key(self.manufacturer, self.model)


# ---------------------------------------------------------------- C. Preis- und Händlerdaten


class Offer(_Versioned):
    product_id: str = Field(min_length=1)
    retailer: str = Field(min_length=1, max_length=80)
    url: HttpUrl
    price: Money | None = None
    availability: Availability = Availability.UNKNOWN
    checked_at: datetime | None = None
    last_success_at: datetime | None = None
    failed_checks: int = Field(default=0, ge=0)
    price_source: str = Field(default="manual", min_length=1)

    @field_validator("checked_at", "last_success_at")
    @classmethod
    def _check_times(cls, v: datetime | None, info: Any) -> datetime | None:
        return _aware_past(v, info.field_name)

    @field_validator("url")
    @classmethod
    def _https_only(cls, v: HttpUrl) -> HttpUrl:
        if v.scheme != "https":
            raise ValueError("Händler-Links müssen https verwenden.")
        return v

    @computed_field  # type: ignore[prop-decorator]
    @property
    def id(self) -> str:
        return identity.offer_id(self.product_id, self.retailer, str(self.url))


class PriceObservation(_Model):
    offer_id: str
    price: Money | None
    availability: Availability
    observed_at: datetime
    price_source: str = "manual"

    @field_validator("observed_at")
    @classmethod
    def _check_time(cls, v: datetime) -> datetime:
        return _aware_past(v, "observed_at")


# ---------------------------------------------------------------- D. Quellen


class Source(_Versioned):
    url: HttpUrl
    source_type: SourceType
    streamer_id: str | None = None  # bei eigenen Seiten/Kanälen eines Streamers
    registry_id: str | None = None
    title: str | None = Field(default=None, max_length=200)
    first_seen_at: datetime = Field(default_factory=utcnow)
    last_checked_at: datetime | None = None
    last_check_ok: bool | None = None
    content_hash: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def id(self) -> str:
        return identity.source_id(str(self.url))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def domain(self) -> str:
        return identity.url_domain(str(self.url))


class SourceRegistryEntry(_Versioned):
    domain: str = Field(pattern=r"^[a-z0-9.-]+\.[a-z]{2,}$")
    source_types: list[SourceType] = Field(min_length=1)
    access_method: AccessMethod = AccessMethod.MANUAL
    auto_fetch_allowed: bool = False
    terms_url: HttpUrl | None = None
    terms_reviewed_at: datetime | None = None
    min_interval_hours: int = Field(default=168, ge=1)
    notes: str | None = Field(default=None, max_length=500)
    enabled: bool = True

    @model_validator(mode="after")
    def _auto_fetch_needs_review(self) -> SourceRegistryEntry:
        if self.auto_fetch_allowed and (self.access_method == AccessMethod.MANUAL or self.terms_reviewed_at is None):
            raise ValueError("Automatischer Abruf nur mit geprüften Nutzungsbedingungen und technischer Zugriffsart.")
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def id(self) -> str:
        return "r_" + identity.slugify(self.domain)


# ---------------------------------------------------------------- E. Änderungshistorie


class AuditEntry(_Model):
    at: datetime = Field(default_factory=utcnow)
    actor: Actor
    action: AuditAction
    entity_type: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    from_version: int | None = Field(default=None, ge=1)
    to_version: int | None = Field(default=None, ge=1)
    # {feld: {"from": alt, "to": neu}} – keine verschachtelten Listen, die Firestore nicht speichern kann
    changes: dict[str, dict[str, Any]] = Field(default_factory=dict)
    reason: str = Field(min_length=3)
    proposal_id: str | None = None

    model_config = ConfigDict(extra="forbid", frozen=True)


# ---------------------------------------------------------------- F. Freigabe


_FINAL = {ProposalStatus.APPROVED, ProposalStatus.REJECTED, ProposalStatus.SUPERSEDED}


class InvalidTransition(ValueError):
    pass


class ChangeProposal(_Model):
    # Vorschläge des Agenten bekommen eine ID aus dem dedupe_key (keine Duplikate bei Wiederholung).
    # Vorschläge aus der Admin-Seite behalten die ID ihres Firestore-Dokuments.
    id: str = Field(default="", max_length=128)
    entity_type: Literal["streamer", "setup_claim", "product", "offer", "source", "source_registry"]
    entity_id: str = Field(min_length=1)
    operation: Operation
    payload: dict[str, Any] = Field(default_factory=dict)
    base_version: int | None = Field(default=None, ge=1)
    reason: str = Field(min_length=3)
    evidence_source_ids: list[str] = Field(default_factory=list)
    origin: str = Field(min_length=1)
    created_by: Actor
    created_at: datetime = Field(default_factory=utcnow)
    status: ProposalStatus = ProposalStatus.PENDING
    decided_by: Actor | None = None
    decided_at: datetime | None = None
    decision_note: str | None = Field(default=None, max_length=500)
    applied_at: datetime | None = None
    apply_error: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _default_id(self) -> ChangeProposal:
        if not self.id:
            object.__setattr__(self, "id", "p_" + self.dedupe_key)
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def dedupe_key(self) -> str:
        # base_version gehört dazu: Ist ein Datensatz inzwischen geändert, ist derselbe Vorschlag eine neue Entscheidung.
        return identity.dedupe_key(self.entity_type, self.entity_id, self.operation.value, {"payload": self.payload, "base_version": self.base_version})

    def decide(self, status: ProposalStatus, by: Actor, at: datetime, note: str | None = None) -> ChangeProposal:
        """Gibt eine entschiedene Kopie zurück. Nur Admins dürfen freigeben oder ablehnen."""
        if self.status in _FINAL:
            raise InvalidTransition(f"Vorschlag ist bereits {self.status.value}.")
        if status == ProposalStatus.PENDING:
            raise InvalidTransition("Zurück auf 'pending' ist nicht erlaubt.")
        if status in (ProposalStatus.APPROVED, ProposalStatus.REJECTED) and by.type != ActorType.ADMIN:
            raise InvalidTransition("Nur ein Admin darf Vorschläge freigeben oder ablehnen.")
        if status == ProposalStatus.REJECTED and not (note and note.strip()):
            raise InvalidTransition("Eine Ablehnung braucht eine Begründung.")
        return self.model_copy(update={"status": status, "decided_by": by, "decided_at": at, "decision_note": note})
