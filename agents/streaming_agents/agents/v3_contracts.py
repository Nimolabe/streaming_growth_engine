"""Typed, offline-only contracts for Content Strategist V3.

Nothing here collects private analytics or invokes external services.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CreatorProfileV3(BaseModel):
    platform: str = Field(default="twitch", min_length=2, max_length=40)
    game: str = Field(min_length=2, max_length=80)
    audience: str = Field(min_length=2, max_length=120)
    language: Literal["de", "en"] = "de"
    experience: Literal["beginner", "intermediate", "advanced"] = "beginner"
    style: Literal["educational", "interactive", "competitive", "creative", "comedy"] = (
        "interactive"
    )
    goal: Literal["discovery", "community", "consistency"] = "discovery"
    average_viewers: int = Field(default=0, ge=0, le=1_000_000)
    active_chatters: int = Field(default=0, ge=0, le=1_000_000)
    hours_per_week: int = Field(default=8, ge=2, le=40)
    streams_per_week: int = Field(default=2, ge=1, le=7)
    ideas_requested: int = Field(default=3, ge=1, le=5)
    exclude_format_ids: list[str] = Field(default_factory=list, max_length=40)

    @field_validator("platform")
    @classmethod
    def normalize_platform(cls, value: str) -> str:
        normalized = value.strip().casefold()
        if normalized not in {"twitch", "youtube", "tiktok", "kick", "other"}:
            raise ValueError("Unsupported platform")
        return normalized

    @field_validator("game", "audience")
    @classmethod
    def reject_whitespace(cls, value: str) -> str:
        result = value.strip()
        if not result:
            raise ValueError("Field cannot be blank")
        return result

    @field_validator("exclude_format_ids")
    @classmethod
    def validate_exclusions(cls, values: list[str]) -> list[str]:
        if any(len(v) > 60 for v in values):
            raise ValueError("Invalid format ID")
        return list(dict.fromkeys(values))


class FormatRecommendationV3(BaseModel):
    format_id: str
    title: str
    reason: str
    fit_score: int = Field(ge=0, le=100)
    score_method: str
    requires_live_chat: bool
    adapted_for_solo: bool
    estimated_hours_per_week: int = Field(ge=1)
    stream_steps: list[str] = Field(min_length=3, max_length=4)
    short_video_hook: str
    short_video_structure: str
    measurement: str
    minimum_viable_test: str
    evidence_links: list[str]
    evidence_note: str


class SeriesEpisodeV3(BaseModel):
    episode: int = Field(ge=1, le=3)
    title: str
    focus: str
    expected_output: str
    check_after: str


class WorkloadV3(BaseModel):
    total_minutes: int = Field(ge=120)
    livestream_minutes: int = Field(ge=0)
    preparation_minutes: int = Field(ge=0)
    editing_minutes: int = Field(ge=0)
    review_minutes: int = Field(ge=0)


class ContentStrategyV3(BaseModel):
    version: str = "v3.0-offline"
    prototype: bool = True
    model_used: bool = False
    game_group: str
    creator_stage: str
    chat_capacity: str
    recommendations: list[FormatRecommendationV3] = Field(min_length=1, max_length=5)
    series_plan: list[SeriesEpisodeV3] = Field(min_length=3, max_length=3)
    workload: WorkloadV3
    evaluation_guide: list[str]
    limitations: list[str]
