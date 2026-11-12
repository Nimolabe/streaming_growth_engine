"""Validated, creator-supplied weekly analytics. No automatic account access."""
from datetime import date
from itertools import pairwise
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class WeeklyMetrics(BaseModel):
    week_start: date
    stream_minutes: int = Field(ge=0, le=10080)
    average_viewers: float | None = Field(default=None, ge=0, le=1_000_000, allow_inf_nan=False)
    unique_viewers: int | None = Field(default=None, ge=0, le=50_000_000)
    follows: int | None = Field(default=None, ge=0, le=10_000_000)
    returning_viewers: int | None = Field(default=None, ge=0, le=50_000_000)
    clips_published: int | None = Field(default=None, ge=0, le=1000)
    clip_views: int | None = Field(default=None, ge=0, le=1_000_000_000)

    @model_validator(mode="after")
    def check_consistency(self):
        if self.stream_minutes == 0 and self.average_viewers is not None:
            raise ValueError("Average viewers without any stream minutes is undefined")
        if (self.returning_viewers is not None and self.unique_viewers is not None
                and self.returning_viewers > self.unique_viewers):
            raise ValueError("Returning viewers cannot exceed unique viewers")
        return self


class CreatorIntelligenceRequest(BaseModel):
    platform: Literal["twitch", "youtube", "kick", "other"] = "twitch"
    channel_category: str = Field(default="gaming", min_length=2, max_length=80)
    primary_goal: Literal["discovery", "retention", "consistency"] = "discovery"
    weekly_hours_available: float = Field(ge=1, le=80, allow_inf_nan=False)
    weeks: list[WeeklyMetrics] = Field(min_length=4, max_length=26)

    @model_validator(mode="after")
    def ensure_weekly_series(self):
        dates = [week.week_start for week in self.weeks]
        if dates != sorted(set(dates)):
            raise ValueError("Weeks must have unique, ascending dates")
        if any((right - left).days != 7 for left, right in pairwise(dates)):
            raise ValueError("Provide consecutive weekly periods, exactly seven days apart")
        return self


class MetricComparison(BaseModel):
    metric: str
    earlier: float | None
    recent: float | None
    change_percent: float | None
    direction: Literal["up", "down", "flat", "unavailable"]
    note: str


class CreatorInsight(BaseModel):
    code: str
    priority: Literal["high", "medium", "low"]
    observation: str
    interpretation: str
    action: str
    verification: str
    evidence_metrics: list[str]
    confidence: Literal["limited", "moderate"]


class CreatorIntelligenceResponse(BaseModel):
    version: str = "creator-intelligence-v1-offline"
    status: Literal["prototype"] = "prototype"
    analyzed_weeks: int
    comparisons: list[MetricComparison]
    insights: list[CreatorInsight]
    missing_metrics: list[str]
    data_quality_notes: list[str]
    limitations: list[str]
    next_review_after_weeks: int = 2
