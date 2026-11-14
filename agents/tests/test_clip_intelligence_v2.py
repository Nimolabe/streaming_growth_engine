"""Offline clip V2 acceptance tests: synthetic audio, real video and no causal claims."""
import shutil
import subprocess
import wave
from array import array
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from streaming_agents.agents.clip_intelligence import ClipScanError
from streaming_agents.agents.clip_intelligence_v2 import (
    _combine,
    _Event,
    scan_recording_v2,
)
from streaming_agents.agents.clip_intelligence_v2_contracts import ClipScanSettingsV2
from streaming_agents.api import app

client = TestClient(app)
HAS_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def synthetic_wav(*, seconds=14, peak_at=(4, 10)):
    stream = BytesIO()
    with wave.open(stream, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(8000)
        for position in range(seconds * 4):
            t = position / 4
            volume = 15000 if any(start <= t < start + 1.5 for start in peak_at) else 150
            output.writeframes((array("h", [volume]) * 2000).tobytes())
    return stream.getvalue()


def make_wav(tmp_path, **options):
    path = tmp_path / "test.wav"
    path.write_bytes(synthetic_wav(**options))
    return path


def make_scene_video(path: Path, *, with_audio=False, first="black", second="white"):
    """Real video frames: hard cut at approximately four seconds."""
    command = [
        "ffmpeg", "-y", "-nostdin", "-loglevel", "error",
        "-f", "lavfi", "-i", f"color=c={first}:size=64x64:rate=4:duration=4",
        "-f", "lavfi", "-i", f"color=c={second}:size=64x64:rate=4:duration=4",
    ]
    if with_audio:
        command.extend([
            "-f", "lavfi", "-i", "sine=frequency=500:sample_rate=8000:duration=8",
        ])
    command.extend([
        "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]",
        "-map", "[v]",
    ])
    if with_audio:
        command.extend(["-map", "2:a", "-c:a", "aac"])
    command.extend(["-c:v", "mpeg4", "-t", "8", str(path)])
    subprocess.run(command, check=True, capture_output=True, timeout=30)
    return path


def test_wav_falls_back_to_audio_evidence(tmp_path):
    result = scan_recording_v2(make_wav(tmp_path))
    assert result.version == "clip-intelligence-v2-offline"
    assert result.audio_track_found
    assert not result.video_track_found
    assert result.candidates
    assert all(c.evidence == ["audio_peak"] for c in result.candidates)
    assert all(c.requires_human_review for c in result.candidates)
    assert all(0 <= c.start_seconds <= c.event_seconds <= c.end_seconds
               <= result.duration_seconds for c in result.candidates)


def test_consistent_tone_does_not_fabricate_audio_event(tmp_path):
    wav = make_wav(tmp_path, peak_at=())
    result = scan_recording_v2(wav)
    assert result.candidates == []


def test_nearby_audio_and_video_evidence_are_fused():
    events = [
        _Event(time=6, score=70, origin="audio_peak"),
        _Event(time=7, score=80, origin="visual_change"),
        _Event(time=20, score=60, origin="audio_peak"),
    ]
    result = _combine(events, 30, ClipScanSettingsV2())
    assert len(result) == 2
    assert result[0].evidence == ["audio_peak", "visual_change"]
    assert result[0].activity_score == 85
    assert result[1].evidence == ["audio_peak"]


def test_multiple_separated_audio_events_are_not_incorrectly_fused():
    events = [
        _Event(time=4, score=75, origin="audio_peak"),
        _Event(time=17, score=70, origin="audio_peak"),
    ]
    result = _combine(events, 30, ClipScanSettingsV2())
    assert len(result) == 2


def test_max_candidates_limit_and_chronological_sorting():
    events = [_Event(time=i * 12 + 4, score=60 + i, origin="visual_change")
              for i in range(6)]
    result = _combine(events, 100, ClipScanSettingsV2(max_candidates=3))
    assert len(result) == 3
    assert [c.event_seconds for c in result] == sorted(c.event_seconds for c in result)


def test_short_input_does_not_produce_invalid_clip():
    assert not _combine([_Event(time=0.2, score=60, origin="audio_peak")],
                        1.0, ClipScanSettingsV2())


def test_bad_settings_are_rejected():
    with pytest.raises(ValidationError):
        ClipScanSettingsV2(visual_change_threshold=0)
    with pytest.raises(ValidationError):
        ClipScanSettingsV2(max_candidates=30)


def test_endpoint_upload_accepts_wav():
    response = client.post(
        "/api/v1/clips/scan",
        files={"file": ("clip.wav", synthetic_wav(), "audio/wav")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["version"] == "clip-intelligence-v2-offline"


def test_endpoint_rejects_remote_playlist_and_corrupt_wav():
    response = client.post(
        "/api/v1/clips/scan",
        files={"file": ("remote.m3u8", b"#EXTM3U", "text/plain")},
    )
    assert response.status_code == 422
    response = client.post(
        "/api/v1/clips/scan",
        files={"file": ("bad.wav", b"bad", "audio/wav")},
    )
    assert response.status_code == 422


def test_superseded_v1_upload_route_is_not_exposed():
    paths = client.get("/api/v1/openapi.json").json()["paths"]
    assert "/api/v1/clips/scan" in paths
    assert "/v1/demo/clip-intelligence" not in paths


@pytest.mark.skipif(not HAS_FFMPEG, reason="FFmpeg required to test real video frames")
def test_silent_video_scene_change_creates_visual_candidate(tmp_path):
    source = make_scene_video(tmp_path / "scene.mp4")
    result = scan_recording_v2(source)
    assert result.video_track_found and not result.audio_track_found
    assert len(result.candidates) == 1
    assert result.candidates[0].evidence == ["visual_change"]
    assert 3.5 <= result.candidates[0].event_seconds <= 4.5


@pytest.mark.skipif(not HAS_FFMPEG, reason="FFmpeg required to test real video frames")
def test_static_video_does_not_fabricate_visual_candidate(tmp_path):
    source = make_scene_video(tmp_path / "static.mp4", first="black", second="black")
    result = scan_recording_v2(source)
    assert result.candidates == []


@pytest.mark.skipif(not HAS_FFMPEG, reason="FFmpeg required to test real video frames")
def test_video_audio_and_scene_reveal_two_media_signals(tmp_path):
    source = make_scene_video(tmp_path / "both.mp4", with_audio=True)
    result = scan_recording_v2(source)
    assert result.audio_track_found and result.video_track_found
    assert any("visual_change" in c.evidence for c in result.candidates)
    assert all(c.requires_human_review for c in result.candidates)


@pytest.mark.skipif(not HAS_FFMPEG, reason="FFmpeg required to test real video frames")
def test_video_duration_limit_blocks_work(tmp_path):
    source = make_scene_video(tmp_path / "long.mp4")
    # Repeat the recording without adding any external assets.
    longer = tmp_path / "longer.mp4"
    subprocess.run(
        ["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-stream_loop", "1",
         "-i", str(source), "-t", "12", "-c:v", "mpeg4", str(longer)],
        check=True, capture_output=True, timeout=30,
    )
    with pytest.raises(ClipScanError):
        scan_recording_v2(longer, ClipScanSettingsV2(max_duration_seconds=10))


@pytest.mark.skipif(not HAS_FFMPEG, reason="FFmpeg required to test real video frames")
def test_api_upload_silent_video(tmp_path):
    source = make_scene_video(tmp_path / "scene.mp4")
    response = client.post(
        "/api/v1/clips/scan",
        files={"file": ("scene.mp4", source.read_bytes(), "video/mp4")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["candidates"][0]["evidence"] == ["visual_change"]
