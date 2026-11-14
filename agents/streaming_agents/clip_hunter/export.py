"""Schneidet Kandidaten aus der eigenen Aufnahme – wahlweise im Hochformat 9:16.

Das Hochformat ist ein einfacher Mittenausschnitt (für TikTok, Shorts, Reels). Facecam- oder
Untertitel-Layouts kommen später; bis dahin bitte jeden Clip vor dem Hochladen ansehen.
Vorhandene Dateien werden nie überschrieben.
"""
from collections.abc import Callable
from pathlib import Path
from subprocess import CalledProcessError, TimeoutExpired, run

from .audio_signal import MediaError, check_media_path, probe_media, require_ffmpeg
from .models import ClipCandidate

VERTICAL_FILTER = "crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',scale=1080:1920,setsar=1"
MAX_EXPORT_SECONDS = 180


def clip_filename(candidate: ClipCandidate, vertical: bool) -> str:
    total = max(0, round(candidate.start_seconds))  # wie format_hms gerundet
    hours, rest = divmod(total, 3600)
    minutes, seconds = divmod(rest, 60)
    suffix = "_9x16" if vertical else ""
    return (f"clip_{candidate.rank:02}_{candidate.category}_"
            f"{hours}h{minutes:02}m{seconds:02}s{suffix}.mp4")


def export_candidates(recording: str | Path, candidates: list[ClipCandidate],
                      output_dir: str | Path, *, vertical: bool = False,
                      runner: Callable[..., object] = run) -> list[Path]:
    require_ffmpeg()
    source = check_media_path(recording)
    info = probe_media(source)
    if not info.has_video:
        raise MediaError("Für den Export wird eine Videodatei benötigt.")
    destination = Path(output_dir).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    planned = [(candidate, destination / clip_filename(candidate, vertical))
               for candidate in candidates]
    existing = [path.name for _, path in planned if path.exists()]
    if existing:
        raise MediaError(f"Datei existiert bereits ({existing[0]}); anderen Ordner wählen.")

    produced: list[Path] = []
    current: Path | None = None
    try:
        for candidate, output in planned:
            current = output
            start = max(0.0, candidate.start_seconds)
            end = min(candidate.end_seconds, info.duration_seconds)
            length = end - start
            if not 0 < length <= MAX_EXPORT_SECONDS:
                raise MediaError(f"Ungültige Clip-Länge bei Kandidat {candidate.rank}.")
            command = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-n",
                       "-ss", f"{start:.2f}", "-protocol_whitelist", "file,pipe",
                       "-i", str(source), "-t", f"{length:.2f}",
                       "-map", "0:v:0", "-map", "0:a:0?"]
            if vertical:
                command += ["-vf", VERTICAL_FILTER]
            command += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                        "-movflags", "+faststart", str(output)]
            runner(command, check=True, capture_output=True, timeout=600)
            produced.append(output)
            current = None
    except (CalledProcessError, TimeoutExpired, MediaError) as exc:
        for path in [*produced, *([current] if current else [])]:
            if path.exists():
                path.unlink()
        if isinstance(exc, MediaError):
            raise
        raise MediaError("Export fehlgeschlagen; es wurden keine halbfertigen Clips behalten.") \
            from exc
    return produced
