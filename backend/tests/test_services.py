import json

import pytest

from setup_agent import exporter
from setup_agent import repository as R
from setup_agent.approval import ApprovalManager, InvalidInput
from setup_agent.detector import ChangeDetector
from setup_agent.models import (
    AuditAction,
    ChangeProposal,
    InvalidTransition,
    Offer,
    Operation,
    Product,
    ProposalStatus,
    SetupClaim,
    Streamer,
    VerificationStatus as VS,
)
from setup_agent.registry import SourceRegistry
from setup_agent.resolver import ProductResolver

from .conftest import NOW, days_ago
from .helpers import ADMIN, AGENT, MV7, PODMIC, SM7B, admin_do, base_world, claim_payload, evidence, offer_payload


def claim_of(repo, product_id):
    return next(c for c in repo.list(R.CLAIMS, SetupClaim) if c.product_id == product_id)


class TestApprovalWorkflow:
    def test_agent_proposal_is_not_applied_until_admin_approves(self):
        repo, am = base_world()
        p, created = am.propose(entity_type="setup_claim", entity_id="new", operation=Operation.CREATE,
                                payload=claim_payload("shure-sm7b", "Shure SM7B", evidence("own_setup_page", 5)),
                                reason="Neue Quelle", actor=AGENT, origin="source_monitor")
        assert created and repo.list(R.CLAIMS, SetupClaim) == []
        with pytest.raises(InvalidTransition):
            am.decide(p.id, ProposalStatus.APPROVED, AGENT)
        done = am.decide(p.id, ProposalStatus.APPROVED, ADMIN, "geprüft")
        assert done.applied_at == NOW
        c = claim_of(repo, "shure-sm7b")
        assert c.status == VS.CONFIRMED and c.published and c.last_verified_at == NOW

    def test_unresolved_product_is_stored_but_never_published(self):
        repo, am = base_world()
        admin_do(am, "setup_claim", claim_payload(None, "Shure SM7 irgendwas", evidence("official_statement", 3)))
        c = repo.list(R.CLAIMS, SetupClaim)[0]
        assert c.status == VS.UNKNOWN and not c.published

    def test_secondary_only_is_published_as_probable(self):
        repo, am = base_world()
        admin_do(am, "setup_claim", claim_payload("shure-sm7b", "SM7B", evidence("video_visual", 3, "https://video.example/v/1")))
        c = claim_of(repo, "shure-sm7b")
        assert c.status == VS.PROBABLE and c.published

    def test_rejection_changes_nothing_and_is_audited(self):
        repo, am = base_world()
        p, _ = am.propose(entity_type="product", entity_id="new", operation=Operation.CREATE,
                          payload={"manufacturer": "Elgato", "model": "Wave:3", "category": "mikrofon"},
                          reason="Neu", actor=AGENT, origin="test")
        am.decide(p.id, ProposalStatus.REJECTED, ADMIN, "Gibt es schon unter anderem Namen")
        assert repo.find(R.PRODUCTS, "elgato-wave-3", Product) is None
        assert [e.action for e in repo.audit_log(entity_id="new")][-1] == AuditAction.REJECT

    def test_references_must_exist(self):
        repo, am = base_world()
        with pytest.raises(InvalidInput, match="unbekannten"):
            am.propose(entity_type="setup_claim", entity_id="new", operation=Operation.CREATE, reason="Tippfehler",
                       payload=claim_payload("shure-sm7-b", "SM7B", evidence("own_setup_page", 5)), actor=ADMIN, origin="admin")
        with pytest.raises(InvalidInput, match="unbekannten"):
            am.propose(entity_type="offer", entity_id="new", operation=Operation.CREATE, reason="Tippfehler",
                       payload=offer_payload("gibt-es-nicht", "Händler A", "https://haendler-a.example/x", 100), actor=ADMIN, origin="admin")

    def test_invalid_input_is_rejected_before_storing(self):
        repo, am = base_world()
        with pytest.raises(InvalidInput):
            am.propose(entity_type="setup_claim", entity_id="new", operation=Operation.CREATE,
                       payload=claim_payload("shure-sm7b", "SM7B"), reason="ohne Quelle", actor=ADMIN, origin="admin")
        with pytest.raises(InvalidInput):
            am.propose(entity_type="streamer", entity_id="new", operation=Operation.CREATE,
                       payload={"id": "x", "display_name": ""}, reason="kaputt", actor=ADMIN, origin="admin")
        with pytest.raises(R.NotFound):
            am.propose(entity_type="offer", entity_id="o_missing", operation=Operation.UPDATE,
                       payload={"retailer": "X"}, reason="fehlt", actor=ADMIN, origin="admin")
        assert repo.list_proposals(ProposalStatus.PENDING) == []

    def test_duplicate_product_spelling_fails_on_apply(self):
        repo, am = base_world()
        p, _ = am.propose(entity_type="product", entity_id="new", operation=Operation.CREATE,
                          payload={"manufacturer": "SHURE", "model": "SM-7B", "category": "mikrofon"},
                          reason="Doppelt", actor=AGENT, origin="test")
        done = am.decide(p.id, ProposalStatus.APPROVED, ADMIN)
        assert done.applied_at is None and "existiert bereits" in done.apply_error
        assert len(repo.list(R.PRODUCTS, Product)) == 4

    def test_stale_base_version_is_not_applied(self):
        repo, am = base_world()
        a, _ = am.propose(entity_type="streamer", entity_id="twitch-nachtfalke", operation=Operation.UPDATE,
                          payload={"display_name": "Nachtfalke"}, base_version=1, reason="Umbenennung", actor=AGENT, origin="t")
        b, _ = am.propose(entity_type="streamer", entity_id="twitch-nachtfalke", operation=Operation.UPDATE,
                          payload={"primary_language": "en"}, base_version=1, reason="Sprache geändert", actor=AGENT, origin="t")
        am.decide(a.id, ProposalStatus.APPROVED, ADMIN)
        done = am.decide(b.id, ProposalStatus.APPROVED, ADMIN)
        assert "inzwischen geändert" in done.apply_error
        s = repo.get(R.STREAMERS, "twitch-nachtfalke", Streamer)
        assert s.display_name == "Nachtfalke" and s.primary_language == "de" and s.version == 2

    def test_audit_trail_with_diff_and_reason(self):
        repo, am = base_world()
        admin_do(am, "streamer", {"display_name": "Nachtfalke"}, entity_id="twitch-nachtfalke", op=Operation.UPDATE,
                 base_version=1, reason="Kanal umbenannt")
        upd = [e for e in repo.audit_log("streamer", "twitch-nachtfalke") if e.action == AuditAction.UPDATE][0]
        assert upd.changes == {"display_name": ("NachtfalkeTV", "Nachtfalke")}
        assert upd.reason == "Kanal umbenannt" and upd.from_version == 1 and upd.to_version == 2 and upd.actor == ADMIN

    def test_apply_pending_from_admin_page(self):
        """Admin-Seite setzt nur status=approved in Firestore; der Job wendet an."""
        repo, am = base_world()
        p = ChangeProposal(id="AbCdEf123", entity_type="product", entity_id="new", operation=Operation.CREATE,
                           payload={"manufacturer": "Elgato", "model": "Key Light", "category": "licht"},
                           reason="Neu", origin="admin", created_by=ADMIN, created_at=NOW)
        repo.add_proposal(p)
        repo.update_proposal(p.decide(ProposalStatus.APPROVED, ADMIN, NOW), expected_status=ProposalStatus.PENDING, expected_applied=False)
        report = am.apply_pending_approvals()
        assert report.applied == ["AbCdEf123"]
        assert repo.find(R.PRODUCTS, "elgato-key-light", Product) is not None
        assert am.apply_pending_approvals().applied == [], "zweiter Lauf wendet nichts doppelt an"

    def test_manual_price_keeps_history(self):
        repo, am = base_world()
        admin_do(am, "offer", offer_payload("shure-sm7b", "Händler A", "https://haendler-a.example/sm7b", 39900))
        o = repo.list(R.OFFERS, Offer)[0]
        admin_do(am, "offer", {"price": {"amount_minor": 35900, "currency": "EUR"}}, entity_id=o.id, op=Operation.UPDATE,
                 base_version=1, reason="Preis laut Händler")
        o2 = repo.get(R.OFFERS, o.id, Offer)
        assert o2.price.amount_minor == 35900 and o2.version == 2 and o2.last_success_at == NOW
        assert [x.price.amount_minor for x in repo.observations(o.id)] == [35900]

    def test_retire_claim_unpublishes(self):
        repo, am = base_world()
        admin_do(am, "setup_claim", claim_payload("shure-sm7b", "SM7B", evidence("own_setup_page", 5)))
        c = claim_of(repo, "shure-sm7b")
        admin_do(am, "setup_claim", {}, entity_id=c.id, op=Operation.RETIRE, base_version=c.version, reason="Falsch zugeordnet")
        c2 = repo.get(R.CLAIMS, c.id, SetupClaim)
        assert not c2.published and c2.status == VS.OUTDATED

    def test_manual_status_correction(self):
        repo, am = base_world()
        admin_do(am, "setup_claim", claim_payload("shure-sm7b", "SM7B", evidence("third_party", 5, "https://news.example/a")))
        c = claim_of(repo, "shure-sm7b")
        admin_do(am, "setup_claim", {"status": "conflicting"}, entity_id=c.id, op=Operation.UPDATE, base_version=c.version,
                 reason="Streamer hat im Chat etwas anderes gesagt")
        c2 = repo.get(R.CLAIMS, c.id, SetupClaim)
        assert c2.status == VS.CONFLICTING and not c2.published and "manuell" in c2.reason

    def test_storage_outage_keeps_proposal_open(self):
        repo, am = base_world()
        p, _ = am.propose(entity_type="product", entity_id="new", operation=Operation.CREATE, payload=PODMIC | {"model": "PodMic"},
                          reason="Neu", actor=AGENT, origin="t")
        repo.available = False
        with pytest.raises(R.StorageUnavailable):
            am.decide(p.id, ProposalStatus.APPROVED, ADMIN)
        repo.available = True
        assert repo.get(R.PROPOSALS, p.id, ChangeProposal).status == ProposalStatus.PENDING


class TestChangeDetector:
    def test_newer_primary_source_supersedes_without_overwriting(self):
        repo, am = base_world()
        clock = {"now": NOW}
        am.clock = lambda: clock["now"]
        admin_do(am, "setup_claim", claim_payload("shure-sm7b", "SM7B", evidence("own_setup_page", 120)))
        admin_do(am, "setup_claim", claim_payload("shure-mv7", "Shure MV7+", evidence("official_statement", 2, "https://social.example/p/9")))
        old = claim_of(repo, "shure-sm7b")
        # Beim Anlegen des neuen wurde der alte nicht verändert:
        assert old.status == VS.CONFIRMED and old.published
        det = ChangeDetector(repo, am, clock=lambda: clock["now"])
        r1 = det.run()
        assert len(r1.created) == 1
        r2 = det.run()
        assert r2.created == [] and r2.already_known == r1.created, "kein doppelter Vorschlag"
        prop = repo.get(R.PROPOSALS, r1.created[0], ChangeProposal)
        assert prop.payload["status"] == "outdated" and prop.entity_id == old.id
        # Erst nach Freigabe:
        am.decide(prop.id, ProposalStatus.APPROVED, ADMIN)
        assert not repo.get(R.CLAIMS, old.id, SetupClaim).published

    def test_conflict_goes_to_review(self):
        repo, am = base_world()
        admin_do(am, "setup_claim", claim_payload("shure-sm7b", "SM7B", evidence("own_setup_page", 10)))
        admin_do(am, "setup_claim", claim_payload("rode-podmic-usb", "Rode PodMic USB", evidence("official_statement", 12, "https://social.example/p/1")))
        # Der zweite wurde beim Anlegen schon als widersprüchlich bewertet, der erste noch nicht:
        assert claim_of(repo, "rode-podmic-usb").status == VS.CONFLICTING
        r = ChangeDetector(repo, am, clock=lambda: NOW).run()
        prop = repo.get(R.PROPOSALS, r.created[0], ChangeProposal)
        assert prop.payload["status"] == "conflicting"

    def test_aging_evidence_triggers_status_change_later(self):
        repo, am = base_world()
        admin_do(am, "setup_claim", claim_payload("shure-sm7b", "SM7B", evidence("own_setup_page", 300)))
        later = NOW.replace(year=NOW.year + 1)
        r = ChangeDetector(repo, am, clock=lambda: later).run()
        assert repo.get(R.PROPOSALS, r.created[0], ChangeProposal).payload["status"] == "probable"

    def test_obsolete_own_proposals_are_superseded(self):
        repo, am = base_world()
        admin_do(am, "setup_claim", claim_payload("shure-sm7b", "SM7B", evidence("own_setup_page", 300)))
        later = NOW.replace(year=NOW.year + 1)
        r1 = ChangeDetector(repo, am, clock=lambda: later).run()
        c = claim_of(repo, "shure-sm7b")
        # Admin bestätigt in der Zwischenzeit mit neuer Quelle
        admin_do(am, "setup_claim", {"evidence": [*([e.model_dump(mode="json") for e in c.evidence]), evidence("official_statement", 1, "https://social.example/neu")]},
                 entity_id=c.id, op=Operation.UPDATE, base_version=c.version, reason="Neue Aussage")
        r2 = ChangeDetector(repo, am, clock=lambda: NOW).run()
        assert r2.superseded == r1.created


class TestResolver:
    @pytest.fixture
    def resolver(self):
        return ProductResolver([Product(**SM7B), Product(manufacturer="Shure", model="SM7dB", category="mikrofon"),
                                Product(**MV7), Product(manufacturer="Elgato", model="Stream Deck MK.2", category="streamdeck"),
                                Product(manufacturer="Elgato", model="Stream Deck Neo", category="streamdeck"),
                                Product(manufacturer="Acme", model="SM7B", category="mikrofon")])

    def test_exact_and_spelling(self, resolver):
        assert resolver.resolve("Shure SM7B").product_id == "shure-sm7b"
        assert resolver.resolve("shure sm-7b").product_id == "shure-sm7b"
        assert resolver.resolve("Shure SM7dB").product_id == "shure-sm7db"

    def test_model_only_is_ambiguous_with_two_makers(self, resolver):
        r = resolver.resolve("SM7B")
        assert r.product_id is None and "Mehrdeutig" in r.reason and set(r.suggestions) == {"shure-sm7b", "acme-sm7b"}

    def test_similar_name_is_never_assigned(self, resolver):
        r = resolver.resolve("Shure SM7")
        assert r.product_id is None and "shure-sm7b" in r.suggestions
        assert resolver.resolve("Stream Deck").product_id is None

    def test_category_narrows(self, resolver):
        assert resolver.resolve("Elgato Stream Deck MK.2", category="streamdeck").product_id == "elgato-stream-deck-mk-2"
        assert resolver.resolve("Shure SM7B", category="licht").product_id is None

    def test_mentions_in_text_need_full_name(self, resolver):
        text = "Mein Setup: Shure SM7B am Arm, dazu ein Stream Deck MK.2 und eine Kamera. Früher: SM7dB."
        assert resolver.find_mentions(text) == ["shure-sm7b"]
        assert resolver.find_mentions("Ich nutze das neue Shure SM7dB!") == ["shure-sm7db"]


class TestRegistry:
    def test_rules(self):
        from setup_agent.models import SourceRegistryEntry, SourceType
        reg = SourceRegistry([
            SourceRegistryEntry(domain="nachtfalke.example", source_types=["own_setup_page"], access_method="http_allowed",
                                auto_fetch_allowed=True, terms_reviewed_at=days_ago(10), min_interval_hours=24),
            SourceRegistryEntry(domain="news.example", source_types=["third_party"]),
        ])
        assert reg.check_use("https://www.nachtfalke.example/setup", SourceType.OWN_SETUP_PAGE).allowed
        assert reg.check_use("https://blog.nachtfalke.example/x", SourceType.OWN_SETUP_PAGE).allowed
        assert not reg.check_use("https://nachtfalke.example/setup", SourceType.THIRD_PARTY).allowed
        assert not reg.check_use("https://unbekannt.example/x", SourceType.THIRD_PARTY).allowed
        assert not reg.check_auto_fetch("https://news.example/a", None, NOW).allowed
        assert reg.check_auto_fetch("https://nachtfalke.example/setup", None, NOW).allowed
        assert not reg.check_auto_fetch("https://nachtfalke.example/setup", days_ago(0), NOW).allowed


class TestExport:
    def _world(self):
        repo, am = base_world()
        admin_do(am, "setup_claim", claim_payload("shure-sm7b", "SM7B", evidence("own_setup_page", 10)))
        admin_do(am, "setup_claim", claim_payload(None, "Kamera unbekannt", evidence("own_setup_page", 10), category="kamera"))
        admin_do(am, "offer", offer_payload("shure-sm7b", "Händler A", "https://haendler-a.example/sm7b", 39900))
        admin_do(am, "offer", offer_payload("shure-sm7b", "Händler B", "https://haendler-b.example/sm7b", 37900, age_days=30))
        admin_do(am, "offer", offer_payload("shure-mv7", "Händler A", "https://haendler-a.example/mv7", 24900))
        return repo, am

    def test_only_published_facts_are_exported(self):
        repo, _ = self._world()
        files = exporter.build(repo, NOW)
        setup = files["v1/streamers/twitch-nachtfalke/setup.json"]
        assert [i["product"]["id"] for i in setup["items"]] == ["shure-sm7b"], "unbekannte Kamera erscheint nicht"
        item = setup["items"][0]
        assert item["status"] == "confirmed" and item["sources"][0]["source_type"] == "own_setup_page"
        assert item["last_verified_at"] == "2026-11-10T12:00:00Z"

    def test_prices_states_and_alternatives(self):
        repo, _ = self._world()
        files = exporter.build(repo, NOW)
        offers = files["v1/products/shure-sm7b/offers.json"]["items"]
        assert [(o["retailer"], o["price_state"]) for o in offers] == [("Händler B", "stale"), ("Händler A", "current")]
        sm7b = files["v1/products/shure-sm7b.json"]
        assert sm7b["best_price"]["amount_minor"] == 39900, "veralteter günstigerer Preis zählt nicht"
        alts = files["v1/products/shure-sm7b/alternatives.json"]["items"]
        assert [a["id"] for a in alts] == ["shure-mv7"]
        products = {p["id"] for p in files["v1/products.json"]["items"]}
        assert {"shure-sm7b", "shure-sm7db"} <= products

    def test_write_is_idempotent_and_removes_old_files(self, tmp_path):
        repo, am = self._world()
        r1 = exporter.write(repo, tmp_path, NOW)
        assert "v1/meta.json" in r1.written
        r2 = exporter.write(repo, tmp_path, NOW)
        assert r2.written == [] and r2.removed == []
        (tmp_path / "v1/streamers/geloescht.json").write_text("{}")
        assert exporter.write(repo, tmp_path, NOW).removed == ["v1/streamers/geloescht.json"]
        meta = json.loads((tmp_path / "v1/meta.json").read_text())
        assert meta["counts"]["published_setup_items"] == 1
