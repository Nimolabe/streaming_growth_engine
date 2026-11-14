import io
import json
from itertools import pairwise
from urllib.error import HTTPError

import pytest

from streaming_agents.clip_hunter.evaluation import (
    community_moments,
    evaluate_against_viewer_clips,
)
from streaming_agents.clip_hunter.fusion import build_candidates, format_hms, twitch_vod_link
from streaming_agents.clip_hunter.models import (
    AudioSpike,
    ChatMoment,
    ChatStats,
    ClipCandidate,
    HuntResult,
    HuntSettings,
)
from streaming_agents.clip_hunter.report import render_report
from streaming_agents.clip_hunter.twitch_api import (
    HelixClient,
    TwitchApiError,
    ViewerClip,
    parse_twitch_duration,
    parse_video_id,
)

ACTIVE = ChatStats(level="active", messages_used=5000, messages_ignored=10,
                   median_chatters_per_minute=40)


def moment(event, z=8.0, category="funny", share=0.8, alert=None, chatters=50):
    return ChatMoment(event_seconds=event, onset_seconds=event + 5, peak_seconds=event + 9,
                      z_score=z, chatters=chatters, baseline_chatters=9, reaction_share=share,
                      categories={category: 30} if category != "reaction" else {},
                      dominant_category=category, alert_nearby=alert,
                      sample_messages=["KEKW", "<script>alert(1)</script>"])


def spike(peak, rise=18.0):
    return AudioSpike(peak_seconds=peak, onset_seconds=peak - 0.5, rise_db=rise, level_db=-12)


# ---------- Zusammenführung ----------
def test_chat_and_audio_together_rank_highest_and_use_audio_timing():
    result = build_candidates([moment(600), moment(1500, z=5, category="hype")], ACTIVE,
                              [spike(601.5), spike(2500)], 3600, HuntSettings())
    first = result[0]
    assert first.signals == ["chat", "audio"] and first.confidence == "high"
    assert first.anchor_seconds == 601.5
    assert first.start_seconds == pytest.approx(581.5) and first.end_seconds == pytest.approx(611.5)
    assert first.category == "funny"
    assert [item.rank for item in result] == list(range(1, len(result) + 1))
    audio_only = next(item for item in result if item.signals == ["audio"])
    assert audio_only.confidence == "low"
    assert any("nicht auffällig" in reason for reason in audio_only.reasons)


def test_audio_far_from_chat_is_not_matched():
    result = build_candidates([moment(600)], ACTIVE, [spike(700)], 3600, HuntSettings())
    assert all(len(item.signals) == 1 for item in result)


def test_audio_only_weight_depends_on_chat():
    loud = [spike(300, rise=24)]
    with_chat = build_candidates([], ACTIVE, loud, 900, HuntSettings())[0]
    without_chat = build_candidates([], None, loud, 900, HuntSettings())[0]
    assert without_chat.score > with_chat.score
    assert without_chat.score >= 80


def test_alert_reactions_are_penalized_and_explained():
    normal = build_candidates([moment(600)], ACTIVE, [], 3600, HuntSettings())[0]
    alerted = build_candidates([moment(600, alert="raid")], ACTIVE, [], 3600, HuntSettings())[0]
    assert alerted.score < normal.score
    assert any("Raid" in reason for reason in alerted.reasons)


def test_overlapping_candidates_are_merged_and_limit_respected():
    moments = [moment(600), moment(605, z=4)] + [moment(1000 + 100 * i) for i in range(30)]
    result = build_candidates(moments, ACTIVE, [], 5000, HuntSettings(max_candidates=10))
    assert len(result) == 10
    starts = sorted(item.start_seconds for item in result)
    assert all(b - a >= 10 for a, b in pairwise(starts))


def test_window_is_clamped_to_video():
    early = build_candidates([], None, [spike(3)], 100, HuntSettings())[0]
    late = build_candidates([], None, [spike(98)], 100, HuntSettings())[0]
    assert early.start_seconds == 0 and early.end_seconds == 30
    assert late.end_seconds == 100 and late.start_seconds == 70


def test_english_and_vod_links():
    result = build_candidates([moment(3725)], ACTIVE, [], 7200, HuntSettings(language="en"),
                              twitch_video_id="1234567890")
    item = result[0]
    assert item.reasons[0].startswith("Chat spike")
    assert item.vod_link == "https://www.twitch.tv/videos/1234567890?t=1h1m45s"


def test_time_helpers():
    assert format_hms(3725.4) == "1:02:05"
    assert twitch_vod_link("123456", 59.9) == "https://www.twitch.tv/videos/123456?t=0h0m59s"


# ---------- Abgleich mit Zuschauer-Clips ----------
def clip(offset, duration=30, views=10, title="t"):
    return ViewerClip(vod_offset=offset, duration=duration, view_count=views, title=title,
                      id=f"c{offset}")


def candidate(rank, start, end):
    return ClipCandidate(rank=rank, start_seconds=start, end_seconds=end, anchor_seconds=start,
                         score=50, confidence="medium", category="funny", signals=["chat"],
                         reasons=["x"])


def test_viewer_clips_of_same_moment_are_merged():
    moments = community_moments([clip(100), clip(110), clip(125), clip(500)])
    assert len(moments) == 2
    assert moments[0].clips == 3 and moments[0].end_seconds == 155


def test_evaluation_metrics():
    clips = [clip(100, views=900), clip(105, views=100), clip(1000, views=10), clip(2000, views=0)]
    candidates = [candidate(1, 95, 125), candidate(2, 400, 430), candidate(3, 1990, 2010)]
    report = evaluate_against_viewer_clips(candidates, clips, top_n=3)
    assert report.community_moments == 3
    assert report.covered_moments == 2
    assert report.coverage == pytest.approx(0.667, abs=0.001)
    assert report.view_weighted_coverage == pytest.approx(1000 / 1010, abs=0.001)
    assert report.precision_at_n == pytest.approx(0.667, abs=0.001)
    assert report.moments[0].matched_rank == 1


def test_evaluation_without_clips():
    report = evaluate_against_viewer_clips([candidate(1, 0, 30)], [])
    assert report.coverage is None and report.precision_at_n is None


# ---------- Bericht ----------
def test_report_escapes_chat_text_and_contains_candidates():
    candidates = build_candidates([moment(600)], ACTIVE, [spike(601)], 3600, HuntSettings(),
                                  twitch_video_id="1234567")
    result = HuntResult(language="de", duration_seconds=3600, mode="chat+audio", chat=ACTIVE,
                        candidates=candidates, limitations=["Grenze <b>"])
    evaluation = evaluate_against_viewer_clips(candidates, [clip(590, title="<img src=x>")])
    html = render_report(result, evaluation=evaluation)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    assert "<img src=x>" not in html and "Grenze &lt;b&gt;" in html
    assert "0:09:41" in html and "twitch.tv/videos/1234567" in html
    assert "Abgleich mit Zuschauer-Clips" in html
    assert html.startswith("<!DOCTYPE html>")


def test_report_without_candidates():
    result = HuntResult(language="en", mode="audio", candidates=[], limitations=[])
    assert "No candidates found." in render_report(result)


# ---------- Twitch-API ----------
class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeTwitch:
    def __init__(self, pages=None, video=None, fail=None):
        self.requests = []
        self.pages = pages or []
        self.video = video
        self.fail = fail

    def __call__(self, request, timeout):
        self.requests.append(request)
        url = request.full_url
        if self.fail and "helix" in url:
            raise HTTPError(url, self.fail, "err", {}, None)
        if "oauth2/token" in url:
            body = {"access_token": "tok", "expires_in": 3600, "token_type": "bearer"}
        elif "/videos" in url:
            body = {"data": [self.video] if self.video else []}
        else:
            body = self.pages.pop(0)
        return FakeResponse(json.dumps(body).encode())


VIDEO = {"id": "2345678901", "user_id": "77", "user_login": "kanal", "title": "Stream",
         "created_at": "2026-11-14T18:00:05Z", "duration": "3h8m33s",
         "url": "https://www.twitch.tv/videos/2345678901"}


def test_get_video_and_clips_with_pagination_and_filtering():
    pages = [
        {"data": [
            {"id": "a", "video_id": "2345678901", "vod_offset": 222, "duration": 28,
             "view_count": 50, "title": "LOL"},
            {"id": "b", "video_id": "999", "vod_offset": 10, "duration": 30, "view_count": 5},
            {"id": "c", "video_id": "2345678901", "vod_offset": None, "duration": 30},
        ], "pagination": {"cursor": "next"}},
        {"data": [{"id": "d", "video_id": "2345678901", "vod_offset": 100, "duration": 30.5,
                   "view_count": 3, "title": "W"}], "pagination": {}},
    ]
    fake = FakeTwitch(pages=pages, video=VIDEO)
    client = HelixClient("cid", "secret", opener=fake)
    video = client.get_video("https://www.twitch.tv/videos/2345678901")
    assert video.duration_seconds == 3 * 3600 + 8 * 60 + 33
    assert video.started_at == pytest.approx(1794679205)
    clips = client.get_viewer_clips(video)
    assert [c.id for c in clips] == ["d", "a"]
    token_request = fake.requests[0]
    assert token_request.get_method() == "POST" and b"grant_type=client_credentials" in \
        token_request.data
    clip_request = fake.requests[2]
    assert clip_request.get_header("Authorization") == "Bearer tok"
    assert clip_request.get_header("Client-id") == "cid"
    assert "broadcaster_id=77" in clip_request.full_url
    assert "after=next" in fake.requests[3].full_url
    assert len([r for r in fake.requests if "oauth2" in r.full_url]) == 1


def test_api_errors_do_not_leak_secrets():
    client = HelixClient("cid", "supersecret", opener=FakeTwitch(video=VIDEO, fail=401))
    with pytest.raises(TwitchApiError) as error:
        client.get_video("2345678901")
    assert "supersecret" not in str(error.value) and "Client-ID" in str(error.value)


def test_missing_video_and_env(monkeypatch):
    with pytest.raises(TwitchApiError):
        HelixClient("cid", "s", opener=FakeTwitch()).get_video("2345678901")
    monkeypatch.delenv("TWITCH_CLIENT_ID", raising=False)
    with pytest.raises(TwitchApiError):
        HelixClient.from_env()


@pytest.mark.parametrize("text,seconds", [("3h8m33s", 11313), ("45m", 2700), ("59s", 59),
                                          ("1h", 3600)])
def test_duration_parsing(text, seconds):
    assert parse_twitch_duration(text) == seconds


@pytest.mark.parametrize("bad", ["", "abc", "1x2m"])
def test_bad_duration(bad):
    with pytest.raises(TwitchApiError):
        parse_twitch_duration(bad)


@pytest.mark.parametrize("value", ["2345678901", "v2345678901",
                                   "https://www.twitch.tv/videos/2345678901?filter=archives"])
def test_video_id_parsing(value):
    assert parse_video_id(value) == "2345678901"


def test_bad_video_id():
    with pytest.raises(TwitchApiError):
        parse_video_id("https://www.twitch.tv/kanal")
