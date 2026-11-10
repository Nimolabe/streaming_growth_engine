"""Beispieldaten für lokale Entwicklung und Vorführung.

ACHTUNG: Alle Streamer und Quellen sind ERFUNDEN (Domains unter .example, RFC 2606).
Diese Daten dürfen nie in die Produktions-Datenbank geschrieben werden; die Kommandozeile
erlaubt 'demo' deshalb nur mit dem In-Memory-Speicher.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from . import repository as R
from .approval import NEW, ApprovalManager
from .models import Actor, ActorType, Operation, ProposalStatus

DEMO_ADMIN = Actor(type=ActorType.ADMIN, id="demo-admin")


def _do(am: ApprovalManager, entity_type: str, payload: dict, reason: str = "Beispieldaten") -> None:
    p, _ = am.propose(entity_type=entity_type, entity_id=NEW, operation=Operation.CREATE, payload=payload,
                      reason=reason, actor=DEMO_ADMIN, origin="demo")
    done = am.decide(p.id, ProposalStatus.APPROVED, DEMO_ADMIN, "Beispiel")
    if done.apply_error:
        raise RuntimeError(done.apply_error)


def seed(repo: R.Repository, now: datetime) -> None:
    am = ApprovalManager(repo, clock=lambda: now)
    d = lambda n: (now - timedelta(days=n)).isoformat()  # noqa: E731

    def ev(url: str, kind: str, age: int) -> dict:
        return {"source_url": url, "source_type": kind, "observed_at": d(age), "retrieved_at": d(max(age - 1, 0))}

    for s in [
        {"id": "twitch-nachtfalke", "display_name": "NachtfalkeTV (Beispiel)", "categories": ["gaming"], "primary_language": "de",
         "platforms": [{"platform": "twitch", "handle": "nachtfalke", "url": "https://twitch.example/nachtfalke"}]},
        {"id": "tiktok-lenalounge", "display_name": "LenaLiveLounge (Beispiel)", "categories": ["chatting"], "primary_language": "de",
         "platforms": [{"platform": "tiktok", "handle": "lenalounge", "url": "https://tiktok.example/@lenalounge"}]},
    ]:
        _do(am, "streamer", s)

    for p in [
        {"manufacturer": "Shure", "model": "SM7B", "category": "mikrofon", "aliases": ["Shure SM-7B"], "specs": {"anschluss": "XLR"}},
        {"manufacturer": "Shure", "model": "MV7+", "category": "mikrofon", "specs": {"anschluss": "USB-C/XLR"}},
        {"manufacturer": "Focusrite", "model": "Scarlett Solo", "category": "audio_interface"},
        {"manufacturer": "Elgato", "model": "Key Light", "category": "licht"},
        {"manufacturer": "Elgato", "model": "Key Light Mini", "category": "licht"},
        {"manufacturer": "Logitech", "model": "MX Brio", "category": "kamera"},
        {"manufacturer": "Sony", "model": "ZV-E10", "category": "kamera"},
        {"manufacturer": "OBS Project", "model": "OBS Studio", "category": "software_streaming", "aliases": ["OBS"]},
    ]:
        _do(am, "product", p)

    for r in [
        {"domain": "nachtfalke.example", "source_types": ["own_setup_page", "official_statement"]},
        {"domain": "social.example", "source_types": ["official_statement"]},
        {"domain": "news.example", "source_types": ["third_party"]},
    ]:
        _do(am, "source_registry", r)

    claims = [
        ("twitch-nachtfalke", "mikrofon", "shure-mv7", "Shure MV7+", [ev("https://nachtfalke.example/setup", "own_setup_page", 20)]),
        ("twitch-nachtfalke", "kamera", "logitech-mx-brio", "Logitech MX Brio", [ev("https://nachtfalke.example/setup", "own_setup_page", 20)]),
        ("twitch-nachtfalke", "licht", "elgato-key-light", "Elgato Key Light",
         [ev("https://news.example/artikel/streamer-setups", "third_party", 40)]),
        ("tiktok-lenalounge", "mikrofon", "shure-sm7b", "Shure SM7B", [ev("https://social.example/lenalounge/post/1", "official_statement", 60)]),
        ("tiktok-lenalounge", "audio_interface", "focusrite-scarlett-solo", "Focusrite Scarlett Solo",
         [ev("https://social.example/lenalounge/post/1", "official_statement", 60)]),
        ("tiktok-lenalounge", "kamera", None, "irgendeine Sony-Kamera", [ev("https://news.example/artikel/lena", "third_party", 15)]),
    ]
    for sid, cat, pid, raw, evidence in claims:
        _do(am, "setup_claim", {"streamer_id": sid, "category": cat, "product_id": pid, "raw_name": raw, "evidence": evidence})

    for pid, retailer, url, cents, age in [
        ("shure-sm7b", "Händler A (Beispiel)", "https://haendler-a.example/shure-sm7b", 39900, 1),
        ("shure-mv7", "Händler A (Beispiel)", "https://haendler-a.example/shure-mv7", 27900, 1),
        ("shure-mv7", "Händler B (Beispiel)", "https://haendler-b.example/mv7", 25900, 20),
        ("elgato-key-light", "Händler B (Beispiel)", "https://haendler-b.example/key-light", 16900, 2),
        ("elgato-key-light-mini", "Händler B (Beispiel)", "https://haendler-b.example/key-light-mini", 9900, 2),
        ("logitech-mx-brio", "Händler A (Beispiel)", "https://haendler-a.example/mx-brio", 19900, 3),
        ("focusrite-scarlett-solo", "Händler A (Beispiel)", "https://haendler-a.example/scarlett-solo", 11900, 3),
        ("obs-project-obs-studio", "Hersteller", "https://obs.example/download", 0, 1),
    ]:
        _do(am, "offer", {"product_id": pid, "retailer": retailer, "url": url, "availability": "in_stock",
                          "price": {"amount_minor": cents, "currency": "EUR"}, "checked_at": d(age), "last_success_at": d(age)})
