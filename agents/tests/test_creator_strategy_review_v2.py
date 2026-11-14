"""Experiment review V2: descriptive trend, not a growth guarantee."""
import math

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from streaming_agents.agents.creator_strategy_review import (
    ExperimentReviewRequestV2,
    review_creator_experiment,
)
from streaming_agents.api import app

client = TestClient(app)


def body(**changes):
    item = {
        "strategy_code": "start_clip_experiment",
        "metric": "clip_views",
        "baseline_weeks": [50, 60],
        "followup_weeks": [75, 85],
        "observation_windows_comparable": True,
        "changed_only_one_major_factor": True,
    }
    item.update(changes)
    return item


def test_review_reports_observed_increase_not_success():
    response = client.post("/api/v1/growth/review", json=body())
    assert response.status_code == 200, response.text
    output = response.json()
    assert output["assessment"] == "observed_increase"
    assert output["baseline_mean"] == 55
    assert output["followup_mean"] == 80
    assert output["change_percent"] == 45.5
    assert any("not a causal" in message for message in output["limitations"])


def test_review_does_not_claim_causation_with_other_changes():
    output = review_creator_experiment(
        ExperimentReviewRequestV2(**body(changed_only_one_major_factor=False))
    )
    assert output.assessment == "inconclusive"
    assert output.change_percent is None
    assert any("Several factors changed" in note for note in output.limitations)


def test_noncomparable_windows_are_inconclusive():
    output = review_creator_experiment(
        ExperimentReviewRequestV2(**body(observation_windows_comparable=False))
    )
    assert output.assessment == "inconclusive"
    assert output.baseline_mean is None


def test_missing_values_are_inconclusive_not_imputed():
    output = review_creator_experiment(
        ExperimentReviewRequestV2(**body(followup_weeks=[None, 85]))
    )
    assert output.assessment == "inconclusive"
    assert output.followup_mean is None
    assert any("missing" in text for text in output.limitations)


@pytest.mark.parametrize(("before", "after", "expected"), [
    ([100, 100], [70, 70], "observed_decrease"),
    ([100, 100], [103, 103], "approximately_stable"),
    ([0, 0], [20, 20], "observed_increase"),
    ([0, 0], [0, 0], "approximately_stable"),
])
def test_review_classifies_direction_conservatively(before, after, expected):
    output = review_creator_experiment(
        ExperimentReviewRequestV2(**body(baseline_weeks=before, followup_weeks=after))
    )
    assert output.assessment == expected
    if before == [0, 0] and after == [20, 20]:
        assert output.change_percent is None


@pytest.mark.parametrize("bad", [
    {"baseline_weeks": [100]},
    {"followup_weeks": [100] * 9},
    {"followup_weeks": [-1, 10]},
    {"metric": "follower_retention_probability"},
    {"strategy_code": "instant_success"},
])
def test_invalid_review_payload_is_rejected(bad):
    data = body()
    data.update(bad)
    assert client.post("/api/v1/growth/review", json=data).status_code == 422


def test_review_is_deterministic():
    value = ExperimentReviewRequestV2(**body())
    assert review_creator_experiment(value).model_dump() == (
        review_creator_experiment(value).model_dump()
    )


def test_non_finite_values_rejected_before_json_serialization():
    with pytest.raises(ValidationError):
        ExperimentReviewRequestV2(**body(baseline_weeks=[math.inf, 1]))
