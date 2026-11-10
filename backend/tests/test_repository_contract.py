"""Dieselben Anforderungen an beide Speicher-Umsetzungen (In-Memory und Firestore-Adapter)."""

import pytest

from setup_agent import repository as R
from setup_agent.approval import ApprovalManager
from setup_agent.firestore_repo import FirestoreRepository
from setup_agent.models import (
    AuditAction,
    AuditEntry,
    Availability,
    ChangeProposal,
    Money,
    Offer,
    Operation,
    PriceObservation,
    Product,
    ProposalStatus,
    SetupClaim,
    SourceType,
)

from .conftest import NOW, claim, days_ago, ev
from .fake_firestore import FakeClient
from .helpers import ADMIN, AGENT, admin_do, claim_payload, evidence


@pytest.fixture(params=["memory", "firestore"])
def repo(request):
    if request.param == "memory":
        r = R.InMemoryRepository()
        r.go_down = lambda: setattr(r, "available", False)
        r.go_up = lambda: setattr(r, "available", True)
    else:
        client = FakeClient()
        r = FirestoreRepository(client)
        r.go_down = lambda: setattr(client, "down", True)
        r.go_up = lambda: setattr(client, "down", False)
    return r


def offer():
    return Offer(product_id="shure-sm7b", retailer="Händler A", url="https://haendler-a.example/p/1",
                 price=Money(amount_minor=39900, currency="EUR"), availability=Availability.IN_STOCK,
                 checked_at=days_ago(1), last_success_at=days_ago(1))


def test_round_trip(repo):
    c = claim(ev(SourceType.OWN_SETUP_PAGE, 10), ev(SourceType.THIRD_PARTY, 4, "https://news.example/a"))
    repo.save(R.CLAIMS, c, expected_version=None)
    assert repo.get(R.CLAIMS, c.id, SetupClaim) == c
    assert repo.find(R.CLAIMS, "c_fehlt", SetupClaim) is None
    with pytest.raises(R.NotFound):
        repo.get(R.CLAIMS, "c_fehlt", SetupClaim)


def test_duplicates_and_versions(repo):
    repo.save(R.PRODUCTS, Product(manufacturer="Shure", model="SM7B", category="mikrofon"), expected_version=None)
    with pytest.raises(R.Duplicate):
        repo.save(R.PRODUCTS, Product(manufacturer="SHURE", model="SM-7B", category="mikrofon"), expected_version=None)
    o = offer()
    repo.save(R.OFFERS, o, expected_version=None)
    with pytest.raises(R.Duplicate):
        repo.save(R.OFFERS, o, expected_version=None)
    repo.save(R.OFFERS, o.model_copy(update={"version": 2, "retailer": "Händler A"}), expected_version=1)
    with pytest.raises(R.VersionConflict):
        repo.save(R.OFFERS, o.model_copy(update={"version": 2}), expected_version=1)
    with pytest.raises(R.NotFound):
        repo.save(R.OFFERS, offer().model_copy(update={"product_id": "x", "version": 2}), expected_version=1)


def test_proposals(repo):
    p = ChangeProposal(entity_type="offer", entity_id="o_1", operation=Operation.UPDATE, payload={"x": [1, 2]},
                       base_version=1, reason="Test", origin="t", created_by=AGENT, created_at=NOW)
    assert repo.add_proposal(p)[1] and not repo.add_proposal(p)[1]
    decided = p.decide(ProposalStatus.APPROVED, ADMIN, NOW)
    repo.update_proposal(decided, expected_status=ProposalStatus.PENDING, expected_applied=False)
    with pytest.raises(R.VersionConflict):
        repo.update_proposal(decided, expected_status=ProposalStatus.PENDING, expected_applied=False)
    assert [x.id for x in repo.list_proposals(ProposalStatus.APPROVED)] == [p.id]
    assert repo.list_proposals(ProposalStatus.PENDING) == []


def test_audit_with_list_values_is_storable(repo):
    entry = AuditEntry(at=NOW, actor=ADMIN, action=AuditAction.UPDATE, entity_type="setup_claim", entity_id="c_1",
                       changes={"evidence": {"from": [{"a": 1}], "to": [{"a": 1}, {"b": 2}]}, "aliases": {"from": [], "to": ["x"]}},
                       reason="Neue Quelle")
    repo.append_audit(entry)
    assert repo.audit_log("setup_claim", "c_1") == [entry]
    assert repo.audit_log("offer") == []


def test_observations_and_meta(repo):
    obs = PriceObservation(offer_id="o_1", price=Money(amount_minor=100, currency="EUR"), availability="in_stock", observed_at=NOW)
    repo.add_observation(obs)
    assert repo.observations("o_1") == [obs] and repo.observations("o_2") == []
    assert repo.get_meta("agent") == {}
    repo.set_meta("agent", {"last_run": {"weekly": "2026-11-10T12:00:00Z"}})
    assert repo.get_meta("agent")["last_run"]["weekly"].startswith("2026")


def test_outage_raises_storage_unavailable_and_changes_nothing(repo):
    o = offer()
    repo.save(R.OFFERS, o, expected_version=None)
    repo.go_down()
    with pytest.raises(R.StorageUnavailable):
        repo.save(R.OFFERS, o.model_copy(update={"version": 2}), expected_version=1)
    with pytest.raises(R.StorageUnavailable):
        repo.list(R.OFFERS, Offer)
    repo.go_up()
    assert repo.get(R.OFFERS, o.id, Offer) == o


def test_full_workflow_on_both_backends(repo):
    am = ApprovalManager(repo, clock=lambda: NOW)
    from .helpers import SM7B, STREAMER
    admin_do(am, "streamer", STREAMER)
    admin_do(am, "product", SM7B)
    admin_do(am, "setup_claim", claim_payload("shure-sm7b", "SM7B", evidence("own_setup_page", 5)))
    c = repo.list(R.CLAIMS, SetupClaim)[0]
    assert c.published and c.status == "confirmed"
    assert len(repo.audit_log()) >= 6
