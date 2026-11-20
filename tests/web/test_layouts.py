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


# ---------------------------------------------------------------------------
# Layouts v2: Facecam-Position, eigene Schriften
# ---------------------------------------------------------------------------

# Erwartete Webcam-Rahmen (außen) im 1920 × 1080-Bild, siehe js/layout-core.js
CAM_RECTS = {
    "tl": {"x": 60, "y": 112, "w": 480, "h": 270},
    "tr": {"x": 1380, "y": 112, "w": 480, "h": 270},
    "bl": {"x": 60, "y": 640, "w": 480, "h": 270},
    "br": {"x": 1380, "y": 640, "w": 480, "h": 270},
}
RECT_JS = """sel => { const e = document.querySelector(sel); if (!e) return null;
  const r = e.getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom }; }"""


def overlaps(a, b):
    return a["l"] < b["r"] and b["l"] < a["r"] and a["t"] < b["b"] and b["t"] < a["b"]


def open_overlay(context, base_url, query):
    page = context.new_page()
    page.set_viewport_size({"width": 1920, "height": 1080})
    errors = collect_errors(page)
    page.goto(f"{base_url}/overlay.html?{query}", wait_until="load")
    page.evaluate("document.fonts.ready.then(() => true)")
    return page, errors


@pytest.mark.parametrize("theme", ["neon", "minimal", "bold"])
@pytest.mark.parametrize("cam", ["tl", "tr", "bl", "br"])
def test_facecam_position_in_overlay(context, base_url, cam, theme):
    long_handle = "a" * 30
    query = (
        f"s=live&t={theme}&cam={cam}&n={quote('KonsolenKönigin_Grüße')}&tw={long_handle}&yt=luna"
    )
    page, errors = open_overlay(context, base_url, query)
    frame = page.evaluate(RECT_JS, ".cam-frame")
    label = page.evaluate(RECT_JS, ".cam-label")
    badge = page.evaluate(RECT_JS, ".social-badge")
    expected = CAM_RECTS[cam]

    assert frame == {
        "l": expected["x"],
        "t": expected["y"],
        "r": expected["x"] + expected["w"],
        "b": expected["y"] + expected["h"],
    }
    for box in (frame, label, badge):
        assert box["l"] >= 0 and box["t"] >= 0 and box["r"] <= 1920 and box["b"] <= 1080, box
    # Namensschild hängt unter dem Rahmen und schließt bündig mit seiner äußeren Seite ab
    assert label["t"] == frame["b"]
    if cam.endswith("l"):
        assert label["l"] == frame["l"]
    else:
        assert label["r"] == frame["r"]
    # Der Social-Hinweis weicht der Facecam aus
    assert not overlaps(badge, frame) and not overlaps(badge, label)
    assert (badge["l"] < 960) == (cam == "br")
    assert errors == []


@pytest.mark.parametrize("cam", ["tl", "tr", "bl", "br"])
def test_obs_export_uses_facecam_position(context, base_url, cam):
    page, errors = open_layouts(context, base_url, "?n=Testkanal")
    page.check(f'input[name="cam"][value="{cam}"]', force=True)
    data = download_collection(page, "windows")
    by_uuid = {s["uuid"]: s for s in data["sources"]}
    live = [s for s in data["sources"] if s["id"] == "scene"][1]
    cam_item = next(
        i for i in live["settings"]["items"] if by_uuid[i["source_uuid"]]["id"] == "dshow_input"
    )
    expected = CAM_RECTS[cam]
    assert cam_item["pos"] == {"x": expected["x"], "y": expected["y"]}
    assert cam_item["bounds"] == {"x": expected["w"], "y": expected["h"]}
    # Das Live-Overlay im Export zeigt den Rahmen an derselben Stelle
    overlay = next(
        s
        for s in data["sources"]
        if s["id"] == "browser_source" and "s=live" in s["settings"]["url"]
    )
    assert ("cam=" in overlay["settings"]["url"]) == (cam != "bl")
    assert errors == []


@pytest.mark.parametrize(
    "query", ["s=live&n=Alt", "s=live&n=Alt&cam=zz", "s=live&n=Alt&cam=BR", "s=live&cam="]
)
def test_invalid_or_missing_cam_uses_default(context, base_url, query):
    page, errors = open_overlay(context, base_url, query)
    frame = page.evaluate(RECT_JS, ".cam-frame")
    assert (frame["l"], frame["t"]) == (60, 640)
    assert page.evaluate("document.body.classList.contains('cam-bl')")
    assert errors == []


def test_editor_cam_choice_and_share_link(context, base_url):
    page, errors = open_layouts(context, base_url, "?n=Alt&cam=zz")
    assert page.is_checked('input[name="cam"][value="bl"]')
    page.wait_for_function("() => document.getElementById('preview').src.includes('n=Alt')")
    assert "cam=" not in page.get_attribute("#preview", "src")  # Standard steht nicht in der URL

    page.click('[data-scene="live"]')
    page.check('input[name="cam"][value="tr"]', force=True)
    page.wait_for_function("() => document.getElementById('preview').src.includes('cam=tr')")
    assert page.get_attribute("#preview-stage", "data-cam") == "tr"
    share = page.evaluate("SGE_LAYOUT_EXPORT.shareUrl(SGE_LAYOUT_EXPORT.read())")
    assert "cam=tr" in share

    # Ein geteilter Link mit cam füllt das Formular
    page2, _ = open_layouts(context, base_url, "?cam=br")
    assert page2.is_checked('input[name="cam"][value="br"]')
    assert errors == []


def test_cam_choice_translated(context, base_url):
    page, _ = open_layouts(context, base_url)
    page.select_option("[data-sge-language] >> nth=0", "en")
    page.wait_for_function("() => document.documentElement.lang === 'en'")
    names = [t.strip() for t in page.locator(".cam-name").all_text_contents()]
    assert names == ["Top left", "Top right", "Bottom left", "Bottom right"]
    assert page.locator("#cam-choices").locator("xpath=..").locator("legend").text_content() == (
        "5. Facecam position"
    )


THEME_FONTS = {
    "neon": ("SGE Oxanium", "700"),
    "minimal": ("SGE Sora", "600"),
    "bold": ("SGE Anton", "400"),
}


@pytest.mark.parametrize("theme", ["neon", "minimal", "bold"])
def test_self_hosted_fonts_are_loaded(context, base_url, theme):
    requests = []
    page = context.new_page()
    page.set_viewport_size({"width": 1920, "height": 1080})
    page.on("request", lambda r: requests.append(r.url))
    responses = {}
    page.on("response", lambda r: responses.__setitem__(r.url, r.status))
    page.goto(f"{base_url}/overlay.html?s=start&t={theme}&n=LunaPlays&tw=luna", wait_until="load")
    page.evaluate("document.fonts.ready.then(() => true)")

    faces = page.evaluate(
        "[...document.fonts].map(f => ({ family: f.family.replace(/\"/g, ''), weight: f.weight, status: f.status }))"
    )
    loaded = {(f["family"], f["weight"]) for f in faces if f["status"] == "loaded"}
    assert THEME_FONTS[theme] in loaded, faces
    assert any(family == "SGE Manrope" for family, _ in loaded), faces

    font_responses = {u: s for u, s in responses.items() if "/fonts/" in u}
    assert font_responses and all(s == 200 for s in font_responses.values()), font_responses
    assert not [u for u in requests if "fonts.googleapis.com" in u or "fonts.gstatic.com" in u]


@pytest.mark.parametrize(
    ("family", "weight"),
    [
        ("SGE Oxanium", "700"),
        ("SGE Sora", "600"),
        ("SGE Anton", "400"),
        ("SGE Manrope", "400"),
        ("SGE Manrope", "600"),
        ("SGE Manrope", "700"),
    ],
)
def test_fonts_have_german_characters(context, base_url, family, weight):
    page, _ = open_overlay(context, base_url, "s=start")
    missing = page.evaluate(
        """async ([family, weight]) => {
          const chars = "äöüÄÖÜß„“–";
          await document.fonts.load(`${weight} 80px "${family}"`, chars);
          const ctx = document.createElement("canvas").getContext("2d");
          const width = (font, ch) => { ctx.font = font; return ctx.measureText(ch).width; };
          // Fehlt ein Zeichen, springt die Ersatzschrift ein und die Breite gleicht ihr exakt.
          return [...chars].filter((ch) =>
            ["monospace", "serif"].some((fb) => width(`${weight} 80px "${family}", ${fb}`, ch) === width(`${weight} 80px ${fb}`, ch)));
        }""",
        [family, weight],
    )
    assert missing == [], f"{family} {weight}: fehlende Zeichen {missing}"
