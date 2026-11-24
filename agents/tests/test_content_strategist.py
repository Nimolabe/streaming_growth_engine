"""Content Strategist (Variante A): Genres, Formate, Wochenplan, Twitch-Grenzen, Messungen."""
import json
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
    CLIP_MINUTES,
    PREP_MINUTES,
    REVIEW_MINUTES,
    PlanError,
    build_plan,
)
from streaming_agents.content_strategist.report import render_html, render_text
from streaming_agents.content_strategist.titles import (
    ALL_EMOJIS,
    CLIP_TITLES,
    EMOJIS,
    FILLS,
    MOOD_LEADS,
    STREAM_TITLES,
    TITLE_TARGET_CHARS,
    build_titles,
    emojis_for,
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
                   *(STREAM_TITLES[item.id].goal[1], STREAM_TITLES[item.id].question[1])]
        for text in english:
            assert not set(text) & set("äöüßÄÖÜ"), (item.id, text)
            assert not any(word in text.split() for word in ("und", "mit", "der", "die", "das"))


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
    with pytest.raises(PlanError, match="mindestens 6 Stunden"):
        build_plan(request(streams_per_week=3, hours_per_week=5))


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


# ------------------------------------------------------------------ Titel (Nachtrag 2)
SINGLE_MOMENT = (  # Regel 1: Titel beziehen sich auf den ganzen Stream
    "diese runde", "dieser runde", "dieses match", "diesem match", "diese ecke", "dieser ecke",
    "dieser abschnitt", "diesen abschnitt", "diesem abschnitt", "diese szene", "dieser szene",
    "diesen moment", "diesem moment", "dieses spiel verloren",
    "this round", "that round", "this match", "that match", "this corner", "this section",
    "this scene", "this moment", "that game",
)
DISHONEST = (  # Regel 5
    "unmöglich", "impossible", "gleich passiert", "you won't believe", "garantiert",
    "guaranteed", "weltrekord", "world record", "rekord", "record",
)
ABBREVIATIONS = {"PB", "CS", "RP", "FPS", "KO"}
TITLE_GAMES = ["Valorant", "League of Legends", "Stardew Valley", "Tetris Effect"]
GENRE_OF_FORMAT = {item.id: item.genre for item in FORMATS}


def strip_emoji(text: str) -> tuple[str, list[str]]:
    found = [emoji for emoji in sorted(ALL_EMOJIS, key=len, reverse=True) if emoji in text]
    for emoji in found:
        text = text.replace(emoji, "")
    return text, found


def check_title(option, genre, game, *, target=True):
    title = option.text
    low = title.casefold()
    rest, found = strip_emoji(title)
    # Regel 3: genau ein Emoji aus der Liste des Genres, sonst keine Symbole/Emojis
    assert sum(title.count(emoji) for emoji in found) == 1, title
    assert option.emoji in emojis_for(genre, game) and option.emoji in title, title
    assert all(ord(ch) < 0x2190 or ch in "–„“”’…" for ch in rest), title
    # Regel 2: Bausteine – Ziel/Stimmung UND Einladung/Frage
    assert option.lead_kind in ("goal", "mood") and option.tail_kind in ("question", "invite")
    # Regel 1 und 5
    assert not any(word in low for word in SINGLE_MOMENT), title
    assert not any(word in low for word in DISHONEST), title
    for word in rest.replace("–", " ").replace("/", " ").split():
        letters = "".join(ch for ch in word if ch.isalpha())
        if len(letters) >= 2 and letters.isupper():
            assert letters in ABBREVIATIONS, title
    assert title.count("!") <= 1, title
    assert "{" not in title and "}" not in title, title
    # Regel 6
    if target:
        assert len(title) <= TITLE_TARGET_CHARS, (len(title), title)
    assert is_valid_title(fit_title(title))


@pytest.mark.parametrize("language", ["de", "en"])
@pytest.mark.parametrize("mood", [None, "chill", "ambitious", "funny"])
@pytest.mark.parametrize("format_id", sorted(STREAM_TITLES))
def test_stream_titles_follow_the_rules(format_id, mood, language):
    genre = GENRE_OF_FORMAT[format_id]
    for game in TITLE_GAMES:
        for start in (10 * 60, 15 * 60, 19 * 60, 23 * 60):
            for kwargs in ({}, {"rank_goal": "Platin", "rank_counter": 12},
                           {"first_time": True}, {"counter": 9}):
                options = build_titles(format_id, genre, game, language, mood=mood,
                                       start_minute=start, **kwargs)
                assert len(options) == 3
                assert {option.approach for option in options} == {"goal", "mood", "invite"}
                assert len({option.text for option in options}) == 3
                for option in options:
                    check_title(option, genre, game)


def test_titles_with_very_long_names_stay_within_twitch_limit():
    for format_id in STREAM_TITLES:
        for language in ("de", "en"):
            for option in build_titles(format_id, GENRE_OF_FORMAT[format_id], "x" * 80, language,
                                       rank_goal="y" * 20, first_time=True):
                check_title(option, GENRE_OF_FORMAT[format_id], "x" * 80, target=False)


def test_title_data_is_complete():
    assert set(STREAM_TITLES) == set(FORMATS_BY_ID) == set(CLIP_TITLES)
    assert set(FILLS) <= set(STREAM_TITLES)
    assert set(MOOD_LEADS) == {*GENRES, None}
    assert all(len(group) == 2 for group in EMOJIS.values())


def test_rank_goal_only_where_given_and_ranked():
    plain = build_titles("shooter-decision-review", "shooter", "Valorant", "de")
    assert not any("Road to" in option.text for option in plain)
    assert any("Ranked-Abend" in option.text for option in plain)
    goal = build_titles("shooter-decision-review", "shooter", "Valorant", "de",
                        rank_goal="Platin", rank_counter=5)
    assert goal[0].text.startswith("Road to Platin, Tag 5")
    cozy = build_titles("cozy-three-goals", "cozy", "Stardew Valley", "de", rank_goal="Platin")
    assert not any("Platin" in option.text for option in cozy)


def test_first_time_and_daypart():
    first = build_titles("story-first-playthrough", "story", "Elden Ring", "de", first_time=True)
    assert first[0].text.startswith("Zum ersten Mal Elden Ring, blind")
    afternoon = build_titles("horror-honest-reactions", "horror", "Phasmophobia", "de",
                             start_minute=14 * 60, rotation=1)
    assert afternoon[0].text.startswith("Horror-Nachmittag")
    night = build_titles("horror-honest-reactions", "horror", "Phasmophobia", "de",
                         start_minute=23 * 60, rotation=1)
    assert night[0].text.startswith("Horror-Nacht")


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
