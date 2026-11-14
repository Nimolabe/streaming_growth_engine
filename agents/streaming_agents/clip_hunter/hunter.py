"""Gesamtablauf: Aufnahme und/oder Chat-Mitschnitt rein, sortierte Clip-Kandidaten raus."""
from pathlib import Path

from .audio_signal import MediaError, audio_levels, detect_spikes, probe_media
from .chat_signal import analyze_chat
from .fusion import build_candidates, limitations
from .models import AudioSpike, ChatLog, ChatMoment, ChatStats, HuntResult, HuntSettings


def _alignment_note(language: str, used_recording_start: bool, offset: float) -> str | None:
    if not used_recording_start and not offset:
        return None
    if language == "de":
        note = ("Chat-Zeiten wurden ab Beginn des Mitschnitts gerechnet, weil keine VOD-Startzeit "
                "angegeben war. Wurde der Mitschnitt nicht genau beim Stream-Start begonnen, "
                "mit --vod-start oder --twitch-video ausrichten."
                if used_recording_start else "")
        if offset:
            note = (note + " " if note else "") + f"Manuelle Chat-Verschiebung: {offset:+.1f} s."
        return note
    note = ("Chat times were measured from the start of the recording because no VOD start "
            "was given. If recording did not start with the stream, align with --vod-start "
            "or --twitch-video." if used_recording_start else "")
    if offset:
        note = (note + " " if note else "") + f"Manual chat offset: {offset:+.1f} s."
    return note


def hunt(*, recording: str | Path | None = None, chat_log: ChatLog | None = None,
         vod_start: float | None = None, settings: HuntSettings | None = None,
         twitch_video_id: str | None = None) -> HuntResult:
    """Analysiert eine Aufnahme (Audio) und/oder einen Chat-Mitschnitt."""
    settings = settings or HuntSettings()
    if recording is None and chat_log is None:
        raise ValueError("Es wird eine Aufnahme, ein Chat-Mitschnitt oder beides benötigt.")

    duration: float | None = None
    spikes: list[AudioSpike] = []
    audio_used = False
    if recording is not None:
        info = probe_media(recording)
        duration = info.duration_seconds
        if info.has_audio:
            levels = audio_levels(recording, settings.audio_frame_seconds,
                                  duration_hint=duration)
            spikes = detect_spikes(levels, settings)
            audio_used = True
        elif chat_log is None:
            raise MediaError("Die Aufnahme hat keine Tonspur.")

    moments: list[ChatMoment] = []
    chat_stats: ChatStats | None = None
    used_recording_start = False
    if chat_log is not None:
        if vod_start is None:
            vod_start = chat_log.header.started_at
            used_recording_start = True
        moments, chat_stats = analyze_chat(chat_log, settings, vod_start, duration)
        if duration is None and chat_log.messages:
            duration = max(0.0, chat_log.messages[-1].ts - vod_start
                           + settings.chat_offset_seconds)

    mode = ("chat+audio" if audio_used and chat_log is not None
            else "audio" if audio_used else "chat")
    candidates = build_candidates(moments, chat_stats, spikes, duration, settings,
                                  twitch_video_id=twitch_video_id)
    return HuntResult(
        language=settings.language,
        duration_seconds=round(duration, 1) if duration is not None else None,
        mode=mode,
        chat=chat_stats,
        audio_spikes_found=len(spikes),
        chat_moments_found=len(moments),
        alignment_note=_alignment_note(settings.language, used_recording_start,
                                       settings.chat_offset_seconds) if chat_log else None,
        candidates=candidates,
        limitations=limitations(settings.language, mode, chat_stats),
    )
