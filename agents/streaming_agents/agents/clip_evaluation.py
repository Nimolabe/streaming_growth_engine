"""Human-labelled clip benchmark. Does not infer content quality or truth.

Review labels are supplied by a human. Matching is one-to-one and based on
timestamps only; neither the recording nor labels are persisted.
"""
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ClipEvaluationRequest(BaseModel):
    duration_seconds: float = Field(gt=0, le=7200, allow_inf_nan=False)
    suggested_event_seconds: list[float] = Field(default_factory=list, max_length=100)
    human_highlight_seconds: list[float] = Field(default_factory=list, max_length=100)
    tolerance_seconds: float = Field(default=5, ge=0.25, le=30, allow_inf_nan=False)

    @model_validator(mode="after")
    def check_timestamps(self):
        for name in ("suggested_event_seconds", "human_highlight_seconds"):
            values = getattr(self, name)
            if any(not 0 <= value <= self.duration_seconds for value in values):
                raise ValueError("Highlight timestamps must be inside the recording")
            if len(set(values)) != len(values):
                raise ValueError("Duplicate timestamps are not accepted")
        return self


class ClipEvaluationReport(BaseModel):
    version: Literal["clip-evaluation-v1-offline"] = "clip-evaluation-v1-offline"
    suggested_count: int
    human_highlight_count: int
    matched_count: int
    false_positive_count: int
    missed_count: int
    precision: float | None
    recall: float | None
    f1: float | None
    matched_pairs_seconds: list[tuple[float, float]]
    limitations: list[str]


def evaluate_human_labels(request: ClipEvaluationRequest) -> ClipEvaluationReport:
    suggestions = sorted(request.suggested_event_seconds)
    labels = sorted(request.human_highlight_seconds)

    # Ordered dynamic programming maximizes the NUMBER of one-to-one
    # matches first, then minimizes total timestamp deviation. Greedy
    # nearest-neighbor matching can incorrectly miss a second valid pair.
    n = len(suggestions)
    m = len(labels)
    table = [[(0, 0.0) for _ in range(m + 1)] for _ in range(n + 1)]
    choices = [["end" for _ in range(m + 1)] for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            options = [
                (table[i + 1][j], "skip_prediction"),
                (table[i][j + 1], "skip_label"),
            ]
            distance = abs(suggestions[i] - labels[j])
            if distance <= request.tolerance_seconds:
                later = table[i + 1][j + 1]
                options.append(((later[0] + 1, later[1] + distance), "match"))
            score, choice = max(
                options,
                key=lambda entry: (entry[0][0], -entry[0][1], entry[1] == "match"),
            )
            table[i][j] = score
            choices[i][j] = choice

    pairs: list[tuple[float, float]] = []
    i = j = 0
    while i < n and j < m:
        choice = choices[i][j]
        if choice == "match":
            pairs.append((suggestions[i], labels[j]))
            i += 1
            j += 1
        elif choice == "skip_prediction":
            i += 1
        else:
            j += 1

    total = len(pairs)
    precision = total / len(suggestions) if suggestions else None
    recall = total / len(labels) if labels else None
    if precision is None or recall is None or precision + recall == 0:
        f1 = None if precision is None or recall is None else 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)

    return ClipEvaluationReport(
        suggested_count=len(suggestions),
        human_highlight_count=len(labels),
        matched_count=total,
        false_positive_count=len(suggestions) - total,
        missed_count=len(labels) - total,
        precision=round(precision, 4) if precision is not None else None,
        recall=round(recall, 4) if recall is not None else None,
        f1=round(f1, 4) if f1 is not None else None,
        matched_pairs_seconds=sorted(pairs),
        limitations=[
            "Time-near matches do not prove the proposed video cut is watchable.",
            "These scores reflect subjective human labels and a chosen tolerance.",
            "Precision is undefined without predictions; recall without labels.",
            "Test on separate creators, games and recording conditions before generalizing.",
            "No audio, video or private account data is transmitted or retained.",
        ],
    )
