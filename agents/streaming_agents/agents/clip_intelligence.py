"""Local-first acoustic clip-candidate scanner.

Uses PCM WAV directly or FFmpeg to extract a temporary mono WAV from a
user-owned local recording. No network, models, uploads or telemetry.
"""
import json
import shutil
import wave
from array import array
from math import log2, sqrt
from pathlib import Path
from statistics import median
from subprocess import CalledProcessError, TimeoutExpired, run
from sys import byteorder
from tempfile import TemporaryDirectory

from .clip_intelligence_contracts import ClipCandidate, ClipScanResult, ClipScanSettings

VIDEO_SUFFIXES = frozenset({".mp4", ".mov", ".mkv", ".webm"})
SUPPORTED_SUFFIXES = VIDEO_SUFFIXES | {".wav"}
_MAX_FILE_BYTES = 1024 * 1024 * 1024


class ClipScanError(ValueError):
    """A clear, non-sensitive reason the input could not be processed."""


def _wav_levels(path: Path, settings: ClipScanSettings) -> tuple[list[float], float]:
    try:
        with wave.open(str(path), "rb") as audio:
            if audio.getsampwidth() != 2 or audio.getcomptype() != "NONE":
                raise ClipScanError("Only uncompressed 16-bit PCM WAV is supported.")
            if audio.getnchannels() not in (1, 2):
                raise ClipScanError("Audio must have one or two channels.")
            if not 8000 <= audio.getframerate() <= 192000:
                raise ClipScanError("Unsupported audio sample rate.")
            duration = audio.getnframes() / audio.getframerate()
            if duration > settings.max_duration_seconds:
                raise ClipScanError("Recording exceeds the configured duration limit.")
            frame_size = max(1, round(settings.frame_ms * audio.getframerate() / 1000))
            levels = []
            while True:
                raw = audio.readframes(frame_size)
                if not raw:
                    break
                samples = array("h")
                samples.frombytes(raw)
                if byteorder != "little":
                    samples.byteswap()
                if not samples:
                    break
                rms = sqrt(sum(value * value for value in samples) / len(samples))
                levels.append(rms / 32768.0)
            return levels, duration
    except (wave.Error, EOFError, OSError) as exc:
        raise ClipScanError("Recording is not a readable 16-bit PCM WAV.") from exc


def _candidates(levels: list[float], duration: float,
                settings: ClipScanSettings) -> list[ClipCandidate]:
    if not levels or duration < 4:
        return []
    baseline = median(levels)
    threshold = max(settings.absolute_floor, baseline * settings.activity_multiplier)
    active = [level >= threshold for level in levels]
    found = []
    frame_seconds = duration / len(levels)
    start = None

    for index in range(len(active) + 1):
        is_active = index < len(active) and active[index]
        if is_active and start is None:
            start = index
        if not is_active and start is not None:
            if index - start >= settings.min_active_frames:
                peak_index = max(range(start, index), key=lambda i: levels[i])
                peak_second = min(duration, (peak_index + 0.5) * frame_seconds)
                clip_start = max(0.0, peak_second - settings.pre_roll_seconds)
                clip_end = min(duration, peak_second + settings.post_roll_seconds)
                if clip_end - clip_start >= 4:
                    ratio = levels[peak_index] / max(threshold, 1e-8)
                    score = min(100, max(0, round(20 + 28 * log2(max(ratio, 1)))))
                    found.append(ClipCandidate(
                        start_seconds=round(clip_start, 2),
                        end_seconds=round(clip_end, 2),
                        peak_seconds=round(peak_second, 2),
                        audio_activity_score=score,
                        reason=(
                            "Sustained audio-level increase; could be speech, "
                            "music, noise or a reaction. Inspect the context."
                        ),
                    ))
            start = None

    # Retain the strongest nonoverlapping peaks, then return chronological order.
    candidates = sorted(found, key=lambda item: (-item.audio_activity_score, item.peak_seconds))
    chosen: list[ClipCandidate] = []
    for candidate in candidates:
        if any(abs(candidate.peak_seconds - item.peak_seconds)
               < settings.min_gap_seconds for item in chosen):
            continue
        if any(
            (min(candidate.end_seconds, item.end_seconds)
             - max(candidate.start_seconds, item.start_seconds))
            > 0.5 * min(
                candidate.end_seconds - candidate.start_seconds,
                item.end_seconds - item.start_seconds,
            )
            for item in chosen
        ):
            continue
        chosen.append(candidate)
        if len(chosen) >= settings.max_candidates:
            break
    return sorted(chosen, key=lambda item: item.start_seconds)


def scan_wav(path: str | Path, settings: ClipScanSettings | None = None) -> ClipScanResult:
    settings = settings or ClipScanSettings()
    levels, duration = _wav_levels(Path(path), settings)
    clips = _candidates(levels, duration, settings)
    return ClipScanResult(
        analyzed_duration_seconds=round(duration, 2),
        candidates=clips,
        limitations=[
            "This analyzes audio energy only, not emotions or video content.",
            "Loud sounds, music and background noise can trigger false candidates.",
            "Quiet, funny or strategically important moments can be missed.",
            "Scores describe relative audio activity, not a probability of virality.",
            "Every suggested segment requires human review before publishing.",
        ],
        suggested_next_step=(
            "Review candidate segments with context before trimming or sharing."
            if clips else
            "No sufficiently distinct audio peaks found; review the recording manually."
        ),
    )


def _video_wav(path: Path, wav_path: Path, settings: ClipScanSettings) -> None:
    if not shutil.which("ffprobe") or not shutil.which("ffmpeg"):
        raise ClipScanError(
            "FFmpeg and FFprobe are required for video analysis; "
            "use a 16-bit WAV file if they are not installed."
        )
    probe = [
        "ffprobe", "-v", "error", "-protocol_whitelist", "file,pipe",
        "-show_entries", "format=duration:stream=codec_type",
        "-of", "json", str(path),
    ]
    try:
        response = run(probe, capture_output=True, text=True, timeout=30, check=True)
        info = json.loads(response.stdout)
    except (CalledProcessError, TimeoutExpired, json.JSONDecodeError) as exc:
        raise ClipScanError("Could not inspect the local video file.") from exc
    streams = info.get("streams", [])
    if not any(stream.get("codec_type") == "audio" for stream in streams):
        raise ClipScanError("The video does not contain an audio track.")
    try:
        duration = float(info["format"]["duration"])
    except (KeyError, ValueError, TypeError) as exc:
        raise ClipScanError("Could not determine the recording duration.") from exc
    if not 0 < duration <= settings.max_duration_seconds:
        raise ClipScanError("Video duration is invalid or exceeds the configured limit.")

    command = [
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
        "-protocol_whitelist", "file,pipe", "-i", str(path),
        "-vn", "-ac", "1", "-ar", "8000", "-c:a", "pcm_s16le", str(wav_path),
    ]
    try:
        run(command, capture_output=True, timeout=300, check=True)
    except (CalledProcessError, TimeoutExpired) as exc:
        raise ClipScanError("Could not decode the recording's audio.") from exc


def scan_recording(path: str | Path,
                   settings: ClipScanSettings | None = None) -> ClipScanResult:
    settings = settings or ClipScanSettings()
    recording = Path(path).resolve()
    if not recording.is_file() or recording.suffix.casefold() not in SUPPORTED_SUFFIXES:
        raise ClipScanError("A local WAV, MP4, MOV, MKV or WEBM file is required.")
    if recording.stat().st_size > _MAX_FILE_BYTES:
        raise ClipScanError("Recording exceeds the 1 GB local scan limit.")
    if recording.suffix.casefold() == ".wav":
        return scan_wav(recording, settings)
    with TemporaryDirectory(prefix="clip-intelligence-") as directory:
        wav_path = Path(directory) / "decoded.wav"
        _video_wav(recording, wav_path, settings)
        return scan_wav(wav_path, settings)
