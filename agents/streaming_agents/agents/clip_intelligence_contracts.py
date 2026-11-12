"""Offline clip candidates based on acoustic changes, not predicted popularity."""
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ClipScanSettings(BaseModel):
    frame_ms: Literal[200, 250, 500] = 250
    min_active_frames: int = Field(default=2, ge=2, le=12)
    activity_multiplier: float = Field(default=2.3, ge=1.5, le=8)
    absolute_floor: float = Field(default=0.045, ge=0.01, le=0.5)
    pre_roll_seconds: float = Field(default=9, ge=0, le=30)
    post_roll_seconds: float = Field(default=12, ge=0, le=30)
    min_gap_seconds: float = Field(default=14, ge=0, le=120)
    max_candidates: int = Field(default=5, ge=1, le=10)
    max_duration_seconds: int = Field(default=3600, ge=10, le=7200)

    @model_validator(mode="after")
    def check_window(self):
        if self.pre_roll_seconds + self.post_roll_seconds < 4:
            raise ValueError("Combined pre-roll and post-roll must be at least four seconds")
        return self


class ClipCandidate(BaseModel):
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(ge=0)
    peak_seconds: float = Field(ge=0)
    audio_activity_score: int = Field(ge=0, le=100)
    reason: str
    needs_human_review: bool = True


class ClipScanResult(BaseModel):
    version: Literal["clip-intelligence-v1-offline"] = "clip-intelligence-v1-offline"
    analysis_type: Literal["audio_activity"] = "audio_activity"
    analyzed_duration_seconds: float = Field(ge=0)
    audio_available: bool = True
    candidates: list[ClipCandidate] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    suggested_next_step: str
