"""Wochenplan für kleine Streamer: was, wann, in welcher Kategorie, mit welchem Titel.

Alles lokal und regelbasiert, ohne Sprachmodell. Gleiche Eingabe → gleicher Plan.

Zeitbudget (``hours_per_week`` ist die GESAMTE Zeit pro Woche):
- je Stream 20 min Vorbereitung (endet 10 min vor dem Start) und 30 min für einen Clip danach,
- einmal 30 min Wochenrückblick,
- der Rest wird gleichmäßig auf die Streams verteilt, in 15-Minuten-Schritten abgerundet,
  höchstens 4 Stunden pro Stream, mindestens 60 Minuten, und nie länger als das Zeitfenster.
"""
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime

from ..category_check.analysis import (
    analyze,
    local_time_from_offset,
    machine_local_time,
    rank_label,
    slot_reach,
    slot_stats,
)
from ..category_check.models import CategorySnapshot, SlotInfo
from .formats import FORMATS, Format, formats_for
from .genres import detect_genre, genre_label, normalize
from .models import (
    DAY_LABELS,
    Budget,
    ContentPlan,
    GameInfo,
    SeriesPlan,
    Session,
    StrategyRequest,
    StreamPlan,
    WeeklyReview,
)
from .titles import STREAM_TITLES, build_titles, clip_titles, stream_mood
from .twitch_limits import (
    SOURCE_DATE,
    SOURCE_URL,
    TAG_MAX_CHARS,
    TAGS_MAX_COUNT,
    TITLE_MAX_CHARS,
    clean_tags,
    fit_title,
    tag_from_text,
)

WEEK = 7 * 1440
PREP_MINUTES = 20
PREP_GAP = 10
CLIP_MINUTES = 30
REVIEW_MINUTES = 30
MIN_STREAM = 60
MAX_STREAM = 240
STEP = 15
CHAT_ORDER = {"none": 0, "low": 1, "active": 2}
GENRE_TAG = {
    "shooter": ("Shooter", "Shooter"), "battle_royale": ("BattleRoyale", "BattleRoyale"),
    "moba": ("MOBA", "MOBA"), "story": ("Singleplayer", "Singleplayer"),
    "horror": ("Horror", "Horror"), "cozy": ("Simulation", "Simulation"),
    "sandbox": ("Sandbox", "Sandbox"), "sports": ("Sport", "Sports"),
    "just_chatting": ("JustChatting", "JustChatting"),
}
GOAL_LABEL = {"discovery": ("neue Zuschauer", "new viewers"),
              "community": ("Community", "community"),
              "consistency": ("Regelmäßigkeit", "consistency")}


class PlanError(ValueError):
    """Verständlicher Grund, warum sich kein Plan erstellen lässt."""


def chat_level(active_chatters: int) -> str:
    """0–2 aktive Chatter: kein Chat-Format; 3–7: leichte Beteiligung; ab 8: lebhaft."""
    if active_chatters <= 2:
        return "none"
    if active_chatters <= 7:
        return "low"
    return "active"


def _t(pair: tuple[str, str], language: str) -> str:
    return pair[0] if language == "de" else pair[1]


def _clock(minute_of_week: int) -> str:
    minute = minute_of_week % 1440
    return f"{minute // 60:02d}:{minute % 60:02d}"


def _day(minute_of_week: int) -> int:
    return (minute_of_week % WEEK) // 1440


def _session(start: int, minutes: int, language: str) -> Session:
    end = start + minutes
    label = DAY_LABELS[language][_day(start)]
    if _day(end - 1) != _day(start):
        label += (f" (bis {DAY_LABELS['de'][_day(end - 1)]})" if language == "de"
                  else f" (until {DAY_LABELS['en'][_day(end - 1)]})")
    return Session(day=_day(start), label=label, start=_clock(start), end=_clock(end),
                   minutes=minutes)


# ------------------------------------------------------------------ Zeitfenster
def _merged_windows(request: StrategyRequest) -> list[tuple[int, int]]:
    """Fenster als [Beginn, Ende) in Wochenminuten; Überlappungen zusammengelegt."""
    spans = sorted((w.week_start, w.week_start + w.minutes) for w in request.windows)
    merged: list[list[int]] = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    # Ein Fenster über das Wochenende hinaus (So → Mo) kann mit dem ersten verschmelzen.
    if len(merged) > 1 and merged[-1][1] >= merged[0][0] + WEEK:
        first = merged.pop(0)
        merged[-1][1] = max(merged[-1][1], first[1] + WEEK)
    return [(start, end) for start, end in merged]


def _stream_length(request: StrategyRequest) -> int:
    count = request.streams_per_week
    available = request.hours_per_week * 60 - REVIEW_MINUTES - count * (PREP_MINUTES + CLIP_MINUTES)
    length = min(MAX_STREAM, max(0, available) // count // STEP * STEP)
    if length < MIN_STREAM:
        needed = -(-(count * (MIN_STREAM + PREP_MINUTES + CLIP_MINUTES) + REVIEW_MINUTES) // 60)
        if request.language == "de":
            raise PlanError(
                f"Zu wenig Zeit: {count} Streams mit je mindestens {MIN_STREAM} Minuten plus "
                f"Vorbereitung, Clip und Wochenrückblick brauchen mindestens {needed} Stunden pro "
                f"Woche. Weniger Streams planen oder mehr Stunden angeben.")
        raise PlanError(
            f"Not enough time: {count} streams of at least {MIN_STREAM} minutes plus preparation, "
            f"clips and a weekly review need at least {needed} hours per week. Plan fewer streams "
            f"or more hours.")
    return length


# ------------------------------------------------------------------ Kategorie-Check
def _snapshots_for(game: str, snapshots: list[CategorySnapshot],
                   language: str) -> list[CategorySnapshot]:
    key = normalize(game)
    matching = [item for item in snapshots if normalize(item.category) == key]
    for wanted in (language, "any"):
        chosen = [item for item in matching if item.language == wanted]
        if chosen:
            return chosen
    return matching


def _fits(slot: SlotInfo, window: tuple[int, int], length: int) -> int | None:
    """Startminute, wenn ein Stream dieser Länge im Fenster den Block überdeckt."""
    win_start, win_end = window
    if win_end - win_start < length:
        return None
    for shift in (-WEEK, 0, WEEK):
        block = slot.weekday * 1440 + slot.hour * 60 + shift
        start = min(max(block, win_start), win_end - length)
        if start < block + 120 and start + length > block:
            return start
    return None


def _best_slot(slots: list[SlotInfo], window: tuple[int, int],
               length: int) -> tuple[SlotInfo, int] | None:
    for slot in slots:  # bereits sortiert: bestes Publikum pro Platz zuerst
        start = _fits(slot, window, length)
        if start is not None:
            return slot, start
    return None


# ------------------------------------------------------------------ Formate
def _score(item: Format, request: StrategyRequest, level: str) -> int:
    score = 0
    if request.goal in item.goals:
        score += 3
    if item.expert and request.experience == "beginner":
        score -= 3
    if item.expert and request.experience == "advanced":
        score += 1
    if item.needs_chat == "low":
        score += 2
    if item.needs_chat == "active":
        score += 3
    if item.needs_collab:
        score += 2
    if item.series and request.goal == "consistency":
        score += 1
    return score


def _eligible(item: Format, request: StrategyRequest, level: str) -> bool:
    if CHAT_ORDER[item.needs_chat] > CHAT_ORDER[level]:
        return False
    return request.collab_partner or not item.needs_collab


def _ranked(genre: str | None, request: StrategyRequest, level: str) -> list[Format]:
    pool = [item for item in formats_for(genre)
            if _eligible(item, request, level) and not item.week_end]
    order = {item.id: index for index, item in enumerate(FORMATS)}
    return sorted(pool, key=lambda item: (-_score(item, request, level), order[item.id]))


def item_mood(format_id: str, genre: str | None, request: StrategyRequest) -> str:
    return stream_mood(format_id, genre, request.mood)


def week_minute(session: Session) -> int:
    hours, minutes = session.start.split(":")
    return session.day * 1440 + int(hours) * 60 + int(minutes)


def _rank_stream(entry: StreamPlan, genres: dict[str, str | None], request: StrategyRequest) -> bool:
    """Zählt für „Road to <Rang>, Tag k“: Rang-Ziel angegeben und Ranked-Format."""
    return bool(request.rank_goal) and STREAM_TITLES[entry.format_id].ranked and \
        genres[entry.game] in {"shooter", "battle_royale", "moba", "sports"}


def _week_closer(genre: str | None, request: StrategyRequest, level: str) -> Format | None:
    """Format für den letzten Stream der Woche (z. B. Wochenrückblick), falls es eines gibt.

    Nur bei mindestens zwei Streams – ein Rückblick auf eine Woche mit einem Stream lohnt nicht –
    und nur, wenn das Format zum Ziel passt.
    """
    for item in formats_for(genre):
        if item.week_end and _eligible(item, request, level) and request.goal in item.goals:
            return item
    return None


def _why(item: Format, genre: str | None, request: StrategyRequest, level: str) -> str:
    de = request.language == "de"
    parts = [(f"passt zu {genre_label(genre, 'de')}" if de else f"fits {genre_label(genre, 'en')}")
             if genre else ("allgemeines Format, weil kein Genre erkannt wurde" if de
                            else "general format because no genre was recognised")]
    if item.needs_chat == "none":
        parts.append("funktioniert ohne Chat" if de else "works without chat")
    else:
        parts.append("nutzt deinen aktiven Chat" if de else "uses your active chat")
    if item.needs_collab:
        parts.append("mit deinem Mitspieler" if de else "with your teammate")
    if request.goal in item.goals:
        goal = _t(GOAL_LABEL[request.goal], request.language)
        parts.append(f"unterstützt dein Ziel „{goal}“" if de else f"supports your goal '{goal}'")
    if item.expert and request.experience == "beginner":
        parts.append("braucht etwas Vorbereitung" if de else "needs some preparation")
    text = "; ".join(parts)
    return text[:1].upper() + text[1:] + "."


def _tags(game: str, genre: str | None, item: Format, language: str) -> list[str]:
    candidates: list[str] = []
    if genre != "just_chatting":
        game_tag = tag_from_text(game)
        if game_tag:
            candidates.append(game_tag)
    candidates.append("Deutsch" if language == "de" else "English")
    if genre:
        candidates.append(_t(GENRE_TAG[genre], language))
    candidates.extend(_t(pair, language) for pair in item.tags)
    return clean_tags(candidates)


# ------------------------------------------------------------------ Hauptfunktion
def build_plan(request: StrategyRequest,
               to_local: Callable[[float], datetime] | None = None) -> ContentPlan:
    de = request.language == "de"
    lang = request.language
    level = chat_level(request.active_chatters)
    length = _stream_length(request)
    count = request.streams_per_week

    windows = [w for w in _merged_windows(request) if w[1] - w[0] >= MIN_STREAM]
    if len(windows) < count:
        raise PlanError(
            f"Du hast {len(windows)} nutzbare(s) Zeitfenster (mindestens {MIN_STREAM} Minuten), "
            f"aber {count} Streams geplant. Mehr Zeitfenster angeben oder weniger Streams planen."
            if de else
            f"You have {len(windows)} usable window(s) (at least {MIN_STREAM} minutes) but "
            f"planned {count} streams. Add windows or plan fewer streams.")

    # Spiele und Genres
    games = request.games
    genres = {game: detect_genre(game) for game in games}
    if to_local is None:
        to_local = (local_time_from_offset(request.utc_offset_minutes)
                    if request.utc_offset_minutes is not None else machine_local_time)
    own = request.average_viewers
    game_snaps = {game: _snapshots_for(game, request.measurements, lang) for game in games}
    game_slots = {game: slot_stats(snaps, own, lang, to_local) if snaps else []
                  for game, snaps in game_snaps.items()}
    game_infos: list[GameInfo] = []
    for game in games:
        verdict = None
        if game_snaps[game]:
            summary = analyze(game_snaps[game], own_viewers=own, language=lang,
                              to_local=to_local).categories[0]
            verdict = summary.verdict_text
        game_infos.append(GameInfo(name=game, genre=genres[game],
                                   genre_label=genre_label(genres[game], lang),
                                   genre_recognized=genres[game] is not None,
                                   category_check=verdict))

    # Zeitfenster wählen: mit Messungen nach Publikum pro Platz, sonst gleichmäßig verteilt
    assignment: list[tuple[str, tuple[int, int], int, SlotInfo | None]] = []
    free = list(windows)
    used_days: set[int] = set()
    spread_order = _spread(windows, count)
    for index in range(count):
        game = games[index % len(games)]
        best: tuple | None = None
        for window in free:
            win_len = min(length, (window[1] - window[0]) // STEP * STEP)
            found = _best_slot(game_slots[game], window, win_len)
            key = (
                0 if found else 1,
                found[0].rank_is_lower_bound if found else False,
                -slot_reach(found[0]) if found else 0.0,
                1 if _day(window[0]) in used_days else 0,
                spread_order.index(window) if window in spread_order else len(windows),
                window[0],
            )
            if best is None or key < best[0]:
                start = found[1] if found else window[0]
                best = (key, window, start, win_len, found[0] if found else None)
        _, window, start, win_len, slot = best
        free.remove(window)
        used_days.add(_day(window[0]))
        assignment.append((game, (start, win_len), index, slot))
    assignment.sort(key=lambda item: item[1][0])

    # Formate: pro Genre reihum aus der Rangliste, damit sich Ideen nicht wiederholen
    queues: dict[str | None, list[Format]] = {}
    position: dict[str | None, int] = defaultdict(int)
    streams: list[StreamPlan] = []
    stream_spans = [(start, start + minutes) for _, (start, minutes), _, _ in assignment]
    for number, (game, (start, minutes), _, slot) in enumerate(assignment, start=1):
        genre = genres[game]
        queue = queues.setdefault(genre, _ranked(genre, request, level))
        closer = _week_closer(genre, request, level) if number == count > 1 else None
        if closer is not None:
            item = closer
        else:
            item = queue[position[genre] % len(queue)]
            position[genre] += 1

        prep_start = start - PREP_GAP - PREP_MINUTES
        while any(a < prep_start + PREP_MINUTES + PREP_GAP and prep_start < b
                  for a, b in stream_spans if a != start):
            prep_start = min(a for a, b in stream_spans
                             if a < prep_start + PREP_MINUTES + PREP_GAP and prep_start < b
                             and a != start) - PREP_GAP - PREP_MINUTES
        prep = _session(prep_start % WEEK, PREP_MINUTES, lang)
        stream = _session(start % WEEK, minutes, lang)
        clip_day = DAY_LABELS[lang][(_day(start) + 1) % 7]

        streams.append(StreamPlan(
            number=number, stream=stream, game=game, genre_label=genre_label(genre, lang),
            format_id=item.id, format_name=_t(item.name, lang), needs_chat=item.needs_chat,
            needs_collab=item.needs_collab,
            title="", title_alternatives=[], title_mood=item_mood(item.id, genre, request),
            clip_title_ideas=clip_titles(item.id, lang),
            tags=_tags(game, genre, item, lang),
            run_of_show=[_t(step, lang) for step in item.steps],
            break_note=_break_note(minutes, lang),
            preparation=prep, prep_steps=[_t(step, lang) for step in item.prep],
            hook=_t(item.hook, lang), clip_idea=_t(item.clip, lang),
            clip_day=(f"{clip_day} (Tag nach dem Stream), {CLIP_MINUTES} min" if de
                      else f"{clip_day} (day after the stream), {CLIP_MINUTES} min"),
            measurement=_t(item.metric, lang),
            why=_why(item, genre, request, level),
            timing_reason=_timing_reason(game, slot, stream, request, game_snaps[game]),
        ))

    # Titel: Zähler laufen über die Wochen weiter (Woche 2 beginnt dort, wo Woche 1 aufhörte),
    # und dasselbe Format bekommt in einer Woche nie zweimal denselben Haupttitel.
    totals: dict[str, int] = defaultdict(int)
    for entry in streams:
        totals[entry.format_id] += 1
    ranked_total = sum(1 for entry in streams if _rank_stream(entry, genres, request))
    seen: dict[str, int] = defaultdict(int)
    used_main: dict[str, set[str]] = defaultdict(set)
    ranked_seen = 0
    for index, entry in enumerate(streams):
        seen[entry.format_id] += 1
        counter = (request.week_number - 1) * totals[entry.format_id] + seen[entry.format_id]
        if _rank_stream(entry, genres, request):
            ranked_seen += 1
        # Ansätze wechseln sich über die Woche ab; dasselbe Format nie mit gleichem Haupttitel.
        for shift in range(3):
            options = build_titles(
                entry.format_id, genres[entry.game], entry.game, lang, counter=counter,
                start_minute=week_minute(entry.stream), mood=request.mood,
                rank_goal=request.rank_goal,
                rank_counter=(request.week_number - 1) * ranked_total + max(ranked_seen, 1),
                first_time=request.first_time, rotation=index + shift)
            if options[0].text not in used_main[entry.format_id]:
                break
        used_main[entry.format_id].add(options[0].text)
        titles = [fit_title(option.text) for option in options]
        entry.title, entry.title_alternatives = titles[0], titles[1:3]

    last_day = streams[-1].stream.day
    review = WeeklyReview(
        day=DAY_LABELS[lang][(last_day + 1) % 7], minutes=REVIEW_MINUTES,
        questions=[
            "Welcher Stream hatte die meisten durchschnittlichen Zuschauer – lag es eher am "
            "Format, an der Uhrzeit oder am Spiel?" if de else
            "Which stream had the most average viewers – was it the format, the time or the game?",
            "Welcher Clip wurde am häufigsten angesehen?" if de else
            "Which clip got the most views?",
            "Was änderst du nächste Woche – nur eine Sache?" if de else
            "What will you change next week – just one thing?",
        ],
    )
    stream_total = sum(item.stream.minutes for item in streams)
    budget = Budget(
        weekly_minutes=request.hours_per_week * 60, stream_minutes=stream_total,
        preparation_minutes=count * PREP_MINUTES, clip_minutes=count * CLIP_MINUTES,
        review_minutes=REVIEW_MINUTES,
        unplanned_minutes=request.hours_per_week * 60 - stream_total
        - count * (PREP_MINUTES + CLIP_MINUTES) - REVIEW_MINUTES,
    )
    series = None
    for entry in streams:
        source = next(item for item in FORMATS if item.id == entry.format_id)
        if source.series:
            series = SeriesPlan(format_name=entry.format_name, game=entry.game,
                                episodes=[_t(step, lang) for step in source.series])
            break

    return ContentPlan(
        language=lang, platform=request.platform, chat_level=level,
        timing_source="measurements" if any(game_slots.values()) else "windows_only",
        games=game_infos, streams=streams, review=review, series=series, budget=budget,
        twitch_limits=(
            f"Titel höchstens {TITLE_MAX_CHARS} Zeichen, höchstens {TAGS_MAX_COUNT} Tags mit je "
            f"höchstens {TAG_MAX_CHARS} Zeichen ohne Leer- und Sonderzeichen. Quelle: "
            f"{SOURCE_URL} (Stand: {SOURCE_DATE})" if de else
            f"Title at most {TITLE_MAX_CHARS} characters, at most {TAGS_MAX_COUNT} tags of at most "
            f"{TAG_MAX_CHARS} characters without spaces or special characters. Source: "
            f"{SOURCE_URL} (as of {SOURCE_DATE})"),
        notes=_notes(request, level, genres, game_slots, streams),
        limitations=[
            "Redaktionelle Regeln, kein Sprachmodell und keine Wachstumsvorhersage." if de else
            "Editorial rules, no language model and no growth prediction.",
            "Titel und Tags sind Vorschläge – vor dem Stream lesen und anpassen." if de else
            "Titles and tags are suggestions – read and adjust them before you go live.",
            "Spielinhalte ändern sich mit Updates; Ideen vor dem Stream in deiner Spielversion "
            "prüfen." if de else
            "Game content changes with updates; check ideas in your game version before streaming.",
        ],
    )


def _spread(windows: list[tuple[int, int]], count: int) -> list[tuple[int, int]]:
    """Reihenfolge ohne Messungen: über die Woche verteilen, ein Stream pro Tag bevorzugt."""
    by_day: dict[int, tuple[int, int]] = {}
    for window in windows:
        day = _day(window[0])
        current = by_day.get(day)
        if current is None or window[1] - window[0] > current[1] - current[0]:
            by_day[day] = window
    days = sorted(by_day.values())
    picks: list[tuple[int, int]] = []
    if len(days) >= count:
        step = len(days) / count
        picks = [days[int(i * step)] for i in range(count)]
    else:
        picks = list(days)
    rest = sorted((w for w in windows if w not in picks), key=lambda w: (-(w[1] - w[0]), w[0]))
    return picks + [w for w in days if w not in picks] + rest


def _break_note(minutes: int, language: str) -> str | None:
    if minutes < 120:
        return None
    marks = [90 * i for i in range(1, 4) if 90 * i < minutes - 20]
    times = ", ".join(f"{mark}" for mark in marks)
    if language == "de":
        return (f"Pause einplanen: nach etwa {times} Minuten je 5–10 Minuten (in der Streamzeit "
                "enthalten). Die Szene „Pause“ aus dem Layout-Baukasten passt dafür.")
    return (f"Plan breaks: 5–10 minutes after about {times} minutes (included in the stream "
            "time). The “Pause” scene from the layout builder fits this.")


def _timing_reason(game: str, slot: SlotInfo | None, stream: Session, request: StrategyRequest,
                   snaps: list[CategorySnapshot]) -> str:
    de = request.language == "de"
    window = f"{stream.label} {stream.start}–{stream.end}"
    if slot is not None:
        own = request.average_viewers
        place = rank_label(slot.median_rank, slot.rank_is_lower_bound, request.language)
        if de:
            viewers = "1 Zuschauer" if own == 1 else f"{own} Zuschauern"
            return (f"Mit {viewers} etwa {place} in {game} ({slot.label}, Median aus "
                    f"{slot.measurements} Messung(en), ca. {slot.median_total_viewers} Zuschauer "
                    "insgesamt) – das beste Publikum pro Platz in deinen Zeitfenstern.")
        viewers = "1 viewer" if own == 1 else f"{own} viewers"
        return (f"With {viewers} about {place} in {game} ({slot.label}, median of "
                f"{slot.measurements} measurement(s), about {slot.median_total_viewers} viewers "
                "in total) – the best audience per position in your windows.")
    if snaps:
        return (f"Für dieses Zeitfenster gibt es keine passende Messung zu {game}; Uhrzeit "
                f"({window}) kommt aus deinem Zeitfenster." if de else
                f"No matching measurement for {game} in this window; the time ({window}) comes "
                "from your window.")
    return (f"Uhrzeit ({window}) kommt nur aus deinem Zeitfenster – ohne Messungen weiß der Plan "
            f"nicht, wann in {game} am meisten los ist." if de else
            f"The time ({window}) only comes from your window – without measurements the plan "
            f"doesn't know when {game} is busiest.")


def _notes(request: StrategyRequest, level: str, genres: dict[str, str | None],
           game_slots: dict[str, list[SlotInfo]], streams: list[StreamPlan]) -> list[str]:
    de = request.language == "de"
    notes: list[str] = []
    if level == "none":
        notes.append(
            "Weil höchstens 2 Leute aktiv chatten, enthält der Plan nur Formate, die ohne Chat "
            "funktionieren – mit Messgrößen, die keine Chat-Reaktionen brauchen." if de else
            "Because at most 2 people chat actively, the plan only contains formats that work "
            "without chat – with measurements that don't need chat reactions.")
    for game, genre in genres.items():
        if genre is None:
            notes.append(
                f"„{game}“: kein Genre erkannt – der Plan nutzt allgemeine Formate. Falls die "
                "Schreibweise nicht stimmt: die Twitch-Kategorie genau angeben." if de else
                f"“{game}”: no genre recognised – the plan uses general formats. If the spelling "
                "is off, use the exact Twitch category.")
    if not any(game_slots.values()):
        notes.append(
            "Uhrzeiten kommen nur aus deinen Zeitfenstern. Für Uhrzeiten nach Publikum eine Woche "
            "messen: python -m streaming_agents.category_check watch \"Spiel\" --every 60 "
            "--hours 168 --out messungen.jsonl – dann den Plan mit --measurements messungen.jsonl "
            "erstellen." if de else
            "Times only come from your windows. To pick times by audience, measure for a week: "
            "python -m streaming_agents.category_check watch \"Game\" --every 60 --hours 168 "
            "--out measurements.jsonl – then build the plan with --measurements "
            "measurements.jsonl.")
    else:
        missing = [game for game, slots in game_slots.items() if not slots]
        if missing:
            notes.append(
                "Keine verwertbaren Messungen für: " + ", ".join(missing) + "." if de else
                "No usable measurements for: " + ", ".join(missing) + ".")
    if request.platform != "twitch":
        notes.append(
            "Titel und Tags folgen den Twitch-Grenzen; auf anderen Plattformen gelten eigene Regeln."
            if de else
            "Titles and tags follow Twitch's limits; other platforms have their own rules.")
    if any(item.needs_collab for item in streams):
        notes.append(
            "Koop- und Coach-Formate nur mit Einverständnis der Mitspieler, dass sie im Stream zu "
            "hören sind." if de else
            "Co-op and coach formats only with your teammates' consent to be heard on stream.")
    if len({item.stream.day for item in streams}) == 7:
        notes.append(
            "Der Plan hat keinen freien Tag. Ein Tag ohne Stream hilft gegen Überlastung." if de else
            "The plan has no day off. One day without streaming helps against burnout.")
    repeated = {item.format_id for item in streams
                if sum(other.format_id == item.format_id for other in streams) > 1}
    if repeated:
        notes.append(
            "Manche Formate kommen mehrmals vor – Wiederholung macht den Kanal für Stammzuschauer "
            "wiedererkennbar." if de else
            "Some formats appear more than once – repetition makes the channel recognisable for "
            "regulars.")
    return notes
