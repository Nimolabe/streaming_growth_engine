from chat_fixtures import START, Burst, ChatScenario, build_chat
from fastapi.testclient import TestClient

from streaming_agents.api import app

client = TestClient(app)


def payload(**extra):
    log = build_chat(ChatScenario(duration=900, bursts=[Burst(500, "hype", 50)]))
    return {"chat_log": log.model_dump(mode="json"), "vod_start": START} | extra


def test_chat_moments_endpoint_finds_moment():
    response = client.post("/api/v1/clips/chat-moments",
                           json=payload(twitch_video_id="2345678901"))
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "chat" and body["version"] == "clip-hunter-v4"
    best = body["candidates"][0]
    assert best["category"] == "hype" and abs(best["anchor_seconds"] - 500) <= 4
    assert best["vod_link"].startswith("https://www.twitch.tv/videos/2345678901?t=")
    assert body["chat"]["level"] == "active"


def test_chat_moments_validation():
    assert client.post("/api/v1/clips/chat-moments",
                       json=payload(twitch_video_id="abc")).status_code == 422
    assert client.post("/api/v1/clips/chat-moments",
                       json=payload(settings={"max_candidates": 0})).status_code == 422
    assert client.post("/api/v1/clips/chat-moments", json={"chat_log": {}}).status_code == 422


def test_english_settings_are_applied():
    response = client.post("/api/v1/clips/chat-moments",
                           json=payload(settings={"language": "en", "max_candidates": 3}))
    assert response.status_code == 200
    assert response.json()["candidates"][0]["reasons"][0].startswith("Chat spike")
