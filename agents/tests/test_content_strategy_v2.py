"""Offline regression tests for content strategy V2: zero network / model calls."""

import pytest

from streaming_agents.agents.v2_catalog import FORMATS, SOURCES
from streaming_agents.agents.v2_contracts import CreatorProfileV2
from streaming_agents.agents.v2_recommender import classify_game, generate_strategy


def profile(**changes):
    base = {
        "platform": "Twitch",
        "category": "Valorant",
        "audience": "Deutschsprachige Einsteiger",
        "language": "de",
        "weekly_hours": 8,
        "content_style": "educational",
        "primary_goal": "discovery",
        "channel_size": "small",
        "experience": "intermediate",
    }
    base.update(changes)
    return CreatorProfileV2(**base)


def test_curated_catalog_has_unique_real_entries():
    assert len(FORMATS) >= 20
    assert len({item.id for item in FORMATS}) == len(FORMATS)
    assert all(item.min_hours >= 2 for item in FORMATS)
    assert all(len(item.steps_de) == len(item.steps_en) == 3 for item in FORMATS)
    assert all(all(key in SOURCES for key in item.source_ids) for item in FORMATS)
    assert all(item.hook_de and item.clip_de and item.metric_de for item in FORMATS)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Valorant", "tactical"),
        ("Counter-Strike 2", "tactical"),
        ("Minecraft", "sandbox"),
        ("Fortnite", "battle_royale"),
        ("Something unknown", "general"),
    ],
)
def test_genre_classification(name, expected):
    assert classify_game(name) == expected


def test_valorant_recommendations_are_detailed_and_not_generic():
    output = generate_strategy(profile())
    assert output.generator == "curated_rules_v2"
    assert len(output.recommendations) == 3
    assert output.game_group == "tactical"
    assert output.total_formats_considered >= 3
    assert all("Valorant" in rec.title for rec in output.recommendations)
    assert all(len(rec.stream_run_of_show) == 3 for rec in output.recommendations)
    assert all(rec.evidence_links for rec in output.recommendations)
    assert all("KEINE Erfolgswahrscheinlichkeit" in rec.score_interpretation
               for rec in output.recommendations)


def test_distinct_game_genres_produce_distinct_ideas():
    tactical = generate_strategy(profile(category="Valorant"))
    sandbox = generate_strategy(profile(category="Minecraft"))
    ids_a = {rec.format_id for rec in tactical.recommendations}
    ids_b = {rec.format_id for rec in sandbox.recommendations}
    assert ids_a != ids_b


def test_style_and_goal_change_ranking():
    educational = generate_strategy(profile(content_style="educational", primary_goal="discovery"))
    community = generate_strategy(profile(content_style="interactive", primary_goal="community"))
    assert educational.recommendations[0].format_id != community.recommendations[0].format_id


def test_recommendations_respect_budget_and_exclusions():
    initial = generate_strategy(profile(weekly_hours=2))
    assert all(x.estimated_min_hours_per_week <= 2 for x in initial.recommendations)
    ids = [x.format_id for x in initial.recommendations]
    changed = generate_strategy(profile(exclude_format_ids=ids))
    assert not set(ids).intersection(x.format_id for x in changed.recommendations)


def test_returns_422_if_every_applicable_format_excluded():
    ids = [f.id for f in FORMATS if f.genre in {"tactical", "general"}]
    body = profile(exclude_format_ids=ids).model_dump()
    with pytest.raises(ValueError):
        generate_strategy(CreatorProfileV2(**body))


def test_bad_profiles_are_rejected():
    for patch in (
        {"weekly_hours": 0},
        {"count": 6},
        {"content_style": "guaranteed_viral"},
        {"category": "  "},
        {"language": "fr"},
    ):
        with pytest.raises(ValueError):
            CreatorProfileV2(**(profile().model_dump() | patch))


def test_english_localization():
    payload = generate_strategy(
        profile(language="en", category="Minecraft", primary_goal="community")
    ).model_dump(mode="json")
    assert payload["game_group"] == "sandbox"
    assert payload["recommendations"][0]["score_interpretation"].startswith("Editorial")
    assert payload["recommendations"][0]["short_video_hook"]


def test_deterministic_and_no_external_calls(monkeypatch):
    import socket

    def no_network(*args, **kwargs):
        raise AssertionError("Unexpected network access")

    monkeypatch.setattr(socket, "socket", no_network)
    output1 = generate_strategy(profile())
    output2 = generate_strategy(profile())
    assert output1.model_dump() == output2.model_dump()
