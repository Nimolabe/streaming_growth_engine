"""Contract and behavior checks for the isolated offline weekly planner."""
from fastapi.testclient import TestClient

from streaming_agents.api import app

client = TestClient(app)


def payload(**overrides):
    result = {
        "platform": "Twitch",
        "category": "Minecraft",
        "audience": "New streamers",
        "language": "de",
        "weekly_hours": 8,
        "stream_days": 3,
        "primary_goal": "consistency",
    }
    result.update(overrides)
    return result


def test_weekly_plan_allocates_exactly_available_time():
    response = client.post("/api/v1/content/weekly-plan", json=payload())
    assert response.status_code == 200
    data = response.json()
    assert data["prototype"] is True
    assert data["generator"] == "deterministic_rules_v1"
    assert data["weekly_minutes"] == 480
    assert data["allocated_minutes"] == 480
    assert len([t for t in data["tasks"] if t["kind"] == "stream"]) == 3
    assert all(t["minutes"] > 0 for t in data["tasks"])


def test_weekly_plan_is_deterministic():
    first = client.post("/api/v1/content/weekly-plan", json=payload()).json()
    second = client.post("/api/v1/content/weekly-plan", json=payload()).json()
    assert first == second


def test_goal_and_language_affect_output():
    a = client.post("/api/v1/content/weekly-plan", json=payload()).json()
    b = client.post(
        "/api/v1/content/weekly-plan",
        json=payload(primary_goal="community", language="en"),
    ).json()
    assert a["goal"] == "consistency"
    assert b["goal"] == "community"
    assert "live on Twitch" in b["tasks"][0]["title"]
    assert a["tasks"][0]["details"] != b["tasks"][0]["details"]


def test_invalid_parameters_rejected():
    for updates in [
        {"weekly_hours": 1},
        {"weekly_hours": 41},
        {"stream_days": 0},
        {"stream_days": 8},
        {"primary_goal": "overnight_fame"},
    ]:
        response = client.post("/api/v1/content/weekly-plan", json=payload(**updates))
        assert response.status_code == 422


def test_insufficient_time_rejected():
    response = client.post(
        "/api/v1/content/weekly-plan", json=payload(weekly_hours=2, stream_days=7)
    )
    assert response.status_code == 422


def test_small_valid_budget():
    response = client.post("/api/v1/content/weekly-plan", json=payload(weekly_hours=2, stream_days=1))
    assert response.status_code == 200
    assert response.json()["allocated_minutes"] == 120
