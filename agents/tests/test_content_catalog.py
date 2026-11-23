"""Formatkatalog und Spiel-Zuordnung des Content Strategist (offline)."""

import pytest

from streaming_agents.agents.catalog import FORMATS, SOURCES
from streaming_agents.agents.v3_recommender import classify_game


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
