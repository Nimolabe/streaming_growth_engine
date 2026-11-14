"""Strongly typed V2 contracts; old /v1/demo endpoints stay backwards-compatible."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CreatorProfileV2(BaseModel):
    platform: str = Field(min_length=2, max_length=40)
    category: str = Field(min_length=2, max_length=80)
    audience: str = Field(min_length=2, max_length=120)
    language: Literal["de", "en"] = "de"
    experience: Literal["beginner", "intermediate", "advanced"] = "beginner"
    channel_size: Literal["new", "small", "established"] = "new"
    content_style: Literal["educational", "interactive", "competitive", "creative", "comedy"] = (
        "interactive"
    )
    primary_goal: Literal["consistency", "discovery", "community"] = "discovery"
    weekly_hours: int = Field(ge=2, le=40)
    count: int = Field(default=3, ge=1, le=5)
    exclude_format_ids: list[str] = Field(default_factory=list, max_length=25)

    @field_validator("platform", "category", "audience")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("The field cannot be blank.")
        return value.strip()

    @field_validator("exclude_format_ids")
    @classmethod
    def validate_exclusions(cls, values: list[str]) -> list[str]:
        if any(len(value) > 60 for value in values):
            raise ValueError("A format ID is too long.")
        return list(dict.fromkeys(values))


class RecommendationV2(BaseModel):
    format_id: str
    title: str
    rationale: str
    fit_score: int = Field(ge=0, le=100)
    score_interpretation: str
    estimated_min_hours_per_week: int
    stream_run_of_show: list[str] = Field(min_length=3, max_length=3)
    short_video_hook: str
    short_video_edit: str
    measurement: str
    evidence_links: list[str]
    limitations: str


class ContentStrategyV2(BaseModel):
    version: str = "v2.0-offline"
    prototype: bool = True
    generator: str = "curated_rules_v2"
    game_group: str
    total_formats_considered: int
    recommendations: list[RecommendationV2] = Field(min_length=1, max_length=5)
    next_step: str
    disclaimer: str
