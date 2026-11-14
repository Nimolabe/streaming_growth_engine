"""Führt Chat-Momente und Audio-Spitzen zu bewerteten Clip-Kandidaten zusammen.

Grundidee: Reagiert der Chat *und* gibt es eine Audio-Spitze kurz davor, ist es mit hoher
Wahrscheinlichkeit ein echter Moment. Audio legt dabei den genauen Zeitpunkt fest, der Chat
liefert die Art der Reaktion. Eine Audio-Spitze ohne Chat-Reaktion zählt bei aktivem Chat
nur wenig (vermutlich Alert, Musik oder Lärm), bei kleinem oder fehlendem Chat dagegen voll.
"""
from .models import (
    AudioEvidence,
    AudioSpike,
    ChatEvidence,
    ChatMoment,
    ChatStats,
    ClipCandidate,
    HuntSettings,
    Language,
)

CATEGORY_LABELS = {
    "de": {"funny": "lustig", "hype": "Hype", "shock": "Schock", "fail": "Fail",
           "tension": "Spannung", "loud": "laut", "reaction": "Reaktion"},
    "en": {"funny": "funny", "hype": "hype", "shock": "shock", "fail": "fail",
           "tension": "tension", "loud": "loud", "reaction": "reaction"},
}
ALERT_LABELS = {
    "de": {"raid": "Raid", "gift": "Sub-Geschenk", "sub": "Sub", "cheer": "Bits",
           "announcement": "Ankündigung", "event": "Ereignis"},
    "en": {"raid": "raid", "gift": "gifted sub", "sub": "sub", "cheer": "bits",
           "announcement": "announcement", "event": "event"},
}


def format_hms(seconds: float) -> str:
    total = max(0, round(seconds))
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02}:{secs:02}"


def twitch_vod_link(video_id: str, seconds: float) -> str:
    total = max(0, int(seconds))
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    return f"https://www.twitch.tv/videos/{video_id}?t={hours}h{minutes}m{secs}s"


def _chat_strength(moment: ChatMoment) -> float:
    return min(1.0, moment.z_score / 12) * (0.7 + 0.3 * moment.reaction_share)


def _audio_strength(spike: AudioSpike) -> float:
    return max(0.0, min(1.0, (spike.rise_db - 6) / 18))


def _chat_reason(moment: ChatMoment, language: Language) -> str:
    ratio = moment.chatters / max(moment.baseline_chatters, 1)
    label = CATEGORY_LABELS[language][moment.dominant_category]
    share = round(moment.reaction_share * 100)
    if language == "de":
        text = (f"Chat-Ausschlag: {moment.chatters} verschiedene Chatter in wenigen Sekunden "
                f"(etwa {ratio:.1f}× so viele wie normal), {share} % mit Reaktions-Emotes")
        if moment.dominant_category != "reaction":
            text += f", überwiegend {label}"
    else:
        text = (f"Chat spike: {moment.chatters} different chatters within seconds "
                f"(about {ratio:.1f}× the usual rate), {share}% with reaction emotes")
        if moment.dominant_category != "reaction":
            text += f", mostly {label}"
    return text + "."


def _audio_reason(spike: AudioSpike, language: Language) -> str:
    if language == "de":
        return f"Plötzlicher Lautstärke-Anstieg um {spike.rise_db:.0f} dB."
    return f"Sudden loudness increase of {spike.rise_db:.0f} dB."


def _alert_reason(kind: str, language: Language) -> str:
    label = ALERT_LABELS[language].get(kind, kind)
    if language == "de":
        return f"Achtung: kurz davor gab es ein {label}-Ereignis – evtl. nur eine Alert-Reaktion."
    return f"Note: a {label} event happened just before – this may only be an alert reaction."


def _quiet_chat_reason(language: Language) -> str:
    if language == "de":
        return "Der Chat hat hier nicht auffällig reagiert."
    return "The chat did not react noticeably here."


def _window(anchor: float, duration: float | None, settings: HuntSettings) -> tuple[float, float]:
    start = anchor - settings.pre_roll_seconds
    end = anchor + settings.post_roll_seconds
    length = min(max(end - start, settings.min_clip_seconds), settings.max_clip_seconds)
    start = max(0.0, start)
    end = start + length
    if duration is not None and end > duration:
        end = duration
        start = max(0.0, end - length)
    return round(start, 1), round(end, 1)


def build_candidates(moments: list[ChatMoment], chat: ChatStats | None,
                     spikes: list[AudioSpike], duration: float | None,
                     settings: HuntSettings, *,
                     twitch_video_id: str | None = None) -> list[ClipCandidate]:
    language = settings.language
    chat_level = chat.level if chat else None
    raw: list[dict] = []
    used_spikes: set[int] = set()

    for moment in sorted(moments, key=lambda item: -item.z_score):
        low = moment.event_seconds - settings.match_tolerance_seconds
        high = moment.peak_seconds + 2
        options = [(index, spike) for index, spike in enumerate(spikes)
                   if index not in used_spikes and low <= spike.peak_seconds <= high]
        match = max(options, key=lambda item: item[1].rise_db) if options else None
        chat_s = _chat_strength(moment)
        reasons = [_chat_reason(moment, language)]
        if match:
            used_spikes.add(match[0])
            spike = match[1]
            score = 0.6 * chat_s + 0.4 * _audio_strength(spike) + 0.2
            anchor = spike.peak_seconds
            reasons.append(_audio_reason(spike, language))
            signals = ["chat", "audio"]
        else:
            spike = None
            score = 0.85 * chat_s
            anchor = moment.event_seconds
            signals = ["chat"]
        if moment.alert_nearby:
            score *= 0.5
            reasons.append(_alert_reason(moment.alert_nearby, language))
        raw.append({"anchor": anchor, "score": min(1.0, score), "moment": moment,
                    "spike": spike, "signals": signals, "reasons": reasons})

    for index, spike in enumerate(spikes):
        if index in used_spikes:
            continue
        weight = {"active": 0.35, "low": 0.6}.get(chat_level or "", 0.9)
        reasons = [_audio_reason(spike, language)]
        if chat_level in {"active", "low"}:
            reasons.append(_quiet_chat_reason(language))
        raw.append({"anchor": spike.peak_seconds, "score": weight * _audio_strength(spike),
                    "moment": None, "spike": spike, "signals": ["audio"], "reasons": reasons})

    chosen: list[dict] = []
    for item in sorted(raw, key=lambda entry: (-entry["score"], entry["anchor"])):
        start, end = _window(item["anchor"], duration, settings)
        if end - start < 3:
            continue
        overlapping = any(
            min(end, other["end"]) - max(start, other["start"])
            > 0.5 * min(end - start, other["end"] - other["start"])
            for other in chosen
        )
        if overlapping:
            continue
        item["start"], item["end"] = start, end
        chosen.append(item)
        if len(chosen) >= settings.max_candidates:
            break

    candidates = []
    for rank, item in enumerate(chosen, start=1):
        moment: ChatMoment | None = item["moment"]
        spike: AudioSpike | None = item["spike"]
        score = round(item["score"] * 100)
        both = moment is not None and spike is not None
        if both and score >= 45:
            confidence = "high"
        elif both or score >= 40:
            confidence = "medium"
        else:
            confidence = "low"
        candidates.append(ClipCandidate(
            rank=rank,
            start_seconds=item["start"],
            end_seconds=item["end"],
            anchor_seconds=round(item["anchor"], 1),
            score=score,
            confidence=confidence,
            category=moment.dominant_category if moment else "loud",
            signals=item["signals"],
            chat=ChatEvidence(
                z_score=moment.z_score, chatters=moment.chatters,
                baseline_chatters=moment.baseline_chatters,
                reaction_share=moment.reaction_share, categories=moment.categories,
                alert_nearby=moment.alert_nearby, sample_messages=moment.sample_messages,
            ) if moment else None,
            audio=AudioEvidence(rise_db=spike.rise_db, level_db=spike.level_db) if spike else None,
            reasons=item["reasons"],
            vod_link=twitch_vod_link(twitch_video_id, item["start"]) if twitch_video_id else None,
        ))
    return candidates


def limitations(language: Language, mode: str, chat: ChatStats | None) -> list[str]:
    de = language == "de"
    items = [
        "Kandidaten sind Stellen zum Ansehen, keine Vorhersage, ob ein Clip gut ankommt."
        if de else "Candidates are moments to review, not a prediction of clip performance.",
        "Leise Komik ohne Chat-Reaktion und rein visuelle Momente können fehlen."
        if de else "Quiet humour without chat reaction and purely visual moments can be missed.",
        "Schwellenwerte sind Startwerte und sollten mit eigenen Streams kalibriert werden."
        if de else "Thresholds are starting values and should be calibrated with your own streams.",
    ]
    if mode == "audio" or (chat and chat.level != "active"):
        items.append(
            "Ohne aktiven Chat beruht die Auswahl fast nur auf Lautstärke – mehr Fehlalarme."
            if de else "Without an active chat the selection relies on loudness – more false hits."
        )
    if "chat" in mode:
        items.append(
            "Die Chat-Verzögerung ist geschätzt; Clip-Grenzen vor dem Export prüfen."
            if de else "Chat delay is estimated; check clip boundaries before exporting."
        )
    return items
