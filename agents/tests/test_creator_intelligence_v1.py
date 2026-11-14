"""Offline regression and data-quality tests for Creator Intelligence V1."""
import socket

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from streaming_agents.agents.creator_intelligence import analyze_creator
from streaming_agents.agents.creator_intelligence_contracts import CreatorIntelligenceRequest
from streaming_agents.api import app

client = TestClient(app)


def payload(*, viewers=(3, 4, 5, 6), clips=(0, 0, 0, 0), **updates):
    weeks = []
    for index in range(4):
        weeks.append({
            "week_start": f"2026-10-{5 + index * 7:02d}",
            "stream_minutes": 360,
            "average_viewers": viewers[index],
            "unique_viewers": 50 + 10 * index,
            "returning_viewers": 12 + index,
            "follows": 3 + index,
            "clips_published": clips[index],
            "clip_views": 0,
        })
    result = {
        "platform": "twitch", "channel_category": "Valorant",
        "primary_goal": "discovery", "weekly_hours_available": 12,
        "weeks": weeks,
    }
    result.update(updates)
    return result


def test_endpoint_returns_observations_without_model():
    result = client.post("/api/v1/growth/analysis", json=payload())
    assert result.status_code == 200, result.text
    data = result.json()
    assert data["version"] == "creator-intelligence-v1-offline"
    assert data["analyzed_weeks"] == 4
    assert any(x["code"] == "no_clips" for x in data["insights"])
    assert data["limitations"]


def test_viewer_improvement_is_not_guaranteed_growth():
    r = analyze_creator(CreatorIntelligenceRequest(**payload()))
    assert any(x.code == "viewer_growth" for x in r.insights)
    assert all("not proof" in x.interpretation or "not a growth guarantee" in x.interpretation
               for x in r.insights)


def test_weekly_hours_over_budget_is_high_priority():
    r = analyze_creator(CreatorIntelligenceRequest(**payload(weekly_hours_available=3)))
    assert r.insights[0].code == "time_budget_overrun"
    assert r.insights[0].priority == "high"


def test_resource_constraints_precede_growth_tasks_when_both_high():
    result = analyze_creator(CreatorIntelligenceRequest(**payload(
        weekly_hours_available=3,
        viewers=(20, 20, 10, 10),
    )))
    high = [item.code for item in result.insights if item.priority == "high"]
    assert high == ["time_budget_overrun", "viewer_decline", "no_clips"]


def test_priorities_are_sorted_without_reordering_equal_priority_dependencies():
    result = analyze_creator(CreatorIntelligenceRequest(**payload(
        weekly_hours_available=3,
    )))
    priority_rank = {"high": 0, "medium": 1, "low": 2}
    priorities = [priority_rank[item.priority] for item in result.insights]
    assert priorities == sorted(priorities)
    assert result.insights[0].code == "time_budget_overrun"


def test_no_clips_missing_is_not_zero():
    data = payload()
    for week in data["weeks"]:
        week.pop("clips_published")
        week.pop("clip_views")
    r = analyze_creator(CreatorIntelligenceRequest(**data))
    assert "clips_published" in r.missing_metrics
    assert "clip_views" in r.missing_metrics
    assert not any(x.code == "no_clips" for x in r.insights)


def test_weighted_viewer_average_not_simple_mean():
    data = payload(viewers=(1, 9, 10, 10))
    data["weeks"][0]["stream_minutes"] = 60
    data["weeks"][1]["stream_minutes"] = 540
    data["weeks"][2]["stream_minutes"] = 300
    data["weeks"][3]["stream_minutes"] = 300
    r = analyze_creator(CreatorIntelligenceRequest(**data))
    c = next(x for x in r.comparisons if x.metric == "average_viewers")
    assert c.earlier == 8.2
    assert c.recent == 10.0


def test_zero_to_positive_growth_is_not_an_infinite_percentage():
    data = payload(viewers=(0, 0, 1, 3))
    r = analyze_creator(CreatorIntelligenceRequest(**data))
    comparison = next(x for x in r.comparisons if x.metric == "average_viewers")
    assert comparison.direction == "up"
    assert comparison.change_percent is None


@pytest.mark.parametrize("change", [
    {"weeks": []},
    {"weeks": payload()["weeks"][:3]},
    {"weeks": payload()["weeks"] * 7},
    {"weekly_hours_available": -1},
    {"primary_goal": "viral"},
])
def test_invalid_profile_rejected(change):
    data = payload()
    data.update(change)
    assert client.post("/api/v1/growth/analysis", json=data).status_code == 422


def test_duplicate_or_out_of_order_weeks_rejected():
    data = payload()
    data["weeks"][2]["week_start"] = data["weeks"][1]["week_start"]
    assert client.post("/api/v1/growth/analysis", json=data).status_code == 422
    data = payload()
    data["weeks"] = data["weeks"][::-1]
    assert client.post("/api/v1/growth/analysis", json=data).status_code == 422


def test_invalid_metric_relationship_rejected():
    data = payload()
    data["weeks"][0]["returning_viewers"] = 900
    assert client.post("/api/v1/growth/analysis", json=data).status_code == 422
    data = payload()
    data["weeks"][0]["average_viewers"] = -1
    assert client.post("/api/v1/growth/analysis", json=data).status_code == 422


def test_historic_clip_views_allowed_even_if_no_new_clips():
    data = payload()
    data["weeks"][0]["clip_views"] = 120
    assert client.post("/api/v1/growth/analysis", json=data).status_code == 200


def test_decline_detection_with_sufficient_data():
    data = payload(viewers=(20, 20, 10, 9))
    r = analyze_creator(CreatorIntelligenceRequest(**data))
    assert any(x.code == "viewer_decline" for x in r.insights)


def test_offline_and_deterministic(monkeypatch):
    def reject(*args, **kwargs):
        raise AssertionError("Unexpected network request")

    obj = CreatorIntelligenceRequest(**payload())
    monkeypatch.setattr(socket, "socket", reject)
    assert analyze_creator(obj).model_dump() == analyze_creator(obj).model_dump()


def test_zero_stream_week_with_viewer_metric_rejected():
    data = payload()
    data["weeks"][1]["stream_minutes"] = 0
    with pytest.raises(ValidationError):
        CreatorIntelligenceRequest(**data)


def test_no_stream_week_without_viewer_metric_is_valid():
    data = payload()
    data["weeks"][1]["stream_minutes"] = 0
    data["weeks"][1]["average_viewers"] = None
    assert client.post("/api/v1/growth/analysis", json=data).status_code == 200


def test_related_endpoints_remain_available():
    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/agents").status_code == 200
    paths = client.get("/api/v1/openapi.json").json()["paths"]
    assert "/api/v1/content/strategy" in paths
    assert "/api/v1/growth/strategy" in paths


def test_all_optional_stats_missing_causes_no_false_growth_claims():
    data = payload()
    for week in data["weeks"]:
        for field in ("average_viewers", "unique_viewers", "returning_viewers",
                      "follows", "clips_published", "clip_views"):
            week.pop(field)
    result = client.post("/api/v1/growth/analysis", json=data)
    assert result.status_code == 200, result.text
    output = result.json()
    assert "average_viewers" in output["missing_metrics"]
    assert not any(item["code"] in {"viewer_growth", "viewer_decline", "no_clips"}
                   for item in output["insights"])


def test_incomplete_period_is_not_compared_using_partial_week_values():
    data = payload()
    data["weeks"][2].pop("average_viewers")
    output = client.post("/api/v1/growth/analysis", json=data).json()
    viewers = next(c for c in output["comparisons"] if c["metric"] == "average_viewers")
    assert viewers["direction"] == "unavailable"
    assert viewers["change_percent"] is None
