"""Creator Intelligence V2 strategy acceptance and backwards-compatibility tests."""
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from streaming_agents.agents.creator_strategy import build_creator_strategy
from streaming_agents.agents.creator_strategy_contracts import StrategyRequestV2
from streaming_agents.api import app

client = TestClient(app)


def profile(*, viewers=(4, 4, 4, 4), clips=(0, 0, 0, 0),
            stream_minutes=360, budget=12, **changes):
    start = date(2026, 10, 5)
    weeks = [
        {
            "week_start": (start + timedelta(days=index * 7)).isoformat(),
            "stream_minutes": stream_minutes,
            "average_viewers": viewers[index],
            "unique_viewers": 40,
            "returning_viewers": 12,
            "follows": 2,
            "clips_published": clips[index],
            "clip_views": 0,
        }
        for index in range(4)
    ]
    result = {
        "platform": "twitch", "channel_category": "Valorant",
        "primary_goal": "discovery",
        "weekly_hours_available": budget,
        "has_own_recordings": True,
        "can_edit_short_clips": True,
        "can_access_stream_summaries": True,
        "minimum_stream_hours": 0,
        "weeks": weeks,
    }
    result.update(changes)
    return result


def strategy(**changes):
    return build_creator_strategy(StrategyRequestV2(**profile(**changes)))


def assert_budget_balanced(result):
    budget = result.budget
    assert (
        budget.streaming_minutes + budget.experiment_minutes
        + budget.measurement_minutes + budget.unallocated_minutes
        == budget.available_minutes
    )
    assert min(
        budget.streaming_minutes,
        budget.experiment_minutes,
        budget.measurement_minutes,
        budget.unallocated_minutes,
    ) >= 0
    assert result.strategy.extra_minutes_per_week == budget.experiment_minutes


def test_no_clips_with_recording_and_editor_means_one_clipping_experiment():
    output = strategy()
    assert output.version == "creator-intelligence-v2-offline"
    assert output.paid_api_calls is False
    assert output.strategy.code == "start_clip_experiment"
    assert output.experiment_weeks == 2
    assert len(output.strategy.steps) >= 2
    assert "no_clips" in output.considered_signals
    assert_budget_balanced(output)


def test_missing_recordings_yields_setup_not_fake_publishing_plan():
    output = strategy(has_own_recordings=False)
    assert output.strategy.code == "prepare_recordings"
    assert any("not yet available" in note for note in output.strategy.prerequisite_notes)
    assert_budget_balanced(output)


def test_no_editor_yields_capability_preparation():
    output = strategy(can_edit_short_clips=False)
    assert output.strategy.code == "prepare_recordings"
    assert any("editing workflow" in note for note in output.strategy.prerequisite_notes)
    assert any("editing method" in step for step in output.strategy.steps)


def test_overload_takes_precedence_over_clips():
    output = strategy(budget=3, stream_minutes=540)
    assert output.strategy.code == "reduce_overload"
    assert output.considered_signals[0] == "time_budget_overrun"
    assert "no_clips" in output.deferred_signals
    assert_budget_balanced(output)


def test_viewer_drop_is_treated_as_hypothesis_not_cause():
    output = strategy(viewers=(20, 20, 10, 10), clips=(1, 1, 1, 1))
    assert output.strategy.code == "investigate_viewer_decline"
    assert any("cannot prove" in text for text in output.strategy.limitations)
    assert output.strategy.evidence == ["average_viewers", "stream_minutes"]
    assert_budget_balanced(output)


def test_retention_goal_beats_unrelated_medium_growth_signal():
    data = profile(
        viewers=(4, 4, 6, 6),
        clips=(1, 1, 1, 1),
        primary_goal="retention",
    )
    for index, week in enumerate(data["weeks"]):
        week["unique_viewers"] = [100, 110, 150, 160][index]
        week["returning_viewers"] = [40, 41, 30, 28][index]
    output = build_creator_strategy(StrategyRequestV2(**data))
    assert "viewer_growth" in output.considered_signals
    assert "returning_viewers_decline" in output.considered_signals
    assert output.strategy.code == "build_returner_habit"
    assert output.considered_signals[0] == "returning_viewers_decline"
    assert_budget_balanced(output)


def test_high_severity_outweighs_medium_goal_match():
    data = profile(
        viewers=(20, 20, 10, 10),
        clips=(1, 1, 1, 1),
        primary_goal="retention",
    )
    for index, week in enumerate(data["weeks"]):
        week["unique_viewers"] = [100, 110, 160, 170][index]
        week["returning_viewers"] = [40, 40, 20, 19][index]
    output = build_creator_strategy(StrategyRequestV2(**data))
    assert output.strategy.code == "investigate_viewer_decline"
    assert "returning_viewers_decline" in output.deferred_signals


def test_steady_channel_collects_baseline_instead_of_inventing_problem():
    output = strategy(clips=(1, 1, 1, 1))
    assert output.strategy.code == "collect_baseline"
    assert output.considered_signals == ["baseline_review"]
    assert_budget_balanced(output)


@pytest.mark.parametrize("budget", [1, 1.5, 3, 8, 12, 40, 80])
def test_allocation_never_exceeds_available_hours(budget):
    output = strategy(budget=budget)
    assert_budget_balanced(output)
    assert output.budget.available_minutes == round(budget * 60)


def test_protected_full_streaming_commitment_prevents_added_tasks():
    output = strategy(budget=3, minimum_stream_hours=3, stream_minutes=120)
    assert output.strategy.code == "collect_baseline"
    assert output.budget.streaming_minutes == 180
    assert output.budget.experiment_minutes == 0
    assert output.budget.measurement_minutes == 0
    assert any("No experiment fits" in note for note in output.strategy.prerequisite_notes)
    assert "no_clips" in output.deferred_signals
    assert_budget_balanced(output)


def test_protected_minimum_streaming_hours_never_violated():
    output = strategy(budget=8, minimum_stream_hours=6, stream_minutes=420)
    assert output.budget.streaming_minutes >= 360
    assert_budget_balanced(output)


@pytest.mark.parametrize("bad", [
    {"minimum_stream_hours": -1},
    {"minimum_stream_hours": 20, "weekly_hours_available": 10},
    {"weekly_hours_available": 0},
    {"has_own_recordings": "not a boolean"},
    {"weeks": []},
])
def test_bad_input_is_rejected(bad):
    data = profile()
    data.update(bad)
    result = client.post("/api/v1/growth/strategy", json=data)
    assert result.status_code == 422


def test_route_and_v1_legacy_remain_compatible():
    data = profile()
    v2 = client.post("/api/v1/growth/strategy", json=data)
    v1 = client.post("/api/v1/growth/analysis", json=data)
    assert v2.status_code == 200, v2.text
    assert v1.status_code == 200, v1.text
    assert v1.json()["version"] == "creator-intelligence-v1-offline"
    assert v2.json()["analysis"]["version"] == "creator-intelligence-v1-offline"
    assert_budget_balanced(build_creator_strategy(StrategyRequestV2(**data)))


def test_strategy_is_stable_for_identical_input():
    data = StrategyRequestV2(**profile())
    assert build_creator_strategy(data).model_dump() == build_creator_strategy(data).model_dump()


def test_reports_a_review_rule_not_a_growth_promise():
    output = strategy()
    assert "compare" in output.strategy.evaluation_rule.lower()
    assert output.strategy.confidence in {"limited", "moderate"}
    assert all(output.strategy.evidence)
