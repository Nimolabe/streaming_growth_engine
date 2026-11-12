"""Reproducible, blind candidate/control review worksheets.

Accepts only an already-analyzed, locally supplied ClipReviewResultV2.
No media fetching, scraping, storage, sentiment inference or stochastic
sampling. Controls are UNFLAGGED times, not confirmed negative examples.
"""
from hashlib import sha256
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .clip_intelligence_v2_contracts import ClipReviewResultV2


class ClipReviewQueueRequestV3(BaseModel):
    scan: ClipReviewResultV2
    control_count: int = Field(default=3, ge=0, le=10)
    control_window_seconds: float = Field(default=16, ge=4, le=60)
    control_gap_seconds: float = Field(default=2, ge=0, le=30)

    @model_validator(mode="after")
    def validate_scan(self):
        length = self.scan.duration_seconds
        for candidate in self.scan.candidates:
            if not (0 <= candidate.start_seconds <= candidate.event_seconds
                    <= candidate.end_seconds <= length):
                raise ValueError("Candidates must lie within the recording")
            if candidate.end_seconds - candidate.start_seconds < 4:
                raise ValueError("Reviewable candidates must be at least four seconds")
        return self


class ClipReviewTaskV3(BaseModel):
    task_id: str
    start_seconds: float
    end_seconds: float
    question: str = "Is this segment independently worth clipping? What context is needed?"


class ClipReviewQueueV3(BaseModel):
    version: Literal["clip-review-queue-v3-offline"] = "clip-review-queue-v3-offline"
    tasks: list[ClipReviewTaskV3]
    candidate_tasks: int
    unflagged_control_tasks: int
    missing_controls: int
    reviewer_instructions: list[str]
    limitations: list[str]


def _id(start: float, end: float) -> str:
    payload = f"{start:.3f}:{end:.3f}".encode("ascii")
    return sha256(payload).hexdigest()[:16]


def _overlap(a: float, b: float, c: float, d: float, margin: float) -> bool:
    """Two review windows overlap after enlarging the excluded one by margin."""
    return a < d + margin and b > c - margin


def make_review_queue(request: ClipReviewQueueRequestV3) -> ClipReviewQueueV3:
    scan = request.scan
    duration = scan.duration_seconds
    excluded = [(x.start_seconds, x.end_seconds) for x in scan.candidates]
    # Expand candidate windows only when searching for controls. Do not claim
    # that unflagged controls are non-highlights.
    selected = []
    known = set()
    for candidate in sorted(scan.candidates, key=lambda x: (x.start_seconds, x.end_seconds)):
        interval = (round(candidate.start_seconds, 3), round(candidate.end_seconds, 3))
        if interval not in known:
            selected.append(interval)
            known.add(interval)
    candidate_count = len(selected)

    controls = []
    width = min(duration, request.control_window_seconds)
    if duration >= 4 and width >= 4 and request.control_count:
        # Regular 1-second grid; far more robust than a few random guesses.
        # Select an approximately evenly spaced subset after filtering.
        possibilities = []
        for second in range(int(duration - width) + 1):
            start = float(second)
            end = round(start + width, 3)
            if all(not _overlap(start, end, a, b, request.control_gap_seconds)
                   for a, b in excluded):
                possibilities.append((start, end))

        # Greedy max-min coverage spreads control windows across the timeline.
        # It also avoids overlapping controls; tie-breaks favor earliest time.
        while possibilities and len(controls) < request.control_count:
            eligible = [
                window for window in possibilities
                if all(not _overlap(*window, *other, 0.0) for other in controls)
            ]
            if not eligible:
                break
            anchors = [((a + b) / 2) for a, b in controls]
            if not anchors:
                mid = duration / 2
                choice = min(eligible, key=lambda p: (abs((p[0] + p[1]) / 2 - mid), p[0]))
            else:
                choice = max(
                    eligible,
                    key=lambda p: (
                        min(abs((p[0] + p[1]) / 2 - anchor) for anchor in anchors),
                        -p[0],
                    ),
                )
            controls.append(choice)
        selected.extend(controls)

    # Reversible hidden ordering via timestamp-based opaque task IDs. No cue
    # types or control flags are included in the reviewer-facing tasks.
    tasks = [
        ClipReviewTaskV3(task_id=_id(start, end),
                         start_seconds=start, end_seconds=end)
        for start, end in selected
    ]
    tasks.sort(key=lambda task: task.task_id)
    return ClipReviewQueueV3(
        tasks=tasks,
        candidate_tasks=candidate_count,
        unflagged_control_tasks=len(controls),
        missing_controls=request.control_count - len(controls),
        reviewer_instructions=[
            "Review every interval without consulting the agent's scores or event evidence.",
            "Record yes/no/uncertain, content category and a short explanation in your own words.",
            "Mark moments interesting even when they were not suggested by the scanner.",
            "Use two or more independent reviewers and keep disagreements visible.",
        ],
        limitations=[
            "Unflagged controls are NOT verified negative examples.",
            "Timestamp-only review cannot judge rights or publication permission.",
            "This worksheet does not access Twitch, YouTube or any recording.",
            "Task IDs are stable identifiers, not secure secrets or authentication tokens.",
        ],
    )
