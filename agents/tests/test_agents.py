from fastapi.testclient import TestClient

from streaming_agents.api import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_agents_are_explicitly_planned_or_prototype():
    response = client.get("/api/v1/agents")
    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert "content_strategist" in names
    assert "trend_scout" in names
    assert all(item["status"] != "ready" for item in response.json())


def test_api_exposes_one_route_per_agent_function():
    paths = set(client.get("/api/v1/openapi.json").json()["paths"])
    assert {
        "/api/v1/agents",
        "/api/v1/content/strategy",
        "/api/v1/growth/analysis",
        "/api/v1/growth/strategy",
        "/api/v1/growth/review",
        "/api/v1/clips/chat-moments",
        "/api/v1/content/category-check",
    } <= paths
    assert not any("/demo/" in path for path in paths)


def test_removed_legacy_routes_are_gone():
    paths = set(client.get("/api/v1/openapi.json").json()["paths"])
    assert not paths & {
        "/api/v1/clips/scan",
        "/api/v1/clips/evaluate",
        "/api/v1/clips/review-queue",
        "/api/v1/content/weekly-plan",
    }


def test_invalid_language_rejected():
    response = client.post("/api/v1/content/strategy", json={
        "games": ["Minecraft"], "windows": [{"day": "Mo", "start": "18", "end": "22"}],
        "hours_per_week": 8, "streams_per_week": 1, "language": "xx",
    })
    assert response.status_code == 422
