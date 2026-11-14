import pytest

from setup_agent import identity


class TestProductNames:
    def test_similar_model_names_stay_different(self):
        assert identity.product_match_key("Shure", "SM7B") != identity.product_match_key("Shure", "SM7dB")
        assert identity.product_id("Shure", "SM7B") != identity.product_id("Shure", "SM7dB")
        assert identity.product_match_key("Elgato", "Stream Deck MK.2") != identity.product_match_key("Elgato", "Stream Deck Neo")

    def test_spelling_variants_are_the_same_product(self):
        key = identity.product_match_key("Shure", "SM7B")
        assert identity.product_match_key("SHURE", "SM-7B") == key
        assert identity.product_match_key(" shure ", "sm 7 b") == key

    def test_umlauts_and_accents(self):
        assert identity.slugify("Großes Mikrofon für Ü-Streams") == "grosses-mikrofon-fuer-ue-streams"
        assert identity.slugify("Rødecaster") == "rodecaster"

    @pytest.mark.parametrize("bad", ["", "   ", "!!!"])
    def test_empty_names_are_rejected(self, bad):
        with pytest.raises(ValueError):
            identity.slugify(bad)
        with pytest.raises(ValueError):
            identity.product_match_key(bad, "SM7B")


class TestUrls:
    def test_normalization_removes_noise(self):
        a = identity.normalize_url("http://WWW.Nachtfalke.example/setup/?utm_source=x&b=2&a=1#mikro")
        assert a == "https://nachtfalke.example/setup?a=1&b=2"

    def test_same_source_same_id(self):
        assert identity.source_id("https://nachtfalke.example/setup") == identity.source_id("http://www.nachtfalke.example/setup/?utm_campaign=y")

    def test_different_pages_different_id(self):
        assert identity.source_id("https://nachtfalke.example/setup") != identity.source_id("https://nachtfalke.example/setup-2024")

    @pytest.mark.parametrize("bad", ["ftp://x.example/a", "javascript:alert(1)", "nachtfalke.example/setup", ""])
    def test_invalid_urls(self, bad):
        with pytest.raises(ValueError):
            identity.normalize_url(bad)


class TestDeterministicIds:
    def test_claim_id_is_stable(self):
        a = identity.claim_id("twitch-nachtfalke", "mikrofon:primary", "shure-sm7b", "Shure SM7B")
        b = identity.claim_id("twitch-nachtfalke", "mikrofon:primary", "shure-sm7b", "SHURE sm7b (neu)")
        assert a == b, "Mit Produkt-ID entscheidet das Produkt, nicht der Rohtext"

    def test_unresolved_claim_uses_raw_name(self):
        a = identity.claim_id("twitch-nachtfalke", "mikrofon:primary", None, "Shure SM-7B")
        b = identity.claim_id("twitch-nachtfalke", "mikrofon:primary", None, "shure sm7b")
        c = identity.claim_id("twitch-nachtfalke", "mikrofon:primary", None, "Shure SM7dB")
        assert a == b != c

    def test_dedupe_key_ignores_dict_order(self):
        k1 = identity.dedupe_key("offer", "o_1", "update", {"a": 1, "b": {"x": 1, "y": 2}})
        k2 = identity.dedupe_key("offer", "o_1", "update", {"b": {"y": 2, "x": 1}, "a": 1})
        assert k1 == k2
        assert k1 != identity.dedupe_key("offer", "o_1", "update", {"a": 2, "b": {"x": 1, "y": 2}})


class TestGtin:
    @pytest.mark.parametrize("code", ["4006381333931", "042100005264", "96385074", "10614141000415"])
    def test_valid(self, code):
        assert identity.gtin_is_valid(code)

    @pytest.mark.parametrize("code", ["4006381333932", "12345", "40063813339A1", ""])
    def test_invalid(self, code):
        assert not identity.gtin_is_valid(code)
