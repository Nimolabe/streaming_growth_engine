"""Reproducible synthetic benchmark, NOT evidence of real clip quality.

Labels refer to known artificial hard scene cuts, not human-rated highlights.
"""
import shutil
import subprocess

import pytest

from streaming_agents.agents.clip_intelligence_v2 import scan_recording_v2

HAS_VIDEO_TOOL = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
pytestmark = pytest.mark.skipif(not HAS_VIDEO_TOOL, reason="FFmpeg is required for this benchmark")


def make_video(tmp_path, *, cut: bool):
    output = tmp_path / ("hard_cut.mp4" if cut else "constant.mp4")
    first = "black"
    second = "white" if cut else "black"
    command = [
        "ffmpeg", "-nostdin", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", f"color=c={first}:size=64x64:rate=4:duration=4",
        "-f", "lavfi", "-i", f"color=c={second}:size=64x64:rate=4:duration=4",
        "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]",
        "-map", "[v]", "-c:v", "mpeg4", "-t", "8", str(output),
    ]
    subprocess.run(command, check=True, capture_output=True, timeout=30)
    return output


def count_matching(detected, truth, tolerance=1.0):
    remaining = list(detected)
    matched = 0
    for target in truth:
        closest = min(remaining, key=lambda x: abs(x - target), default=None)
        if closest is not None and abs(closest - target) <= tolerance:
            matched += 1
            remaining.remove(closest)
    precision = matched / len(detected) if detected else (1.0 if not truth else 0.0)
    recall = matched / len(truth) if truth else 1.0
    return matched, precision, recall


def test_synthetic_cut_detection_and_static_false_alarm_rate(tmp_path):
    positives = scan_recording_v2(make_video(tmp_path, cut=True))
    negatives = scan_recording_v2(make_video(tmp_path, cut=False))
    detected_positive = [item.event_seconds for item in positives.candidates]
    detected_negative = [item.event_seconds for item in negatives.candidates]

    matched, precision, recall = count_matching(detected_positive, [4.0])
    assert matched == 1
    assert precision == 1.0
    assert recall == 1.0
    assert detected_negative == []

    # This controlled score is NOT representative of real gaming content.
    _, static_precision, static_recall = count_matching(detected_negative, [])
    assert static_precision == static_recall == 1.0


def test_benchmark_scoring_penalizes_extra_false_alarms():
    assert count_matching([4.0, 5.5], [4.0]) == (1, 0.5, 1.0)
    assert count_matching([], [4.0]) == (0, 0.0, 0.0)
