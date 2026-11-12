"""V3 quality, edge-case and backward compatibility tests — all offline."""

import socket

import pytest
from fastapi.testclient import TestClient

from streaming_agents.agents.v3_contracts import CreatorProfileV3
from streaming_agents.agents.v3_recommender import CHAT_DEPENDENT, generate_strategy_v3
from streaming_agents.api import app

client = TestClient(app)


def profile(**changes):
    values = {
        "platform": "twitch",
        "game": "Valorant",
        "audience": "German gaming viewers",
        "language": "de",
        "experience": "intermediate",
        "style": "educational",
        "goal": "discovery",
        "average_viewers": 0,
        "active_chatters": 0,
        "hours_per_week": 10,
        "streams_per_week": 2,
        "ideas_requested": 4,
    }
    values.update(changes)
    return CreatorProfileV3(**values)


def test_platform_name_is_case_insensitive():
    item = profile(platform="Twitch")
    assert item.platform == "twitch"


def test_solo_streamer_gets_no_chat_dependent_formats():
    result = generate_strategy_v3(profile())
    assert result.creator_stage == "early"
    assert result.chat_capacity == "low"
    assert len(result.recommendations) == 4
    assert all(not idea.requires_live_chat for idea in result.recommendations)
    assert all(idea.format_id not in CHAT_DEPENDENT for idea in result.recommendations)
    assert all(not idea.requires_live_chat for idea in result.recommendations)
    assert all(not any("Zuschauer abstimmen lassen" in step for step in idea.stream_steps)
               for idea in result.recommendations)


def test_game_specific_valorant_suggestion():
    output = generate_strategy_v3(profile(ideas_requested=5))
    assert output.game_group == "tactical"
    assert any("Retake" in item.title or "Crosshair" in item.title
               for item in output.recommendations)
    assert any("Valorant" in item.title for item in output.recommendations)


@pytest.mark.parametrize(
    ("game", "group"),
    [
        ("Minecraft", "sandbox"),
        ("Fortnite", "battle_royale"),
        ("Valorant", "tactical"),
        ("Unknown Game", "general"),
    ],
)
def test_game_classification(game, group):
    result = generate_strategy_v3(profile(game=game))
    assert result.game_group == group
    assert result.recommendations


def test_known_games_produce_distinct_recommendations():
    valorant = generate_strategy_v3(profile(game="Valorant"))
    minecraft = generate_strategy_v3(profile(game="Minecraft"))
    fortnite = generate_strategy_v3(profile(game="Fortnite"))
    assert {x.format_id for x in valorant.recommendations} != {
        x.format_id for x in minecraft.recommendations
    }
    assert {x.format_id for x in minecraft.recommendations} != {
        x.format_id for x in fortnite.recommendations
    }


def test_chat_interaction_only_suggested_when_viable():
    result = generate_strategy_v3(
        profile(active_chatters=9, average_viewers=25, style="interactive", goal="community")
    )
    assert result.chat_capacity == "moderate"
    assert any(x.requires_live_chat for x in result.recommendations)


def test_many_reported_chatters_do_not_override_zero_viewers():
    result = generate_strategy_v3(profile(active_chatters=9, average_viewers=0))
    assert result.chat_capacity == "low"
    assert all(not idea.requires_live_chat for idea in result.recommendations)


def test_audience_affects_suitability_scores():
    from streaming_agents.agents.v2_catalog import FORMATS
    from streaming_agents.agents.v3_recommender import _score

    tutorial = next(item for item in FORMATS if item.id == "micro-skill")
    general = _score(tutorial, profile(audience="Gaming viewers"), "tactical")[0]
    beginners = _score(tutorial, profile(audience="Deutschsprachige Anfänger"), "tactical")[0]
    assert beginners > general


def test_platform_affects_relevant_format_score():
    from streaming_agents.agents.v2_catalog import FORMATS
    from streaming_agents.agents.v3_recommender import _score

    tutorial = next(item for item in FORMATS if item.id == "micro-skill")
    twitch_score = _score(tutorial, profile(platform="Twitch"), "tactical")[0]
    youtube_score = _score(tutorial, profile(platform="YouTube"), "tactical")[0]
    assert youtube_score > twitch_score


def test_experience_changes_format_priorities():
    from streaming_agents.agents.v2_catalog import FORMATS
    from streaming_agents.agents.v3_recommender import _score

    analysis = next(item for item in FORMATS if item.id == "decision-review")
    beginner = _score(analysis, profile(experience="beginner"), "tactical")[0]
    advanced = _score(analysis, profile(experience="advanced"), "tactical")[0]
    assert advanced > beginner


def test_creator_stages_are_distinct():
    for viewers, stage in [(0, "early"), (4, "early"), (5, "growing"),
                           (49, "growing"), (50, "established")]:
        output = generate_strategy_v3(profile(average_viewers=viewers))
        assert output.creator_stage == stage


def test_workload_exactly_matches_weekly_budget():
    for hours, stream_count in [(2, 1), (8, 2), (12, 3), (40, 7)]:
        output = generate_strategy_v3(profile(
            hours_per_week=hours,
            streams_per_week=stream_count,
        ))
        w = output.workload
        assert w.total_minutes == hours * 60
        assert (w.livestream_minutes + w.preparation_minutes
                + w.editing_minutes + w.review_minutes) == w.total_minutes
        assert w.livestream_minutes // stream_count >= 30


def test_impossible_stream_schedule_rejected():
    response = client.post(
        "/api/v1/content/strategy",
        json=profile(hours_per_week=2, streams_per_week=7).model_dump(),
    )
    assert response.status_code == 422


def test_zero_chat_video_has_no_vote_or_poll_steps():
    output = generate_strategy_v3(profile(
        game="Valorant", average_viewers=2, active_chatters=0, ideas_requested=5
    ))
    decision = next(x for x in output.recommendations if x.format_id == "decision-review")
    full_plan = " ".join(decision.stream_steps + [decision.short_video_structure]).casefold()
    assert "abstimmung" not in full_plan
    assert "zuschauer abstimmen" not in full_plan
    assert decision.adapted_for_solo is True


def test_zero_chat_metrics_are_format_specific():
    output = generate_strategy_v3(profile(
        game="Valorant", average_viewers=2, active_chatters=0, ideas_requested=5
    ))
    metrics = [item.measurement for item in output.recommendations]
    assert len(set(metrics)) >= 4
    assert all(metric.strip() for metric in metrics)
    assert not any("setze keine Chat-Antworten voraus" in metric for metric in metrics)


def test_three_episode_plan_is_complete():
    output = generate_strategy_v3(profile())
    assert [episode.episode for episode in output.series_plan] == [1, 2, 3]
    assert len({episode.focus for episode in output.series_plan}) == 3
    assert all(episode.title for episode in output.series_plan)
    assert len({episode.expected_output for episode in output.series_plan}) == 3
    assert len({episode.check_after for episode in output.series_plan}) == 3


def test_scores_are_explanatory_not_saturated():
    output = generate_strategy_v3(profile())
    scores = [idea.fit_score for idea in output.recommendations]
    assert max(scores) < 100
    assert len(set(scores)) >= 2


def test_recommendation_has_executable_information():
    output = generate_strategy_v3(profile())
    for idea in output.recommendations:
        assert idea.estimated_hours_per_week <= 10
        assert len(idea.stream_steps) == 3
        assert all(step.strip() for step in idea.stream_steps)
        assert idea.short_video_hook and idea.short_video_structure
        assert idea.measurement and idea.minimum_viable_test
        assert idea.evidence_links
        assert 0 <= idea.fit_score <= 100
        assert "keine Wachstumswahrscheinlichkeit" in idea.score_method


def test_english_recommendations_are_localized():
    output = generate_strategy_v3(profile(language="en"))
    assert output.version == "v3.0-offline"
    assert all("not a likelihood" in item.score_method for item in output.recommendations)
    assert len(output.evaluation_guide) == 3


def test_exclusions_produce_new_choices():
    initial = generate_strategy_v3(profile(ideas_requested=2))
    ids = [x.format_id for x in initial.recommendations]
    later = generate_strategy_v3(profile(exclude_format_ids=ids, ideas_requested=2))
    assert not set(ids).intersection(x.format_id for x in later.recommendations)


def test_no_viable_formats_returns_422():
    from streaming_agents.agents.v2_catalog import FORMATS

    all_ids = [item.id for item in FORMATS]
    response = client.post(
        "/api/v1/content/strategy",
        json=profile(exclude_format_ids=all_ids).model_dump(),
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "override",
    [
        {"hours_per_week": 1},
        {"streams_per_week": 0},
        {"active_chatters": -1},
        {"average_viewers": -1},
        {"ideas_requested": 6},
        {"language": "xx"},
        {"style": "always_viral"},
        {"game": "   "},
        {"platform": "unrecognized"},
    ],
)
def test_bad_profiles_return_422(override):
    data = profile().model_dump()
    data.update(override)
    assert client.post("/api/v1/content/strategy", json=data).status_code == 422


def test_output_is_deterministic_and_offline(monkeypatch):
    def forbid_network(*args, **kwargs):
        raise AssertionError("Unexpected network request")

    monkeypatch.setattr(socket, "socket", forbid_network)
    a = generate_strategy_v3(profile())
    b = generate_strategy_v3(profile())
    assert a.model_dump() == b.model_dump()
    assert a.model_used is False


def test_api_endpoint_returns_v3_strategy():
    response = client.post("/api/v1/content/strategy", json=profile().model_dump())
    assert response.status_code == 200
    assert response.json()["version"] == "v3.0-offline"
