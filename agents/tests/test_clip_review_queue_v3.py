"""Deterministic offline reviewer tasks, with no fake negative ground truth."""
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from streaming_agents.agents.clip_intelligence_v2_contracts import (
    ClipReviewCandidateV2,
    ClipReviewResultV2,
)
from streaming_agents.agents.clip_review_queue_v3 import (
    ClipReviewQueueRequestV3,
    make_review_queue,
)
from streaming_agents.api import app

client = TestClient(app)


def scan(*, duration=120, events=(20, 90)):
    return ClipReviewResultV2(
        duration_seconds=duration,
        audio_track_found=True,
        video_track_found=True,
        candidates=[
            ClipReviewCandidateV2(
                start_seconds=event - 5,
                end_seconds=event + 5,
                event_seconds=event,
                evidence=["audio_peak"],
                activity_score=70,
                explanation="Synthetic signal only",
            )
            for event in events
        ],
        limitations=[],
        review_guidance="Review",
    )


def test_review_queue_contains_candidates_and_blind_controls():
    result = make_review_queue(ClipReviewQueueRequestV3(
        scan=scan(), control_count=3, control_window_seconds=8,
    ))
    assert result.version == "clip-review-queue-v3-offline"
    assert result.candidate_tasks == 2
    assert result.unflagged_control_tasks == 3
    assert result.missing_controls == 0
    assert len(result.tasks) == 5
    assert len({task.task_id for task in result.tasks}) == 5
    assert all(task.start_seconds < task.end_seconds for task in result.tasks)
    assert all("audio" not in task.model_dump_json().lower()
               for task in result.tasks)


def test_no_controls_that_overlap_candidate_windows():
    result = make_review_queue(ClipReviewQueueRequestV3(
        scan=scan(), control_count=8, control_window_seconds=8,
        control_gap_seconds=2,
    ))
    candidate_windows = [(15, 25), (85, 95)]
    for task in result.tasks:
        if (task.start_seconds, task.end_seconds) in candidate_windows:
            continue
        assert all(task.end_seconds <= a - 2 or task.start_seconds >= b + 2
                   for a, b in candidate_windows)


def test_no_room_for_control_does_not_invent_negative():
    result = make_review_queue(ClipReviewQueueRequestV3(
        scan=scan(duration=12, events=()), control_count=3,
        control_window_seconds=10,
    ))
    assert result.unflagged_control_tasks == 1
    assert result.missing_controls == 2


def test_same_input_produces_same_review_sheet():
    req = ClipReviewQueueRequestV3(scan=scan(), control_count=3)
    assert make_review_queue(req).model_dump() == make_review_queue(req).model_dump()


def test_candidate_queues_are_valid_when_controls_disabled():
    result = make_review_queue(ClipReviewQueueRequestV3(
        scan=scan(), control_count=0,
    ))
    assert result.candidate_tasks == 2
    assert result.unflagged_control_tasks == 0
    assert result.missing_controls == 0


def test_invalid_scan_ranges_rejected():
    incorrect = scan().model_dump()
    incorrect["candidates"][0]["end_seconds"] = 130
    with pytest.raises(ValidationError):
        ClipReviewQueueRequestV3(scan=incorrect)


def test_api_rejects_out_of_bounds_controls():
    response = client.post("/api/v1/clips/review-queue", json={
        "scan": scan().model_dump(),
        "control_count": 100,
    })
    assert response.status_code == 422


def test_api_generates_review_sheet_without_video():
    response = client.post("/api/v1/clips/review-queue", json={
        "scan": scan().model_dump(),
        "control_count": 2,
    })
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["candidate_tasks"] == 2
    assert data["unflagged_control_tasks"] == 2
    assert any("NOT verified negative" in x for x in data["limitations"])
