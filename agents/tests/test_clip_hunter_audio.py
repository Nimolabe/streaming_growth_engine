import math
import random
import shutil
import wave
from array import array

import pytest

from streaming_agents.clip_hunter.audio_signal import (
    SILENCE_DB,
    MediaError,
    audio_levels,
    check_media_path,
    detect_spikes,
    parse_astats,
    probe_media,
)
from streaming_agents.clip_hunter.models import HuntSettings

needs_ffmpeg = pytest.mark.skipif(not (shutil.which("ffmpeg") and shutil.which("ffprobe")),
                                  reason="FFmpeg nicht installiert")


def test_parse_astats_handles_silence_and_garbage():
    output = """
frame:0    pts:0       pts_time:0
lavfi.astats.Overall.RMS_level=-inf
frame:1    pts:8000    pts_time:0.5
lavfi.astats.Overall.RMS_level=-23.5
frame:2    pts:16000   pts_time:1
lavfi.astats.Overall.RMS_level=nan
lavfi.astats.Overall.RMS_level=-1.0
frame:3    pts:24000   pts_time:kaputt
lavfi.astats.Overall.RMS_level=-3
"""  # Zeile 7 ohne Zeitangabe und Zeile 8 mit kaputter Zeit werden ignoriert
    assert parse_astats(output) == [(0.0, SILENCE_DB), (0.5, -23.5), (1.0, SILENCE_DB)]


def levels(seconds: float, base: float = -30.0, events=(), step: float = 0.5, seed: int = 1):
    rng = random.Random(seed)
    result = []
    for index in range(int(seconds / step)):
        t = index * step
        value = base + rng.uniform(-2, 2)
        for start, length, level in events:
            if start <= t < start + length:
                value = level
        result.append((t, value))
    return result


def test_detects_sudden_spikes_with_onset():
    spikes = detect_spikes(levels(600, events=[(120, 2, -10), (300, 1.5, -12)]), HuntSettings())
    assert [round(s.peak_seconds) for s in spikes] == [120, 300]
    assert all(s.rise_db >= 15 for s in spikes)
    assert all(abs(s.onset_seconds - s.peak_seconds) <= 1 for s in spikes)


def test_silence_to_normal_speech_is_not_a_spike():
    data = levels(600, events=[(200, 60, -70)])  # 1 Minute Stille, dann normal weiter
    assert detect_spikes(data, HuntSettings()) == []


def test_sustained_loud_music_gives_one_spike_not_many():
    data = levels(900, events=[(300, 240, -12)])
    spikes = detect_spikes(data, HuntSettings())
    assert len(spikes) == 1 and round(spikes[0].peak_seconds) == 300


def test_quiet_spikes_below_absolute_floor_are_ignored():
    data = levels(600, base=-70, events=[(200, 2, -50)])
    assert detect_spikes(data, HuntSettings()) == []
    assert detect_spikes(data, HuntSettings(audio_min_level_db=-60))


def test_min_gap_keeps_strongest():
    data = levels(600, events=[(200, 1, -15), (205, 1, -5)])
    spikes = detect_spikes(data, HuntSettings())
    assert len(spikes) == 1
    assert spikes[0].peak_seconds == pytest.approx(205.5, abs=0.6)  # Mitte des lauten Moments


def test_too_short_input():
    assert detect_spikes([(0, -20), (0.5, -10)], HuntSettings()) == []


def test_media_path_checks(tmp_path):
    with pytest.raises(MediaError):
        check_media_path(tmp_path / "fehlt.mp4")
    text = tmp_path / "notes.txt"
    text.write_text("x")
    with pytest.raises(MediaError):
        check_media_path(text)


def write_wav(path, seconds=240, spikes=((60, 2), (150, 1.5)), rate=8000):
    rng = random.Random(5)
    samples = array("h")
    for index in range(rate * seconds):
        t = index / rate
        amp = 0.03 * (1 + 0.4 * math.sin(t * 0.5))
        if any(start <= t < start + length for start, length in spikes):
            amp = 0.3
        samples.append(int(max(-32767, min(32767, rng.gauss(0, amp) * 32767))))
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(samples.tobytes())
    return path


@needs_ffmpeg
def test_real_ffmpeg_levels_and_spikes(tmp_path):
    wav = write_wav(tmp_path / "audio.wav")
    info = probe_media(wav)
    assert info.has_audio and not info.has_video
    assert info.duration_seconds == pytest.approx(240, abs=0.1)
    data = audio_levels(wav, duration_hint=info.duration_seconds)
    assert len(data) == pytest.approx(480, abs=2)
    spikes = detect_spikes(data, HuntSettings())
    assert [round(s.peak_seconds) for s in spikes] == [60, 150]


@needs_ffmpeg
def test_unreadable_media_is_reported(tmp_path):
    fake = tmp_path / "kaputt.mp4"
    fake.write_bytes(b"not a video")
    with pytest.raises(MediaError):
        probe_media(fake)
