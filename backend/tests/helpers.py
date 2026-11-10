"""Aufbau eines kleinen, synthetischen Datenbestands für Service-Tests."""

from __future__ import annotations

from setup_agent import repository as R
from setup_agent.approval import NEW, ApprovalManager
from setup_agent.models import Actor, ActorType, Operation, ProposalStatus

from .conftest import NOW, days_ago

ADMIN = Actor(type=ActorType.ADMIN, id="admin-uid-1")
AGENT = Actor(type=ActorType.AGENT, id="test-agent")


def admin_do(am: ApprovalManager, entity_type: str, payload: dict, *, entity_id: str = NEW, op: Operation = Operation.CREATE,
             base_version: int | None = None, reason: str = "Admin-Eingabe"):
    """Admin legt etwas an oder ändert es: Vorschlag + sofortige Freigabe (wie in der API)."""
    p, _ = am.propose(entity_type=entity_type, entity_id=entity_id, operation=op, payload=payload, reason=reason,
                      actor=ADMIN, origin="admin", base_version=base_version)
    done = am.decide(p.id, ProposalStatus.APPROVED, ADMIN, "ok")
    assert done.apply_error is None, done.apply_error
    return done


STREAMER = {"id": "twitch-nachtfalke", "display_name": "NachtfalkeTV", "categories": ["gaming"], "primary_language": "de",
            "platforms": [{"platform": "twitch", "handle": "nachtfalke", "url": "https://twitch.example/nachtfalke"}]}
SM7B = {"manufacturer": "Shure", "model": "SM7B", "category": "mikrofon", "aliases": ["Shure SM-7B"], "specs": {"anschluss": "XLR"}}
SM7DB = {"manufacturer": "Shure", "model": "SM7dB", "category": "mikrofon"}
MV7 = {"manufacturer": "Shure", "model": "MV7+", "category": "mikrofon"}
PODMIC = {"manufacturer": "Rode", "model": "PodMic USB", "category": "mikrofon"}


def evidence(source_type: str, age_days: int, url: str = "https://nachtfalke.example/setup") -> dict:
    return {"source_url": url, "source_type": source_type, "observed_at": days_ago(age_days).isoformat(),
            "retrieved_at": days_ago(max(age_days - 1, 0)).isoformat()}


def claim_payload(product_id: str | None, raw_name: str, *ev: dict, role: str = "primary", category: str = "mikrofon",
                  streamer_id: str = "twitch-nachtfalke") -> dict:
    return {"streamer_id": streamer_id, "category": category, "role": role, "product_id": product_id,
            "raw_name": raw_name, "evidence": list(ev)}


def offer_payload(product_id: str, retailer: str, url: str, cents: int | None, age_days: int = 1) -> dict:
    return {"product_id": product_id, "retailer": retailer, "url": url, "availability": "in_stock",
            "price": None if cents is None else {"amount_minor": cents, "currency": "EUR"},
            "checked_at": days_ago(age_days).isoformat(), "last_success_at": days_ago(age_days).isoformat()}


def base_world():
    repo = R.InMemoryRepository()
    am = ApprovalManager(repo, clock=lambda: NOW)
    admin_do(am, "streamer", STREAMER)
    for p in (SM7B, SM7DB, MV7, PODMIC):
        admin_do(am, "product", p)
    return repo, am
