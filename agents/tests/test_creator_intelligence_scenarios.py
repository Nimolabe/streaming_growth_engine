"""Acceptance scenarios: realistic channels, output priorities, and safe uncertainty.

These synthetic scenarios do not represent real channel analytics.
"""
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from streaming_agents.api import app

client = TestClient(app)


def scenario(viewers, unique, returning, follows, clips, clip_views,
             *, goal="discovery", weekly_hours=10, minutes=360):
    """Four complete consecutive weekly records with explicit observation windows."""
    anchor = date(2026, 10, 5)
    records = []
    for index in range(4):
        records.append({
            "week_start": (anchor + timedelta(days=index * 7)).isoformat(),
            "stream_minutes": minutes,
            "average_viewers": viewers[index],
            "unique_viewers": unique[index],
            "returning_viewers": returning[index],
            "follows": follows[index],
            "clips_published": clips[index],
            "clip_views": clip_views[index],
        })
    return {
        "platform": "twitch", "channel_category": "Valorant",
        "primary_goal": goal, "weekly_hours_available": weekly_hours,
        "weeks": records,
    }


@pytest.mark.parametrize(
    ("case", "profile_data", "expected", "excluded"),
    [
        (
            "new_streamer_no_clips",
            scenario(
                viewers=[2, 2, 2, 2],
                unique=[20, 22, 21, 20],
                returning=[2, 2, 2, 2],
                follows=[1, 1, 1, 1],
                clips=[0, 0, 0, 0],
                clip_views=[0, 0, 0, 0],
            ),
            {"no_clips"},
            {"viewer_decline", "viewer_growth", "clip_reach_decline"},
        ),
        (
            "growing_streamer_stable_reach",
            scenario(
                viewers=[11, 10.5, 10.8, 10.7],
                unique=[140, 141, 142, 140],
                returning=[40, 40, 41, 40],
                follows=[8, 8, 8, 8],
                clips=[3, 3, 3, 3],
                clip_views=[600, 620, 610, 625],
                goal="consistency",
            ),
            {"baseline_review"},
            {"viewer_decline", "no_clips", "viewer_growth"},
        ),
        (
            "established_creator_returning_viewers_decline",
            scenario(
                viewers=[105, 104, 106, 105],
                unique=[2000, 2100, 2600, 2800],
                returning=[650, 630, 460, 410],
                follows=[150, 160, 145, 140],
                clips=[5, 5, 5, 5],
                clip_views=[24000, 25000, 25000, 26000],
                goal="retention",
            ),
            {"returning_viewers_decline"},
            {"viewer_decline", "no_clips", "clip_reach_decline"},
        ),
        (
            "capacity_before_growth",
            scenario(
                viewers=[6, 6, 6, 6],
                unique=[80, 80, 80, 80],
                returning=[20, 20, 20, 20],
                follows=[3, 3, 3, 3],
                clips=[0, 0, 0, 0],
                clip_views=[0, 0, 0, 0],
                weekly_hours=3,
                minutes=540,
            ),
            {"time_budget_overrun", "no_clips"},
            {"viewer_decline", "viewer_growth"},
        ),
    ],
)
def test_synthetic_creator_cases(case, profile_data, expected, excluded):
    response = client.post("/api/v1/growth/analysis", json=profile_data)
    assert response.status_code == 200, (case, response.text)
    body = response.json()
    codes = [insight["code"] for insight in body["insights"]]
    assert expected <= set(codes), case
    assert not excluded.intersection(codes), case
    assert len(body["comparisons"]) == 7
    assert all(insight["evidence_metrics"] for insight in body["insights"])
    assert all(insight["action"] and insight["verification"] for insight in body["insights"])
    assert all(insight["confidence"] in ("limited", "moderate") for insight in body["insights"])
    assert all("proof" in insight["interpretation"]
               or "guarantee" in insight["interpretation"] for insight in body["insights"])
    if case == "capacity_before_growth":
        assert codes[0] == "time_budget_overrun"


def test_unreported_clips_never_trigger_no_clips_action():
    request = scenario(
        viewers=[1, 1, 1, 1],
        unique=[10, 10, 10, 10],
        returning=[1, 1, 1, 1],
        follows=[0, 0, 0, 0],
        clips=[0, 0, 0, 0],
        clip_views=[0, 0, 0, 0],
    )
    for week in request["weeks"]:
        week.pop("clips_published")
    response = client.post("/api/v1/growth/analysis", json=request)
    assert response.status_code == 200
    body = response.json()
    assert "clips_published" in body["missing_metrics"]
    assert all(insight["code"] != "no_clips" for insight in body["insights"])


def test_missing_retention_data_never_makes_retention_claim():
    request = scenario(
        viewers=[20, 20, 20, 20],
        unique=[100, 110, 140, 150],
        returning=[30, 30, 20, 19],
        follows=[3, 3, 3, 3],
        clips=[1, 1, 1, 1],
        clip_views=[50, 50, 50, 50],
        goal="retention",
    )
    request["weeks"][2].pop("returning_viewers")
    response = client.post("/api/v1/growth/analysis", json=request)
    assert response.status_code == 200
    body = response.json()
    assert "returning_viewers" in body["missing_metrics"]
    assert all(item["code"] != "returning_viewers_decline" for item in body["insights"])


def test_weekly_sums_not_mistaken_for_unique_viewers_across_many_weeks():
    """The reported metric is explicitly weekly counts, not distinct users across a month."""
    request = scenario(
        viewers=[6, 6, 6, 6],
        unique=[100, 100, 100, 100],
        returning=[50, 50, 50, 50],
        follows=[1, 1, 1, 1],
        clips=[1, 1, 1, 1],
        clip_views=[100, 100, 100, 100],
    )
    body = client.post("/api/v1/growth/analysis", json=request).json()
    compare = next(x for x in body["comparisons"] if x["metric"] == "unique_viewers")
    assert compare["earlier"] == 100
    assert compare["recent"] == 100
    assert compare["direction"] == "flat"
