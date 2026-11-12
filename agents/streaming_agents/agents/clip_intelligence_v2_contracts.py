"""Typed, explicitly heuristic multimodal clip suggestions.

Audio-energy peaks and visual changes are cues for HUMAN review, not AI
understanding of gameplay, speech, jokes or audience response.
"""
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ClipScanSettingsV2(BaseModel):
    max_candidates: int = Field(default=5, ge=1, le=10)
    max_duration_seconds: int = Field(default=900, ge=10, le=7200)
    pre_roll_seconds: float = Field(default=9, ge=0, le=30)
    post_roll_seconds: float = Field(default=12, ge=0, le=30)
    min_event_gap_seconds: float = Field(default=7, ge=2, le=120)
    visual_change_threshold: float = Field(default=0.24, ge=0.12, le=0.8)

    @model_validator(mode="after")
    def valid_window(self):
        if self.pre_roll_seconds + self.post_roll_seconds < 4:
            raise ValueError("A review window must have at least four seconds")
        return self


class ClipReviewCandidateV2(BaseModel):
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(ge=0)
    event_seconds: float = Field(ge=0)
    evidence: list[Literal["audio_peak", "visual_change"]] = Field(min_length=1)
    activity_score: int = Field(ge=0, le=100)
    explanation: str
    requires_human_review: Literal[True] = True


class ClipReviewResultV2(BaseModel):
    version: Literal["clip-intelligence-v2-offline"] = "clip-intelligence-v2-offline"
    duration_seconds: float = Field(ge=0)
    audio_track_found: bool
    video_track_found: bool
    candidates: list[ClipReviewCandidateV2]
    limitations: list[str]
    review_guidance: str
