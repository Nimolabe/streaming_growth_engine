"""API-Tests. Der Kern (api_core) läuft immer; die FastAPI-Verdrahtung nur, wenn FastAPI installiert ist (CI)."""

import pytest

from setup_agent import repository as R
from setup_agent.api_core import SetupApi
from setup_agent.demo import seed
from setup_agent.models import Offer, ProposalStatus, SetupClaim, Streamer

from .conftest import NOW


class FakeVerifier:
    tokens = {"admin-token": {"uid": "admin-1", "admin": True}, "user-token": {"uid": "user-7"},
              "fake-admin": {"uid": "x", "admin": "true"}}

    def verify(self, token):
        if token not in self.tokens:
            raise ValueError("ungültig")
        return self.tokens[token]


ADMIN = "Bearer admin-token"


@pytest.fixture
def api():
    repo = R.InMemoryRepository()
    seed(repo, NOW)
    return SetupApi(repo, FakeVerifier(), clock=lambda: NOW)


class TestPublic:
    def test_list_and_filter_streamers(self, api):
        st, body = api.call(api.list_streamers)
        assert st == 200 and body["total"] == 2
        assert [s["id"] for s in api.call(api.list_streamers, platform="tiktok")[1]["items"]] == ["tiktok-lenalounge"]
        assert api.call(api.list_streamers, page=2, page_size=1)[1]["items"][0]["id"] == "twitch-nachtfalke"

    def test_setup_shows_sources_and_check_date(self, api):
        st, body = api.call(api.setup, "twitch-nachtfalke")
        assert st == 200 and body["generated_at"].startswith("2025-06-02")
        light = next(i for i in body["items"] if i["category"] == "licht")
        assert light["status"] == "probable" and light["sources"][0]["source_type"] == "third_party"
        assert all(i["sources"] and i["last_verified_at"] for i in body["items"])

    def test_filter_hardware_by_category_and_price(self, api):
        items = api.call(api.list_products, category="licht", max_price=12000)[1]["items"]
        assert [p["id"] for p in items] == ["elgato-key-light-mini"]
        assert api.call(api.list_products, min_price=50000, max_price=100)[0] == 400

    def test_alternatives(self, api):
        items = api.call(api.alternatives, "elgato-key-light")[1]["items"]
        assert [a["id"] for a in items] == ["elgato-key-light-mini"]
        assert api.call(api.alternatives, "elgato-key-light", limit=0)[0] == 400

    def test_not_found_and_invalid(self, api):
        assert api.call(api.streamer, "twitch-gibtsnicht") == (404, {"error": {"code": "not_found", "message": "Streamer nicht gefunden.", "details": {}}})
        assert api.call(api.offers, "nix")[0] == 404
        assert api.call(api.list_streamers, page_size=1000)[0] == 400

    def test_meta(self, api):
        body = api.call(api.meta)[1]
        assert body["api_version"] == "v1" and body["counts"]["streamers"] == 2


class TestAccessControl:
    @pytest.mark.parametrize("auth,status", [(None, 401), ("admin-token", 401), ("Bearer falsch", 401),
                                             ("Bearer user-token", 403), ("Bearer fake-admin", 403)])
    def test_admin_endpoints_need_admin(self, api, auth, status):
        before = api.repo.list(R.STREAMERS, Streamer)
        st, body = api.call(api.admin_create, auth, "streamers", {"id": "twitch-boese", "display_name": "Böse", "categories": ["gaming"],
                                                                 "platforms": [{"platform": "twitch", "handle": "b", "url": "https://twitch.example/b"}]})
        assert st == status and body["error"]["code"] in ("unauthenticated", "forbidden")
        assert api.repo.list(R.STREAMERS, Streamer) == before
        for fn, args in [(api.admin_proposals, ()), (api.admin_sources, ()), (api.admin_audit, ()),
                         (api.admin_decide, ("p_x", True, None)), (api.admin_set_price, ("o_x", {"price": None}))]:
            assert api.call(fn, auth, *args)[0] == status

    def test_public_reads_never_show_unpublished(self, api):
        lena = api.call(api.setup, "tiktok-lenalounge")[1]
        assert "kamera" not in [i["category"] for i in lena["items"]]
        unknown = [c for c in api.repo.list(R.CLAIMS, SetupClaim) if c.product_id is None]
        assert unknown and not unknown[0].published


class TestAdmin:
    def test_create_streamer_and_claim(self, api):
        st, _ = api.call(api.admin_create, ADMIN, "streamers", {
            "id": "youtube-pixelpia", "display_name": "PixelPia", "categories": ["creative"],
            "platforms": [{"platform": "youtube", "handle": "pixelpia", "url": "https://youtube.example/@pixelpia"}],
            "reason": "Neuer Streamer"})
        assert st == 200
        st, body = api.call(api.admin_create, ADMIN, "claims", {
            "streamer_id": "youtube-pixelpia", "category": "licht", "product_id": "elgato-key-light", "raw_name": "Key Light",
            "evidence": [{"source_url": "https://pixelpia.example/gear", "source_type": "own_setup_page",
                          "observed_at": "2025-05-30T00:00:00Z", "retrieved_at": "2025-06-01T00:00:00Z"}]})
        assert st == 200 and body["proposal_id"]
        setup = api.call(api.setup, "youtube-pixelpia")[1]
        assert setup["items"][0]["status"] == "confirmed"
        audit = api.call(api.admin_audit, ADMIN, entity_type="setup_claim")[1]["items"]
        assert audit[-1]["actor"] == {"type": "admin", "id": "admin-1"}

    def test_invalid_input_is_400_and_stores_nothing(self, api):
        n = len(api.repo.list_proposals())
        st, body = api.call(api.admin_create, ADMIN, "claims", {"streamer_id": "twitch-nachtfalke", "category": "licht",
                                                                "product_id": "elgato-key-light", "raw_name": "x", "evidence": []})
        assert st == 400 and body["error"]["code"] == "invalid_input"
        assert len(api.repo.list_proposals()) == n

    def test_update_needs_version_and_reason(self, api):
        s = api.repo.get(R.STREAMERS, "twitch-nachtfalke", Streamer)
        assert api.call(api.admin_update, ADMIN, "streamers", s.id, {"changes": {"primary_language": "en"}})[0] == 400
        assert api.call(api.admin_update, ADMIN, "streamers", s.id, {"changes": {}, "expected_version": 1})[0] == 400
        ok = api.call(api.admin_update, ADMIN, "streamers", s.id, {"changes": {"primary_language": "en"}, "expected_version": 1,
                                                                   "reason": "Kanal jetzt englisch"})
        assert ok[0] == 200
        conflict = api.call(api.admin_update, ADMIN, "streamers", s.id, {"changes": {"primary_language": "fr"}, "expected_version": 1,
                                                                         "reason": "Alter Stand"})
        assert conflict[0] == 409
        assert api.repo.get(R.STREAMERS, s.id, Streamer).primary_language == "en"

    def test_unknown_fields_rejected(self, api):
        st, body = api.call(api.admin_update, ADMIN, "streamers", "twitch-nachtfalke",
                            {"changes": {}, "expected_version": 1, "reason": "Test", "admin": True})
        assert st == 400 and "Unbekannte Felder" in body["error"]["message"]

    def test_manual_price(self, api):
        o = next(o for o in api.repo.list(R.OFFERS, Offer) if o.product_id == "shure-sm7b")
        st, _ = api.call(api.admin_set_price, ADMIN, o.id, {"price": {"amount_minor": 37900, "currency": "EUR"}, "reason": "Händlerseite"})
        assert st == 200
        offers = api.call(api.offers, "shure-sm7b")[1]["items"]
        assert offers[0]["price"]["amount_minor"] == 37900 and offers[0]["price_state"] == "current"
        assert api.call(api.admin_set_price, ADMIN, o.id, {"price": {"amount_minor": -1, "currency": "EUR"}})[0] == 400

    def test_review_queue(self, api):
        from setup_agent.detector import ChangeDetector
        from datetime import timedelta
        ChangeDetector(api.repo, api.approvals, clock=lambda: NOW + timedelta(days=360)).run()
        pending = api.call(api.admin_proposals, ADMIN)[1]["items"]
        assert pending
        pid = pending[0]["id"]
        assert api.call(api.admin_decide, ADMIN, pid, False, "")[0] == 422, "Ablehnung ohne Begründung"
        assert api.call(api.admin_decide, ADMIN, pid, False, "Quelle ist noch aktuell")[0] == 200
        assert api.call(api.admin_decide, ADMIN, pid, True, None)[0] == 422, "bereits entschieden"
        assert api.call(api.admin_proposals, ADMIN, status="rejected")[1]["items"][0]["id"] == pid
        assert api.call(api.admin_proposals, ADMIN, status="quatsch")[0] == 400

    def test_storage_outage(self, api):
        api.repo.available = False
        assert api.call(api.list_streamers)[0] == 503
        assert api.call(api.admin_create, ADMIN, "products", {"manufacturer": "A", "model": "B", "category": "maus"})[0] == 503
