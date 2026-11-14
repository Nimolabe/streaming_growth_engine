"""Plötzliche Lautstärke-Spitzen in langen Aufnahmen finden (lokal mit FFmpeg).

FFmpeg berechnet die Lautstärke (RMS in dBFS) pro Halbsekunde direkt beim Dekodieren;
Python verarbeitet nur diese Zahlenreihe. Dadurch funktionieren auch mehrstündige VODs
ohne großen Speicherbedarf. Eine Spitze ist ein deutlicher Anstieg gegenüber der
Lautstärke der vorangegangenen Sekunden – nicht einfach „die lautesten Stellen“.
"""
import json
import shutil
from bisect import bisect_left, insort
from collections.abc import Callable
from dataclasses import dataclass
from itertools import pairwise
from math import isnan, log10
from pathlib import Path
from statistics import median
from subprocess import CalledProcessError, TimeoutExpired, run

from .models import AudioSpike, HuntSettings

MEDIA_SUFFIXES = frozenset({".mp4", ".mkv", ".mov", ".webm", ".flv", ".ts", ".wav", ".mp3",
                            ".m4a", ".aac", ".flac", ".ogg", ".opus"})
SILENCE_DB = -120.0
_RMS_KEY = "lavfi.astats.Overall.RMS_level="


class MediaError(ValueError):
    """Verständlicher Grund, warum eine Aufnahme nicht verarbeitet werden kann."""


@dataclass(frozen=True)
class MediaInfo:
    duration_seconds: float
    has_audio: bool
    has_video: bool
    width: int | None = None
    height: int | None = None


def require_ffmpeg() -> None:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise MediaError(
            "FFmpeg und FFprobe werden benötigt (https://ffmpeg.org). "
            "Nach der Installation muss `ffmpeg -version` in der Konsole funktionieren."
        )


def check_media_path(path: str | Path) -> Path:
    media = Path(path).expanduser().resolve()
    if not media.is_file():
        raise MediaError(f"Datei nicht gefunden: {media}")
    if media.suffix.casefold() not in MEDIA_SUFFIXES:
        raise MediaError("Nicht unterstütztes Dateiformat. Erlaubt: "
                         + ", ".join(sorted(MEDIA_SUFFIXES)))
    return media


def probe_media(path: str | Path) -> MediaInfo:
    require_ffmpeg()
    media = check_media_path(path)
    command = ["ffprobe", "-v", "error", "-protocol_whitelist", "file,pipe",
               "-show_entries", "format=duration:stream=codec_type,width,height",
               "-of", "json", str(media)]
    try:
        response = run(command, capture_output=True, text=True, timeout=60, check=True)
        info = json.loads(response.stdout)
        duration = float(info["format"]["duration"])
    except (CalledProcessError, TimeoutExpired, json.JSONDecodeError, KeyError, TypeError,
            ValueError) as exc:
        raise MediaError("Die Aufnahme konnte nicht gelesen werden.") from exc
    streams = info.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    return MediaInfo(
        duration_seconds=duration,
        has_audio=any(item.get("codec_type") == "audio" for item in streams),
        has_video=video is not None,
        width=video.get("width") if video else None,
        height=video.get("height") if video else None,
    )


def parse_astats(output: str) -> list[tuple[float, float]]:
    """Liest Zeit/Lautstärke-Paare aus der `ametadata`-Ausgabe von FFmpeg."""
    levels: list[tuple[float, float]] = []
    current_time: float | None = None
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("frame:"):
            current_time = None
            for part in line.split():
                if part.startswith("pts_time:"):
                    try:
                        current_time = float(part.split(":", 1)[1])
                    except ValueError:
                        current_time = None
        elif line.startswith(_RMS_KEY) and current_time is not None:
            raw = line[len(_RMS_KEY):]
            try:
                value = float(raw)
            except ValueError:
                value = SILENCE_DB
            if isnan(value) or value < SILENCE_DB:  # NaN oder -inf
                value = SILENCE_DB
            levels.append((current_time, min(value, 0.0)))
            current_time = None
    return levels


def audio_levels(path: str | Path, frame_seconds: float = 0.5, *,
                 duration_hint: float | None = None,
                 runner: Callable[..., object] = run) -> list[tuple[float, float]]:
    """Lautstärke pro Zeitabschnitt (Sekunde, dBFS) für die ganze Aufnahme."""
    require_ffmpeg()
    media = check_media_path(path)
    samples = max(160, round(16000 * frame_seconds))
    audio_filter = (
        "aformat=channel_layouts=mono,aresample=16000,"
        f"asetnsamples=n={samples}:p=0,astats=metadata=1:reset=1,"
        "ametadata=mode=print:key=lavfi.astats.Overall.RMS_level:file=-"
    )
    command = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
               "-protocol_whitelist", "file,pipe", "-i", str(media),
               "-vn", "-af", audio_filter, "-f", "null", "-"]
    timeout = 300 + (duration_hint or 3600) * 0.5
    try:
        response = runner(command, capture_output=True, text=True, timeout=timeout, check=True)
    except TimeoutExpired as exc:
        raise MediaError("Die Audio-Analyse hat zu lange gedauert.") from exc
    except CalledProcessError as exc:
        raise MediaError("Die Tonspur konnte nicht dekodiert werden.") from exc
    levels = parse_astats(response.stdout)
    if not levels:
        raise MediaError("In der Aufnahme wurde keine auswertbare Tonspur gefunden.")
    return levels


def _power_mean_db(values: list[float]) -> float:
    power = sum(10 ** (value / 10) for value in values) / len(values)
    return 10 * log10(power) if power > 0 else SILENCE_DB


def detect_spikes(levels: list[tuple[float, float]], settings: HuntSettings) -> list[AudioSpike]:
    """Findet plötzliche Anstiege gegenüber der Lautstärke der vorherigen Sekunden."""
    if len(levels) < 4:
        return []
    times = [time for time, _ in levels]
    values = [value for _, value in levels]
    step = max(1e-3, median(b - a for a, b in pairwise(times)))
    short = max(1, round(1.0 / step))
    history_size = max(4, round(settings.audio_baseline_seconds / step))
    audible = [value for value in values if value > SILENCE_DB + 1]
    # Typische Lautstärke der ganzen Aufnahme: Wechsel von Stille zu normalem Reden
    # soll keine Spitze sein.
    typical = median(audible) if audible else SILENCE_DB

    history: list[float] = []
    rises: list[float] = [0.0] * len(values)
    levels_short: list[float] = [SILENCE_DB] * len(values)
    for index in range(len(values)):
        if index > 0:
            insort(history, values[index - 1])
            leaving = index - 1 - history_size
            if leaving >= 0:
                history.pop(bisect_left(history, values[leaving]))
        if len(history) < min(history_size, 10):
            continue
        local = history[len(history) // 2]
        baseline = max(local, typical - 3)
        level = _power_mean_db(values[index:index + short])
        levels_short[index] = level
        rises[index] = level - baseline

    candidates = [index for index, rise in enumerate(rises)
                  if rise >= settings.audio_min_rise_db
                  and levels_short[index] >= settings.audio_min_level_db]
    chosen: list[int] = []
    for index in sorted(candidates, key=lambda item: (-rises[item], item)):
        if all(abs(times[index] - times[other]) >= settings.audio_min_gap_seconds
               for other in chosen):
            chosen.append(index)

    spikes = []
    max_back = max(1, round(10 / step))
    for strongest in sorted(chosen):
        # Bei länger anhaltendem Lärm den frühesten fast gleich starken Punkt nehmen,
        # damit der Höhepunkt nicht mitten in der lauten Phase liegt.
        index = strongest
        while (index > 0 and strongest - index < max_back
               and rises[index - 1] >= settings.audio_min_rise_db
               and rises[index - 1] >= rises[strongest] - 2):
            index -= 1
        onset = index
        half_rise = max(3.0, rises[index] / 2)
        while onset > 0 and index - onset < max_back and rises[onset - 1] >= half_rise:
            onset -= 1
        peak_offset = min(short, len(values) - index) * step / 2
        spikes.append(AudioSpike(
            peak_seconds=round(times[index] + peak_offset, 2),
            onset_seconds=round(times[onset], 2),
            rise_db=round(rises[strongest], 1),
            level_db=round(levels_short[strongest], 1),
        ))
    return spikes
