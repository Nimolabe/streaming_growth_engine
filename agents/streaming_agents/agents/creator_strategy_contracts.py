"""Typed, deliberately conservative V2 growth-strategy contracts.

Only user-supplied aggregate analytics are accepted; no platform connection.
"""
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .creator_intelligence_contracts import (
    CreatorIntelligenceRequest,
    CreatorIntelligenceResponse,
)

StrategyCode = Literal[
    "reduce_overload",
    "investigate_viewer_decline",
    "start_clip_experiment",
    "prepare_recordings",
    "review_clip_openings",
    "build_returner_habit",
    "clarify_follow_value",
    "protect_successful_format",
    "collect_baseline",
]


class StrategyRequestV2(CreatorIntelligenceRequest):
    """All V1 input fields plus honest production capabilities."""

    has_own_recordings: bool = False
    can_edit_short_clips: bool = False
    can_access_stream_summaries: bool = False
    minimum_stream_hours: float = Field(default=0, ge=0, le=80, allow_inf_nan=False)

    @model_validator(mode="after")
    def check_time_commitment(self):
        if self.minimum_stream_hours > self.weekly_hours_available:
            raise ValueError("Minimum streaming hours exceed the available weekly budget")
        return self


class StrategyActionV2(BaseModel):
    code: StrategyCode
    title: str
    reason: str
    hypothesis: str
    steps: list[str] = Field(min_length=2, max_length=5)
    evidence: list[str]
    prerequisite_notes: list[str]
    measurement: str
    evaluation_rule: str
    limitations: list[str]
    extra_minutes_per_week: int = Field(ge=0)
    confidence: Literal["limited", "moderate"] = "limited"


class StrategyBudgetV2(BaseModel):
    available_minutes: int = Field(ge=60)
    streaming_minutes: int = Field(ge=0)
    experiment_minutes: int = Field(ge=0)
    measurement_minutes: int = Field(ge=0)
    unallocated_minutes: int = Field(ge=0)


class StrategyDecisionV2(BaseModel):
    version: Literal["creator-intelligence-v2-offline"] = "creator-intelligence-v2-offline"
    prototype: bool = True
    paid_api_calls: bool = False
    strategy: StrategyActionV2
    budget: StrategyBudgetV2
    analysis: CreatorIntelligenceResponse
    considered_signals: list[str]
    deferred_signals: list[str]
    experiment_weeks: int = 2
    caveats: list[str]
