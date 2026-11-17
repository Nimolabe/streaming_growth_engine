"""Layout-Baukasten (layouts.html), OBS-Export und Overlay (overlay.html)."""

from __future__ import annotations

import json
from urllib.parse import quote

import pytest
from conftest import collect_errors, set_language, wait_for_auth

SCENES_DE = ["Startet gleich", "Live", "Pause", "Ende"]


def open_layouts(context, base_url, query=""):
    set_language(context, "de")
    page = context.new_page()
    errors = collect_errors(page)
    page.goto(f"{base_url}/layouts.html{query}", wait_until="load")
    wait_for_auth(page)
    return page, errors


def preview_state(page):
    """Name, Stil und Farbe, wie sie das Vorschau-Overlay gerade zeigt."""
    frame = page.frame_locator("#preview")
    frame.locator("#overlay .screen").wait_for(state="attached")
    return {
        "name": frame.locator(".kicker").text_content(),
        "classes": frame.locator("body").get_attribute("class"),
        "accent": frame.locator("body").evaluate("b => b.style.getPropertyValue('--accent')"),
    }


def test_preview_shows_name_theme_and_color(context, base_url):
    page, errors = open_layouts(context, base_url)
    page.fill("#name", "Testkanal")
    page.check('input[name="theme"][value="bold"]', force=True)
    page.click('.swatch[data-color="#ff4655"]')
    page.wait_for_function(
        "() => document.getElementById('preview').src.includes('n=Testkanal')"
        " && document.getElementById('preview').src.includes('c=ff4655')"
        " && document.getElementById('preview').src.includes('t=bold')"
    )
    state = preview_state(page)
    assert state["name"] == "Testkanal"
    assert "theme-bold" in state["classes"] and "scene-start" in state["classes"]
    assert state["accent"] == "#ff4655"
    assert errors == []


def download_collection(page, os_name):
    page.select_option("#os", os_name)
    with page.expect_download() as info:
        page.click("#download")
    download = info.value
    assert download.suggested_filename.endswith(f"-{os_name}.json")
    return json.loads(open(download.path(), encoding="utf-8").read())


@pytest.mark.parametrize("os_name", ["windows", "mac"])
def test_obs_scene_collection(context, base_url, os_name):
    page, errors = open_layouts(context, base_url)
    page.fill("#name", "Testkanal")
    page.wait_for_function("() => document.getElementById('preview').src.includes('n=Testkanal')")
    data = download_collection(page, os_name)

    # Diese Schlüssel prüft OBS beim Import
    for key in ("sources", "name", "current_scene"):
        assert key in data
    assert data["name"] == "SGE Layout – Testkanal"
    assert data["current_scene"] == SCENES_DE[0]
    assert [s["name"] for s in data["scene_order"]] == SCENES_DE

    scenes = [s for s in data["sources"] if s["id"] == "scene"]
    assert [s["name"] for s in scenes] == SCENES_DE

    uuids = {s["uuid"] for s in data["sources"]}
    assert len(uuids) == len(data["sources"]), "UUIDs sind nicht eindeutig"
    for scene in scenes:
        items = scene["settings"]["items"]
        assert items, f"Szene {scene['name']} ist leer"
        for item in items:
            assert item["source_uuid"] in uuids, f"{scene['name']}: {item['name']} zeigt ins Leere"

    by_uuid = {s["uuid"]: s for s in data["sources"]}
    live_items = scenes[1]["settings"]["items"]
    kinds = [by_uuid[i["source_uuid"]]["id"] for i in live_items]
    overlays = [s for s in data["sources"] if s["id"] == "browser_source"]
    assert len(overlays) == 4
    assert all("n=Testkanal" in s["settings"]["url"] for s in overlays)
    assert all(s["settings"]["width"] == 1920 and s["settings"]["height"] == 1080 for s in overlays)

    if os_name == "windows":
        assert kinds == ["game_capture", "dshow_input", "browser_source"]
        cam = live_items[1]
        assert cam["pos"] == {"x": 60, "y": 640} and cam["bounds"] == {"x": 480, "y": 270}
        assert data["DesktopAudioDevice1"]["id"] == "wasapi_output_capture"
        assert data["AuxAudioDevice1"]["id"] == "wasapi_input_capture"
    else:
        assert kinds == ["browser_source"]
        assert "DesktopAudioDevice1" not in data
        assert data["AuxAudioDevice1"]["id"] == "coreaudio_input_capture"
    assert errors == []


def test_share_link_fills_form(context, base_url):
    query = "?t=minimal&c=20c997&l=en&n=Geteilt&ms=Gleich+da&nx=Freitag+20+Uhr&cd=10&tw=anna_tv"
    page, errors = open_layouts(context, base_url, query)
    assert page.is_checked('input[name="theme"][value="minimal"]')
    assert page.input_value("#color") == "#20c997"
    assert page.input_value("#name") == "Geteilt"
    assert page.input_value("#start") == "Gleich da"
    assert page.input_value("#next") == "Freitag 20 Uhr"
    assert page.input_value("#countdown") == "10"
    assert page.input_value("#lang") == "en"
    assert page.input_value("#social-tw") == "anna_tv"
    assert errors == []


def test_share_link_with_invalid_values_falls_back(context, base_url):
    page, errors = open_layouts(context, base_url, "?t=evil&c=zzzzzz&cd=999&tw=%40bad%21%21name")
    assert page.is_checked('input[name="theme"][value="neon"]')
    assert page.input_value("#color") == "#8b7cf6"
    assert page.input_value("#countdown") == "30"
    assert page.input_value("#social-tw") == "badname"
    assert errors == []


@pytest.mark.parametrize(
    ("param", "selector"),
    [
        ("n", ".kicker"),  # Name, höchstens 25 Zeichen
        ("ms", ".title"),  # eigener Text „Startet gleich“
    ],
)
def test_overlay_url_xss_stays_text(context, base_url, param, selector):
    attack = "<img src=x onerror=__x=1>" if param == "n" else '<img src=x onerror="window.__x=1">'
    page = context.new_page()
    errors = collect_errors(page)
    page.goto(f"{base_url}/overlay.html?s=start&{param}={quote(attack)}", wait_until="load")
    page.wait_for_timeout(300)
    assert page.locator(selector).text_content() == attack
    assert page.locator("#overlay img").count() == 0
    assert page.evaluate("window.__x") is None
    assert errors == []


def test_overlay_live_scene_with_socials(context, base_url):
    page = context.new_page()
    errors = collect_errors(page)
    page.goto(f"{base_url}/overlay.html?s=live&n=Test&tw=anna_tv&yt=anna", wait_until="load")
    assert page.locator(".cam-label").text_content() == "Test"
    assert page.locator(".social-text").text_content() == "twitch.tv/anna_tv"
    assert errors == []
