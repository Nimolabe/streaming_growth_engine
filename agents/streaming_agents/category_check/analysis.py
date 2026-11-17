"""Auswertung der Messungen: Wie sichtbar wärst du in einer Kategorie – und wann?

Kernzahl ist der Platz in der Live-Liste einer Kategorie, wenn man nach Zuschauern sortiert
(so liefert auch die Twitch-API die Streams). Mit wenigen Zuschauern landet man in großen
Kategorien weit hinten; in kleinen, aber besuchten Kategorien weit vorn.
Die Schwellen unten sind nachvollziehbare Faustregeln, keine Twitch-Vorgaben.
"""
from collections import defaultdict
from collections.abc import Callable, Iterable
from datetime import UTC, datetime, timedelta, timezone
from statistics import median

from .models import (
    CategoryCheckResult,
    CategorySnapshot,
    CategorySummary,
    SlotInfo,
    Verdict,
)

LOW_DEMAND_VIEWERS = 25   # weniger Zuschauer insgesamt: kaum Publikum in dieser Sprache
GOOD_RANK = 15            # so weit oben sieht man dich ohne langes Scrollen
OK_RANK = 40
MIN_MEASUREMENTS = 3
VERDICT_ORDER = {"good": 0, "ok": 1, "hard": 2, "low_demand": 3}
WEEKDAYS = {"de": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
            "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}


def rank_for(snapshot: CategorySnapshot, own_viewers: int) -> tuple[int, bool]:
    """Platz in der nach Zuschauern sortierten Liste (vorsichtig: hinter Gleichstand).

    Zweiter Wert True: Es ist nur eine Untergrenze, weil nicht alle Kanäle gemessen wurden.
    """
    viewers = snapshot.viewers
    if not snapshot.complete and (not viewers or own_viewers <= viewers[-1]):
        return len(viewers) + 1, True
    ahead = sum(1 for value in viewers if value >= own_viewers)
    return ahead + 1, False


def _median_pair(values: list[tuple[int, bool]]) -> tuple[int, bool]:
    """Oberer Median (vorsichtig); das Flag gehört zum gewählten Wert."""
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def _verdict(total: int, rank: int, lower_bound: bool) -> Verdict:
    if total < LOW_DEMAND_VIEWERS:
        return "low_demand"
    if rank <= GOOD_RANK and not lower_bound:
        return "good"
    if rank <= OK_RANK and not lower_bound:
        return "ok"
    return "hard"


def _rank_label(rank: int, lower_bound: bool, language: str) -> str:
    if lower_bound:
        return f"hinter Platz {rank - 1}" if language == "de" else f"below #{rank - 1}"
    return f"Platz {rank}" if language == "de" else f"#{rank}"


def _verdict_text(verdict: Verdict, rank: int, lower_bound: bool, own: int, total: int,
                  language: str) -> str:
    place = _rank_label(rank, lower_bound, language)
    if language == "de":
        viewers = "1 Zuschauer" if own == 1 else f"{own} Zuschauern"
        return {
            "good": f"Gute Chance: Mit {viewers} stehst du etwa auf {place} der Liste.",
            "ok": f"Machbar: Mit {viewers} etwa {place} – ein Titel, der neugierig macht, hilft.",
            "hard": f"Schwer sichtbar: Mit {viewers} {place}. Eher eine kleinere Kategorie "
                    "oder eine andere Uhrzeit wählen.",
            "low_demand": f"Wenig Publikum: Zusammen nur etwa {total} Zuschauer in dieser "
                          "Sprache – du wärst sichtbar, aber es schauen kaum Leute.",
        }[verdict]
    viewers = "1 viewer" if own == 1 else f"{own} viewers"
    return {
        "good": f"Good chance: with {viewers} you'd be around {place} in the list.",
        "ok": f"Doable: with {viewers} around {place} – a curious title helps.",
        "hard": f"Hard to be seen: with {viewers} {place}. Try a smaller category or another time.",
        "low_demand": f"Small audience: only about {total} viewers in total in this language – "
                      "you'd be visible, but few people are watching.",
    }[verdict]


def _slot_label(weekday: int, hour: int, language: str) -> str:
    day = WEEKDAYS[language][weekday]
    end = (hour + 2) % 24
    if language == "de":
        return f"{day} {hour}–{end if end else 24} Uhr"
    return f"{day} {hour:02d}:00–{end if end else 24:02d}:00"


def local_time_from_offset(minutes: int) -> Callable[[float], datetime]:
    zone = timezone(timedelta(minutes=minutes))
    return lambda ts: datetime.fromtimestamp(ts, zone)


def machine_local_time(ts: float) -> datetime:
    """Ortszeit des Rechners (inklusive Sommerzeit), ohne zusätzliche Zeitzonen-Pakete."""
    return datetime.fromtimestamp(ts, UTC).astimezone()


def in_window(hour: int, window: tuple[int, int] | None) -> bool:
    """Liegt ein Zwei-Stunden-Block (Beginn ``hour``) im Zeitfenster [von, bis)? Über Mitternacht erlaubt."""
    if window is None:
        return True
    start, end = window
    if start == end:
        return True
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end


def parse_window(text: str) -> tuple[int, int]:
    """„16-24“ → (16, 24); „20-2“ geht über Mitternacht."""
    try:
        start_text, end_text = text.replace("–", "-").split("-")
        start, end = int(start_text), int(end_text)
    except ValueError as exc:
        raise ValueError("Zeitfenster als Stunden angeben, z. B. 16-24 oder 20-2") from exc
    if not (0 <= start <= 23 and 0 <= end <= 24):
        raise ValueError("Zeitfenster als Stunden angeben, z. B. 16-24 oder 20-2")
    return start, end % 24 if end == 24 and start else end


def _reach(total: int, rank: int) -> float:
    """Wie viel Publikum pro Platz vor dir: hoch = viele Zuschauer und trotzdem weit oben."""
    return total / rank


def _summarize(snapshots: list[CategorySnapshot], own: int, language: str,
               to_local: Callable[[float], datetime],
               window: tuple[int, int] | None = None) -> CategorySummary:
    first = snapshots[-1]  # neuester Name gewinnt
    ranks = [rank_for(item, own) for item in snapshots]
    rank, rank_floor = _median_pair(ranks)
    channels, channels_floor = _median_pair([(item.channels, not item.complete) for item in snapshots])
    totals = [sum(item.viewers) for item in snapshots]
    total = int(median(totals))
    per_channel = median([median(item.viewers) if item.viewers else 0 for item in snapshots])
    shares = [sum(item.viewers[:3]) / sum(item.viewers) for item in snapshots if sum(item.viewers)]
    verdict = _verdict(total, rank, rank_floor)

    slots: dict[tuple[int, int], list[CategorySnapshot]] = defaultdict(list)
    measured_slots: set[tuple[int, int]] = set()
    for item in snapshots:
        moment = to_local(item.taken_at)
        key = (moment.weekday(), moment.hour // 2 * 2)
        measured_slots.add(key)
        if in_window(key[1], window):
            slots[key].append(item)
    best: list[SlotInfo] = []
    # „Beste Zeit“ ergibt nur Sinn, wenn zu mindestens zwei Zeiten gemessen wurde.
    if len(measured_slots) >= 2:
        for (weekday, hour), group in slots.items():
            slot_rank, slot_floor = _median_pair([rank_for(item, own) for item in group])
            slot_total = int(median([sum(item.viewers) for item in group]))
            if slot_total < LOW_DEMAND_VIEWERS:
                continue
            best.append(SlotInfo(weekday=weekday, hour=hour,
                                 label=_slot_label(weekday, hour, language),
                                 measurements=len(group), median_rank=slot_rank,
                                 rank_is_lower_bound=slot_floor,
                                 median_total_viewers=slot_total))
        best.sort(key=lambda slot: (slot.rank_is_lower_bound,
                                    -_reach(slot.median_total_viewers, slot.median_rank),
                                    slot.median_rank, slot.weekday, slot.hour))
    return CategorySummary(
        category=first.category, category_id=first.category_id, language=first.language,
        measurements=len(snapshots), median_channels=channels,
        channels_is_lower_bound=channels_floor, median_total_viewers=total,
        median_viewers_per_channel=round(float(per_channel), 1),
        top3_share=round(median(shares), 3) if shares else 0.0,
        median_rank=rank, rank_is_lower_bound=rank_floor, verdict=verdict,
        verdict_text=_verdict_text(verdict, rank, rank_floor, own, total, language),
        best_slots=best[:3],
    )


def analyze(snapshots: Iterable[CategorySnapshot], *, own_viewers: int = 2,
            language: str = "de",
            to_local: Callable[[float], datetime] = machine_local_time,
            window: tuple[int, int] | None = None) -> CategoryCheckResult:
    """Fasst alle Messungen je Kategorie und Sprache zusammen und sortiert nach Chance."""
    if language not in ("de", "en"):
        raise ValueError("language must be 'de' or 'en'")
    if own_viewers < 0:
        raise ValueError("own_viewers must not be negative")
    groups: dict[tuple[str, str], list[CategorySnapshot]] = defaultdict(list)
    count = 0
    for item in snapshots:
        groups[(item.category_id, item.language)].append(item)
        count += 1
    summaries = [
        _summarize(sorted(group, key=lambda s: s.taken_at), own_viewers, language, to_local, window)
        for group in groups.values()
    ]
    summaries.sort(key=lambda s: (VERDICT_ORDER[s.verdict], s.rank_is_lower_bound, s.median_rank,
                                  -s.median_total_viewers, s.category.casefold()))
    return CategoryCheckResult(own_viewers=own_viewers, language=language, measurements=count,
                               categories=summaries, notes=_notes(summaries, language))


def _notes(summaries: list[CategorySummary], language: str) -> list[str]:
    de = language == "de"
    notes = [
        "Der Platz ist eine Näherung für die Sichtbarkeit: gezählt wird, wie viele Live-Kanäle "
        "mindestens so viele Zuschauer haben wie du. Twitch kann Listen auch personalisiert "
        "sortieren."
        if de else
        "Your position approximates visibility: it counts live channels with at least as many "
        "viewers as you. Twitch may also sort lists in a personalised way.",
        f"Faustregeln: bis Platz {GOOD_RANK} gut, bis {OK_RANK} machbar; unter "
        f"{LOW_DEMAND_VIEWERS} Zuschauern insgesamt kaum Publikum."
        if de else
        f"Rules of thumb: up to #{GOOD_RANK} good, up to #{OK_RANK} doable; below "
        f"{LOW_DEMAND_VIEWERS} total viewers there is hardly an audience.",
    ]
    if any(item.measurements < MIN_MEASUREMENTS for item in summaries):
        notes.append(
            "Einige Kategorien haben weniger als drei Messungen. Für ein belastbares Bild an "
            "mehreren Tagen zur geplanten Streamzeit messen."
            if de else
            "Some categories have fewer than three measurements. Measure on several days at "
            "your planned stream time for a reliable picture."
        )
    if any(item.best_slots for item in summaries):
        notes.append(
            "Beste Zeiten: wo die Kategorie viel Publikum hat und du trotzdem weit oben stehst – "
            "nicht einfach die leerste Uhrzeit."
            if de else
            "Best times: when the category has a large audience and you still rank high – "
            "not simply the emptiest hour."
        )
    if summaries and not any(item.best_slots for item in summaries):
        notes.append(
            "Für die besten Uhrzeiten zu mindestens zwei verschiedenen Zeiten messen "
            "(z. B. mit „watch“)."
            if de else
            "Measure at two or more different times (e.g. with “watch”) to see the best times."
        )
    return notes
