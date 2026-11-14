"""Human-annotated clip quality evaluation, no actual user data."""
import pytest
from fastapi.testclient import TestClient

from streaming_agents.agents.clip_evaluation import (
    ClipEvaluationRequest,
    evaluate_human_labels,
)
from streaming_agents.api import app

client = TestClient(app)


def case(**changes):
    data = {
        "duration_seconds": 120,
        "suggested_event_seconds": [10, 30, 80],
        "human_highlight_seconds": [11, 31, 60],
        "tolerance_seconds": 3,
    }
    data.update(changes)
    return data


def test_counts_precision_recall_and_f1():
    result = evaluate_human_labels(ClipEvaluationRequest(**case()))
    assert result.matched_count == 2
    assert result.false_positive_count == 1
    assert result.missed_count == 1
    assert result.precision == pytest.approx(2 / 3, abs=0.0001)
    assert result.recall == pytest.approx(2 / 3, abs=0.0001)
    assert result.f1 == pytest.approx(2 / 3, abs=0.0001)


def test_one_to_one_matching_not_double_counted():
    result = evaluate_human_labels(ClipEvaluationRequest(**case(
        suggested_event_seconds=[10, 12],
        human_highlight_seconds=[11],
    )))
    assert result.matched_count == 1
    assert result.false_positive_count == 1
    assert result.missed_count == 0


def test_global_optimal_matching_not_nearest_greedy():
    result = evaluate_human_labels(ClipEvaluationRequest(**case(
        suggested_event_seconds=[0, 4],
        human_highlight_seconds=[3, 8],
        tolerance_seconds=4,
    )))
    assert result.matched_count == 2
    assert result.matched_pairs_seconds == [(0, 3), (4, 8)]


def test_no_predictions_does_not_report_perfect_precision():
    result = evaluate_human_labels(ClipEvaluationRequest(**case(
        suggested_event_seconds=[],
    )))
    assert result.precision is None
    assert result.recall == 0
    assert result.f1 is None


def test_no_human_labels_does_not_report_perfect_recall():
    result = evaluate_human_labels(ClipEvaluationRequest(**case(
        human_highlight_seconds=[],
    )))
    assert result.recall is None
    assert result.precision == 0
    assert result.f1 is None


def test_empty_labels_and_predictions_are_inconclusive():
    result = evaluate_human_labels(ClipEvaluationRequest(**case(
        human_highlight_seconds=[],
        suggested_event_seconds=[],
    )))
    assert result.precision is None
    assert result.recall is None
    assert result.f1 is None


def test_request_order_does_not_change_results():
    normal = evaluate_human_labels(ClipEvaluationRequest(**case()))
    shuffled = evaluate_human_labels(ClipEvaluationRequest(**case(
        suggested_event_seconds=[80, 10, 30],
        human_highlight_seconds=[60, 31, 11],
    )))
    assert normal.model_dump() == shuffled.model_dump()


@pytest.mark.parametrize("bad", [
    {"duration_seconds": 0},
    {"suggested_event_seconds": [-1]},
    {"suggested_event_seconds": [121]},
    {"human_highlight_seconds": [10, 10]},
    {"tolerance_seconds": -2},
    {"tolerance_seconds": 100},
])
def test_input_guardrails(bad):
    response = client.post("/api/v1/clips/evaluate", json=case(**bad))
    assert response.status_code == 422


def test_api_returns_results_without_video_or_external_provider():
    response = client.post("/api/v1/clips/evaluate", json=case())
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["version"] == "clip-evaluation-v1-offline"
    assert result["matched_count"] == 2
    assert any("subjective human labels" in note for note in result["limitations"])
