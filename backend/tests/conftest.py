"""Synthetische Testdaten: erfundene Streamer, Domains unter .example (RFC 2606), keine echten Abrufe."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from setup_agent.models import Evidence, ProductCategory, SetupClaim, SourceType

# Fester Zeitpunkt deutlich in der Vergangenheit, damit Tests mit "später" (bis +1 Jahr) nicht in der Zukunft landen
NOW = datetime(2025, 6, 2, 12, 0, tzinfo=timezone.utc)


def days_ago(n: int) -> datetime:
    return NOW - timedelta(days=n)


def ev(source_type: SourceType, age_days: int, url: str = "https://nachtfalke.example/setup") -> Evidence:
    return Evidence(source_url=url, source_type=source_type, observed_at=days_ago(age_days), retrieved_at=days_ago(max(age_days - 1, 0)))


def claim(*evidence: Evidence, product_id: str | None = "shure-sm7b", role: str = "primary", raw_name: str = "Shure SM7B",
          category: ProductCategory = ProductCategory.MIKROFON, streamer_id: str = "twitch-nachtfalke") -> SetupClaim:
    return SetupClaim(streamer_id=streamer_id, category=category, role=role, product_id=product_id, raw_name=raw_name, evidence=list(evidence))


@pytest.fixture
def now() -> datetime:
    return NOW
