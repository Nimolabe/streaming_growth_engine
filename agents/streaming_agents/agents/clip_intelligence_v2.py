"""Conservative, fully offline *multi-signal* clip review candidates.

This deliberately avoids "virality" scores. Bright visual changes and
relative audio peaks can only locate possible review moments, never judge
storytelling, jokes, gameplay importance or audience preference.
"""
import json
import math
import shutil
from dataclasses import dataclass
from pathlib import Path
from subprocess import CalledProcessError, TimeoutExpired, run
from tempfile import TemporaryDirectory

from .clip_intelligence import (
    SUPPORTED_SUFFIXES,
    VIDEO_SUFFIXES,
    ClipScanError,
    _candidates,
    _video_wav,
    _wav_levels,
)
from .clip_intelligence_contracts import ClipScanSettings
from .clip_intelligence_v2_contracts import (
    ClipReviewCandidateV2,
    ClipReviewResultV2,
    ClipScanSettingsV2,
)

_WIDTH = 32
_HEIGHT = 18
_FRAME_BYTES = _WIDTH * _HEIGHT
_FRAMES_PER_SECOND = 2
_MAX_FILE_BYTES = 1024 * 1024 * 1024


@dataclass(frozen=True)
class _Event:
    time: float
    score: int
    origin: str


def _probe_video(path: Path, max_seconds: int) -> tuple[float, bool, bool]:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise ClipScanError("FFmpeg and FFprobe are required to scan videos.")
    try:
        completed = run(
            [
                "ffprobe", "-v", "error", "-protocol_whitelist", "file,pipe",
                "-show_entries", "format=duration:stream=codec_type",
                "-of", "json", str(path),
            ],
            capture_output=True, check=True, timeout=30, text=True,
        )
        info = json.loads(completed.stdout)
        duration = float(info["format"]["duration"])
    except (CalledProcessError, TimeoutExpired, ValueError, KeyError, TypeError) as exc:
        raise ClipScanError("Could not read the local video's track metadata.") from exc

    if not math.isfinite(duration) or not 0 < duration <= max_seconds:
        raise ClipScanError("Invalid or excessive video duration.")
    streams = info.get("streams", [])
    if not isinstance(streams, list):
        raise ClipScanError("Unexpected video track metadata.")
    audio = any(isinstance(s, dict) and s.get("codec_type") == "audio" for s in streams)
    video = any(isinstance(s, dict) and s.get("codec_type") == "video" for s in streams)
    if not video:
        raise ClipScanError("Video input must contain a video track.")
    return duration, audio, video


def _visual_events(
    path: Path, duration: float, settings: ClipScanSettingsV2,
) -> list[_Event]:
    """Inspect small gray frames; fixed sampling keeps memory and work bounded."""
    if duration > settings.max_duration_seconds:
        raise ClipScanError("Video duration exceeds the configured scan limit.")
    command = [
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-protocol_whitelist", "file,pipe", "-i", str(path),
        "-map", "0:v:0", "-an",
        "-vf", f"fps={_FRAMES_PER_SECOND},scale={_WIDTH}:{_HEIGHT}:flags=fast_bilinear,format=gray",
        "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1",
    ]
    try:
        completed = run(command, capture_output=True, timeout=300, check=True)
    except (CalledProcessError, TimeoutExpired) as exc:
        raise ClipScanError("Unable to decode local video frames.") from exc

    data = completed.stdout
    max_frames = math.ceil(duration * _FRAMES_PER_SECOND) + 3
    if len(data) > max_frames * _FRAME_BYTES or len(data) % _FRAME_BYTES:
        raise ClipScanError("Video frame decoding produced unexpected data size.")
    frames = len(data) // _FRAME_BYTES
    if frames < 2:
        return []

    found: list[_Event] = []
    last_event = float("-inf")
    last = memoryview(data)[:_FRAME_BYTES]
    for index in range(1, frames):
        current = memoryview(data)[index * _FRAME_BYTES:(index + 1) * _FRAME_BYTES]
        # Normalized mean per-pixel change. Motion/camera cuts are NOT
        # distinguishable at this resolution; reviewers must verify context.
        changed = sum(abs(a - b) for a, b in zip(last, current)) / (255 * _FRAME_BYTES)
        timestamp = min(duration, index / _FRAMES_PER_SECOND)
        if (changed >= settings.visual_change_threshold
                and timestamp - last_event >= settings.min_event_gap_seconds):
            score = min(100, round(35 + 65 * changed))
            found.append(_Event(timestamp, score, "visual_change"))
            last_event = timestamp
        last = current
    return found


def _audio_events(
    path: Path, settings: ClipScanSettingsV2,
) -> tuple[list[_Event], float]:
    audio_settings = ClipScanSettings(
        max_duration_seconds=settings.max_duration_seconds,
        max_candidates=10,
        min_gap_seconds=settings.min_event_gap_seconds,
        pre_roll_seconds=settings.pre_roll_seconds,
        post_roll_seconds=settings.post_roll_seconds,
    )
    levels, duration = _wav_levels(path, audio_settings)
    candidates = _candidates(levels, duration, audio_settings)
    return [
        _Event(candidate.peak_seconds, candidate.audio_activity_score, "audio_peak")
        for candidate in candidates
    ], duration


def _combine(
    events: list[_Event], duration: float, settings: ClipScanSettingsV2,
) -> list[ClipReviewCandidateV2]:
    """Merge nearby *different* evidence sources; do not merge unrelated peaks."""
    ordered = sorted(events, key=lambda e: (e.time, e.origin))
    groups: list[list[_Event]] = []
    for event in ordered:
        if (
            groups
            and event.time - groups[-1][0].time <= 2.0
            and event.origin not in {item.origin for item in groups[-1]}
        ):
            groups[-1].append(event)
        else:
            groups.append([event])

    result: list[ClipReviewCandidateV2] = []
    for group in groups:
        reference = max(group, key=lambda e: (e.score, -e.time))
        start = max(0.0, reference.time - settings.pre_roll_seconds)
        end = min(duration, reference.time + settings.post_roll_seconds)
        if end - start < 4:
            continue
        sources = sorted({item.origin for item in group})
        score = max(item.score for item in group)
        if len(sources) == 2:
            score = min(100, score + 5)
        explanation = (
            "A local audio-level increase and a visual-frame change occurred close together."
            if len(sources) == 2
            else "A local audio-level increase was detected; verify speech/music/noise."
            if sources == ["audio_peak"]
            else "A large visual-frame change was detected; verify gameplay/camera/overlay."
        )
        result.append(ClipReviewCandidateV2(
            start_seconds=round(start, 2),
            end_seconds=round(end, 2),
            event_seconds=round(reference.time, 2),
            evidence=sources,
            activity_score=score,
            explanation=explanation,
        ))

    # Prefer corroborating evidence, then activity, then earliest occurrence.
    ranked = sorted(
        result,
        key=lambda c: (-len(c.evidence), -c.activity_score, c.event_seconds),
    )
    selected: list[ClipReviewCandidateV2] = []
    for item in ranked:
        if any(
            abs(item.event_seconds - previous.event_seconds)
            < settings.min_event_gap_seconds for previous in selected
        ):
            continue
        selected.append(item)
        if len(selected) == settings.max_candidates:
            break
    return sorted(selected, key=lambda c: c.event_seconds)


def scan_recording_v2(
    path: str | Path, settings: ClipScanSettingsV2 | None = None,
) -> ClipReviewResultV2:
    settings = settings or ClipScanSettingsV2()
    recording = Path(path).resolve()
    if not recording.is_file() or recording.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ClipScanError("Provide an existing local WAV, MP4, MOV, MKV or WEBM file.")
    if recording.stat().st_size > _MAX_FILE_BYTES:
        raise ClipScanError("Local recording exceeds the 1 GB scan limit.")

    is_video = recording.suffix.lower() in VIDEO_SUFFIXES
    if is_video:
        duration, audio_present, _ = _probe_video(recording, settings.max_duration_seconds)
        visual = _visual_events(recording, duration, settings)
        if audio_present:
            with TemporaryDirectory(prefix="clip-review-v2-") as directory:
                wav_file = Path(directory) / "audio.wav"
                basic = ClipScanSettings(max_duration_seconds=settings.max_duration_seconds)
                _video_wav(recording, wav_file, basic)
                audio, _ = _audio_events(wav_file, settings)
        else:
            audio = []
    else:
        visual = []
        audio, duration = _audio_events(recording, settings)
        audio_present = True

    return ClipReviewResultV2(
        duration_seconds=round(duration, 2),
        audio_track_found=audio_present,
        video_track_found=is_video,
        candidates=_combine(audio + visual, duration, settings),
        limitations=[
            "Audio energy and pixel changes are only review cues; this does not understand gameplay.",
            "Volume changes, music, flashes, overlays and camera movement can produce false positives.",
            "Quiet clutch plays, jokes or useful conversations can be missed entirely.",
            "Activity scores are heuristic ranking values, NOT virality or growth probabilities.",
            "Time ranges require human review and publication permission.",
        ],
        review_guidance=(
            "Review all candidate windows in context, then select and edit manually."
            if audio or visual else
            "No distinctive cues found. Review the original recording manually."
        ),
    )
