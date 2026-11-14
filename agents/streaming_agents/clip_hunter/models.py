"""Datenmodelle des Clip Hunter (Chat + Audio).

Zeiten im Chat-Mitschnitt sind Unix-Sekunden (Server-Zeit von Twitch).
Alle Zeiten in Ergebnissen sind Sekunden ab VOD-Beginn.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CHAT_LOG_FORMAT = "sge-chat-log"
CHAT_LOG_VERSION = 1
MAX_CHAT_MESSAGES = 2_000_000

EventKind = Literal["message", "cheer", "sub", "gift", "raid", "announcement", "event"]
Category = Literal["funny", "hype", "shock", "fail", "tension", "loud", "reaction"]
ChatLevel = Literal["none", "low", "active"]
Language = Literal["de", "en"]


class ChatMessage(BaseModel):
    """Eine Chat-Zeile ohne Klarnamen: `user` ist ein Pseudonym, nur pro Mitschnitt gültig."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    ts: float = Field(gt=0, description="Unix-Zeit in Sekunden")
    user: str = Field(min_length=1, max_length=64)
    text: str = Field(default="", max_length=600)
    kind: EventKind = "message"
    bot: bool = False
    mod: bool = False
    broadcaster: bool = False
    subscriber: bool = False


class ChatLogHeader(BaseModel):
    model_config = ConfigDict(extra="ignore")

    format: Literal["sge-chat-log"] = CHAT_LOG_FORMAT
    version: Literal[1] = CHAT_LOG_VERSION
    channel: str = Field(min_length=1, max_length=40)
    started_at: float = Field(gt=0, description="Beginn des Mitschnitts, Unix-Sekunden")
    source: str = Field(default="twitch-irc", max_length=40)


class ChatLog(BaseModel):
    header: ChatLogHeader
    messages: list[ChatMessage] = Field(default_factory=list, max_length=MAX_CHAT_MESSAGES)
    skipped_lines: int = Field(default=0, ge=0)


class HuntSettings(BaseModel):
    """Einstellungen; Standardwerte sind Startpunkte und mit echten Streams zu kalibrieren."""

    language: Language = "de"
    max_candidates: int = Field(default=15, ge=1, le=50)
    pre_roll_seconds: float = Field(default=20, ge=3, le=60)
    post_roll_seconds: float = Field(default=10, ge=2, le=30)
    min_clip_seconds: float = Field(default=12, ge=5, le=60)
    max_clip_seconds: float = Field(default=60, ge=10, le=180)
    # Chat
    chat_window_seconds: int = Field(default=8, ge=3, le=30)
    chat_baseline_seconds: int = Field(default=300, ge=60, le=1800)
    chat_min_z: float = Field(default=3.0, ge=1.0, le=20)
    chat_min_chatters: int = Field(default=4, ge=2, le=200)
    chat_reaction_lag_seconds: float = Field(default=5, ge=0, le=20)
    chat_offset_seconds: float = Field(default=0, ge=-600, le=600)
    chat_min_gap_seconds: int = Field(default=25, ge=5, le=300)
    # Audio
    audio_frame_seconds: float = Field(default=0.5, ge=0.1, le=2)
    audio_baseline_seconds: float = Field(default=30, ge=5, le=300)
    audio_min_rise_db: float = Field(default=9, ge=3, le=40)
    audio_min_level_db: float = Field(default=-35, ge=-80, le=0)
    audio_min_gap_seconds: float = Field(default=20, ge=2, le=300)
    # Zusammenführung
    match_tolerance_seconds: float = Field(default=12, ge=1, le=60)

    @model_validator(mode="after")
    def _check(self):
        if self.min_clip_seconds > self.max_clip_seconds:
            raise ValueError("min_clip_seconds must not exceed max_clip_seconds")
        return self


class ChatMoment(BaseModel):
    """Ein Ausschlag im Chat. Zeiten in Sekunden ab VOD-Beginn."""

    event_seconds: float = Field(description="Geschätzter Zeitpunkt des Ereignisses")
    onset_seconds: float = Field(description="Beginn des Chat-Ausschlags")
    peak_seconds: float
    z_score: float = Field(ge=0)
    chatters: int = Field(ge=0, description="Verschiedene Chatter im Spitzenfenster")
    baseline_chatters: float = Field(ge=0)
    reaction_share: float = Field(ge=0, le=1)
    categories: dict[str, int] = Field(default_factory=dict)
    dominant_category: Category = "reaction"
    alert_nearby: str | None = None
    alert_share: float = Field(default=0, ge=0, le=1)
    sample_messages: list[str] = Field(default_factory=list, max_length=5)


class AudioSpike(BaseModel):
    peak_seconds: float = Field(ge=0)
    onset_seconds: float = Field(ge=0)
    rise_db: float = Field(ge=0)
    level_db: float


class ChatStats(BaseModel):
    level: ChatLevel
    messages_used: int = Field(ge=0)
    messages_ignored: int = Field(ge=0)
    events: dict[str, int] = Field(default_factory=dict)
    median_chatters_per_minute: float = Field(ge=0)


class ChatEvidence(BaseModel):
    z_score: float
    chatters: int
    baseline_chatters: float
    reaction_share: float
    categories: dict[str, int]
    alert_nearby: str | None = None
    sample_messages: list[str] = Field(default_factory=list)


class AudioEvidence(BaseModel):
    rise_db: float
    level_db: float


class ClipCandidate(BaseModel):
    rank: int = Field(ge=1)
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    anchor_seconds: float = Field(ge=0, description="Geschätzter Höhepunkt")
    score: int = Field(ge=0, le=100)
    confidence: Literal["high", "medium", "low"]
    category: Category
    signals: list[Literal["chat", "audio"]]
    chat: ChatEvidence | None = None
    audio: AudioEvidence | None = None
    reasons: list[str]
    vod_link: str | None = None
    needs_human_review: Literal[True] = True


class HuntResult(BaseModel):
    version: Literal["clip-hunter-v4"] = "clip-hunter-v4"
    language: Language
    duration_seconds: float | None = None
    mode: Literal["chat+audio", "chat", "audio"]
    chat: ChatStats | None = None
    audio_spikes_found: int = Field(default=0, ge=0)
    chat_moments_found: int = Field(default=0, ge=0)
    alignment_note: str | None = None
    candidates: list[ClipCandidate]
    limitations: list[str]


class ChatHuntRequest(BaseModel):
    """API-Anfrage: Chat-Mitschnitt auswerten (ohne Video-Upload)."""

    chat_log: ChatLog
    vod_start: float | None = Field(default=None, gt=0,
                                    description="VOD-Start als Unix-Zeit; sonst Mitschnitt-Beginn")
    twitch_video_id: str | None = Field(default=None, pattern=r"^\d{5,15}$")
    settings: HuntSettings = Field(default_factory=HuntSettings)
