"""Offline clip intelligence tests with synthetic, user-independent PCM audio."""
import json
import shutil
import subprocess
import wave
from array import array
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from streaming_agents.agents.clip_export import export_clip_candidates
from streaming_agents.agents.clip_intelligence import (
    ClipScanError,
    scan_recording,
    scan_wav,
)
from streaming_agents.agents.clip_intelligence_contracts import (
    ClipCandidate,
    ClipScanResult,
    ClipScanSettings,
)
from streaming_agents.api import app
from streaming_agents.clip_cli import main

client = TestClient(app)


def wav_bytes(*, seconds=30, peaks=((5, 8), (21, 24)), background=300,
              loud=13000, channels=1):
    frame_rate = 8000
    frames_per_quarter = frame_rate // 4
    output = BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(channels)
        audio.setsampwidth(2)
        audio.setframerate(frame_rate)
        for quarter in range(seconds * 4):
            now = quarter / 4
            amplitude = loud if any(start <= now < end for start, end in peaks) else background
            samples = array("h", [amplitude]) * (frames_per_quarter * channels)
            audio.writeframes(samples.tobytes())
    return output.getvalue()


def write_file(tmp_path, **kwargs):
    path = tmp_path / "recording.wav"
    path.write_bytes(wav_bytes(**kwargs))
    return path


def test_two_distinct_audio_bursts_produce_two_chronological_candidates(tmp_path):
    result = scan_recording(write_file(tmp_path))
    assert result.version == "clip-intelligence-v1-offline"
    assert result.analysis_type == "audio_activity"
    assert result.analyzed_duration_seconds == 30
    assert len(result.candidates) == 2
    assert result.candidates[0].peak_seconds < result.candidates[1].peak_seconds
    assert all(candidate.start_seconds <= candidate.peak_seconds
               <= candidate.end_seconds for candidate in result.candidates)
    assert all(candidate.needs_human_review for candidate in result.candidates)


def test_no_signal_does_not_invent_candidate(tmp_path):
    result = scan_wav(write_file(tmp_path, peaks=(), background=0))
    assert result.candidates == []
    assert "No sufficiently distinct" in result.suggested_next_step


def test_constant_loudness_does_not_look_like_a_highlight(tmp_path):
    result = scan_wav(write_file(tmp_path, peaks=(), background=12000))
    assert result.candidates == []


def test_single_impulse_is_ignored(tmp_path):
    path = write_file(tmp_path, peaks=((10, 10.25),))
    result = scan_wav(path)
    assert result.candidates == []


def test_timestamps_remain_inside_recording_duration(tmp_path):
    path = write_file(tmp_path, seconds=12, peaks=((1, 3), (9, 11)))
    result = scan_wav(path, ClipScanSettings(min_gap_seconds=0))
    assert result.candidates
    assert all(0 <= x.start_seconds <= x.peak_seconds <= x.end_seconds <= 12
               for x in result.candidates)


def test_candidate_count_is_bounded(tmp_path):
    path = write_file(tmp_path)
    settings = ClipScanSettings(max_candidates=1)
    assert len(scan_recording(path, settings).candidates) == 1


def test_unknown_file_does_not_trigger_external_access(tmp_path):
    with pytest.raises(ClipScanError):
        scan_recording(tmp_path / "not-here.mp4")
    invalid = tmp_path / "fake.m3u8"
    invalid.write_text("#EXTM3U")
    with pytest.raises(ClipScanError):
        scan_recording(invalid)


def test_invalid_or_compressed_wav_is_rejected(tmp_path):
    bogus = tmp_path / "bogus.wav"
    bogus.write_bytes(b"not a wav")
    with pytest.raises(ClipScanError):
        scan_wav(bogus)


def test_duration_limit_is_enforced_before_processing(tmp_path):
    path = write_file(tmp_path, seconds=30)
    with pytest.raises(ClipScanError):
        scan_wav(path, ClipScanSettings(max_duration_seconds=20))


def test_invalid_settings_rejected():
    with pytest.raises(ValidationError):
        ClipScanSettings(max_candidates=11)
    with pytest.raises(ValidationError):
        ClipScanSettings(pre_roll_seconds=0, post_roll_seconds=0)


def test_upload_does_not_trust_supplied_file_path():
    response = client.post(
        "/api/v1/clips/scan",
        files={"file": ("../../outside.wav", wav_bytes(), "audio/wav")},
    )
    assert response.status_code == 200


def test_upload_rejects_unapproved_file_type():
    response = client.post(
        "/api/v1/clips/scan",
        files={"file": ("remote.m3u8", b"#EXTM3U", "text/plain")},
    )
    assert response.status_code == 422


def test_upload_rejects_invalid_max_candidates():
    response = client.post(
        "/api/v1/clips/scan?max_candidates=100",
        files={"file": ("sample.wav", wav_bytes(), "audio/wav")},
    )
    assert response.status_code == 422


def test_upload_does_not_accept_corrupt_wav():
    response = client.post(
        "/api/v1/clips/scan",
        files={"file": ("sample.wav", b"bad audio", "audio/wav")},
    )
    assert response.status_code == 422


def test_scanner_only_reports_audio_activity_not_semantic_quality(tmp_path):
    result = scan_recording(write_file(tmp_path))
    assert result.analysis_type == "audio_activity"
    assert all(0 <= c.audio_activity_score <= 100 for c in result.candidates)
    assert all("music" in c.reason.lower() for c in result.candidates)
    assert all(c.needs_human_review for c in result.candidates)


@pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="FFmpeg is optional on the test host",
)
def test_real_local_mp4_audio_decode(tmp_path):
    source = tmp_path / "synthetic.mp4"
    command = [
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "color=size=64x64:rate=2:duration=6",
        "-f", "lavfi", "-i", "sine=frequency=500:sample_rate=8000:duration=6",
        "-t", "6", "-c:v", "mpeg4", "-c:a", "aac", str(source),
    ]
    subprocess.run(command, check=True, capture_output=True, timeout=25)
    result = scan_recording(source)
    assert 5 <= result.analyzed_duration_seconds <= 7
    assert result.audio_available is True

    # An export requires a real video input and must produce a reviewable MP4.
    chosen = ClipScanResult(
        analyzed_duration_seconds=result.analyzed_duration_seconds,
        suggested_next_step="Review this clip",
        candidates=[
            ClipCandidate(
                start_seconds=0,
                end_seconds=4,
                peak_seconds=2,
                audio_activity_score=50,
                reason="Synthetic test",
            )
        ],
    )
    outputs = export_clip_candidates(source, chosen, tmp_path / "exported")
    assert len(outputs) == 1
    assert outputs[0].exists()
    assert outputs[0].stat().st_size > 0
    with pytest.raises(ClipScanError):
        export_clip_candidates(source, chosen, tmp_path / "exported")


def test_cli_writes_candidate_json(tmp_path):
    video = write_file(tmp_path)
    target = tmp_path / "candidates.json"
    result = main(["--input", str(video), "--json", str(target)])
    assert result == 0
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["analysis_type"] == "audio_activity"
    assert len(data["candidates"]) == 2


def test_cli_refuses_to_overwrite_json(tmp_path):
    video = write_file(tmp_path)
    target = tmp_path / "candidates.json"
    target.write_text("already exists")
    with pytest.raises(SystemExit) as caught:
        main(["--input", str(video), "--json", str(target)])
    assert caught.value.code == 2
    assert target.read_text() == "already exists"


def test_clip_export_rejects_wav_file(tmp_path):
    source = write_file(tmp_path)
    result = scan_wav(source)
    with pytest.raises(ClipScanError):
        export_clip_candidates(source, result, tmp_path / "clips")


def test_clip_export_refuses_existing_output(tmp_path, monkeypatch):
    source = tmp_path / "synthetic.mp4"
    source.write_bytes(b"placeholder")
    output_dir = tmp_path / "clips"
    output_dir.mkdir()
    (output_dir / "review_candidate_01.mp4").write_bytes(b"existing")
    monkeypatch.setattr("streaming_agents.agents.clip_export.shutil.which", lambda _: "ffmpeg")
    reference = scan_wav(write_file(tmp_path))
    with pytest.raises(ClipScanError):
        export_clip_candidates(source, reference, output_dir)
    assert (output_dir / "review_candidate_01.mp4").read_bytes() == b"existing"
