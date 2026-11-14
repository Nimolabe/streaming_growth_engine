import json
from datetime import timedelta

import pytest

from setup_agent import repository as R
from setup_agent.cli import main as cli_main
from setup_agent.fetcher import FetchResult, HttpFetcher
from setup_agent.jobs import run_job
from setup_agent.models import AuditAction, ChangeProposal, Offer, Operation, ProposalStatus, SetupClaim, Source
from setup_agent.monitors import JsonFeedPriceSource, PriceMonitor, PriceSourceError, SourceMonitor, html_to_text

from .conftest import NOW, days_ago
from .helpers import ADMIN, admin_do, base_world, claim_payload, evidence, offer_payload


class FakeFetcher:
    def __init__(self, pages: dict[str, FetchResult]):
        self.pages, self.calls = pages, []

    def fetch(self, url):
        self.calls.append(url)
        return self.pages.get(url, FetchResult(False, error="HTTP 404", status=404))


def html(body: str) -> FetchResult:
    return FetchResult(True, f"<html><head><style>.shure-sm7db{{}}</style></head><body>{body}</body></html>", 200,
                       final_url="https://nachtfalke.example/setup")


def world_with_source(auto=True):
    repo, am = base_world()
    admin_do(am, "source_registry", {"domain": "nachtfalke.example", "source_types": ["own_setup_page"],
                                     "access_method": "http_allowed" if auto else "manual", "auto_fetch_allowed": auto,
                                     "terms_reviewed_at": days_ago(5).isoformat() if auto else None, "min_interval_hours": 24})
    admin_do(am, "source", {"url": "https://nachtfalke.example/setup", "source_type": "own_setup_page",
                            "streamer_id": "twitch-nachtfalke"})
    return repo, am


class TestSourceMonitor:
    def test_new_product_on_page_becomes_proposal_not_fact(self):
        repo, am = world_with_source()
        f = FakeFetcher({"https://nachtfalke.example/setup": html("<p>Mikro: <b>Shure SM7B</b></p>")})
        r = SourceMonitor(repo, am, f, clock=lambda: NOW).run()
        assert r.checked == 1 and len(r.proposals) == 1
        assert repo.list(R.CLAIMS, SetupClaim) == []
        p = repo.get(R.PROPOSALS, r.proposals[0], ChangeProposal)
        assert p.operation == Operation.CREATE and p.payload["product_id"] == "shure-sm7b" and p.status == ProposalStatus.PENDING
        assert "shure-sm7db" not in json.dumps(p.payload), "Text in <style> wird ignoriert"

    def test_unchanged_page_creates_nothing(self):
        repo, am = world_with_source()
        page = {"https://nachtfalke.example/setup": html("Shure SM7B")}
        SourceMonitor(repo, am, FakeFetcher(page), clock=lambda: NOW).run()
        later = NOW + timedelta(days=2)
        r = SourceMonitor(repo, am, FakeFetcher(page), clock=lambda: later).run()
        assert r.unchanged == 1 and r.proposals == []
        assert len(repo.list_proposals(ProposalStatus.PENDING)) == 1

    def test_unreachable_source_keeps_data(self):
        repo, am = world_with_source()
        admin_do(am, "setup_claim", claim_payload("shure-sm7b", "SM7B", evidence("own_setup_page", 10)))
        before = repo.list(R.CLAIMS, SetupClaim)
        r = SourceMonitor(repo, am, FakeFetcher({}), clock=lambda: NOW).run()
        assert r.failed and repo.list(R.CLAIMS, SetupClaim) == before
        src = repo.list(R.SOURCES, Source)[0]
        assert src.last_check_ok is False and src.content_hash is None
        assert repo.audit_log("source")[-1].action == AuditAction.CHECK_FAILED

    def test_manual_only_sources_are_never_fetched(self):
        repo, am = world_with_source(auto=False)
        f = FakeFetcher({})
        r = SourceMonitor(repo, am, f, clock=lambda: NOW).run()
        assert f.calls == [] and r.skipped == 1

    def test_interval_is_respected(self):
        repo, am = world_with_source()
        page = {"https://nachtfalke.example/setup": html("Shure SM7B")}
        SourceMonitor(repo, am, FakeFetcher(page), clock=lambda: NOW).run()
        f = FakeFetcher(page)
        SourceMonitor(repo, am, f, clock=lambda: NOW + timedelta(hours=2)).run()
        assert f.calls == []

    def test_redirect_to_unregistered_domain_is_refused(self):
        repo, am = world_with_source()
        f = FakeFetcher({"https://nachtfalke.example/setup": FetchResult(True, "Shure SM7B", 200, final_url="https://andere.example/x")})
        r = SourceMonitor(repo, am, f, clock=lambda: NOW).run()
        assert r.failed and r.proposals == []

    def test_product_removed_from_page_is_only_proposed_outdated(self):
        repo, am = world_with_source()
        SourceMonitor(repo, am, FakeFetcher({"https://nachtfalke.example/setup": html("Shure SM7B")}), clock=lambda: NOW).run()
        am.decide(repo.list_proposals(ProposalStatus.PENDING)[0].id, ProposalStatus.APPROVED, ADMIN)
        claim = repo.list(R.CLAIMS, SetupClaim)[0]
        assert claim.published
        later = NOW + timedelta(days=8)
        r = SourceMonitor(repo, am, FakeFetcher({"https://nachtfalke.example/setup": html("Shure MV7+")}), clock=lambda: later).run()
        payloads = [repo.get(R.PROPOSALS, pid, ChangeProposal).payload for pid in r.proposals]
        assert any(p.get("status") == "outdated" for p in payloads)
        assert repo.get(R.CLAIMS, claim.id, SetupClaim).published, "bis zur Freigabe unverändert"

    def test_html_to_text(self):
        assert " ".join(html_to_text("<p>A<script>Shure SM7B</script> B</p>").split()) == "A B"


class TestPriceMonitor:
    def _world(self, tmp_path, feed):
        repo, am = base_world()
        admin_do(am, "offer", offer_payload("shure-sm7b", "Partner A", "https://partner-a.example/sm7b", 39900, age_days=2) | {"price_source": "partner-a"})
        admin_do(am, "offer", offer_payload("shure-mv7", "Händler B", "https://haendler-b.example/mv7", 27900, age_days=2))
        path = tmp_path / "feed.json"
        path.write_text(json.dumps(feed))
        return repo, JsonFeedPriceSource("partner-a", path=path)

    def test_price_change_from_feed(self, tmp_path):
        repo, src = self._world(tmp_path, [{"url": "https://partner-a.example/sm7b?utm_source=feed", "amount_minor": 34900, "currency": "EUR", "availability": "in_stock"}])
        r = PriceMonitor(repo, [src], clock=lambda: NOW).run()
        assert len(r.changed) == 1 and r.skipped == 1, "manuell gepflegtes Angebot bleibt unberührt"
        o = next(o for o in repo.list(R.OFFERS, Offer) if o.price_source == "partner-a")
        assert o.price.amount_minor == 34900 and len(repo.observations(o.id)) == 1

    def test_same_price_twice_no_duplicate_history(self, tmp_path):
        repo, src = self._world(tmp_path, [{"url": "https://partner-a.example/sm7b", "amount_minor": 34900, "currency": "EUR", "availability": "in_stock"}])
        PriceMonitor(repo, [src], clock=lambda: NOW).run()
        PriceMonitor(repo, [JsonFeedPriceSource("partner-a", path=tmp_path / "feed.json")], clock=lambda: NOW + timedelta(days=1)).run()
        o = next(o for o in repo.list(R.OFFERS, Offer) if o.price_source == "partner-a")
        assert len(repo.observations(o.id)) == 1

    def test_missing_offer_and_broken_feed_keep_last_price(self, tmp_path):
        repo, src = self._world(tmp_path, [])
        r = PriceMonitor(repo, [src], clock=lambda: NOW).run()
        o = next(o for o in repo.list(R.OFFERS, Offer) if o.price_source == "partner-a")
        assert r.failed and o.price.amount_minor == 39900 and o.failed_checks == 1
        (tmp_path / "feed.json").write_text("{kaputt")
        with pytest.raises(PriceSourceError):
            JsonFeedPriceSource("partner-a", path=tmp_path / "feed.json").lookup(o)

    def test_invalid_feed_entry(self, tmp_path):
        repo, src = self._world(tmp_path, [{"url": "https://partner-a.example/sm7b", "amount_minor": -5, "currency": "EUR"}])
        r = PriceMonitor(repo, [src], clock=lambda: NOW).run()
        assert r.failed and r.changed == []


class TestJobsAndCli:
    def test_apply_job_exports_and_records_run(self, tmp_path):
        repo, am = base_world()
        admin_do(am, "setup_claim", claim_payload("shure-sm7b", "SM7B", evidence("own_setup_page", 10)))
        result = run_job("apply", repo, out_dir=tmp_path, clock=lambda: NOW)
        assert result["export"]["written"] > 0
        assert repo.get_meta("agent")["runs"]["apply"]["ok"] is True
        setup = json.loads((tmp_path / "v1/streamers/twitch-nachtfalke/setup.json").read_text())
        assert setup["items"][0]["product"]["id"] == "shure-sm7b"

    def test_weekly_job_runs_detector(self):
        repo, am = base_world()
        admin_do(am, "setup_claim", claim_payload("shure-sm7b", "SM7B", evidence("own_setup_page", 300)))
        result = run_job("weekly", repo, clock=lambda: NOW + timedelta(days=100))
        assert result["detector"]["created"] == 1

    def test_storage_outage_reports_error(self):
        repo, _ = base_world()
        repo.available = False
        assert "error" in run_job("apply", repo, clock=lambda: NOW)

    def test_unknown_job(self):
        with pytest.raises(ValueError):
            run_job("alles", R.InMemoryRepository())

    def test_demo_command(self, tmp_path, capsys):
        assert cli_main(["demo", "--out", str(tmp_path)]) == 0
        streamers = json.loads((tmp_path / "v1/streamers.json").read_text())["items"]
        assert {s["id"] for s in streamers} == {"twitch-nachtfalke", "tiktok-lenalounge"}
        lena = json.loads((tmp_path / "v1/streamers/tiktok-lenalounge/setup.json").read_text())["items"]
        assert "kamera" not in [i["category"] for i in lena], "nicht zugeordnete Kamera erscheint nicht"

    def test_production_commands_need_credentials(self, monkeypatch):
        monkeypatch.delenv("FIREBASE_SERVICE_ACCOUNT", raising=False)
        with pytest.raises(SystemExit, match="FIREBASE_SERVICE_ACCOUNT"):
            cli_main(["run", "apply"])


class TestHttpFetcherWithoutNetwork:
    def test_rejects_non_http(self):
        assert not HttpFetcher().fetch("file:///etc/passwd").ok

    def test_robots_unreachable_means_no_fetch(self, monkeypatch):
        import urllib.request

        def boom(*a, **k):
            raise OSError("kein Netz")

        monkeypatch.setattr(urllib.request, "urlopen", boom)
        r = HttpFetcher().fetch("https://nachtfalke.example/setup")
        assert not r.ok and "robots" in r.error
