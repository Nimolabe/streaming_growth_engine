"""Optional offline export of suggested clips from user-owned local videos."""
import shutil
from pathlib import Path
from subprocess import CalledProcessError, TimeoutExpired, run

from .clip_intelligence import VIDEO_SUFFIXES, ClipScanError
from .clip_intelligence_contracts import ClipScanResult


def export_clip_candidates(
    recording: str | Path,
    result: ClipScanResult,
    output_dir: str | Path,
) -> list[Path]:
    """Write short MP4 review clips; never overwrite existing outputs."""
    source = Path(recording).resolve()
    if not source.is_file() or source.suffix.casefold() not in VIDEO_SUFFIXES:
        raise ClipScanError("Clip export requires an existing local video file.")
    if not shutil.which("ffmpeg"):
        raise ClipScanError("FFmpeg is required to export video clips.")

    destination = Path(output_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    planned = [
        destination / f"review_candidate_{number:02}.mp4"
        for number in range(1, len(result.candidates) + 1)
    ]
    if any(path.exists() for path in planned):
        raise ClipScanError("An output clip already exists. Choose a different folder.")

    produced: list[Path] = []
    try:
        for candidate, output in zip(result.candidates, planned):
            duration = candidate.end_seconds - candidate.start_seconds
            if duration <= 0 or duration > 60:
                raise ClipScanError("Candidate length is invalid for the review export.")
            command = [
                "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                "-n", "-ss", str(candidate.start_seconds),
                "-protocol_whitelist", "file,pipe", "-i", str(source),
                "-t", str(duration),
                "-map", "0:v:0", "-map", "0:a:0?",
                "-c:v", "libx264", "-preset", "veryfast",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart",
                str(output),
            ]
            run(command, check=True, capture_output=True, timeout=120)
            produced.append(output)
    except (CalledProcessError, TimeoutExpired, ClipScanError) as exc:
        for output in planned:
            if output.exists():
                output.unlink()
        raise ClipScanError("Could not export all candidate clips.") from exc
    return produced
