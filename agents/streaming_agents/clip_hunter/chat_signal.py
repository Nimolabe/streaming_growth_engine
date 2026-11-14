"""Findet Momente, in denen der Chat deutlich stärker reagiert als üblich.

Gemessen wird die Zahl *verschiedener* Chatter in einem kurzen Fenster (Spam einzelner
Nutzer zählt also nicht mehrfach) im Vergleich zum normalen Tempo der vorherigen Minuten.
Bots, Befehle (``!``) und Nachrichten des Streamers werden ignoriert; Ausschläge, die
offensichtlich auf Subs, Raids oder Spenden reagieren, werden aussortiert oder markiert.
"""
from bisect import bisect_left, insort
from collections import Counter
from math import ceil, sqrt
from statistics import median

from .models import ChatLog, ChatMoment, ChatStats, HuntSettings
from .reactions import REACTION_CATEGORIES, classify_message, is_alert_reaction

_EVENT_PRIORITY = ("raid", "gift", "sub", "cheer", "announcement", "event")
_MAX_STREAM_SECONDS = 48 * 3600


class _Bin:
    __slots__ = ("users",)

    def __init__(self):
        # Nutzer -> (Reaktionsarten, Alert-Reaktion?, Text)
        self.users: dict[str, tuple[frozenset[str], bool, str]] = {}


def _spread(baseline: float) -> float:
    """Erwartbare Schwankung um den Normalwert (robust auch für sehr kleine Chats)."""
    return max(1.0, 1.5 * sqrt(baseline), 0.3 * baseline)


def _chat_level(minutes: list[int], used: int) -> tuple[str, float]:
    if not minutes:
        return "none", 0.0
    per_minute = float(median(minutes))
    if used < 20 or per_minute < 0.5:
        return "none", per_minute
    if per_minute < 10:
        return "low", per_minute
    return "active", per_minute


def analyze_chat(log: ChatLog, settings: HuntSettings, vod_start: float,
                 duration_seconds: float | None = None) -> tuple[list[ChatMoment], ChatStats]:
    """Gibt Chat-Momente (Sekunden ab VOD-Beginn) und Kennzahlen zum Chat zurück."""
    limit = min(duration_seconds + 60 if duration_seconds else _MAX_STREAM_SECONDS,
                _MAX_STREAM_SECONDS)
    shift = settings.chat_offset_seconds - vod_start
    used: list[tuple[float, str, str]] = []
    events: dict[str, list[float]] = {}
    ignored = 0
    for message in log.messages:
        second = message.ts + shift
        if second < 0 or second > limit:
            ignored += 1
            continue
        if message.kind != "message":
            events.setdefault(message.kind, []).append(second)
            continue
        text = message.text.strip()
        if message.bot or message.broadcaster or not text or text.startswith("!"):
            ignored += 1
            continue
        used.append((second, message.user, text))

    event_counts = {kind: len(times) for kind, times in events.items()}
    if not used:
        return [], ChatStats(level="none", messages_used=0, messages_ignored=ignored,
                             events=event_counts, median_chatters_per_minute=0)

    last_second = max(item[0] for item in used)
    size = ceil(last_second) + 1
    bins = [_Bin() for _ in range(size)]
    per_minute: dict[int, set[str]] = {}
    for second, user, text in used:
        index = int(second)
        cats = classify_message(text)
        alert = is_alert_reaction(text)
        previous = bins[index].users.get(user)
        if previous:
            cats = cats | previous[0]
            alert = alert or previous[1]
            text = previous[2]
        bins[index].users[user] = (cats, alert, text)
        per_minute.setdefault(index // 60, set()).add(user)

    first_minute, last_minute = min(per_minute), max(per_minute)
    minute_counts = [len(per_minute.get(m, ())) for m in range(first_minute, last_minute + 1)]
    level, cpm = _chat_level(minute_counts, len(used))
    stats = ChatStats(level=level, messages_used=len(used), messages_ignored=ignored,
                      events=event_counts, median_chatters_per_minute=round(cpm, 2))
    if level == "none":
        return [], stats

    window = settings.chat_window_seconds
    activity = _window_unique(bins, window)
    baseline = _rolling_baseline(activity, window, settings.chat_baseline_seconds)
    per_second = [len(item.users) for item in bins]
    reaction_per_second = [sum(1 for cats, _, _ in item.users.values() if cats) for item in bins]

    peaks: list[tuple[float, int]] = []
    for start, value in enumerate(activity):
        if value < settings.chat_min_chatters:
            continue
        z = (value - baseline[start]) / _spread(baseline[start])
        if z >= settings.chat_min_z:
            peaks.append((z, start))
    chosen: list[tuple[float, int]] = []
    for z, start in sorted(peaks, key=lambda item: (-item[0], item[1])):
        if all(abs(start - other) >= settings.chat_min_gap_seconds for _, other in chosen):
            chosen.append((z, start))

    moments = []
    for z, start in chosen:
        moment = _describe(bins, per_second, reaction_per_second, events, start, z,
                           activity[start], baseline[start], settings)
        if moment is not None:
            moments.append(moment)
    moments.sort(key=lambda item: item.event_seconds)
    return moments, stats


def _window_unique(bins: list[_Bin], window: int) -> list[int]:
    """Anzahl verschiedener Chatter in [t, t + window) für jedes t."""
    counter: Counter[str] = Counter()
    result = []
    for index in range(min(window, len(bins))):
        counter.update(bins[index].users.keys())
    for start in range(len(bins)):
        result.append(len(counter))
        counter.subtract(bins[start].users.keys())
        for user in list(bins[start].users):
            if counter[user] <= 0:
                del counter[user]
        incoming = start + window
        if incoming < len(bins):
            counter.update(bins[incoming].users.keys())
    return result


def _rolling_baseline(activity: list[int], window: int, span: int) -> list[float]:
    """Median der Aktivität im Zeitraum *vor* dem jeweiligen Fenster (ohne Überlappung).

    Der Wert fällt nie unter die Hälfte des typischen Tempos des ganzen Streams, damit z. B.
    der Chat-Beginn nach einem leeren Stream-Anfang nicht als Ausschlag zählt.
    """
    nonzero = [value for value in activity if value > 0]
    typical = float(median(nonzero)) if nonzero else 0.0
    floor = 0.5 * typical
    fallback = typical
    history: list[int] = []
    result = []
    for start in range(len(activity)):
        entering = start - window
        if entering >= 0:
            insort(history, activity[entering])
            leaving = entering - (span - window)
            if leaving >= 0:
                history.pop(_index(history, activity[leaving]))
        if len(history) >= 30:
            result.append(max(floor, float(_median_sorted(history))))
        else:
            result.append(fallback)
    return result


def _index(values: list[int], value: int) -> int:
    return bisect_left(values, value)


def _median_sorted(values: list[int]) -> float:
    middle = len(values) // 2
    if len(values) % 2:
        return values[middle]
    return (values[middle - 1] + values[middle]) / 2


def _describe(bins: list[_Bin], per_second: list[int], reaction_per_second: list[int],
              events: dict[str, list[float]],
              start: int, z: float, value: int, base: float,
              settings: HuntSettings) -> ChatMoment | None:
    window = settings.chat_window_seconds
    window_users: dict[str, tuple[frozenset[str], bool, str]] = {}
    for index in range(start, min(start + window, len(bins))):
        for user, info in bins[index].users.items():
            window_users.setdefault(user, info)
    total = len(window_users) or 1

    # Beginn des Ausschlags: erste Sekunde, ab der zwei Sekunden zusammen die halbe Höhe
    # der Spitze erreichen. Gezählt werden bevorzugt reagierende Chatter (Emotes usw.),
    # weil normales Geplauder sonst Zufallsspitzen erzeugt.
    reacting_users = sum(1 for cats, _, _ in window_users.values() if cats)
    use_reactions = reacting_users / total >= 0.25
    series = reaction_per_second if use_reactions else per_second
    base_two = 0.0 if use_reactions else 2 * base / window
    lo = max(0, start - 3)
    hi = min(start + window, len(series) - 1)
    sums = [series[index] + series[index + 1] for index in range(lo, hi)]
    onset = float(start)
    if sums:
        peak_two = max(sums)
        threshold = max(base_two + 2, base_two + 0.5 * (peak_two - base_two))
        for offset, value_two in enumerate(sums):
            if value_two >= threshold:
                onset = float(lo + offset)
                break
    event_second = max(0.0, onset - settings.chat_reaction_lag_seconds)

    categories = {name: 0 for name in REACTION_CATEGORIES}
    reacting = 0
    alerting = 0
    texts: Counter[str] = Counter()
    reaction_texts: Counter[str] = Counter()
    for cats, alert, text in window_users.values():
        if cats:
            reacting += 1
        if alert:
            alerting += 1
        for cat in cats:
            categories[cat] += 1
        short = " ".join(text.split())[:80]
        texts[short] += 1
        if cats:
            reaction_texts[short] += 1
    categories = {name: count for name, count in categories.items() if count}
    dominant = "reaction"
    if categories:
        name, count = max(categories.items(), key=lambda item: item[1])
        if count >= max(2, 0.15 * total):
            dominant = name

    # Ohne erkennbare Reaktions-Emotes kann ein Ausschlag auch zufälliges Geplauder sein:
    # dann muss er deutlich stärker sein.
    if reacting / total < 0.25 and z < settings.chat_min_z + 1.5:
        return None

    alert_kind = None
    for kind in _EVENT_PRIORITY:
        before = 90 if kind == "raid" else 20
        if any(onset - before <= second <= start + window for second in events.get(kind, ())):
            alert_kind = kind
            break
    alert_share = alerting / total
    copypasta_share = (texts.most_common(1)[0][1] / total) if texts else 0.0
    if alert_kind and alert_share >= 0.3:
        return None
    if alert_kind == "raid" and (alert_share >= 0.2 or copypasta_share >= 0.4):
        return None

    samples = [text for text, _ in (reaction_texts or texts).most_common(3)]
    return ChatMoment(
        event_seconds=round(event_second, 1),
        onset_seconds=round(onset, 1),
        peak_seconds=round(start + window / 2, 1),
        z_score=round(z, 2),
        chatters=value,
        baseline_chatters=round(base, 2),
        reaction_share=round(reacting / total, 3),
        categories=categories,
        dominant_category=dominant,
        alert_nearby=alert_kind,
        alert_share=round(alert_share, 3),
        sample_messages=samples,
    )
