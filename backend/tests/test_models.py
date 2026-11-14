from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from setup_agent.models import (
    AccessMethod,
    Actor,
    ActorType,
    ChangeProposal,
    Evidence,
    InvalidTransition,
    Money,
    Offer,
    Operation,
    Platform,
    Product,
    ProductCategory,
    ProposalStatus,
    SetupClaim,
    SourceRegistryEntry,
    SourceType,
    Streamer,
)

from .conftest import NOW, claim, days_ago, ev

ADMIN = Actor(type=ActorType.ADMIN, id="admin-1")
AGENT = Actor(type=ActorType.AGENT, id="change_detector")


class TestMissingSources:
    def test_claim_without_evidence_is_rejected(self):
        with pytest.raises(ValidationError, match="evidence"):
            SetupClaim(streamer_id="twitch-nachtfalke", category="mikrofon", raw_name="Shure SM7B", product_id="shure-sm7b", evidence=[])

    def test_same_source_twice_is_rejected(self):
        a = ev(SourceType.OWN_SETUP_PAGE, 10, "https://nachtfalke.example/setup")
        b = ev(SourceType.OWN_SETUP_PAGE, 20, "http://www.nachtfalke.example/setup/?utm_source=x")
        with pytest.raises(ValidationError, match="mehrfach"):
            claim(a, b)


class TestInvalidInput:
    def test_future_observation_is_rejected(self):
        future = datetime.now(timezone.utc) + timedelta(days=2)
        with pytest.raises(ValidationError, match="Zukunft"):
            Evidence(source_url="https://a.example/x", source_type="own_setup_page", observed_at=future, retrieved_at=future)

    def test_naive_datetime_is_rejected(self):
        with pytest.raises(ValidationError, match="Zeitzone"):
            Evidence(source_url="https://a.example/x", source_type="own_setup_page", observed_at=datetime(2026, 1, 1), retrieved_at=datetime(2026, 1, 2))

    def test_retrieved_before_observed_is_rejected(self):
        with pytest.raises(ValidationError, match="retrieved_at"):
            Evidence(source_url="https://a.example/x", source_type="own_setup_page", observed_at=days_ago(1), retrieved_at=days_ago(5))

    def test_non_http_source_is_rejected(self):
        with pytest.raises(ValidationError):
            Evidence(source_url="ftp://a.example/x", source_type="own_setup_page", observed_at=days_ago(5), retrieved_at=days_ago(1))

    def test_unknown_source_type_is_rejected(self):
        with pytest.raises(ValidationError):
            Evidence(source_url="https://a.example/x", source_type="hoerensagen", observed_at=days_ago(5), retrieved_at=days_ago(1))

    def test_note_length_is_limited(self):
        with pytest.raises(ValidationError):
            Evidence(source_url="https://a.example/x", source_type="own_setup_page", observed_at=days_ago(5), retrieved_at=days_ago(1), note="x" * 281)

    def test_unknown_fields_are_rejected(self):
        with pytest.raises(ValidationError):
            Product(manufacturer="Shure", model="SM7B", category="mikrofon", preis=399)

    @pytest.mark.parametrize("bad", [{"amount_minor": -1, "currency": "EUR"}, {"amount_minor": 100, "currency": "eur"}, {"amount_minor": 1.5, "currency": "EUR"}])
    def test_invalid_money(self, bad):
        with pytest.raises(ValidationError):
            Money(**bad)

    def test_offer_must_use_https(self):
        with pytest.raises(ValidationError, match="https"):
            Offer(product_id="shure-sm7b", retailer="Händler A", url="http://haendler-a.example/p/1")

    def test_invalid_gtin(self):
        with pytest.raises(ValidationError, match="GTIN"):
            Product(manufacturer="Shure", model="SM7B", category="mikrofon", gtin="4006381333932")

    def test_streamer_needs_platform_and_category(self):
        with pytest.raises(ValidationError):
            Streamer(id="twitch-nachtfalke", display_name="NachtfalkeTV", platforms=[], categories=["gaming"])
        with pytest.raises(ValidationError):
            Streamer(id="twitch-nachtfalke", display_name="NachtfalkeTV",
                     platforms=[{"platform": "twitch", "handle": "nachtfalke", "url": "https://twitch.example/nachtfalke"}], categories=[])

    def test_invalid_role(self):
        with pytest.raises(ValidationError):
            claim(ev(SourceType.OWN_SETUP_PAGE, 10), role="Haupt Mikro!")


class TestUnknownIsExplicit:
    def test_defaults_mean_unknown(self):
        offer = Offer(product_id="shure-sm7b", retailer="Händler A", url="https://haendler-a.example/p/1")
        assert offer.price is None and offer.availability == "unknown" and offer.last_success_at is None
        p = Product(manufacturer="Shure", model="SM7B", category="mikrofon")
        assert p.discontinued is None and p.gtin is None
        c = claim(ev(SourceType.OWN_SETUP_PAGE, 10))
        assert c.status == "unknown" and c.published is False


class TestIds:
    def test_streamer_id(self):
        assert Streamer.make_id(Platform.TWITCH, "Nacht_Falke") == "twitch-nacht-falke"

    def test_product_and_claim_ids(self):
        p = Product(manufacturer="Shure", model="SM7B", category="mikrofon")
        assert p.id == "shure-sm7b" and p.match_key == "shure:sm7b"
        c1, c2 = claim(ev(SourceType.OWN_SETUP_PAGE, 10)), claim(ev(SourceType.THIRD_PARTY, 3, "https://news.example/a"))
        assert c1.id == c2.id, "Gleicher Streamer, Slot und Produkt = gleiche Angabe"
        assert claim(ev(SourceType.OWN_SETUP_PAGE, 10), role="secondary").id != c1.id

    def test_offer_id_ignores_tracking(self):
        a = Offer(product_id="shure-sm7b", retailer="Händler A", url="https://haendler-a.example/p/1?utm_source=x")
        b = Offer(product_id="shure-sm7b", retailer="händler a", url="https://www.haendler-a.example/p/1")
        assert a.id == b.id


class TestSourceRegistry:
    def test_auto_fetch_is_off_by_default(self):
        r = SourceRegistryEntry(domain="nachtfalke.example", source_types=["own_setup_page"])
        assert r.auto_fetch_allowed is False and r.access_method == AccessMethod.MANUAL

    def test_auto_fetch_requires_reviewed_terms(self):
        with pytest.raises(ValidationError, match="Nutzungsbedingungen"):
            SourceRegistryEntry(domain="nachtfalke.example", source_types=["own_setup_page"], access_method="rss", auto_fetch_allowed=True)
        with pytest.raises(ValidationError):
            SourceRegistryEntry(domain="nachtfalke.example", source_types=["own_setup_page"], auto_fetch_allowed=True, terms_reviewed_at=days_ago(3))
        ok = SourceRegistryEntry(domain="nachtfalke.example", source_types=["own_setup_page"], access_method="rss",
                                 auto_fetch_allowed=True, terms_reviewed_at=days_ago(3))
        assert ok.id == "r_nachtfalke-example"


def _proposal(**kw) -> ChangeProposal:
    base = dict(entity_type="setup_claim", entity_id="c_1", operation=Operation.UPDATE, payload={"status": "outdated"},
                base_version=2, reason="Neuerer Primärbeleg", origin="change_detector", created_by=AGENT)
    base.update(kw)
    return ChangeProposal(**base)


class TestApprovalTransitions:
    def test_admin_can_approve(self):
        p = _proposal().decide(ProposalStatus.APPROVED, ADMIN, NOW)
        assert p.status == "approved" and p.decided_by == ADMIN

    def test_agent_cannot_approve_or_reject(self):
        with pytest.raises(InvalidTransition, match="Admin"):
            _proposal().decide(ProposalStatus.APPROVED, AGENT, NOW)
        with pytest.raises(InvalidTransition, match="Admin"):
            _proposal().decide(ProposalStatus.REJECTED, AGENT, NOW, note="falsch")

    def test_agent_may_mark_superseded(self):
        assert _proposal().decide(ProposalStatus.SUPERSEDED, AGENT, NOW).status == "superseded"

    def test_reject_needs_reason(self):
        with pytest.raises(InvalidTransition, match="Begründung"):
            _proposal().decide(ProposalStatus.REJECTED, ADMIN, NOW, note="  ")

    def test_decisions_are_final(self):
        p = _proposal().decide(ProposalStatus.REJECTED, ADMIN, NOW, note="Quelle ist ein Fake-Account")
        for status in (ProposalStatus.APPROVED, ProposalStatus.PENDING, ProposalStatus.SUPERSEDED):
            with pytest.raises(InvalidTransition):
                p.decide(status, ADMIN, NOW)

    def test_same_change_same_id(self):
        assert _proposal().id == _proposal(reason="anderer Text", created_at=days_ago(1)).id
        assert _proposal().id != _proposal(payload={"status": "conflicting"}).id
