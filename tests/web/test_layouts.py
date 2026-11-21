"""Layout-Baukasten (layouts.html), OBS-Export und Overlay (overlay.html)."""

from __future__ import annotations

import json
from pathlib import Path
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
    names = [t.strip() for t in page.locator("#cam-choices .cam-name").all_text_contents()]
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
          // Fehlt ein Zeichen, springt die Ersatzschrift ein und die Breite gleicht ihr exakt –
          // und zwar bei JEDER Ersatzschrift. Eine einzelne Übereinstimmung kann Zufall sein
          // (in der CI war z. B. Antons „ö“ genau so breit wie das der Monospace-Schrift).
          return [...chars].filter((ch) =>
            ["monospace", "serif", "sans-serif"].every((fb) => width(`${weight} 80px "${family}", ${fb}`, ch) === width(`${weight} 80px ${fb}`, ch)));
        }""",
        [family, weight],
    )
    assert missing == [], f"{family} {weight}: fehlende Zeichen {missing}"


# ---------------------------------------------------------------------------
# Facecam-Rahmen "schlicht", Socials am Rahmen, Logos
# ---------------------------------------------------------------------------

ICON_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "social-icons"

# Schlichter Rahmen: 6 px Saum, 42 px Leisten, Kamerabild 480 × 270 (js/layout-core.js)
PLAIN_FRAMES = {
    "tl": {"x": 60, "y": 112, "w": 492, "h": 354},
    "tr": {"x": 1368, "y": 112, "w": 492, "h": 354},
    "bl": {"x": 60, "y": 614, "w": 492, "h": 354},
    "br": {"x": 1368, "y": 614, "w": 492, "h": 354},
}
PLAIN_CAMS = {
    k: {"x": v["x"] + 6, "y": v["y"] + 42, "w": 480, "h": 270} for k, v in PLAIN_FRAMES.items()
}

SIZES = {"s": (480, 270), "m": (640, 360), "l": (800, 450)}


def geometry(cam="bl", frame="color", cs="s", fs=False):
    """Erwartete Maße unabhängig von js/layout-core.js nachgerechnet: (Rahmen, Kamerabild)."""
    w, h = SIZES[cs]
    if frame == "plain":
        side, top, bottom = 6, (42 if fs else 6), 42
        ow, oh, group = w + 2 * side, h + top + bottom, h + top + bottom
    else:
        side = top = 0
        ow, oh, group = w, h, h + 58  # Namensschild unter dem farbigen Rahmen
    x = 60 if cam.endswith("l") else 1920 - 60 - ow
    y = 112 if cam.startswith("t") else 968 - group
    outer = {"x": x, "y": y, "w": ow, "h": oh}
    inner = {"x": x + side, "y": y + top, "w": w, "h": h}
    return outer, inner


INNER_JS = """() => { const e = document.querySelector('.cam-frame'); const r = e.getBoundingClientRect();
  const cs = getComputedStyle(e); const px = (v) => parseFloat(cs[v]);
  return { outer: { x: r.left, y: r.top, w: r.width, h: r.height },
           inner: { x: r.left + px('borderLeftWidth'), y: r.top + px('borderTopWidth'),
                    w: r.width - px('borderLeftWidth') - px('borderRightWidth'),
                    h: r.height - px('borderTopWidth') - px('borderBottomWidth') } }; }"""


def route_icons(context, all_present=False):
    """Anfragen an assets/social-icons/ mit den Testformen beantworten (fehlende → 404).

    all_present: jede angefragte .svg mit der Kreis-Testform beantworten."""
    requested = []

    def handle(route):
        name = route.request.url.split("?")[0].rsplit("/", 1)[-1]
        requested.append(name)
        path = ICON_FIXTURES / name
        if all_present and name.endswith(".svg"):
            path = ICON_FIXTURES / "twitch.svg"
        if path.is_file():
            route.fulfill(
                status=200,
                path=str(path),
                content_type="image/png" if path.suffix == ".png" else "image/svg+xml",
            )
        else:
            route.fulfill(status=404, body="")

    context.route("**/assets/social-icons/*", handle)
    return requested


def real_errors(errors):
    """JS-Fehler ohne die Konsolenmeldung des Browsers zu absichtlich fehlenden Icon-Dateien."""
    return [e for e in errors if "Failed to load resource" not in e]


@pytest.mark.parametrize("theme", ["neon", "bold"])
@pytest.mark.parametrize("cam", ["tl", "tr", "bl", "br"])
def test_plain_frame_in_overlay(context, base_url, cam, theme):
    query = f"s=live&t={theme}&cam={cam}&frame=plain&fs=1&n=MatrixxJJ&tw=a&yt=b&ig=c"
    page, errors = open_overlay(context, base_url, query)
    box = page.evaluate(INNER_JS)
    assert box["outer"] == PLAIN_FRAMES[cam]
    assert box["inner"] == PLAIN_CAMS[cam]  # genau die Fläche, auf die der Export die Webcam legt
    for sel in (".cam-frame", ".cam-bar-top", ".cam-bar-bottom", ".cam-strokes", ".cam-ticks"):
        r = page.evaluate(RECT_JS, sel)
        assert r["l"] >= 0 and r["t"] >= 0 and r["r"] <= 1920 and r["b"] <= 1080, (sel, r)
    # Kanalname nur als Text in der unteren Leiste, kein Schild, kein Symbol davor
    assert page.locator(".cam-bar-bottom .cam-name").text_content() == "MatrixxJJ"
    assert page.locator(".cam-label").count() == 0
    assert (
        page.locator(".cam-bar-bottom img, .cam-bar-bottom svg, .cam-bar-bottom .fs-icon").count()
        == 0
    )
    assert errors == []


FRAME_VARIANTS = [("color", False), ("plain", False), ("plain", True)]


@pytest.mark.parametrize(
    ("frame", "fs"), FRAME_VARIANTS, ids=["farbig", "schlicht", "schlicht-socials"]
)
@pytest.mark.parametrize("cs", ["s", "m", "l"])
@pytest.mark.parametrize("cam", ["tl", "tr", "bl", "br"])
def test_obs_export_matches_camera_area(context, base_url, cam, cs, frame, fs):
    query = f"?n=Testkanal&frame={frame}&cam={cam}&cs={cs}&tw=luna&yt=luna" + (
        "&fs=1" if fs else ""
    )
    page, errors = open_layouts(context, base_url, query)
    data = download_collection(page, "windows")
    by_uuid = {s["uuid"]: s for s in data["sources"]}
    live = [s for s in data["sources"] if s["id"] == "scene"][1]
    cam_item = next(
        i for i in live["settings"]["items"] if by_uuid[i["source_uuid"]]["id"] == "dshow_input"
    )
    outer, inner = geometry(cam, frame, cs, fs)
    assert cam_item["pos"] == {"x": inner["x"], "y": inner["y"]}
    assert cam_item["bounds"] == {"x": inner["w"], "y": inner["h"]}

    # Im Overlay liegt die Kamerafläche genau dort, alles ist im Bild
    overlay = next(
        s
        for s in data["sources"]
        if s["id"] == "browser_source" and "s=live" in s["settings"]["url"]
    )
    ov, ov_errors = open_overlay(context, base_url, overlay["settings"]["url"].split("?", 1)[1])
    box = ov.evaluate(INNER_JS)
    assert box["outer"] == outer
    assert box["inner" if frame == "plain" else "outer"] == inner
    groups = [".cam-frame", ".cam-label", ".cam-bar-top", ".cam-bar-bottom", ".social-badge"]
    rects = {sel: ov.evaluate(RECT_JS, sel) for sel in groups}
    for sel, r in rects.items():
        if r:
            assert r["l"] >= 0 and r["t"] >= 0 and r["r"] <= 1920 and r["b"] <= 1080, (sel, r)
    # Der Social-Hinweis in der Ecke überlappt die Facecam nicht (auch nicht bei „groß“)
    badge = rects[".social-badge"]
    assert (badge is None) == (frame == "plain" and fs)
    if badge:
        for sel in (".cam-frame", ".cam-label", ".cam-bar-bottom"):
            if rects[sel]:
                assert not overlaps(badge, rects[sel]), (sel, rects[sel], badge)
    assert errors == [] and ov_errors == []


def test_plain_frame_without_socials_has_thin_top(context, base_url):
    page, errors = open_overlay(context, base_url, "s=live&frame=plain&cam=tl&n=Luna&tw=luna")
    assert page.locator(".cam-bar-top").count() == 0
    widths = page.evaluate(
        "(() => { const cs = getComputedStyle(document.querySelector('.cam-frame'));"
        " return [cs.borderTopWidth, cs.borderLeftWidth, cs.borderBottomWidth]; })()"
    )
    assert widths == ["6px", "6px", "42px"]  # oben so schmal wie der Seitensaum
    outer, inner = geometry("tl", "plain", "s", False)
    assert page.evaluate(INNER_JS) == {"outer": outer, "inner": inner}
    assert errors == []


@pytest.mark.parametrize("query", ["cs=xl", "cs=M", "cs=", "cs=constructor"])
def test_invalid_size_uses_small(context, base_url, query):
    page, errors = open_overlay(context, base_url, f"s=live&n=Alt&{query}")
    outer, _ = geometry("bl", "color", "s")
    assert page.evaluate(INNER_JS)["outer"] == outer  # 60/640, 480×270 wie bisher
    assert errors == []


def test_frame_socials_as_text_and_rotation(context, base_url):
    page = context.new_page()
    page.set_viewport_size({"width": 1920, "height": 1080})
    errors = collect_errors(page)
    page.clock.install()
    page.goto(
        f"{base_url}/overlay.html?s=live&frame=plain&fs=1&n=Luna"
        "&tw=lunaplays&yt=luna&tt=luna_tt&ig=luna_ig&x=luna_x",
        wait_until="load",
    )
    page.evaluate("document.fonts.ready.then(() => true)")

    def items():
        return [t.strip() for t in page.locator(".fs-item").all_text_contents()]

    # Als Text höchstens 2 Einträge gleichzeitig
    assert items() == ["Twitch /lunaplays", "YouTube /@luna"]
    # Nur Text: keine Bilder, keine Icons; kein Hinweis in der Ecke
    assert page.locator(".cam-frame img, .cam-frame svg, .fs-icon").count() == 0
    assert page.locator(".social-badge").count() == 0

    page.clock.run_for(9000)  # nach 8 s blendet die nächste Gruppe ein
    assert items() == ["TikTok @luna_tt", "Instagram @luna_ig"]
    page.clock.run_for(8000)
    assert items() == ["X @luna_x"]
    page.clock.run_for(8000)
    assert items() == ["Twitch /lunaplays", "YouTube /@luna"]
    assert errors == []


@pytest.mark.parametrize("theme", ["neon", "minimal", "bold"])
@pytest.mark.parametrize("fi", [False, True], ids=["text", "logos"])
def test_handles_up_to_15_chars_are_never_shortened(context, base_url, theme, fi):
    if fi:
        route_icons(context, all_present=True)
    handles = {
        "tw": "luna_plays_1234",
        "yt": "MaxMustermannTV",
        "ig": "konsolenkoenig_",
        "tt": "WWWWWWWWWWWWWWW",
        "x": "streamer_2026xx",
    }
    query = "&".join(f"{k}={v}" for k, v in handles.items())
    page = context.new_page()
    page.set_viewport_size({"width": 1920, "height": 1080})
    errors = collect_errors(page)
    page.clock.install()
    page.goto(
        f"{base_url}/overlay.html?s=live&t={theme}&frame=plain&fs=1{'&fi=1' if fi else ''}&{query}",
        wait_until="load",
    )
    page.evaluate("document.fonts.ready.then(() => true)")
    if fi:
        page.wait_for_function("() => document.querySelectorAll('.fs-icon').length > 0")
    seen = []
    for _ in range(6):
        texts = page.evaluate(
            "[...document.querySelectorAll('.fs-text')].map(e => [e.textContent, e.scrollWidth <= e.clientWidth])"
        )
        assert all(full for _, full in texts), texts  # nichts mit „…“ gekürzt
        assert len(texts) <= (3 if fi else 2)
        seen += [t for t, _ in texts]
        page.clock.run_for(8700)
    for handle in handles.values():
        assert any(handle in t for t in seen), (handle, seen)
    assert real_errors(errors) == []


def test_long_social_names_are_shortened(context, base_url):
    page, errors = open_overlay(context, base_url, f"s=live&frame=plain&fs=1&tw={'a' * 30}&yt=b")
    bar = page.evaluate(RECT_JS, ".cam-bar-top")
    count = page.locator(".fs-item").count()
    assert count == 2
    for i in range(count):
        r = page.evaluate(
            f"() => {{ const b = document.querySelectorAll('.fs-item')[{i}].getBoundingClientRect();"
            " return { l: b.left, r: b.right }; }"
        )
        assert bar["l"] <= r["l"] and r["r"] <= bar["r"]
    clipped = page.evaluate(
        "[...document.querySelectorAll('.fs-text')].map(e => e.scrollWidth > e.clientWidth)"
    )
    assert clipped == [True, False]  # nur der Name über 15 Zeichen wird mit „…“ gekürzt
    assert (
        page.evaluate("getComputedStyle(document.querySelector('.fs-text')).textOverflow")
        == "ellipsis"
    )
    assert errors == []


@pytest.mark.parametrize(
    "query",
    [
        "s=live&n=Alt&tw=a",  # alter Link ohne frame
        "s=live&n=Alt&tw=a&frame=zz",
        "s=live&n=Alt&tw=a&frame=PLAIN",
        "s=live&n=Alt&tw=a&fs=1",  # Socials am Rahmen nur beim schlichten Rahmen
    ],
)
def test_invalid_frame_or_old_link_keeps_colored_frame(context, base_url, query):
    page, errors = open_overlay(context, base_url, query)
    assert page.evaluate("document.body.classList.contains('frame-color')")
    assert page.locator(".cam-frame.is-plain, .fs-row").count() == 0
    assert page.locator(".cam-label").text_content() == "Alt"
    assert page.locator(".social-badge").count() == 1
    assert errors == []


def test_plain_frame_without_frame_socials_keeps_corner_hint(context, base_url):
    page, errors = open_overlay(context, base_url, "s=live&frame=plain&n=Luna&tw=luna")
    assert page.locator(".fs-row").count() == 0
    assert page.locator(".social-text").text_content() == "twitch.tv/luna"
    assert errors == []


ITEMS_JS = """[...document.querySelectorAll('.fs-item')].map(e => {
  const icon = e.querySelector('.fs-icon');
  return { key: e.dataset.social, text: e.textContent.trim(),
           mask: icon ? (icon.style.maskImage || icon.style.webkitMaskImage) : null }; })"""


def test_logos_from_files_svg_then_png(context, base_url):
    requested = route_icons(context)
    page = context.new_page()
    page.set_viewport_size({"width": 1920, "height": 1080})
    errors = collect_errors(page)
    page.goto(
        f"{base_url}/overlay.html?s=live&frame=plain&fs=1&fi=1&tw=luna&yt=luna&tt=luna",
        wait_until="load",
    )
    page.wait_for_function("() => document.querySelectorAll('.fs-icon').length === 3")
    entries = page.evaluate(ITEMS_JS)
    # Mit Logos: 3 Einträge, nur Logo + Name, kein Plattformwort
    assert [e["text"] for e in entries] == ["/luna", "/@luna", "@luna"]
    assert "assets/social-icons/twitch.svg" in entries[0]["mask"]
    assert "assets/social-icons/youtube.svg" in entries[1]["mask"]
    assert "assets/social-icons/tiktok.png" in entries[2]["mask"]  # kein .svg → .png
    assert page.locator(".cam-frame img, .cam-frame svg").count() == 0
    assert "tiktok.svg" in requested and "tiktok.png" in requested
    assert real_errors(errors) == []


def test_missing_logo_falls_back_to_text(context, base_url):
    route_icons(context)
    page = context.new_page()
    page.set_viewport_size({"width": 1920, "height": 1080})
    errors = collect_errors(page)
    page.goto(
        f"{base_url}/overlay.html?s=live&frame=plain&fs=1&fi=1&tw=luna&ig=luna",
        wait_until="load",
    )
    page.wait_for_function("() => document.querySelectorAll('.fs-icon').length === 1")
    page.wait_for_timeout(300)  # instagram.svg und .png sind beide nicht da
    entries = page.evaluate(ITEMS_JS)
    assert entries[0]["text"] == "/luna" and "twitch.svg" in entries[0]["mask"]
    # instagram fehlt → Textformat, kein leerer Platz; gemischt gilt die Text-Regel (≤ 2)
    assert entries[1] == {"key": "ig", "text": "Instagram @luna", "mask": None}
    assert len(entries) == 2
    assert real_errors(errors) == []


def test_no_logos_when_option_is_off(context, base_url):
    requested = route_icons(context)
    page, errors = open_overlay(context, base_url, "s=live&frame=plain&fs=1&tw=luna&yt=luna")
    page.wait_for_timeout(300)
    assert page.locator(".fs-icon, .cam-frame img").count() == 0
    assert requested == []  # Logo-Dateien werden gar nicht erst geladen
    assert errors == []


def test_editor_frame_options_preview_and_share(context, base_url):
    page, errors = open_layouts(context, base_url, "?n=Luna&cam=tr&tw=luna")
    assert page.is_checked('input[name="frame"][value="color"]')
    assert not page.is_checked("#fs") and not page.is_checked("#fi")
    page.click('[data-scene="live"]')
    page.check('input[name="frame"][value="plain"]', force=True)
    page.check("#fs")
    page.check("#fi")
    page.wait_for_function("() => document.getElementById('preview').src.includes('frame=plain')")
    src = page.get_attribute("#preview", "src")
    assert "fs=1" in src and "fi=1" in src
    share = page.evaluate("SGE_LAYOUT_EXPORT.shareUrl(SGE_LAYOUT_EXPORT.read())")
    assert "frame=plain" in share and "fs=1" in share and "fi=1" in share

    # Platzhalter „Webcam“ in der Vorschau liegt auf dem Kamerabild des schlichten Rahmens
    # Innenfläche der Bühne (ohne ihren 1-px-Rand), darin liegt der Platzhalter
    stage = page.evaluate(
        """() => { const s = document.getElementById('preview-stage'); const r = s.getBoundingClientRect();
          return { l: r.left + s.clientLeft, t: r.top + s.clientTop, w: s.clientWidth }; }"""
    )
    cam = page.evaluate(RECT_JS, ".preview-cam")
    scale = stage["w"] / 1920
    expected = PLAIN_CAMS["tr"]
    assert abs((cam["l"] - stage["l"]) / scale - expected["x"]) < 1.5
    assert abs((cam["t"] - stage["t"]) / scale - expected["y"]) < 1.5
    assert abs((cam["r"] - cam["l"]) / scale - expected["w"]) < 1.5

    # Geteilter Link füllt die Optionen wieder ein
    page2, _ = open_layouts(context, base_url, "?frame=plain&fs=1&fi=1")
    assert page2.is_checked('input[name="frame"][value="plain"]')
    assert page2.is_checked("#fs") and page2.is_checked("#fi")
    # Die Vorschau fragt die (noch nicht abgelegten) Logo-Dateien an → nur 404-Meldungen erlaubt
    assert real_errors(errors) == []


def test_frame_options_translated(context, base_url):
    page, _ = open_layouts(context, base_url)
    page.select_option("[data-sge-language] >> nth=0", "en")
    page.wait_for_function("() => document.documentElement.lang === 'en'")
    names = [t.strip() for t in page.locator("#frame-choices .cam-name").all_text_contents()]
    assert names == ["Colored", "Plain"]
    hints = [t.strip() for t in page.locator(".check-field span, .check-hint").all_text_contents()]
    assert "Socials on the frame" in hints and "Show logos" in hints
    assert "Logos appear once the official files are placed in assets/social-icons/." in hints


def test_editor_size_choice_preview_and_share(context, base_url):
    page, errors = open_layouts(context, base_url, "?n=Luna&cam=br")
    assert page.is_checked('input[name="cs"][value="s"]')
    page.click('[data-scene="live"]')
    page.check('input[name="cs"][value="l"]', force=True)
    page.wait_for_function("() => document.getElementById('preview').src.includes('cs=l')")
    stage = page.evaluate(
        """() => { const s = document.getElementById('preview-stage'); const r = s.getBoundingClientRect();
          return { l: r.left + s.clientLeft, t: r.top + s.clientTop, w: s.clientWidth }; }"""
    )
    cam = page.evaluate(RECT_JS, ".preview-cam")
    scale = stage["w"] / 1920
    _, inner = geometry("br", "color", "l")
    assert abs((cam["l"] - stage["l"]) / scale - inner["x"]) < 1.5
    assert abs((cam["r"] - cam["l"]) / scale - inner["w"]) < 1.5
    assert "cs=l" in page.evaluate("SGE_LAYOUT_EXPORT.shareUrl(SGE_LAYOUT_EXPORT.read())")
    page2, _ = open_layouts(context, base_url, "?cs=m")
    assert page2.is_checked('input[name="cs"][value="m"]')
    page3, _ = open_layouts(context, base_url, "?cs=riesig")
    assert page3.is_checked('input[name="cs"][value="s"]')
    assert real_errors(errors) == []


def test_editor_frame_socials_turn_on_logos(context, base_url):
    page, errors = open_layouts(context, base_url, "?n=Luna&frame=plain&tw=luna")
    assert not page.is_checked("#fs") and not page.is_checked("#fi")
    page.check("#fs")
    assert page.is_checked("#fi")  # neue Designs: Logos mit angehakt
    page.wait_for_function("() => document.getElementById('preview').src.includes('fi=1')")

    # Wer die Logos selbst abwählt, behält das
    page.uncheck("#fi")
    page.uncheck("#fs")
    page.check("#fs")
    assert not page.is_checked("#fi")

    # Ein alter Link mit Socials am Rahmen, aber ohne Logos, bleibt ohne Logos
    page2, _ = open_layouts(context, base_url, "?frame=plain&fs=1")
    assert page2.is_checked("#fs") and not page2.is_checked("#fi")
    assert real_errors(errors) == []


def test_size_choice_translated(context, base_url):
    page, _ = open_layouts(context, base_url)
    page.select_option("[data-sge-language] >> nth=0", "en")
    page.wait_for_function("() => document.documentElement.lang === 'en'")
    names = [t.strip() for t in page.locator("#size-choices span").all_text_contents()]
    assert names == ["Small", "Medium", "Large"]
