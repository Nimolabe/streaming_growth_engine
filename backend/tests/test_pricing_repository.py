from datetime import timedelta

import pytest

from setup_agent.models import (
    Actor,
    ActorType,
    AuditAction,
    AuditEntry,
    Availability,
    ChangeProposal,
    Money,
    Offer,
    Operation,
    Product,
    SetupClaim,
    SourceType,
)
from setup_agent.pricing import PriceState, apply_check_failure, apply_observation, needs_review, price_state
from setup_agent.repository import Duplicate, InMemoryRepository, NotFound, StorageUnavailable, VersionConflict

from .conftest import NOW, claim, days_ago, ev

EUR = lambda cents: Money(amount_minor=cents, currency="EUR")  # noqa: E731
AGENT = Actor(type=ActorType.AGENT, id="price_monitor")


def offer(**kw) -> Offer:
    base = dict(product_id="shure-sm7b", retailer="Händler A", url="https://haendler-a.example/p/1",
                price=EUR(39900), availability=Availability.IN_STOCK, checked_at=days_ago(2), last_success_at=days_ago(2))
    base.update(kw)
    return Offer(**base)


class TestPriceChanges:
    def test_new_price_is_detected(self):
        res = apply_observation(offer(), EUR(34900), Availability.IN_STOCK, NOW, "manual")
        assert res.change and res.change.old_price == EUR(39900) and res.change.new_price == EUR(34900)
        assert res.observation and res.offer.version == 2 and res.offer.failed_checks == 0

    def test_same_price_creates_no_new_history(self):
        res = apply_observation(offer(), EUR(39900), Availability.IN_STOCK, NOW, "manual")
        assert res.change is None and res.observation is None
        assert res.offer.version == 1 and res.offer.checked_at == NOW

    def test_availability_change_counts(self):
        res = apply_observation(offer(), EUR(39900), Availability.OUT_OF_STOCK, NOW, "manual")
        assert res.change and res.change.new_availability == Availability.OUT_OF_STOCK

    def test_price_change_does_not_touch_setup(self):
        repo = InMemoryRepository()
        c = claim(ev(SourceType.OWN_SETUP_PAGE, 10))
        o = offer()
        repo.save("setup_claims", c, expected_version=None)
        repo.save("offers", o, expected_version=None)
        res = apply_observation(o, EUR(29900), Availability.IN_STOCK, NOW, "manual")
        repo.save("offers", res.offer, expected_version=o.version)
        assert repo.get("setup_claims", c.id, SetupClaim) == c
        assert repo.get("offers", o.id, Offer).price == EUR(29900)


class TestUnavailableRetailerData:
    def test_failure_keeps_last_known_price(self):
        o = apply_check_failure(offer(), NOW)
        assert o.price == EUR(39900) and o.last_success_at == days_ago(2)
        assert o.checked_at == NOW and o.failed_checks == 1

    def test_review_after_three_failures(self):
        o = offer()
        for i in range(3):
            assert not needs_review(o)
            o = apply_check_failure(o, NOW - timedelta(hours=3 - i))
        assert needs_review(o)
        assert apply_observation(o, EUR(39900), Availability.IN_STOCK, NOW, "manual").offer.failed_checks == 0

    def test_price_states(self):
        assert price_state(offer(), NOW) == PriceState.CURRENT
        assert price_state(offer(last_success_at=days_ago(15), checked_at=days_ago(1)), NOW) == PriceState.STALE
        assert price_state(offer(price=None, last_success_at=None), NOW) == PriceState.UNKNOWN


class TestRepository:
    def test_duplicate_products_by_spelling(self):
        repo = InMemoryRepository()
        repo.save("products", Product(manufacturer="Shure", model="SM7B", category="mikrofon"), expected_version=None)
        with pytest.raises(Duplicate):
            repo.save("products", Product(manufacturer="SHURE", model="SM-7B", category="mikrofon"), expected_version=None)
        repo.save("products", Product(manufacturer="Shure", model="SM7dB", category="mikrofon"), expected_version=None)
        assert len(repo.list("products", Product)) == 2

    def test_repeated_create_is_rejected(self):
        repo = InMemoryRepository()
        c = claim(ev(SourceType.OWN_SETUP_PAGE, 10))
        repo.save("setup_claims", c, expected_version=None)
        with pytest.raises(Duplicate):
            repo.save("setup_claims", c, expected_version=None)

    def test_version_conflict_does_not_overwrite(self):
        repo = InMemoryRepository()
        o = offer()
        repo.save("offers", o, expected_version=None)
        repo.save("offers", o.model_copy(update={"version": 2, "price": EUR(100)}), expected_version=1)
        with pytest.raises(VersionConflict):
            repo.save("offers", o.model_copy(update={"version": 2, "price": EUR(999)}), expected_version=1)
        assert repo.get("offers", o.id, Offer).price == EUR(100)

    def test_update_of_missing_entity(self):
        with pytest.raises(NotFound):
            InMemoryRepository().save("offers", offer(version=2), expected_version=1)
        with pytest.raises(NotFound):
            InMemoryRepository().get("offers", "o_missing", Offer)

    def test_repeated_runs_create_one_proposal(self):
        repo = InMemoryRepository()
        make = lambda: ChangeProposal(entity_type="offer", entity_id="o_1", operation=Operation.UPDATE,  # noqa: E731
                                      payload={"price": {"amount_minor": 34900, "currency": "EUR"}}, base_version=1,
                                      reason="Preis gesunken", origin="price_monitor", created_by=AGENT)
        first, created1 = repo.add_proposal(make())
        second, created2 = repo.add_proposal(make())
        assert created1 and not created2 and first.id == second.id
        assert len(repo.list("change_proposals", ChangeProposal)) == 1

    def test_storage_failure_changes_nothing(self):
        repo = InMemoryRepository()
        o = offer()
        repo.save("offers", o, expected_version=None)
        repo.available = False
        with pytest.raises(StorageUnavailable):
            repo.save("offers", o.model_copy(update={"version": 2, "price": EUR(1)}), expected_version=1)
        repo.available = True
        assert repo.get("offers", o.id, Offer) == o

    def test_stored_data_cannot_be_mutated_from_outside(self):
        repo = InMemoryRepository()
        o = offer()
        repo.save("offers", o, expected_version=None)
        loaded = repo.get("offers", o.id, Offer)
        loaded.retailer = "Manipuliert"
        assert repo.get("offers", o.id, Offer).retailer == "Händler A"

    def test_audit_log_is_append_only_and_filterable(self):
        repo = InMemoryRepository()
        e1 = AuditEntry(at=NOW, actor=AGENT, action=AuditAction.CHECK_FAILED, entity_type="offer", entity_id="o_1", reason="Timeout")
        e2 = AuditEntry(at=NOW, actor=AGENT, action=AuditAction.UPDATE, entity_type="offer", entity_id="o_2",
                        from_version=1, to_version=2, changes={"price": {"from": 39900, "to": 34900}}, reason="Preis gesunken")
        repo.append_audit(e1)
        repo.append_audit(e2)
        assert repo.audit_log(entity_id="o_2") == [e2]
        with pytest.raises(Exception):
            e1.reason = "nachträglich geändert"  # Einträge sind unveränderbar

    def test_audit_needs_reason(self):
        with pytest.raises(Exception):
            AuditEntry(actor=AGENT, action=AuditAction.UPDATE, entity_type="offer", entity_id="o_1", reason="")


class TestRoundTrip:
    def test_stored_json_round_trips_and_keeps_query_fields(self):
        repo = InMemoryRepository()
        c = claim(ev(SourceType.OWN_SETUP_PAGE, 10), ev(SourceType.THIRD_PARTY, 4, "https://news.example/a"))
        p = Product(manufacturer="Shure", model="SM7B", category="mikrofon", gtin="4006381333931", specs={"anschluss": "XLR"})
        repo.save("setup_claims", c, expected_version=None)
        repo.save("products", p, expected_version=None)
        raw = repo._data["setup_claims"][c.id]
        assert raw["slot"] == "mikrofon:primary" and raw["evidence"][0]["source_id"].startswith("s_")
        assert repo._data["products"][p.id]["match_key"] == "shure:sm7b"
        assert repo.get("setup_claims", c.id, SetupClaim) == c
        assert repo.get("products", p.id, Product) == p

    def test_tampered_derived_fields_are_recomputed(self):
        repo = InMemoryRepository()
        p = Product(manufacturer="Shure", model="SM7B", category="mikrofon")
        repo.save("products", p, expected_version=None)
        repo._data["products"][p.id]["match_key"] = "falsch:falsch"
        assert repo.get("products", p.id, Product).match_key == "shure:sm7b"
