"""Website-Version des Content Strategist: Export, Fixtures und Parität Python ↔ JavaScript."""
import json
import shutil
import subprocess

import pytest
import strategist_parity

from streaming_agents.content_strategist import web_export
from streaming_agents.content_strategist.cli import main as cli_main

ROOT = strategist_parity.ROOT
EXPORT = ROOT / "data" / "content-strategist.json"
FIXTURES = strategist_parity.FIXTURE_PATH
HINT = ("Export vergessen? In agents/ ausführen: python -m streaming_agents.content_strategist "
        "export-web --out ../data/content-strategist.json && python tests/strategist_parity.py")


def test_export_file_matches_current_code():
    assert EXPORT.is_file(), HINT
    assert EXPORT.read_text(encoding="utf-8") == web_export.render(), HINT


def test_export_is_small_complete_and_checksummed():
    assert EXPORT.stat().st_size < 300 * 1024
    data = json.loads(EXPORT.read_text(encoding="utf-8"))
    body = {key: value for key, value in data.items() if key != "sha256"}
    assert data["sha256"] == web_export.checksum(body)
    assert data["format"] == 1 and data["version"] == "content-strategist-a1"
    assert len(data["formats"]) == 55 and len(data["genres"]["labels"]) == 9
    assert {"mood_titles", "stream_titles", "clip_titles", "ranked_goal_mood", "rank_journey",
            "fills", "dayparts"} <= set(data["titles"])
    assert "_general" in data["titles"]["mood_titles"]
    # Glücksspiel-Liste (Fallstrick 15) in normalisierter Form
    assert {"slots", "virtual casino", "poker", "texas hold em"} <= set(data["gambling"]["names"])
    assert "{name}" in data["gambling"]["rejection"]["de"]
    # Kein Kategorie-Check und keine Zugangsdaten im Browser-Export
    text = EXPORT.read_text(encoding="utf-8")
    assert "TWITCH_CLIENT" not in text and "helix" not in text and "id.twitch.tv" not in text


def test_export_web_cli(tmp_path, capsys):
    target = tmp_path / "data" / "export.json"
    assert cli_main(["export-web", "--out", str(target)]) == 0
    assert target.read_text(encoding="utf-8") == web_export.render()
    assert "KB" in capsys.readouterr().out


def test_parity_fixtures_match_current_code():
    assert FIXTURES.is_file(), HINT
    assert FIXTURES.read_text(encoding="utf-8") == strategist_parity.render(), HINT


def test_parity_fixtures_cover_the_required_profiles():
    data = json.loads(FIXTURES.read_text(encoding="utf-8"))
    names = [case["name"] for case in data["cases"]]
    assert len(names) == len(set(names)) and len(names) >= 60
    assert sum(name.startswith("beispiel-") for name in names) == 54   # 9 Genres × 3 × DE/EN
    assert sum(name.startswith("simulation-") for name in names) == 30
    by_name = {case["name"]: case["expected"] for case in data["cases"]}
    assert by_name["gluecksspiel-allein"]["error"]["type"] == "plan"
    mixed = by_name["gluecksspiel-gemischt"]["plan"]
    assert [game["name"] for game in mixed["games"]] == ["Valorant"]
    assert mixed["notes"][0].startswith("„Slots“ ist eine Glücksspiel-Kategorie.")
    assert all("python -m" not in note for case in data["cases"] if "plan" in case["expected"]
               for note in case["expected"]["plan"]["notes"])
    languages = {case["expected"]["plan"]["language"] for case in data["cases"]
                 if "plan" in case["expected"]}
    assert languages == {"de", "en"}


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js nicht installiert")
def test_javascript_core_matches_python_in_node():
    result = subprocess.run(["node", str(ROOT / "tests" / "web" / "strategist_parity.mjs")],
                            capture_output=True, text=True, timeout=120, check=False)
    assert result.stdout, result.stderr
    report = json.loads(result.stdout.splitlines()[-1])
    assert report["dataMatches"], "Fixtures passen nicht zum Export – " + HINT
    assert report["casefold"] == []
    first = report["mismatches"][:1]
    assert report["mismatches"] == [], first
    assert report["total"] >= 60 and result.returncode == 0
