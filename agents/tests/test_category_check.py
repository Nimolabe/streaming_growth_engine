"""Kategorie-Check – mit nachgebauter Twitch-API (kein Netz)."""
import io
import json
from datetime import UTC, datetime
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

import pytest

from streaming_agents.category_check import cli as cli_module
from streaming_agents.category_check.aliases import (
    CATEGORY_ALIASES,
    alias_label,
    alias_target,
    normalize,
)
from streaming_agents.category_check.analysis import (
    analyze,
    in_window,
    local_time_from_offset,
    parse_window,
    rank_for,
)
from streaming_agents.category_check.collect import (
    Category,
    CategoryNotFound,
    measure,
    measure_many,
    resolve_category,
    suggestion_categories,
    top_categories,
)
from streaming_agents.category_check.gambling import (
    GAMBLING_CATEGORIES,
    GamblingNotSupported,
    is_gambling,
    is_gambling_name,
    rejection,
)
from streaming_agents.category_check.models import CategoryCheckRequest, CategorySnapshot
from streaming_agents.category_check.report import render_report
from streaming_agents.category_check.store import StoreError, append_snapshots, load_snapshots
from streaming_agents.clip_hunter.twitch_api import HelixClient, TwitchApiError

MONDAY_18_UTC = datetime(2026, 11, 16, 17, 0, tzinfo=UTC).timestamp()  # 18:00 MEZ
UTC_PLUS_1 = local_time_from_offset(60)


def snap(viewers, *, cat="1", name="Spiel", complete=True, at=MONDAY_18_UTC, lang="de"):
    return CategorySnapshot(taken_at=at, category_id=cat, category=name, language=lang,
                            complete=complete, viewers=viewers)


# ------------------------------------------------------------- nachgebaute API


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeTwitch:
    """Beantwortet Token-, games-, search-, games/top- und streams-Anfragen."""

    def __init__(self, streams=None, games=None, search=None, top=None, page_size=None,
                 fail=None):
        self.streams = streams or {}      # (game_id, language) -> list[viewer_count]
        self.games = games or {}          # exakter Name -> id
        self.search = search or []        # [(id, name)]
        self.top = top or []              # [(id, name)]
        self.page_size = page_size
        self.fail = fail or {}            # game_id -> HTTP-Code
        self.calls = []

    def __call__(self, request, timeout):
        url = request.full_url
        self.calls.append(request)
        if url.startswith("https://id.twitch.tv/oauth2/token"):
            return FakeResponse(json.dumps({"access_token": "tok"}).encode())
        assert request.get_header("Authorization") == "Bearer tok"
        assert request.get_header("Client-id") == "cid"
        parts = urlsplit(url)
        path = parts.path.removeprefix("/helix/")
        query = parse_qs(parts.query)
        if path == "games":
            name = query["name"][0]
            data = [{"id": self.games[name], "name": name}] if name in self.games else []
            return self._json({"data": data})
        if path == "search/categories":
            return self._json({"data": [{"id": i, "name": n} for i, n in self.search]})
        if path == "games/top":
            first = int(query["first"][0])
            return self._json({"data": [{"id": i, "name": n} for i, n in self.top[:first]]})
        if path == "streams":
            game = query["game_id"][0]
            if game in self.fail:
                raise HTTPError(url, self.fail[game], "x", {}, io.BytesIO(b""))
            lang = query.get("language", ["any"])[0]
            assert query["type"] == ["live"]
            items = self.streams.get((game, lang), [])
            size = self.page_size or int(query["first"][0])
            start = int(query.get("after", ["0"])[0])
            page = items[start:start + size]
            data = [{"id": f"s{start + n}", "user_id": f"u{start + n}", "user_login": "geheim",
                     "viewer_count": value} for n, value in enumerate(page)]
            more = start + size < len(items)
            return self._json({"data": data, "pagination": {"cursor": str(start + size)} if more else {}})
        raise AssertionError(url)

    @staticmethod
    def _json(payload):
        return FakeResponse(json.dumps(payload).encode())


def client(fake):
    return HelixClient("cid", "secret", opener=fake)


# ------------------------------------------------------------------- Platz


@pytest.mark.parametrize(("viewers", "own", "complete", "expected"), [
    ([50, 10, 3, 2, 1], 2, True, (5, False)),     # hinter allen mit >= 2
    ([50, 10, 3, 2, 1], 5, True, (3, False)),
    ([50, 10], 100, True, (1, False)),
    ([], 2, True, (1, False)),
    ([5, 5, 5], 0, True, (4, False)),
    ([90, 40, 7], 2, False, (4, True)),           # unvollständig, man liegt dahinter
    ([90, 40, 7], 7, False, (4, True)),           # Gleichstand am Rand: unklar
    ([90, 40, 7], 20, False, (3, False)),         # sicher vor dem Rest
])
def test_rank(viewers, own, complete, expected):
    assert rank_for(snap(viewers, complete=complete), own) == expected


def test_snapshot_sorts_and_validates():
    assert snap([1, 9, 3]).viewers == [9, 3, 1]
    with pytest.raises(ValueError):
        snap([-1])
    with pytest.raises(ValueError):
        CategorySnapshot(taken_at=MONDAY_18_UTC, category_id="abc", category="x", language="de",
                         complete=True)
    with pytest.raises(ValueError):
        CategorySnapshot(taken_at=MONDAY_18_UTC, category_id="1", category="x", language="deu",
                         complete=True)


# ------------------------------------------------------------------ Messen


def test_resolve_exact_fuzzy_and_suggestions():
    fake = FakeTwitch(games={"Minecraft": "27471"},
                      search=[("1", "Stardew Valley"), ("2", "Stardew Valley Expanded")])
    api = client(fake)
    assert resolve_category(api, "  Minecraft ") == Category("27471", "Minecraft")
    assert resolve_category(api, "stardew valley") == Category("1", "Stardew Valley")
    with pytest.raises(CategoryNotFound, match="Meintest du: Stardew Valley, Stardew Valley Expanded"):
        resolve_category(api, "Stardew")
    with pytest.raises(CategoryNotFound, match="nicht gefunden.$"):
        resolve_category(client(FakeTwitch()), "Gibtsnicht")
    with pytest.raises(CategoryNotFound):
        resolve_category(api, "   ")


def test_measure_pages_dedupes_and_stores_only_numbers():
    viewers = list(range(250, 0, -1))
    fake = FakeTwitch(streams={("7", "de"): viewers})
    pauses = []
    result = measure(client(fake), Category("7", "Spiel"), "DE", pause=0.5,
                     clock=lambda: MONDAY_18_UTC, sleep=pauses.append)
    assert result.complete and result.channels == 250 and result.viewers[0] == 250
    assert result.taken_at == MONDAY_18_UTC and result.language == "de"
    assert pauses == [0.5, 0.5]
    dumped = result.model_dump_json()
    assert "geheim" not in dumped and "user" not in dumped


def test_measure_marks_incomplete_and_handles_odd_data():
    fake = FakeTwitch(streams={("7", "any"): [30, 20, "x", None, 10, 5]}, page_size=2)
    result = measure(client(fake), Category("7", "Spiel"), "any", max_pages=2, sleep=lambda _: None)
    streams = [r for r in fake.calls if "/streams" in r.full_url]
    assert all("language=" not in r.full_url for r in streams)
    assert not result.complete and result.viewers == [30, 20, 0]  # "x" übersprungen, None → 0
    with pytest.raises(ValueError):
        measure(client(fake), Category("7", "Spiel"), max_pages=0)


def test_measure_many_continues_after_single_error_but_stops_on_auth():
    fake = FakeTwitch(streams={("1", "de"): [5], ("3", "de"): [9]}, fail={"2": 500})
    cats = [Category("1", "A"), Category("2", "B"), Category("3", "C")]
    result = measure_many(client(fake), cats, "de", sleep=lambda _: None)
    assert [s.category for s in result.snapshots] == ["A", "C"]
    assert result.errors == ["B: Twitch-API-Fehler (HTTP 500)."]
    fake = FakeTwitch(streams={("1", "de"): [5], ("3", "de"): [9]}, fail={"1": 401})
    result = measure_many(client(fake), cats, "de", sleep=lambda _: None)
    assert result.snapshots == [] and len(result.errors) == 1


def test_top_categories():
    fake = FakeTwitch(top=[(str(i), f"Spiel {i}") for i in range(1, 60)])
    assert [c.name for c in top_categories(client(fake), 3)] == ["Spiel 1", "Spiel 2", "Spiel 3"]
    assert len(top_categories(client(fake), 500)) == 59


# --------------------------------------------------------------- Auswertung


def test_verdicts_and_order():
    big = [5000, 3000] + [100] * 30 + [10] * 40 + [3] * 30 + [1] * 20
    snaps = [
        snap(big, cat="1", name="Riesig"),
        snap([80, 40, 20, 6, 3, 1], cat="2", name="Nische"),
        snap([40, 20, 15, 10] + [3] * 20 + [1] * 10, cat="3", name="Mittel"),
        snap([3, 2, 1], cat="4", name="Leer"),
    ]
    result = analyze(snaps, own_viewers=2, to_local=UTC_PLUS_1)
    verdicts = {item.category: (item.verdict, item.median_rank) for item in result.categories}
    assert verdicts == {"Nische": ("good", 6), "Mittel": ("ok", 25), "Riesig": ("hard", 103),
                        "Leer": ("low_demand", 3)}
    assert [item.category for item in result.categories] == ["Nische", "Mittel", "Riesig", "Leer"]
    nische = result.categories[0]
    assert nische.median_total_viewers == 150 and nische.top3_share == round(140 / 150, 3)
    assert "Gute Chance" in nische.verdict_text and "2 Zuschauern" in nische.verdict_text
    assert any("weniger als drei Messungen" in n for n in result.notes)


def test_incomplete_category_is_never_rated_good():
    result = analyze([snap([500] * 10, complete=False)], own_viewers=2, to_local=UTC_PLUS_1)
    item = result.categories[0]
    assert item.rank_is_lower_bound and item.verdict == "hard"
    assert item.channels_is_lower_bound and "hinter Platz 10" in item.verdict_text


def test_median_over_measurements_and_best_slots():
    hour = 3600
    snaps = []
    for day in range(3):  # Mo/Di/Mi, je 18 Uhr (gut) und 22 Uhr (voll)
        base = MONDAY_18_UTC + day * 24 * hour
        snaps.append(snap([60, 30, 10, 1], at=base))
        snaps.append(snap([90] * 40 + [5] * 10, at=base + 4 * hour))
    result = analyze(snaps, own_viewers=2, to_local=UTC_PLUS_1)
    item = result.categories[0]
    assert item.measurements == 6
    # 22 Uhr: Platz 51, aber 3650 Zuschauer (≈ 72 pro Platz) schlägt 18 Uhr: Platz 4, 101 (≈ 25)
    labels = [slot.label for slot in item.best_slots]
    assert labels[:3] == ["Mo 22–24 Uhr", "Di 22–24 Uhr", "Mi 22–24 Uhr"]
    assert item.best_slots[0].median_rank == 51 and item.best_slots[0].measurements == 1
    assert item.median_rank == 51  # oberer Median über alle sechs Messungen
    early = analyze(snaps, own_viewers=2, to_local=UTC_PLUS_1, window=(16, 20)).categories[0]
    assert [slot.label for slot in early.best_slots] == ["Mo 18–20 Uhr", "Di 18–20 Uhr",
                                                          "Mi 18–20 Uhr"]
    en = analyze(snaps, own_viewers=2, language="en", to_local=UTC_PLUS_1).categories[0]
    assert en.best_slots[0].label == "Mon 22:00–24:00"
    assert not any("drei Messungen" in n for n in result.notes)


def test_best_times_prefer_audience_over_empty_night():
    night = datetime(2026, 11, 17, 2, 0, tzinfo=UTC).timestamp()    # 3 Uhr: leer, Platz 2
    evening = datetime(2026, 11, 17, 18, 0, tzinfo=UTC).timestamp()  # 19 Uhr: voll, Platz 5
    snaps = [snap([20, 10, 1], at=night), snap([400, 200, 100, 50, 1], at=evening)]
    item = analyze(snaps, own_viewers=2, to_local=UTC_PLUS_1).categories[0]
    assert [slot.label for slot in item.best_slots] == ["Di 18–20 Uhr", "Di 2–4 Uhr"]
    only = analyze(snaps, own_viewers=2, to_local=UTC_PLUS_1, window=(16, 24)).categories[0]
    assert [slot.label for slot in only.best_slots] == ["Di 18–20 Uhr"]


@pytest.mark.parametrize(("text", "expected"), [
    ("16-24", (16, 0)), ("20-2", (20, 2)), ("0-24", (0, 24)), ("18–22", (18, 22))])
def test_parse_window(text, expected):
    assert parse_window(text) == expected


@pytest.mark.parametrize("text", ["abends", "25-3", "16", "-1-4", "a-b"])
def test_parse_window_rejects(text):
    with pytest.raises(ValueError):
        parse_window(text)


def test_in_window():
    assert [h for h in range(0, 24, 2) if in_window(h, (20, 2))] == [0, 20, 22]
    assert in_window(4, None) and in_window(4, (6, 6))


def test_slot_label_midnight_and_no_slots_note():
    late = datetime(2026, 11, 15, 22, 30, tzinfo=UTC).timestamp()  # So 23:30 MEZ
    result = analyze([snap([100, 50], at=late), snap([100, 50], at=late - 7200)],
                     to_local=UTC_PLUS_1)
    assert result.categories[0].best_slots[0].label in {"So 22–24 Uhr", "So 20–22 Uhr"}
    single = analyze([snap([100, 50])], to_local=UTC_PLUS_1)
    assert single.categories[0].best_slots == []
    assert any("zwei verschiedenen Zeiten" in n for n in single.notes)


def test_same_category_different_languages_stay_separate():
    result = analyze([snap([10, 5], lang="de"), snap([900, 400, 100], lang="en")],
                     to_local=UTC_PLUS_1)
    assert sorted(item.language for item in result.categories) == ["de", "en"]


def test_analyze_rejects_bad_input():
    with pytest.raises(ValueError):
        analyze([snap([1])], language="fr")
    with pytest.raises(ValueError):
        analyze([snap([1])], own_viewers=-1)


def test_api_request_limits():
    with pytest.raises(ValueError):
        CategoryCheckRequest(snapshots=[])
    with pytest.raises(ValueError):
        CategoryCheckRequest(snapshots=[snap([1] * 2000)] * 101)


# ------------------------------------------------------- Speichern und Bericht


def test_store_roundtrip_and_bad_lines(tmp_path):
    path = tmp_path / "m.jsonl"
    append_snapshots(path, [snap([3, 2])])
    append_snapshots(path, [snap([9], cat="2", name="B")])
    with path.open("ab") as handle:
        handle.write(b'{"kaputt"\n[1,2]\n\xff\xfe\n{"format":"sge-category-snapshot"}\n')
    loaded = load_snapshots(path)
    assert [s.category for s in loaded.snapshots] == ["Spiel", "B"] and loaded.skipped_lines == 4
    empty = tmp_path / "leer.jsonl"
    empty.write_text("\n")
    with pytest.raises(StoreError):
        load_snapshots(empty)
    with pytest.raises(StoreError):
        load_snapshots(tmp_path / "fehlt.jsonl")


def test_report_escapes_and_translates():
    result = analyze([snap([10, 5], name="<script>alert(1)</script>")], to_local=UTC_PLUS_1)
    html = render_report(result, created=datetime(2026, 11, 16, 12, 0, tzinfo=UTC))
    assert "<script>alert" not in html and "&lt;script&gt;" in html
    assert "Kategorie-Check" in html and "16.11.2026 12:00" in html
    en = render_report(analyze([snap([1500, 5])], language="en", to_local=UTC_PLUS_1))
    assert "Category check" in en and "1,505" in en


# --------------------------------------------------------------------- CLI


@pytest.fixture
def fake_env(monkeypatch):
    fake = FakeTwitch(games={"Minecraft": "27471", "Stardew Valley": "1"},
                      streams={("27471", "de"): [400, 200] + [2] * 60, ("1", "de"): [30, 10, 4]},
                      top=[("27471", "Minecraft"), ("1", "Stardew Valley")],
                      search=[("9", "Minecraft Dungeons")])
    monkeypatch.setattr(cli_module.HelixClient, "from_env",
                        classmethod(lambda cls, **kw: HelixClient("cid", "secret", opener=fake)))
    monkeypatch.setattr("streaming_agents.category_check.collect.time.sleep", lambda _: None)
    return fake


def test_cli_measure_and_report(fake_env, tmp_path, capsys):
    out = tmp_path / "m.jsonl"
    assert cli_module.main(["measure", "Minecraft", "Stardew Valley", "Minecraft",
                            "--out", str(out)]) == 0
    printed = capsys.readouterr().out
    assert "2 Messungen ergänzt" in printed and "Stardew Valley" in printed
    assert "gute Chance" in printed
    assert len(out.read_text().splitlines()) == 2
    html, js = tmp_path / "b.html", tmp_path / "e.json"
    assert cli_module.main(["report", str(out), "--viewers", "5", "--html", str(html),
                            "--json", str(js)]) == 0
    assert "Kategorie-Check" in html.read_text(encoding="utf-8")
    assert json.loads(js.read_text())["own_viewers"] == 5
    assert cli_module.main(["report", str(out), "--window", "abends"]) == 2
    assert cli_module.main(["report", str(out), "--html", str(html)]) == 2
    assert "existiert bereits" in capsys.readouterr().err


def test_cli_unknown_category_and_bad_args(fake_env, tmp_path, capsys):
    out = str(tmp_path / "m.jsonl")
    assert cli_module.main(["measure", "Minecraf", "--out", out]) == 2
    assert "Meintest du: Minecraft Dungeons" in capsys.readouterr().err
    assert cli_module.main(["measure", "Minecraft", "--out", out, "--pages", "0"]) == 2
    assert cli_module.main(["measure", "Minecraft", "--out", out, "--viewers", "-1"]) == 2
    assert cli_module.main(["watch", "Minecraft", "--out", out, "--every", "5"]) == 2
    assert cli_module.main(["suggest", "--out", out, "--top", "0"]) == 2
    with pytest.raises(SystemExit):
        cli_module.main(["measure", "Minecraft", "--out", out, "--lang", "deutsch"])


def test_cli_suggest_uses_three_pages(fake_env, tmp_path, capsys):
    out = tmp_path / "m.jsonl"
    assert cli_module.main(["suggest", "--top", "2", "--out", str(out)]) == 0
    assert "Messe die 2 meistgesehenen Kategorien" in capsys.readouterr().out
    assert len(out.read_text().splitlines()) == 2


def test_cli_watch_rounds(fake_env, tmp_path, capsys):
    out = tmp_path / "m.jsonl"
    waits = []
    args = cli_module.build_parser().parse_args(
        ["watch", "Minecraft", "--every", "30", "--hours", "1", "--out", str(out)])
    ticks = iter(range(100))
    assert cli_module.cmd_watch(args, sleep=waits.append, clock=lambda: next(ticks)) == 0
    assert len(out.read_text().splitlines()) == 3 and len(waits) == 2
    assert all(1790 <= wait <= 1800 for wait in waits)
    assert "Runde 3/3" in capsys.readouterr().out


def test_cli_without_credentials(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("TWITCH_CLIENT_ID", raising=False)
    monkeypatch.delenv("TWITCH_CLIENT_SECRET", raising=False)
    assert cli_module.main(["measure", "Minecraft", "--out", str(tmp_path / "m.jsonl")]) == 2
    assert "TWITCH_CLIENT_ID" in capsys.readouterr().err


def test_api_endpoint():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from streaming_agents.api import app

    body = {"snapshots": [json.loads(snap([60, 30, 10, 1]).model_dump_json())],
            "own_viewers": 2, "utc_offset_minutes": 60}
    response = TestClient(app).post("/api/v1/content/category-check", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["categories"][0]["verdict"] == "good" and data["categories"][0]["median_rank"] == 4
    assert TestClient(app).post("/api/v1/content/category-check",
                                json={"snapshots": []}).status_code == 422


def test_twitch_errors_are_typed():
    fake = FakeTwitch(fail={"5": 429})
    with pytest.raises(TwitchApiError, match="Anfragelimit"):
        measure(client(fake), Category("5", "X"), sleep=lambda _: None)


# ------------------------------------------------- Aliasse und Glücksspiel (Echttest 26.11.2026)

@pytest.mark.parametrize(("typed", "official"), [
    ("CS2", "Counter-Strike"), ("cs 2", "Counter-Strike"), ("Counter Strike 2", "Counter-Strike"),
    ("Counter-Strike 2", "Counter-Strike"), ("CS:GO", "Counter-Strike"),
    ("LoL", "League of Legends"), ("GTA", "Grand Theft Auto V"), ("gta 5", "Grand Theft Auto V"),
    ("GTA V", "Grand Theft Auto V"), ("GTA RP", "Grand Theft Auto V"),
    ("GTA 6", "Grand Theft Auto VI"), ("WoW", "World of Warcraft"), ("Apex", "Apex Legends"),
    ("R6", "Rainbow Six Siege"), ("Rainbow Six", "Rainbow Six Siege"),
    ("EA FC", "EA Sports FC 27"), ("FC 26", "EA Sports FC 26"), ("fc26", "EA Sports FC 26"),
    ("TFT", "Teamfight Tactics"), ("DbD", "Dead by Daylight"),
])
def test_alias_targets(typed, official):
    assert alias_target(typed) == official


def test_alias_table_is_clean():
    assert alias_target("Counter-Strike") is None      # offizieller Name: kein Alias
    assert alias_target("Minecraft") is None and alias_target("League") is None
    assert all(key == normalize(key) for key in CATEGORY_ALIASES)  # Schlüssel normalisiert
    assert alias_label("CS2", "Counter-Strike") == "CS2 → Counter-Strike (Alias)"


def test_resolve_uses_alias_before_get_games():
    fake = FakeTwitch(games={"Counter-Strike": "32399", "Carrot Slime 2": "789686325"})
    category = resolve_category(client(fake), " CS2 ")
    assert category == Category("32399", "Counter-Strike", alias="CS2")
    names = [parse_qs(urlsplit(r.full_url).query)["name"][0] for r in fake.calls
             if "/helix/games?" in r.full_url]
    assert names == ["Counter-Strike"]  # nie nach „CS2“ gefragt → kein „Carrot Slime 2“
    assert resolve_category(client(fake), "Counter-Strike").alias is None


def test_alias_falls_back_when_target_is_gone():
    fake = FakeTwitch(games={"LoL": "5"})  # Ziel „League of Legends“ gibt es hier nicht
    assert resolve_category(client(fake), "LoL") == Category("5", "LoL")


def test_measure_stores_alias_and_report_shows_it(tmp_path):
    fake = FakeTwitch(games={"Counter-Strike": "32399"}, streams={("32399", "de"): [90, 4, 1]})
    category = resolve_category(client(fake), "cs2")
    shot = measure(client(fake), category, clock=lambda: MONDAY_18_UTC, sleep=lambda _: None)
    assert shot.alias == "cs2" and shot.category == "Counter-Strike"
    append_snapshots(tmp_path / "m.jsonl", [shot])
    loaded = load_snapshots(tmp_path / "m.jsonl").snapshots[0]
    assert loaded.alias == "cs2"
    result = analyze([loaded, snap([5], cat="32399", name="Counter-Strike", at=MONDAY_18_UTC + 60)],
                     to_local=UTC_PLUS_1)
    assert result.categories[0].aliases == ["cs2"]
    assert "cs2 → Counter-Strike (Alias)" in result.notes
    assert "cs2 → Counter-Strike (Alias)" in render_report(result)
    # Alte Messdateien ohne Alias bleiben lesbar.
    assert CategorySnapshot.model_validate({**json.loads(snap([1]).model_dump_json()),
                                            "alias": None}).alias is None


def test_gambling_list_and_detection():
    assert GAMBLING_CATEGORIES["498566"] == "Slots"
    assert is_gambling("498566", "irgendwas")            # per ID
    assert is_gambling("123", "Blackjack")               # gleichnamige Kategorie, andere ID
    assert is_gambling("1", "virtual casino")
    assert is_gambling_name("SLOTS") and is_gambling_name("Texas Hold'em")
    assert not is_gambling("499634", "Crypto") and not is_gambling("27471", "Minecraft")
    assert "nicht unterstützt" in rejection("Slots", "de")
    assert "not supported" in rejection("Slots", "en")


def test_no_gambling_option_anywhere():
    parser = cli_module.build_parser()
    for command in (["suggest", "--out", "x.jsonl"], ["report", "x.jsonl"]):
        with pytest.raises(SystemExit):
            parser.parse_args(command + ["--include-gambling"])
    assert "include_gambling" not in CategoryCheckRequest.model_fields
    import inspect
    assert "include" not in str(inspect.signature(suggestion_categories))
    assert "include" not in str(inspect.signature(analyze))


GAMBLING_TOP = [("509658", "Just Chatting"), ("498566", "Slots"), ("27471", "Minecraft"),
                ("29452", "Virtual Casino"), ("33214", "Fortnite"), ("516575", "VALORANT")]


def test_suggestion_categories_always_filters_and_refills():
    fake = FakeTwitch(top=GAMBLING_TOP)
    chosen = suggestion_categories(client(fake), 3)
    assert [c.name for c in chosen.categories] == ["Just Chatting", "Minecraft", "Fortnite"]
    assert chosen.skipped_gambling == 2


def test_resolve_and_measure_refuse_gambling():
    fake = FakeTwitch(games={"Slots": "498566", "Blackjack": "999"},
                      streams={("498566", "de"): [50]})
    with pytest.raises(GamblingNotSupported) as caught:
        resolve_category(client(fake), "slots")
    assert caught.value.name == "slots"
    assert not [r for r in fake.calls if "/helix/" in r.full_url]  # gar nicht erst gefragt
    with pytest.raises(GamblingNotSupported):
        measure(client(fake), Category("498566", "Slots"), sleep=lambda _: None)
    assert not [r for r in fake.calls if "/streams" in r.full_url]
    result = measure_many(client(fake), [Category("498566", "Slots")], "de", sleep=lambda _: None)
    assert result.snapshots == [] and "nicht unterstützt" in result.errors[0]


def test_resolve_refuses_gambling_found_by_id_or_alias(monkeypatch):
    # Twitch liefert unter einem harmlos klingenden Namen eine gesperrte ID.
    fake = FakeTwitch(games={"Lucky Spin": "498566"})
    with pytest.raises(GamblingNotSupported, match="Lucky Spin"):
        resolve_category(client(fake), "Lucky Spin")
    # Eine Kurzform, die auf eine Glücksspiel-Kategorie zeigt, wird ebenso abgelehnt.
    monkeypatch.setitem(CATEGORY_ALIASES, "vc", "Virtual Casino")
    fake = FakeTwitch(games={"Virtual Casino": "29452"})
    with pytest.raises(GamblingNotSupported):
        resolve_category(client(fake), "VC")
    assert not [r for r in fake.calls if "/helix/" in r.full_url]


def test_analyze_ignores_gambling_and_counts_neutrally():
    snaps = [snap([50, 1], cat="498566", name="Slots"), snap([9, 1], cat="1", name="Blackjack"),
             snap([900] * 60, cat="2", name="Groß")]
    result = analyze(snaps, to_local=UTC_PLUS_1)
    assert [c.category for c in result.categories] == ["Groß"] and result.measurements == 1
    assert result.notes[0] == "2 Messungen zu Glücksspiel-Kategorien ignoriert (werden nicht unterstützt)."
    assert not any("Slots" in note or "Blackjack" in note for note in result.notes)
    english = analyze(snaps, language="en", skipped_gambling=1, to_local=UTC_PLUS_1)
    assert english.notes[:2] == ["Without 1 gambling category (not supported).",
                                 "2 measurements of gambling categories ignored (not supported)."]
    assert "Slots" not in render_report(result)


@pytest.fixture
def gambling_env(monkeypatch):
    fake = FakeTwitch(games={"Slots": "498566", "Counter-Strike": "32399"},
                      streams={("498566", "de"): [300, 20, 2], ("32399", "de"): [500, 40, 2],
                               ("27471", "de"): [100, 3], ("509658", "de"): [800, 2],
                               ("33214", "de"): [60, 2], ("29452", "de"): [10]},
                      top=GAMBLING_TOP)
    monkeypatch.setattr(cli_module.HelixClient, "from_env",
                        classmethod(lambda cls, **kw: HelixClient("cid", "secret", opener=fake)))
    monkeypatch.setattr("streaming_agents.category_check.collect.time.sleep", lambda _: None)
    return fake


def test_cli_suggest_never_measures_gambling(gambling_env, tmp_path, capsys):
    out = tmp_path / "m.jsonl"
    assert cli_module.main(["suggest", "--top", "3", "--out", str(out)]) == 0
    printed = capsys.readouterr().out
    assert "Ohne 2 Glücksspiel-Kategorien (werden nicht unterstützt)." in printed
    assert "Slots" not in printed and "Virtual Casino" not in printed   # keine Namen
    stored = [json.loads(line)["category"] for line in out.read_text().splitlines()]
    assert stored == ["Just Chatting", "Minecraft", "Fortnite"]
    measured = [r.full_url for r in gambling_env.calls if "/streams" in r.full_url]
    assert not any("game_id=498566" in url or "game_id=29452" in url for url in measured)


def test_cli_measure_mixed_refuses_gambling_and_measures_rest(gambling_env, tmp_path, capsys):
    out = tmp_path / "m.jsonl"
    assert cli_module.main(["measure", "Slots", "CS2", "--out", str(out)]) == 0
    printed = capsys.readouterr().out
    assert "„Slots“ ist eine Glücksspiel-Kategorie. Glücksspiel-Kategorien werden von der " \
           "Streaming Growth Engine nicht unterstützt" in printed
    assert "CS2 → Counter-Strike (Alias)" in printed
    stored = [json.loads(line)["category"] for line in out.read_text().splitlines()]
    assert stored == ["Counter-Strike"]


def test_cli_measure_and_watch_only_gambling_fail(gambling_env, tmp_path, capsys):
    out = tmp_path / "m.jsonl"
    assert cli_module.main(["measure", "Slots", "Poker", "--out", str(out)]) == 2
    captured = capsys.readouterr()
    assert captured.out.count("nicht unterstützt") == 2
    assert "Keine unterstützte Kategorie" in captured.err
    assert not out.exists()
    assert cli_module.main(["measure", "Slots", "--ui", "en", "--out", str(out)]) == 2
    captured = capsys.readouterr()
    assert "“Slots” is a gambling category" in captured.out
    assert "No supported category" in captured.err
    assert cli_module.main(["watch", "Slots", "--every", "30", "--hours", "1",
                            "--out", str(out)]) == 2
    assert "nicht unterstützt" in capsys.readouterr().out and not out.exists()


def test_cli_report_ignores_gambling_in_old_files(tmp_path, capsys):
    old = tmp_path / "alt.jsonl"
    append_snapshots(old, [snap([300, 2], cat="498566", name="Slots"), snap([40, 3, 1])])
    html = tmp_path / "b.html"
    assert cli_module.main(["report", str(old), "--html", str(html)]) == 0
    printed = capsys.readouterr().out
    assert "1 Messung zu Glücksspiel-Kategorien ignoriert" in printed
    assert "Spiel" in printed and "Slots" not in printed
    assert "Slots" not in html.read_text(encoding="utf-8")


def test_api_has_no_include_gambling_and_ignores_unknown_field():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from streaming_agents.api import app

    snaps = [json.loads(snap([60, 30, 10, 1], cat="498566", name="Slots").model_dump_json()),
             json.loads(snap([60, 30, 10, 1]).model_dump_json())]
    api = TestClient(app)
    for body in ({"snapshots": snaps}, {"snapshots": snaps, "include_gambling": True}):
        data = api.post("/api/v1/content/category-check", json=body).json()
        assert [c["category"] for c in data["categories"]] == ["Spiel"]
        assert "1 Messung zu Glücksspiel-Kategorien ignoriert" in data["notes"][0]
        assert "gambling" not in data["categories"][0]
