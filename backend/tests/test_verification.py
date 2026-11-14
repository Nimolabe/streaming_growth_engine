import pytest

from setup_agent.models import ConfidenceLevel, SourceType, VerificationStatus as VS
from setup_agent.verification import analyze_slots, confidence_score, evaluate_claim, is_publishable

from .conftest import NOW, claim, ev

OWN = SourceType.OWN_SETUP_PAGE
STATEMENT = SourceType.OFFICIAL_STATEMENT
VISUAL = SourceType.VIDEO_VISUAL
THIRD = SourceType.THIRD_PARTY


class TestStatusRules:
    def test_fresh_primary_source_confirms(self):
        v = evaluate_claim(claim(ev(OWN, 30)), NOW)
        assert v.status == VS.CONFIRMED and v.level == ConfidenceLevel.HIGH
        assert "own_setup_page" in v.reason

    def test_secondary_sources_never_confirm(self):
        c = claim(*(ev(THIRD, 5, f"https://news{i}.example/a") for i in range(6)), ev(VISUAL, 2, "https://video.example/v1"))
        v = evaluate_claim(c, NOW)
        assert v.status == VS.PROBABLE
        assert "Sekundärquellen" in v.reason

    def test_old_primary_is_not_carried_into_today(self):
        v = evaluate_claim(claim(ev(OWN, 500)), NOW)
        assert v.status == VS.PROBABLE and "älter als 365" in v.reason

    def test_everything_stale_is_outdated(self):
        v = evaluate_claim(claim(ev(OWN, 800), ev(THIRD, 900, "https://news.example/a")), NOW)
        assert v.status == VS.OUTDATED

    def test_unresolved_product_is_unknown_even_with_strong_source(self):
        v = evaluate_claim(claim(ev(STATEMENT, 3), product_id=None, raw_name="Shure SM7"), NOW)
        assert v.status == VS.UNKNOWN and "nicht eindeutig" in v.reason

    def test_flags_take_precedence(self):
        c = claim(ev(OWN, 3))
        assert evaluate_claim(c, NOW, conflicting=True).status == VS.CONFLICTING
        assert evaluate_claim(c, NOW, superseded=True).status == VS.OUTDATED

    def test_boundary_365_days(self):
        assert evaluate_claim(claim(ev(OWN, 365)), NOW).status == VS.CONFIRMED
        assert evaluate_claim(claim(ev(OWN, 366)), NOW).status == VS.PROBABLE

    def test_evaluation_does_not_modify_claim(self):
        c = claim(ev(OWN, 3))
        before = c.model_dump()
        evaluate_claim(c, NOW)
        assert c.model_dump() == before


class TestConfidence:
    def test_weights_and_age(self):
        assert confidence_score([ev(STATEMENT, 10)], NOW) == pytest.approx(0.95)
        assert confidence_score([ev(OWN, 400)], NOW) == pytest.approx(0.63)
        assert confidence_score([ev(THIRD, 1000)], NOW) == pytest.approx(0.16)

    def test_independent_domains_add_bonus_once(self):
        same_domain = [ev(THIRD, 5, "https://news.example/a"), ev(THIRD, 6, "https://news.example/b")]
        assert confidence_score(same_domain, NOW) == pytest.approx(0.40)
        two_domains = [ev(THIRD, 5, "https://news.example/a"), ev(THIRD, 6, "https://blog.example/b")]
        assert confidence_score(two_domains, NOW) == pytest.approx(0.45)

    def test_never_reaches_one(self):
        many = [ev(STATEMENT, 1, f"https://site{i}.example/x") for i in range(10)]
        assert confidence_score(many, NOW) == 0.99

    def test_empty(self):
        assert confidence_score([], NOW) == 0.0


class TestSlotConflicts:
    def test_close_primary_sources_for_different_products_conflict(self):
        a = claim(ev(OWN, 10))
        b = claim(ev(STATEMENT, 25, "https://social.example/post/1"), product_id="shure-mv7plus", raw_name="Shure MV7+")
        flags = analyze_slots([a, b], NOW)
        assert flags.conflicting == {a.id, b.id} and not flags.superseded

    def test_clearly_newer_source_supersedes_older(self):
        old = claim(ev(OWN, 200))
        new = claim(ev(STATEMENT, 5, "https://social.example/post/2"), product_id="shure-mv7plus", raw_name="Shure MV7+")
        flags = analyze_slots([old, new], NOW)
        assert flags.superseded == {old.id} and not flags.conflicting
        assert evaluate_claim(old, NOW, superseded=old.id in flags.superseded).status == VS.OUTDATED
        assert evaluate_claim(new, NOW).status == VS.CONFIRMED

    def test_different_roles_are_no_conflict(self):
        main = claim(ev(OWN, 10))
        irl = claim(ev(OWN, 10, "https://nachtfalke.example/irl"), role="irl", product_id="dji-mic-mini", raw_name="DJI Mic Mini")
        assert analyze_slots([main, irl], NOW).conflicting == set()

    def test_different_streamers_are_no_conflict(self):
        a = claim(ev(OWN, 10))
        b = claim(ev(OWN, 10, "https://other.example/setup"), streamer_id="twitch-startersam", product_id="shure-mv7plus", raw_name="Shure MV7+")
        assert analyze_slots([a, b], NOW).conflicting == set()

    def test_secondary_only_claims_do_not_supersede(self):
        confirmed = claim(ev(OWN, 100))
        rumor = claim(ev(THIRD, 1, "https://forum.example/t/1"), product_id="shure-mv7plus", raw_name="Shure MV7+")
        flags = analyze_slots([confirmed, rumor], NOW)
        assert flags.superseded == set() and flags.conflicting == set()

    def test_three_products(self):
        a = claim(ev(OWN, 5))
        b = claim(ev(STATEMENT, 20, "https://social.example/1"), product_id="shure-mv7plus", raw_name="Shure MV7+")
        c = claim(ev(STATEMENT, 300, "https://social.example/2"), product_id="rode-podmic-usb", raw_name="Rode PodMic USB")
        flags = analyze_slots([a, b, c], NOW)
        assert flags.conflicting == {a.id, b.id} and flags.superseded == {c.id}


class TestPublication:
    def test_only_approved_and_public_statuses(self):
        c = claim(ev(OWN, 5))
        assert not is_publishable(c)  # nicht freigegeben
        c = c.model_copy(update={"published": True, "status": VS.CONFIRMED})
        assert is_publishable(c)
        for status in (VS.UNKNOWN, VS.CONFLICTING, VS.OUTDATED):
            assert not is_publishable(c.model_copy(update={"status": status}))
        assert is_publishable(c.model_copy(update={"status": VS.PROBABLE}))
        assert not is_publishable(c.model_copy(update={"product_id": None}))
