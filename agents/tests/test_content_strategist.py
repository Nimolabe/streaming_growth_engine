"""Content Strategist (Variante A): Genres, Formate, Wochenplan, Twitch-Grenzen, Messungen."""
import json
import re
import unicodedata
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from streaming_agents.api import app
from streaming_agents.category_check.models import CategorySnapshot
from streaming_agents.content_strategist.cli import main as cli_main
from streaming_agents.content_strategist.formats import FORMATS, FORMATS_BY_ID, formats_for
from streaming_agents.content_strategist.genres import GENRE_LABELS, detect_genre
from streaming_agents.content_strategist.models import StrategyRequest, TimeWindow
from streaming_agents.content_strategist.planner import (
    CHAT_ORDER,
    CLIP_MINUTES,
    PREP_MINUTES,
    REVIEW_MINUTES,
    PlanError,
    build_plan,
)
from streaming_agents.content_strategist.report import render_html, render_text
from streaming_agents.content_strategist.titles import (
    CLIP_TITLES,
    FILLS,
    MOOD_TITLES,
    STREAM_TITLES,
    TITLE_TARGET_CHARS,
    build_titles,
    compound_with_daypart,
    is_emoji,
)
from streaming_agents.content_strategist.twitch_limits import (
    TAG_MAX_CHARS,
    TAGS_MAX_COUNT,
    TITLE_MAX_CHARS,
    clean_tags,
    fit_title,
    is_valid_tag,
    is_valid_title,
    tag_from_text,
)

client = TestClient(app)
GENRES = list(GENRE_LABELS)
EXAMPLE_GAMES = {
    "shooter": "Valorant", "battle_royale": "Fortnite", "moba": "League of Legends",
    "story": "Hollow Knight", "horror": "Phasmophobia", "cozy": "Stardew Valley",
    "sandbox": "Minecraft", "sports": "Rocket League", "just_chatting": "Just Chatting",
}
WINDOWS = ["Mo 18-22", "Mi 18-22", "Fr 19-23", "Sa 14-20", "So 15-19"]
PROFILES = {
    "0-3": {"average_viewers": 1, "active_chatters": 0, "hours_per_week": 6,
            "streams_per_week": 2, "experience": "beginner", "goal": "discovery"},
    "5-10": {"average_viewers": 7, "active_chatters": 4, "hours_per_week": 10,
             "streams_per_week": 3, "experience": "intermediate", "goal": "community"},
    "15-20": {"average_viewers": 18, "active_chatters": 9, "hours_per_week": 14,
              "streams_per_week": 4, "experience": "advanced", "goal": "consistency",
              "collab_partner": True},
}


def request(games=("Valorant",), windows=WINDOWS, **extra) -> StrategyRequest:
    base = {"games": list(games), "windows": [TimeWindow.parse(w) for w in windows],
            "hours_per_week": 8, "streams_per_week": 3}
    base.update(extra)
    return StrategyRequest(**base)


def week_minute(day: int, clock: str) -> int:
    hours, minutes = clock.split(":")
    return day * 1440 + int(hours) * 60 + int(minutes)


def stream_span(item) -> tuple[int, int]:
    start = week_minute(item.stream.day, item.stream.start)
    return start, start + item.stream.minutes


# ------------------------------------------------------------------ Genres
@pytest.mark.parametrize(("name", "genre"), [
    ("Valorant", "shooter"), ("CS2", "shooter"), ("Counter-Strike 2", "shooter"),
    ("counter strike", "shooter"), ("Call of Duty", "shooter"), ("Overwatch 2", "shooter"),
    ("Fortnite", "battle_royale"), ("Apex Legends", "battle_royale"),
    ("Call of Duty: Warzone", "battle_royale"), ("PUBG: BATTLEGROUNDS", "battle_royale"),
    ("League of Legends", "moba"), ("LoL", "moba"), ("Dota 2", "moba"),
    ("Hollow Knight", "story"), ("ELDEN RING", "story"), ("The Last of Us Part I", "story"),
    ("Baldur's Gate 3", "story"),
    ("Phasmophobia", "horror"), ("Resident Evil 4", "horror"), ("Lethal Company", "horror"),
    ("Stardew Valley", "cozy"), ("Die Sims 4", "cozy"), ("The Sims 4", "cozy"),
    ("Animal Crossing: New Horizons", "cozy"),
    ("Minecraft", "sandbox"), ("Rust", "sandbox"), ("Valheim", "sandbox"),
    ("ARK: Survival Ascended", "sandbox"),
    ("EA Sports FC 25", "sports"), ("Rocket League", "sports"), ("Forza Horizon 5", "sports"),
    ("Just Chatting", "just_chatting"), ("IRL", "just_chatting"),
    ("Talk Shows & Podcasts", "just_chatting"),
])
def test_genre_detection_covers_common_spellings(name, genre):
    assert detect_genre(name) == genre


@pytest.mark.parametrize("name", ["Dark Souls", "Starfield", "Tetris Effect", "Schach"])
def test_no_false_partial_matches(name):
    # „Dark“ enthält „ark“, „Starfield“ enthält „star“ – nur ganze Wörter zählen.
    assert detect_genre(name) in (None, "story")
    if name != "Dark Souls":
        assert detect_genre(name) is None


def test_unknown_game_is_marked_honestly_and_uses_general_formats():
    plan = build_plan(request(games=("Tetris Effect",), streams_per_week=2))
    assert plan.games[0].genre is None and not plan.games[0].genre_recognized
    assert plan.games[0].genre_label == "kein Genre erkannt"
    assert all(FORMATS_BY_ID[item.format_id].genre is None for item in plan.streams)
    assert any("kein Genre erkannt" in note for note in plan.notes)


# ------------------------------------------------------------------ Katalog
def test_catalog_has_at_least_four_formats_per_genre_and_general():
    for genre in [*GENRES, None]:
        assert len(formats_for(genre)) >= 4, genre
        solo = [f for f in formats_for(genre) if f.needs_chat == "none" and not f.needs_collab]
        assert len(solo) >= 2, genre


def test_catalog_entries_are_complete_and_unique():
    assert len({item.id for item in FORMATS}) == len(FORMATS)
    for item in FORMATS:
        for pair in (item.name, item.hook, item.clip, item.metric,
                     *item.steps, *item.prep, *item.tags, *item.series):
            assert pair[0].strip() and pair[1].strip(), item.id
        assert len(item.steps) == 3 and len(item.prep) == 2
        assert item.series == () or len(item.series) == 3


def test_english_texts_contain_no_german():
    for item in FORMATS:
        english = [item.name[1], item.hook[1], item.clip[1], item.metric[1],
                   *(pair[1] for pair in (*item.steps, *item.prep, *item.tags, *item.series)),
                   *(pair[1] for pair in CLIP_TITLES[item.id]),
                   *(STREAM_TITLES[item.id].goal[1], STREAM_TITLES[item.id].invite[1])]
        for text in english:
            assert not set(text) & set("äöüßÄÖÜ"), (item.id, text)
            # „die“ fehlt bewusst: englisches Verb („We all die. Together.“)
            assert not any(word in text.split() for word in ("und", "mit", "der", "das"))


def test_chat_free_formats_measure_without_chat():
    words = ("chat", "abstimm", "vote", "vorschl", "suggest", "frage", "question")
    for item in FORMATS:
        if item.needs_chat == "none":
            for text in item.metric:
                assert not any(word in text.casefold() for word in words), item.id


def test_team_communication_format_is_reachable():
    plan = build_plan(request(games=("Fortnite",), hours_per_week=14, streams_per_week=5,
                              collab_partner=True, goal="community", active_chatters=0))
    assert "br-squad-comms" in {item.format_id for item in plan.streams}


def test_english_mood_titles_contain_no_german():
    for moods in MOOD_TITLES.values():
        for _, english in moods.values():
            assert not set(english) & set("äöüßÄÖÜ"), english


def test_genres_do_not_borrow_ideas_from_each_other():
    texts = {genre: " ".join(" ".join((f.name[0], *STREAM_TITLES[f.id].goal,
                                       *(s[0] for s in f.steps)))
                             for f in formats_for(genre)).casefold() for genre in GENRES}
    for genre in ("cozy", "horror", "story", "just_chatting", "moba", "sports"):
        assert "baufehler" not in texts[genre] and "fadenkreuz" not in texts[genre]
    assert "landeplatz" not in texts["shooter"] + texts["moba"] + texts["cozy"]


# ------------------------------------------------------------------ Twitch-Grenzen
def test_twitch_limit_helpers():
    assert is_valid_tag("StardewValley") and is_valid_tag("Gemütlich") and is_valid_tag("CS2")
    for bad in ("", "Two words", "Tag-with-dash", "Hash#", "under_score", "x" * 26):
        assert not is_valid_tag(bad)
    assert tag_from_text("Counter-Strike 2") == "CounterStrike2"
    assert tag_from_text("Baldur's Gate 3") == "BaldursGate3"
    assert len(tag_from_text("A very long game name with many words in it")) == TAG_MAX_CHARS
    assert clean_tags(["Deutsch", "deutsch", "Horror", "two words"]) == ["Deutsch", "Horror",
                                                                       "TwoWords"]
    assert len(clean_tags([f"Tag{i}" for i in range(20)])) == TAGS_MAX_COUNT
    long_title = "Wort " * 60
    assert len(fit_title(long_title)) <= TITLE_MAX_CHARS and fit_title(long_title).endswith("…")
    assert not is_valid_title("   ") and is_valid_title("x" * TITLE_MAX_CHARS)
    assert not is_valid_title("x" * (TITLE_MAX_CHARS + 1))


def test_long_game_name_keeps_title_and_tags_within_limits():
    name = "The Extraordinarily Long Adventure of Someone With A Remarkably Lengthy Game Title X"
    plan = build_plan(request(games=(name[:80],), streams_per_week=2))
    for item in plan.streams:
        assert is_valid_title(item.title)
        assert all(is_valid_tag(tag) for tag in item.tags) and len(item.tags) <= TAGS_MAX_COUNT


# ------------------------------------------------------------------ Alle Genres × Profile
@pytest.mark.parametrize("genre", GENRES)
@pytest.mark.parametrize("profile", list(PROFILES))
@pytest.mark.parametrize("language", ["de", "en"])
def test_example_profiles_fit_genre_windows_hours_and_limits(genre, profile, language):
    req = request(games=(EXAMPLE_GAMES[genre],), language=language, **PROFILES[profile])
    plan = build_plan(req)
    assert len(plan.streams) == req.streams_per_week
    windows = [(w.week_start, w.week_start + w.minutes) for w in req.windows]
    previous_end = -1
    for item in plan.streams:
        assert FORMATS_BY_ID[item.format_id].genre == genre
        start, end = stream_span(item)
        assert any(a <= start and end <= b for a, b in windows), item.stream
        assert item.stream.minutes >= 60
        assert start >= previous_end
        previous_end = end
        prep_end = week_minute(item.preparation.day, item.preparation.end)
        assert prep_end <= start
        assert is_valid_title(item.title)
        assert len(item.tags) <= TAGS_MAX_COUNT and all(is_valid_tag(tag) for tag in item.tags)
        if not req.collab_partner:
            assert not item.needs_collab
    used = (plan.budget.stream_minutes + plan.budget.preparation_minutes
            + plan.budget.clip_minutes + plan.budget.review_minutes)
    assert used <= req.hours_per_week * 60 and plan.budget.unplanned_minutes >= 0
    assert plan.budget.preparation_minutes == PREP_MINUTES * req.streams_per_week
    assert plan.budget.clip_minutes == CLIP_MINUTES * req.streams_per_week
    assert plan.budget.review_minutes == REVIEW_MINUTES


@pytest.mark.parametrize("game", [*EXAMPLE_GAMES.values(), "Tetris Effect"])
@pytest.mark.parametrize("chatters", [0, 1, 2])
def test_no_chat_dependent_format_with_two_or_fewer_chatters(game, chatters):
    plan = build_plan(request(games=(game,), hours_per_week=20, streams_per_week=5,
                              active_chatters=chatters, goal="community", collab_partner=True))
    assert plan.chat_level == "none"
    assert all(item.needs_chat == "none" for item in plan.streams)


def test_chat_formats_appear_with_enough_chatters():
    small = build_plan(request(games=("Valorant",), streams_per_week=5, hours_per_week=20,
                               active_chatters=4, goal="community"))
    assert "low" in {item.needs_chat for item in small.streams}
    assert "active" not in {item.needs_chat for item in small.streams}
    busy = build_plan(request(games=("Minecraft",), streams_per_week=5, hours_per_week=20,
                              active_chatters=10, goal="community"))
    assert "sandbox-chat-build" in {item.format_id for item in busy.streams}


# ------------------------------------------------------------------ Zeitfenster und Budget
def test_window_over_midnight():
    plan = build_plan(request(windows=["Fr 22-2"], streams_per_week=1, hours_per_week=6))
    item = plan.streams[0]
    assert item.stream.start == "22:00" and item.stream.minutes == 240
    assert item.stream.end == "02:00" and "bis Sa" in item.stream.label
    assert item.preparation.start == "21:30" and item.preparation.end == "21:50"


def test_single_window_and_stream_shorter_than_budget_when_window_is_short():
    plan = build_plan(request(windows=["Di 19:00-20:15"], streams_per_week=1, hours_per_week=10))
    assert plan.streams[0].stream.minutes == 75
    assert plan.budget.unplanned_minutes > 0


def test_more_streams_than_windows_is_a_clear_error():
    with pytest.raises(PlanError, match="2 nutzbare.*3 Streams"):
        build_plan(request(windows=["Mo 18-22", "Sa 14-16"], streams_per_week=3, hours_per_week=10))
    with pytest.raises(PlanError, match="usable window"):
        build_plan(request(windows=["Mo 18-22"], streams_per_week=2, language="en"))


def test_overlapping_windows_count_once_and_short_windows_are_ignored():
    with pytest.raises(PlanError, match="1 nutzbare"):
        build_plan(request(windows=["Mo 18-22", "Mo 19-21", "Di 18:00-18:45"], streams_per_week=2))


def test_too_few_hours_is_a_clear_error():
    # Fehler nur, wenn nicht einmal 3 × (60 min Stream + 15 min Vorbereitung) passen.
    with pytest.raises(PlanError, match="mindestens 4 Stunden.*gesamte Zeit"):
        build_plan(request(streams_per_week=3, hours_per_week=3))
    with pytest.raises(PlanError, match="at least 4 hours"):
        build_plan(request(streams_per_week=3, hours_per_week=3, language="en"))


def test_stream_never_below_60_or_above_240_minutes():
    plan = build_plan(request(windows=["Sa 0-24"], streams_per_week=1, hours_per_week=40))
    assert plan.streams[0].stream.minutes == 240
    plan = build_plan(request(streams_per_week=3, hours_per_week=6))
    assert all(item.stream.minutes == 60 for item in plan.streams)


def test_streams_are_spread_over_the_week_and_have_breaks():
    plan = build_plan(request(streams_per_week=3, hours_per_week=12))
    days = [item.stream.day for item in plan.streams]
    assert len(set(days)) == 3
    assert all(item.break_note for item in plan.streams if item.stream.minutes >= 120)


@pytest.mark.parametrize("text", ["Mo", "Xy 18-22", "Mo 25-26", "Mo 18-18", "Mo 18:75-20"])
def test_invalid_windows_are_rejected(text):
    with pytest.raises(ValueError):
        TimeWindow.parse(text)


def test_window_parsing_accepts_german_and_english_days():
    assert TimeWindow.parse("Sonntag 9-12").day == 6
    assert TimeWindow.parse("Sun 9:30-12").start == 570
    assert TimeWindow.parse("Mi 0-24").minutes == 1440


# ------------------------------------------------------------------ Kategorie-Check
def snapshot(category: str, weekday: int, hour: int, viewers: list[int]) -> CategorySnapshot:
    # 2026-11-23 ist ein Montag; Zeiten in UTC, Plan mit utc_offset_minutes=0
    taken = datetime(2026, 11, 23 + weekday, hour, 10, tzinfo=UTC).timestamp()
    return CategorySnapshot(taken_at=taken, category_id="21779", category=category, language="de",
                            complete=True, viewers=sorted(viewers, reverse=True))


def measured(games=("League of Legends",), **extra):
    crowded = [900, 400, 200] + [5] * 60          # Mo 18–20: viel Konkurrenz
    sweet = [300, 120, 40] + [4] * 12 + [1] * 10  # Di 20–22: Publikum und guter Platz
    quiet = [30, 2, 1]                            # Sa 14–16: kaum Publikum
    snaps = [snapshot("League of Legends", 0, 18, crowded), snapshot("League of Legends", 0, 18, crowded),
             snapshot("League of Legends", 1, 20, sweet), snapshot("League of Legends", 1, 20, sweet),
             snapshot("League of Legends", 5, 14, quiet)]
    return request(games=games, windows=["Mo 18-22", "Di 18-23", "Sa 14-20"],
                   streams_per_week=1, hours_per_week=4, average_viewers=3, measurements=snaps,
                   utc_offset_minutes=0, **extra)


def test_measurements_pick_the_window_and_time_with_best_audience_per_position():
    plan = build_plan(measured())
    item = plan.streams[0]
    assert plan.timing_source == "measurements"
    assert item.stream.label == "Di" and item.stream.start == "20:00"
    assert "Platz 16" in item.timing_reason and "Di 20–22 Uhr" in item.timing_reason
    assert "3 Zuschauern" in item.timing_reason
    assert plan.games[0].category_check


def test_measurements_for_other_games_do_not_change_times():
    plan = build_plan(measured(games=("Valorant",)))
    assert plan.timing_source == "windows_only"
    assert "kommt nur aus deinem Zeitfenster" in plan.streams[0].timing_reason


def test_measurements_are_found_via_short_names():
    # „LoL“ ist im Kategorie-Check eine Kurzform für „League of Legends“ (aliases.py).
    plan = build_plan(measured(games=("LoL",)))
    assert plan.timing_source == "measurements"
    item = plan.streams[0]
    assert item.game == "LoL" and item.stream.label == "Di" and item.stream.start == "20:00"
    assert plan.games[0].category_check
    cs = [snapshot("Counter-Strike", 1, 20, [300, 120, 40] + [4] * 12)]
    plan = build_plan(request(games=("CS2",), windows=["Di 18-23"], streams_per_week=1,
                              hours_per_week=4, average_viewers=3, measurements=cs,
                              utc_offset_minutes=0))
    assert plan.timing_source == "measurements" and plan.streams[0].stream.start == "20:00"


def test_web_surface_note_has_no_command_line():
    plan = build_plan(request(), surface="web")
    assert not any("python -m" in note for note in plan.notes)
    assert any(note.startswith("Die Uhrzeiten kommen aus deinen eigenen Zeitfenstern.") for note in plan.notes)


def test_without_measurements_the_plan_says_how_to_measure():
    plan = build_plan(request())
    assert plan.timing_source == "windows_only"
    assert any("category_check watch" in note for note in plan.notes)


# ------------------------------------------------------------------ Determinismus, API, CLI
def test_same_input_same_output():
    first = build_plan(measured()).model_dump()
    second = build_plan(measured()).model_dump()
    assert first == second
    many = request(games=("Valorant", "Minecraft", "Just Chatting"), streams_per_week=5,
                   hours_per_week=16, active_chatters=5)
    assert build_plan(many).model_dump() == build_plan(many).model_dump()


def test_multiple_games_rotate_and_do_not_repeat_formats_within_genre():
    plan = build_plan(request(games=("Valorant", "CS2"), streams_per_week=3, hours_per_week=12))
    assert [item.game for item in plan.streams].count("Valorant") == 2
    ids = [item.format_id for item in plan.streams]
    assert len(set(ids)) == len(ids)


def test_api_returns_plan_and_errors():
    body = {"games": ["Stardew Valley"], "windows": [{"day": "Mo", "start": "18", "end": "22"},
                                                     {"day": 5, "start": "14:00", "end": "20:00"}],
            "hours_per_week": 6, "streams_per_week": 2, "average_viewers": 2}
    response = client.post("/api/v1/content/strategy", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "content-strategist-a1" and len(data["streams"]) == 2
    assert client.post("/api/v1/content/strategy",
                       json=body | {"streams_per_week": 3}).status_code == 422
    assert client.post("/api/v1/content/strategy", json=body | {"games": []}).status_code == 422


def test_reports_escape_input(tmp_path):
    plan = build_plan(request(games=("<img src=x onerror=alert(1)>",), streams_per_week=1))
    html = render_html(plan)
    assert "<img src=x" not in html and "&lt;img src=x" in html
    assert "Content-Plan der Woche" in render_text(plan)


def test_cli_writes_json_and_html(tmp_path, capsys):
    out_json, out_html = tmp_path / "plan.json", tmp_path / "plan.html"
    code = cli_main(["plan", "--game", "Phasmophobia", "--window", "Fr 20-23",
                     "--window", "Sa 20-23", "--hours", "6", "--streams", "2", "--viewers", "2",
                     "--json", str(out_json), "--html", str(out_html)])
    assert code == 0
    assert "Phasmophobia" in capsys.readouterr().out
    assert json.loads(out_json.read_text(encoding="utf-8"))["streams"][0]["game"] == "Phasmophobia"
    assert out_html.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")
    assert cli_main(["plan", "--game", "Phasmophobia", "--window", "Fr 20-23", "--hours", "6",
                     "--streams", "2", "--json", str(out_json)]) == 2
    assert "nutzbare" in capsys.readouterr().err


def test_cli_reads_measurements(tmp_path, capsys):
    path = tmp_path / "messungen.jsonl"
    path.write_text("".join(item.model_dump_json() + "\n" for item in measured().measurements),
                    encoding="utf-8")
    code = cli_main(["plan", "--game", "League of Legends", "--window", "Mo 18-22",
                     "--window", "Di 18-23", "--hours", "4", "--streams", "1", "--viewers", "3",
                     "--measurements", str(path), "--utc-offset", "0"])
    assert code == 0 and "Platz 16" in capsys.readouterr().out


# ------------------------------------------------------------------ Titel (Nachtrag 4)
SINGLE_MOMENT = (  # Regel 5: Titel beziehen sich auf den ganzen Stream
    "diese runde", "dieser runde", "dieses match", "diesem match", "diese ecke", "dieser ecke",
    "dieser abschnitt", "diesen abschnitt", "diesem abschnitt", "diese szene", "dieser szene",
    "diesen moment", "diesem moment", "dieses spiel verloren",
    "this round", "that round", "this match", "that match", "this corner", "this section",
    "this scene", "this moment", "that game",
)
ABBREVIATIONS = {"LoL", "CS2", "MMR", "CS", "PB", "RP", "FPS", "KO"}
TITLE_GAMES = ["Valorant", "League of Legends", "Stardew Valley", "Tetris Effect"]
GENRE_OF_FORMAT = {item.id: item.genre for item in FORMATS}


def caps_words(text: str) -> list[str]:
    words = re.findall(r"[A-Za-zÄÖÜäöüß0-9-]+", text)
    return [word for word in words if word not in ABBREVIATIONS
            and len(re.sub(r"[^A-Za-zÄÖÜ]", "", word)) >= 2
            and re.sub(r"[^A-Za-zÄÖÜäöüß]", "", word).isupper()]


def check_title(option, *, target=True):
    text = option.text  # ohne Befehle
    # Regel 2: genau ein Emoji, am Anfang
    assert is_emoji(option.emoji), text
    rest = text[len(option.emoji):]
    assert not any(unicodedata.category(ch) == "So" for ch in rest), text
    # Regel 1: 2–4 Bausteine
    assert 2 <= len(option.blocks) <= 4, text
    assert all(block.strip() for block in option.blocks), text
    # Regel 4 und 5
    assert len(caps_words(rest)) <= 2, (caps_words(rest), text)
    assert text.replace("?!", "!").count("!") <= 1, text
    assert not any(phrase in text.casefold() for phrase in SINGLE_MOMENT), text
    assert "{" not in text and "}" not in text, text
    # Regel 6
    if target:
        assert len(text) <= TITLE_TARGET_CHARS, (len(text), text)
    assert is_valid_title(fit_title(option.full))


@pytest.mark.parametrize("language", ["de", "en"])
@pytest.mark.parametrize("mood", [None, "chill", "ambitious", "funny"])
@pytest.mark.parametrize("format_id", sorted(STREAM_TITLES))
def test_stream_titles_follow_the_rules(format_id, mood, language):
    genre = GENRE_OF_FORMAT[format_id]
    for game in TITLE_GAMES:
        for start in (10 * 60, 15 * 60, 19 * 60, 23 * 60):
            for kwargs in ({}, {"rank_goal": "Platin", "rank_counter": 12},
                           {"rank_goal": "Diamant", "current_rank": "Silber"},
                           {"first_time": True}, {"counter": 9}):
                options = build_titles(format_id, genre, game, language, mood=mood,
                                       start_minute=start, **kwargs)
                assert len(options) == 3
                assert {option.approach for option in options} == {"goal", "mood", "invite"}
                # die drei Titel unterscheiden sich im ersten Baustein
                assert len({option.blocks[0] for option in options}) == 3, options
                for option in options:
                    check_title(option)


def test_titles_with_very_long_names_stay_within_twitch_limit():
    for format_id in STREAM_TITLES:
        for language in ("de", "en"):
            for option in build_titles(format_id, GENRE_OF_FORMAT[format_id], "x" * 80, language,
                                       rank_goal="y" * 20, current_rank="z" * 20,
                                       first_time=True, commands=["!discord"]):
                check_title(option, target=False)
                assert len(option.full) <= TITLE_MAX_CHARS


def test_title_data_is_complete():
    assert set(STREAM_TITLES) == set(FORMATS_BY_ID) == set(CLIP_TITLES)
    assert set(FILLS) <= set(STREAM_TITLES)
    assert set(MOOD_TITLES) == {*GENRES, None}
    assert all(set(moods) == {"chill", "ambitious", "funny"} for moods in MOOD_TITLES.values())
    assert {fid for fid, data in STREAM_TITLES.items() if data.first} == {
        "story-first-playthrough", "horror-honest-reactions", "horror-clue-board",
        "general-first-impressions"}


def test_chat_formats_address_the_chat_with_ihr():
    for format_id, data in STREAM_TITLES.items():
        if FORMATS_BY_ID[format_id].needs_chat != "none":
            german = f"{data.goal[0]} {data.invite[0]}"
            assert re.search(r"\b(Ihr|eure|euch|Chat|Sucht|Stimm|Tipp|Tauf|Gib|Zähl|Rate)\b",
                             german), german


def test_commands_are_appended_validated_and_dropped_when_too_long():
    options = build_titles("sandbox-big-project", "sandbox", "Minecraft", "de",
                           commands=["!discord", "!insta"])
    assert all(option.full.endswith(" | !discord !insta") for option in options)
    assert all(option.commands and option.text in option.full for option in options)
    for bad in (["!Discord"], ["discord"], ["!a b"], ["!" + "x" * 21], ["!a", "!b", "!c", "!d"]):
        with pytest.raises(ValueError):
            build_titles("sandbox-big-project", "sandbox", "Minecraft", "de", commands=bad)
        with pytest.raises(ValueError):
            request(commands=bad)
    long_game = "x" * 80
    options = build_titles("sandbox-chat-build", "sandbox", long_game, "de",
                           commands=["!discord", "!instagram", "!youtube_kanal"])
    dropped = [option for option in options if not option.commands]
    assert dropped and all(option.full == option.text for option in dropped)
    assert all(len(option.full) <= TITLE_MAX_CHARS for option in options)
    plan = build_plan(request(games=("Minecraft",), streams_per_week=1, commands=["!discord"]))
    assert plan.streams[0].title.endswith(" | !discord")


def test_current_rank_needs_a_rank_goal():
    only_current = build_titles("shooter-decision-review", "shooter", "Valorant", "de",
                                current_rank="Silber")
    assert not any("Silber" in option.text for option in only_current)
    journey = build_titles("shooter-decision-review", "shooter", "Valorant", "en",
                           current_rank="Silver", rank_goal="Gold", rank_counter=4)
    assert journey[0].text == "🔴 From Silver to Gold | Day 4 | Come in!"
    road = build_titles("shooter-decision-review", "shooter", "Valorant", "de", rank_goal="Gold")
    assert road[0].text.startswith("🔴 Ranked Grind | Tag 1 | Road to Gold")


def test_rank_goal_only_where_given_and_ranked():
    plain = build_titles("shooter-decision-review", "shooter", "Valorant", "de")
    assert not any("Road to" in option.text for option in plain)
    assert any(option.text.startswith("🔴 Ranked-Abend") for option in plain)
    cozy = build_titles("cozy-three-goals", "cozy", "Stardew Valley", "de", rank_goal="Platin")
    assert not any("Platin" in option.text for option in cozy)


def test_first_time_and_daypart():
    first = build_titles("story-first-playthrough", "story", "Elden Ring", "de", first_time=True)
    assert first[0].text == "🗡️ Zum ersten Mal Elden Ring | Blind | Keine Spoiler!"
    afternoon = build_titles("horror-honest-reactions", "horror", "Phasmophobia", "de",
                             start_minute=14 * 60, rotation=1)
    assert afternoon[0].text.startswith("😱 Horror-Nachmittag")
    night = build_titles("horror-honest-reactions", "horror", "Phasmophobia", "de",
                         start_minute=23 * 60, rotation=1)
    assert night[0].text.startswith("😱 Horror-Nacht")


def test_plan_titles_cover_whole_stream_with_alternatives_and_clip_ideas():
    plan = build_plan(request(games=("Stardew Valley",), streams_per_week=3))
    for item in plan.streams:
        assert len(item.title_alternatives) == 2 and item.title not in item.title_alternatives
        assert all(is_valid_title(text) for text in [item.title, *item.title_alternatives])
        assert item.clip_title_ideas
        assert item.title_mood == ("funny" if item.format_id == "cozy-one-rule" else "chill")
    text, html = render_text(plan), render_html(plan)
    assert "Andere Titel" in text and "Titel fürs Kurzvideo" in html


def test_mood_input_accepts_german_words():
    plan = build_plan(request(games=("Minecraft",), streams_per_week=1, mood="lustig"))
    assert plan.streams[0].title_mood == "funny"
    with pytest.raises(ValueError):
        request(rank_goal="<script>")


def test_same_format_in_one_week_never_repeats_the_main_title():
    plan = build_plan(request(games=("Minecraft",), streams_per_week=5, hours_per_week=20,
                              windows=["Mo 18-22", "Di 18-22", "Mi 18-22", "Fr 18-22", "Sa 12-20"]))
    seen: dict[str, set[str]] = {}
    repeated = False
    for item in plan.streams:
        titles = seen.setdefault(item.format_id, set())
        repeated |= bool(titles)
        assert item.title not in titles
        titles.add(item.title)
    assert repeated  # 5 Streams, 4 passende Formate → eines kommt zweimal


def test_week_number_and_rank_counter_advance():
    first = build_plan(request(games=("Valorant",), streams_per_week=2, rank_goal="Gold"))
    second = build_plan(request(games=("Valorant",), streams_per_week=2, rank_goal="Gold",
                                week_number=3))
    assert "Tag 1" in first.streams[0].title
    assert "Tag 5" in second.streams[0].title


@pytest.mark.parametrize(("name", "genre"), [
    ("GTA V", None), ("Grand Theft Auto V", None), ("GTA RP", None),
    ("World of Warcraft", None), ("ARC Raiders", "shooter"), ("Arc Raiders", "shooter"),
    ("R.E.P.O.", "horror"), ("Repo Man", None),
])
def test_genre_additions_and_removed_repo_alias(name, genre):
    assert detect_genre(name) == genre


def test_week_recap_only_on_the_last_stream():
    plan = build_plan(request(games=("Just Chatting",), streams_per_week=3, goal="community"))
    ids = [item.format_id for item in plan.streams]
    assert ids[-1] == "jc-week-recap" and "jc-week-recap" not in ids[:-1]
    single = build_plan(request(games=("Just Chatting",), streams_per_week=1, goal="community"))
    assert single.streams[0].format_id != "jc-week-recap"
    for profile in PROFILES.values():
        for language in ("de", "en"):
            ids = [item.format_id for item in build_plan(request(
                games=("Just Chatting",), language=language, **profile)).streams]
            assert "jc-week-recap" not in ids[:-1]


# ------------------------------------------------------------------ Simulation (Nachtrag 5)
# Fehler aus einer Simulation mit 100 Test-Streamern: falsche „Erste Stunde“-Titel bei vertrauten
# Spielen, Fehler bei knappen Stunden, TimeWindow-Beschreibung, Wochen-Formate mitten in der Woche.
FIRST_TIME_PHRASES = ("erste stunde", "neues spiel", "zum ersten mal", "first hour", "new game",
                      "first time")


@pytest.mark.parametrize(("name", "genre"), [
    ("Hogwarts Legacy", "story"), ("Pokémon Legenden: Z-A", "story"),
    ("Pokémon Karmesin/Purpur", "story"), ("Pokemon Karmesin", "story"),
    ("Pokémon Legends: Arceus", "story"), ("Pokémon UNITE", "moba"),
    ("Euro Truck Simulator 2", "cozy"), ("ETS2", "cozy"),
    ("GTA V", None), ("World of Warcraft", None), ("Teamfight Tactics", None),
])
def test_genre_detection_after_simulation(name, genre):
    assert detect_genre(name) == genre


@pytest.mark.parametrize("game", ["World of Warcraft", "GTA V", "Teamfight Tactics"])
def test_familiar_unknown_games_never_get_first_hour_titles(game):
    for profile in PROFILES.values():
        for language in ("de", "en"):
            plan = build_plan(request(games=(game,), language=language, **profile))
            ids = {item.format_id for item in plan.streams}
            assert "general-first-impressions" not in ids
            assert ids & {"general-evening-goal", "general-chill", "general-viewer-games",
                          "general-progress"}
            for item in plan.streams:
                for title in (item.title, *item.title_alternatives):
                    assert not any(p in title.casefold() for p in FIRST_TIME_PHRASES), title


def test_first_impressions_only_with_first_time():
    plan = build_plan(request(games=("World of Warcraft",), first_time=True))
    assert plan.streams[0].format_id == "general-first-impressions"
    assert "Zum ersten Mal World of Warcraft" in plan.streams[0].title


def test_new_general_titles_are_taken_over_word_for_word():
    def titles(format_id, language, **extra):
        return {option.approach: option.text for option in build_titles(
            format_id, None, "World of Warcraft", language, start_minute=19 * 60, **extra)}
    assert titles("general-evening-goal", "de")["goal"] == \
        "🎯 Heute mit Ziel in World of Warcraft | Schaffen wir das?"
    assert titles("general-evening-goal", "en")["invite"] == \
        "🎮 World of Warcraft with a plan | Come see if it works!"
    assert titles("general-chill", "de")["invite"] == "🎮 World-of-Warcraft-Abend | Chill mit!"
    assert titles("general-chill", "en")["invite"] == "🎮 World of Warcraft evening | Chill with me!"
    assert titles("general-viewer-games", "de")["goal"] == \
        "🤝 Zuschauerrunde in World of Warcraft | Spiel mit!"
    assert titles("general-progress", "de", counter=4)["goal"] == \
        "📈 World of Warcraft | Tag 4 | Wie weit kommen wir heute?"
    assert titles("general-progress", "en", counter=4)["invite"] == \
        "🔥 Back in World of Warcraft | Day 4 | Come in!"
    assert FORMATS_BY_ID["general-viewer-games"].needs_chat == "low"
    assert FORMATS_BY_ID["general-progress"].series


def test_game_and_daypart_form_one_readable_word():
    assert compound_with_daypart("World of Warcraft", "Abend") == "World-of-Warcraft-Abend"
    assert compound_with_daypart("GTA V", "Nacht") == "GTA-V-Nacht"
    assert compound_with_daypart("Palia", "Vormittag") == "Palia-Vormittag"
    assert compound_with_daypart("Warhammer 40,000: Darktide", "Abend") == \
        "Abend in Warhammer 40,000: Darktide"


def test_tight_hours_trim_extras_instead_of_failing():
    # 2 Streams à 2 h = 4 h: früher ein Fehler, jetzt mit gekürztem Rückblick.
    plan = build_plan(request(streams_per_week=2, hours_per_week=4))
    assert [item.stream.minutes for item in plan.streams] == [60, 60]
    budget = plan.budget
    assert budget.review_minutes < 30 and budget.unplanned_minutes >= 0
    assert budget.stream_minutes + budget.preparation_minutes + budget.clip_minutes + \
        budget.review_minutes + budget.unplanned_minutes == 240
    assert any("Zeit ist knapp" in note and "Wochenrückblick" in note for note in plan.notes)
    # 2 Streams in 3 h: Rückblick und Clip-Zeit fallen weg, Vorbereitung bleibt.
    plan = build_plan(request(streams_per_week=2, hours_per_week=3, language="en"))
    assert plan.budget.clip_minutes == 0 and plan.review.minutes == 0
    assert all(item.preparation.minutes == 20 for item in plan.streams)
    assert "no fixed clip time" in plan.streams[0].clip_day
    assert any("weekly review left out" in note for note in plan.notes)
    assert "optional" in render_text(plan) and "optional" in render_html(plan)
    # 4 Streams in 5 h: als Letztes wird die Vorbereitung auf 15 min gekürzt.
    plan = build_plan(request(streams_per_week=4, hours_per_week=5))
    assert all(item.preparation.minutes == 15 and item.stream.minutes == 60
               for item in plan.streams)
    assert plan.budget.unplanned_minutes == 0
    # Mit genug Zeit bleibt alles wie bisher – ohne Hinweis.
    plan = build_plan(request(streams_per_week=2, hours_per_week=8))
    assert plan.review.minutes == 30 and not any("knapp" in note for note in plan.notes)


def test_time_window_accepts_clock_times_and_rejects_minutes():
    assert TimeWindow(day="Mo", start=18, end="22:30").start == 18 * 60
    assert TimeWindow(day=0, start="18", end=24).end == 1440
    window = TimeWindow(day="Fr", start="22", end=2)
    assert window.model_dump() == {"day": 4, "start": "22:00", "end": "02:00"}
    assert TimeWindow.model_validate(window.model_dump()) == window
    for bad in (1080, 25, -1, 18.5, True):
        with pytest.raises(ValueError, match="HH:MM"):
            TimeWindow(day=0, start=bad, end=22)


def test_api_time_window_numbers_and_schema():
    body = {"games": ["Minecraft"], "hours_per_week": 6, "streams_per_week": 1,
            "windows": [{"day": "Mo", "start": 18, "end": 22}]}
    assert client.post("/api/v1/content/strategy", json=body).status_code == 200
    body["windows"] = [{"day": "Mo", "start": 1080, "end": 1320}]
    response = client.post("/api/v1/content/strategy", json=body)
    assert response.status_code == 422
    assert "HH:MM" in response.text and "Minuten seit Mitternacht" in response.text
    schema = client.get("/api/v1/openapi.json").json()["components"]["schemas"]
    window = schema["TimeWindow"]["properties"]
    for key in ("start", "end"):
        types = {option["type"] for option in window[key]["anyOf"]}
        assert types == {"integer", "string"}
        assert "HH:MM" in window[key]["description"]
        assert "Minuten seit Mitternacht" not in window[key]["description"]
    assert "GESAMTE" in schema["StrategyRequest"]["properties"]["hours_per_week"]["description"]


def test_moment_of_week_only_as_the_last_stream():
    plan = build_plan(request(games=("World of Warcraft",), streams_per_week=4, hours_per_week=12,
                              goal="community", active_chatters=5))
    ids = [item.format_id for item in plan.streams]
    assert ids[-1] == "general-moment-of-week" and "general-moment-of-week" not in ids[:-1]
    single = build_plan(request(games=("World of Warcraft",), streams_per_week=1,
                                goal="community"))
    assert single.streams[0].format_id != "general-moment-of-week"


def test_story_recap_never_opens_a_game_in_week_one():
    seen_later = False
    for game in ("Hogwarts Legacy", "Elden Ring", "Hollow Knight"):
        for experience in ("beginner", "intermediate", "advanced"):
            for goal in ("discovery", "community", "consistency"):
                for streams in (1, 2, 3):
                    plan = build_plan(request(games=(game,), experience=experience, goal=goal,
                                              streams_per_week=streams, hours_per_week=10))
                    assert plan.streams[0].format_id != "story-recap"
                    seen_later |= "story-recap" in {item.format_id for item in plan.streams}
    assert seen_later  # das Format bleibt erreichbar, nur nicht als Einstieg
    later = build_plan(request(games=("Elden Ring",), experience="advanced", week_number=2))
    assert later.streams[0].format_id == "story-recap"


W_FIVE = WINDOWS
W_ALL = ["Mo 18-22", "Di 18-22", "Mi 18-22", "Do 18-22", "Fr 18-23", "Sa 12-20", "So 12-20"]
W_WEEKEND = ["Fr 22-2", "Sa 14-20", "So 15-19"]
W_EVENINGS = ["Mo 19-21", "Di 19-21", "Mi 19-21", "Do 19-21", "Fr 19-21", "Sa 19-21"]
# (Spiele, Streams, Stunden, Zuschauer, Chatter, Ziel, Erfahrung, first_time, Sprache, Fenster,
#  Woche, Mitspieler, Stimmung, Befehle)
SIMULATION = [
    (("World of Warcraft",), 3, 8, 0, 0, "discovery", "advanced", False, "de", W_FIVE, 1, False, None, ()),
    (("GTA V",), 4, 10, 12, 6, "community", "intermediate", False, "de", W_FIVE, 1, False, None, ()),
    (("Teamfight Tactics",), 2, 4, 3, 1, "consistency", "advanced", False, "en", W_FIVE, 2, False, None, ()),
    (("Valorant",), 5, 15, 40, 12, "discovery", "advanced", False, "de", W_ALL, 1, True, None, ("!discord",)),
    (("Fortnite",), 2, 4, 1, 0, "discovery", "beginner", False, "de", W_FIVE, 1, False, None, ()),
    (("League of Legends",), 3, 9, 100, 30, "community", "advanced", False, "en", W_FIVE, 3, True, "ambitious", ()),
    (("Hogwarts Legacy",), 3, 8, 2, 0, "discovery", "beginner", True, "de", W_FIVE, 1, False, None, ()),
    (("Pokémon Karmesin",), 4, 8, 5, 3, "consistency", "intermediate", False, "de", W_ALL, 1, False, "funny", ()),
    (("Elden Ring",), 2, 5, 8, 2, "discovery", "advanced", False, "en", W_WEEKEND, 1, False, None, ()),
    (("Phasmophobia",), 3, 9, 20, 9, "community", "intermediate", True, "de", W_FIVE, 1, True, None, ()),
    (("Stardew Valley",), 6, 12, 4, 1, "consistency", "beginner", False, "de", W_ALL, 1, False, None, ()),
    (("Euro Truck Simulator 2",), 3, 6, 0, 0, "discovery", "beginner", False, "en", W_FIVE, 1, False, None, ()),
    (("Minecraft",), 5, 20, 60, 15, "community", "advanced", False, "de", W_ALL, 4, True, None, ("!insta", "!yt")),
    (("Rocket League",), 2, 3, 7, 4, "discovery", "intermediate", False, "de", W_FIVE, 1, False, None, ()),
    (("Just Chatting",), 4, 8, 15, 10, "community", "intermediate", False, "de", W_EVENINGS, 1, False, None, ()),
    (("Just Chatting", "World of Warcraft"), 4, 12, 9, 5, "community", "intermediate", False, "en", W_ALL, 1, False, None, ()),
    (("Valorant", "Teamfight Tactics"), 3, 6, 2, 0, "discovery", "beginner", False, "de", W_FIVE, 1, False, None, ()),
    (("Tetris Effect",), 2, 4, 0, 0, "discovery", "beginner", True, "de", W_FIVE, 1, False, None, ()),
    (("Palia",), 4, 7, 3, 3, "community", "beginner", False, "de", W_EVENINGS, 1, False, "chill", ()),
    (("Path of Exile 2",), 6, 9, 25, 8, "consistency", "advanced", False, "de", W_EVENINGS, 5, False, None, ()),
    (("Warhammer 40,000: Darktide",), 3, 8, 6, 3, "community", "intermediate", False, "de", W_FIVE, 1, True, None, ()),
    (("CS2",), 6, 24, 80, 25, "discovery", "advanced", False, "en", W_ALL, 1, True, "funny", ("!discord",)),
    (("Apex Legends", "Fortnite"), 4, 10, 10, 5, "discovery", "intermediate", False, "de", W_FIVE, 1, False, None, ()),
    (("Dead by Daylight",), 2, 4, 0, 0, "community", "beginner", False, "de", W_WEEKEND, 1, False, None, ()),
    (("Hollow Knight",), 3, 5, 1, 0, "consistency", "beginner", False, "de", W_FIVE, 1, False, None, ()),
    (("EA Sports FC 26",), 5, 10, 30, 10, "community", "advanced", False, "de", W_ALL, 2, True, None, ()),
    (("Satisfactory",), 3, 12, 5, 2, "consistency", "intermediate", False, "en", W_WEEKEND, 1, False, None, ()),
    (("Lethal Company", "World of Warcraft", "GTA V"), 5, 15, 18, 9, "community", "advanced", False, "de", W_ALL, 1, True, None, ()),
    (("Pokémon Legenden: Z-A", "Animal Crossing"), 2, 4, 4, 2, "discovery", "beginner", True, "en", W_FIVE, 1, False, None, ()),
    (("Grand Theft Auto V",), 6, 8, 0, 0, "consistency", "beginner", False, "de", W_ALL, 1, False, None, ()),
]


def _check_plan_title(title: str, games: tuple[str, ...]) -> None:
    text = title.split(" | !")[0]  # angehängte Befehle abschneiden
    assert is_valid_title(title), title
    emoji = text.split(" ", 1)[0]
    assert is_emoji(emoji), title
    rest = text[len(emoji):]
    assert not any(unicodedata.category(ch) == "So" for ch in rest), title
    assert 2 <= len(text.split(" | ")) <= 4, title
    for game in games:  # Spielnamen wie „GTA V“ zählen nicht als Großbuchstaben-Wort
        rest = rest.replace(game.replace(" ", "-"), "").replace(game, "")
    assert len(caps_words(rest)) <= 2, title
    assert text.replace("?!", "!").count("!") <= 1, title
    assert "{" not in text and "}" not in text, title
    assert not any(phrase in text.casefold() for phrase in SINGLE_MOMENT), title
    # Ziel ≤ 70 Zeichen bei normalen Namen (bis „League of Legends“, 17 Zeichen); längere
    # Namen dürfen den Titel entsprechend verlängern, hart gilt is_valid_title (≤ 140).
    assert len(text) <= TITLE_TARGET_CHARS + max(0, max(len(game) for game in games) - 17), title


def test_simulation_profiles_are_all_planned():
    assert len(SIMULATION) == 30
    assert len({profile[0] for profile in SIMULATION}) >= 25


@pytest.mark.parametrize("profile", SIMULATION, ids=lambda p: "+".join(p[0]) + f"-{p[1]}x{p[2]}h")
def test_simulation_regression(profile):
    (games, streams, hours, viewers, chatters, goal, experience, first_time, language, windows,
     week, collab, mood, commands) = profile
    plan = build_plan(request(
        games=games, windows=windows, streams_per_week=streams, hours_per_week=hours,
        average_viewers=viewers, active_chatters=chatters, goal=goal, experience=experience,
        first_time=first_time, language=language, week_number=week, collab_partner=collab,
        mood=mood, commands=list(commands)))
    assert len(plan.streams) == streams
    assert all(60 <= item.stream.minutes <= 240 for item in plan.streams)
    budget = plan.budget
    assert budget.unplanned_minutes >= 0
    assert budget.stream_minutes + budget.preparation_minutes + budget.clip_minutes + \
        budget.review_minutes + budget.unplanned_minutes == hours * 60
    ids = [item.format_id for item in plan.streams]
    # Wochen-Formate nur am Ende des Plans, und nie bei nur einem Stream
    for index, format_id in enumerate(ids):
        if FORMATS_BY_ID[format_id].week_end:
            assert index == len(ids) - 1 and streams > 1, ids
    # „Erste Stunde“ / „Neues Spiel“ nur mit first_time
    if not first_time:
        assert not any(FORMATS_BY_ID[fid].first_time_only for fid in ids), ids
    # Rückblick-Formate nie als erster Stream eines Spiels in Woche 1
    if week == 1:
        firsts = {}
        for item in plan.streams:
            firsts.setdefault(item.game, item.format_id)
        assert not any(FORMATS_BY_ID[fid].needs_history for fid in firsts.values()), firsts
    level = plan.chat_level
    for item in plan.streams:
        assert CHAT_ORDER[item.needs_chat] <= CHAT_ORDER[level]
        assert collab or not item.needs_collab
        assert 1 <= len(item.tags) <= TAGS_MAX_COUNT and all(is_valid_tag(t) for t in item.tags)
        for title in (item.title, *item.title_alternatives):
            if not first_time:
                assert not any(p in title.casefold() for p in FIRST_TIME_PHRASES), title
            _check_plan_title(title, games)
        if language == "en":
            text = " ".join((item.title, *item.title_alternatives, *item.run_of_show, item.hook))
            assert not set(text) & set("äöüßÄÖÜ") - set("".join(games)), text


@pytest.mark.parametrize(("windows", "streams", "hours", "match"), [
    (W_FIVE, 3, 3, "Zu wenig Zeit"),            # 3 × (60 + 15) min > 3 h
    (W_FIVE, 7, 20, "nutzbare"),                # 5 Fenster, 7 Streams
    (["Mo 18-22", "Mo 19-21"], 2, 10, "nutzbare"),
])
def test_simulation_only_real_impossibilities_fail(windows, streams, hours, match):
    with pytest.raises(PlanError, match=match):
        build_plan(request(windows=windows, streams_per_week=streams, hours_per_week=hours))


# ------------------------------------------- Glücksspiel wird nicht unterstützt (26.11.2026)


def test_gambling_game_alone_is_refused():
    with pytest.raises(PlanError, match="Glücksspiel-Kategorien werden von der Streaming Growth "
                                        "Engine nicht unterstützt"):
        build_plan(request(games=("Slots",)))
    with pytest.raises(PlanError, match="not supported"):
        build_plan(request(games=("virtual casino", "Poker"), language="en"))


def test_gambling_game_is_removed_next_to_a_real_game():
    plan = build_plan(request(games=("Slots", "Valorant")))
    assert [game.name for game in plan.games] == ["Valorant"]
    assert {stream.game for stream in plan.streams} == {"Valorant"}
    assert plan.notes[0].startswith("„Slots“ ist eine Glücksspiel-Kategorie.")
    text = json.dumps(plan.model_dump(), ensure_ascii=False)
    assert text.count("Slots") == 1  # nur im Hinweis – kein Titel, Tag oder Format


def test_gambling_refusal_in_cli_and_api(capsys):
    assert cli_main(["plan", "--game", "Slots", "--window", "Fr 20-23", "--hours", "6",
                     "--streams", "1"]) == 2
    assert "nicht unterstützt" in capsys.readouterr().err
    body = {"games": ["Slots"], "windows": [{"day": "Fr", "start": "20", "end": "23"}],
            "hours_per_week": 6,
            "streams_per_week": 1}
    response = client.post("/api/v1/content/strategy", json=body)
    assert response.status_code == 422 and "nicht unterstützt" in response.text
    response = client.post("/api/v1/content/strategy", json=body | {"games": ["Slots", "Valorant"]})
    assert response.status_code == 200
    assert [game["name"] for game in response.json()["games"]] == ["Valorant"]
