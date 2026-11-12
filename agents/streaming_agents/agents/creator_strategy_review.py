"""A cautious follow-up evaluation of one user-entered experiment.

This evaluates observations only, without causal or statistical claims.
"""
from math import isfinite
from statistics import mean
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .creator_strategy_contracts import StrategyCode

TrackedMetric = Literal[
    "stream_minutes",
    "average_viewers",
    "unique_viewers",
    "returning_viewers",
    "follows",
    "clips_published",
    "clip_views",
]


class ExperimentReviewRequestV2(BaseModel):
    strategy_code: StrategyCode
    metric: TrackedMetric
    baseline_weeks: list[float | None] = Field(min_length=2, max_length=8)
    followup_weeks: list[float | None] = Field(min_length=2, max_length=8)
    observation_windows_comparable: bool
    changed_only_one_major_factor: bool

    @model_validator(mode="after")
    def check_observations(self):
        for value in self.baseline_weeks + self.followup_weeks:
            if value is not None and (not isfinite(value) or value < 0):
                raise ValueError("Measured values must be finite and non-negative")
        return self


class ExperimentReviewV2(BaseModel):
    version: Literal["creator-intelligence-review-v2-offline"] = (
        "creator-intelligence-review-v2-offline"
    )
    assessment: Literal[
        "inconclusive", "observed_increase", "observed_decrease",
        "approximately_stable",
    ]
    metric: TrackedMetric
    baseline_mean: float | None
    followup_mean: float | None
    change_percent: float | None
    limitations: list[str]
    next_action: str


def review_creator_experiment(request: ExperimentReviewRequestV2) -> ExperimentReviewV2:
    notes = [
        "This is descriptive, not a causal claim or proof of growth.",
        "Two to eight weekly aggregates cannot establish statistical significance.",
    ]
    if not request.observation_windows_comparable:
        notes.append("Collection windows are not comparable.")
    if not request.changed_only_one_major_factor:
        notes.append("Several factors changed; effects cannot be separated.")
    if any(x is None for x in request.baseline_weeks + request.followup_weeks):
        notes.append("One or more weekly measurements are missing.")

    ready = (
        request.observation_windows_comparable
        and request.changed_only_one_major_factor
        and all(x is not None for x in request.baseline_weeks + request.followup_weeks)
    )
    if not ready:
        return ExperimentReviewV2(
            assessment="inconclusive", metric=request.metric,
            baseline_mean=None, followup_mean=None, change_percent=None,
            limitations=notes,
            next_action=(
                "Collect two comparable complete weeks with one major change "
                "before evaluating this experiment."
            ),
        )

    before = round(mean(request.baseline_weeks), 2)
    after = round(mean(request.followup_weeks), 2)
    if before == 0:
        change = 0.0 if after == 0 else None
        assessment = "approximately_stable" if after == 0 else "observed_increase"
        notes.append("Percentage change from zero is undefined.")
    else:
        change = round(100 * (after - before) / before, 1)
        assessment = (
            "observed_increase" if change > 5 else
            "observed_decrease" if change < -5 else
            "approximately_stable"
        )
    return ExperimentReviewV2(
        assessment=assessment, metric=request.metric,
        baseline_mean=before, followup_mean=after, change_percent=change,
        limitations=notes,
        next_action=(
            "Record confounders, retain the measurement definition, and compare "
            "additional weeks before deciding whether to repeat or change the experiment."
        ),
    )
