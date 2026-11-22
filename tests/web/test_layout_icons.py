"""Eigene Logos für die Socials am Rahmen (js/layout-icons.js, js/overlay.js).

Die Testbilder unter fixtures/uploads/ sind einfache geometrische Formen, keine Logos.
"""

from __future__ import annotations

import json
from urllib.parse import parse_qs, urlsplit

import pytest
from conftest import (
    collect_errors,
    login,
    profile,
    read_db,
    seed_db,
    set_language,
    wait_for_auth,
)
from test_layouts import ICON_UID, UPLOADS, icon_data_url, real_errors, route_db_icons

PREFIX = "data:image/png;base64,"
EDITOR = "layouts.html?n=Anna&frame=plain&fs=1&tw=anna_tv&yt=anna"


def open_editor(context, base_url, query=EDITOR, data=None, uid=ICON_UID):
    set_language(context, "de")
    # Mit Profil, sonst fragt die Seite (richtig) zuerst nach einem Nutzernamen
    seed = {"profiles": {ICON_UID: profile(ICON_UID, "anna")}, "usernames": {"anna": ICON_UID}}
    seed.update(data or {})
    seed_db(context, seed)
    page = context.new_page()
    errors = collect_errors(page)
    page.goto(f"{base_url}/{query}", wait_until="load")
    wait_for_auth(page)
    if uid:
        login(page, uid, "Anna")
    page.locator("#icon-upload").wait_for(state="visible")
    return page, errors


def row(page, key):
    return page.locator(f'.icon-row[data-social="{key}"]')


def status(page, key):
    return row(page, key).locator(".icon-status").text_content().strip()


def upload(page, key, name=None, files=None):
    page.set_input_files(f'.icon-row[data-social="{key}"] .icon-file', files or str(UPLOADS / name))
    page.wait_for_function(
        """key => { const s = document.querySelector(`.icon-row[data-social="${key}"] .icon-status`);
                    return s && !s.hidden; }""",
        arg=key,
    )


def saved(page, key, uid=ICON_UID):
    return read_db(page).get("socialIcons", {}).get(uid, {}).get(key)


# Prüft ein gespeichertes PNG im Browser: Größe, nur weiße Pixel, Deckkraft an Stellen
MASK_JS = """async (url) => {
  const img = new Image(); img.src = url; await img.decode();
  const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
  const ctx = c.getContext('2d'); ctx.drawImage(img, 0, 0);
  const d = ctx.getImageData(0, 0, c.width, c.height).data;
  let nonWhite = 0, ink = 0;
  for (let i = 0; i < d.length; i += 4) {
    if (d[i + 3] > 0) { ink += 1; if (d[i] < 250 || d[i + 1] < 250 || d[i + 2] < 250) nonWhite += 1; }
  }
  const alpha = (x, y) => d[(y * c.width + x) * 4 + 3];
  return { w: c.width, h: c.height, nonWhite, ink, center: alpha(64, 64), corner: alpha(2, 2) };
}"""


# ---------------------------------------------------------------------------
# Editor: Upload
# ---------------------------------------------------------------------------


def test_upload_needs_login(context, base_url):
    page, errors = open_editor(context, base_url, uid=None)
    assert page.locator(".icon-file").count() == 0
    assert "Melde dich an" in page.locator("#icon-upload .icon-login").text_content()
    page.locator("#icon-upload button", has_text="Anmelden").click()
    assert page.locator("#auth-modal").is_visible()
    assert errors == []


def test_upload_area_only_with_frame_socials(context, base_url):
    page, _ = open_editor(context, base_url)
    # Rechtliche Hinweise stehen da
    hint = page.locator("#icon-upload .cam-hint").text_content()
    assert "Du bist für hochgeladene Bilder selbst verantwortlich" in hint
    assert "Marken ihrer jeweiligen Inhaber" in hint
    # Nur Plattformen mit ausgefülltem Namen bekommen ein Feld
    keys = page.evaluate("[...document.querySelectorAll('.icon-row')].map(r => r.dataset.social)")
    assert keys == ["tw", "yt"]
    page.uncheck("#fs")
    page.locator("#icon-upload").wait_for(state="hidden")


def test_upload_transparent_png_becomes_white_mask(context, base_url):
    page, errors = open_editor(context, base_url)
    upload(page, "tw", "kreis-transparent.png")
    assert status(page, "tw") == "Logo gespeichert ✓"
    value = saved(page, "tw")
    assert value.startswith(PREFIX) and len(value) <= 40000
    mask = page.evaluate(MASK_JS, value)
    assert (mask["w"], mask["h"]) == (128, 128)
    assert mask["nonWhite"] == 0  # einfarbig weiß
    assert mask["center"] == 255 and mask["corner"] == 0  # Alphakanal war die Form
    assert row(page, "tw").locator(".icon-mark").count() == 1  # Vorschau
    assert errors == []


def test_upload_without_transparency_uses_dark_pixels(context, base_url):
    page, errors = open_editor(context, base_url)
    upload(page, "yt", "dreieck-ohne-transparenz.png")
    assert status(page, "yt") == "Logo gespeichert ✓"
    mask = page.evaluate(MASK_JS, saved(page, "yt"))
    assert mask["nonWhite"] == 0
    assert mask["corner"] == 0  # der weiße Hintergrund ist weg
    assert mask["center"] > 200  # das dunkle Dreieck ist die Form
    assert errors == []


def test_upload_webp(context, base_url):
    page, errors = open_editor(context, base_url)
    upload(page, "tw", "quadrat.webp")
    assert status(page, "tw") == "Logo gespeichert ✓"
    assert page.evaluate(MASK_JS, saved(page, "tw"))["center"] == 255
    assert errors == []


def test_svg_with_script_is_not_executed(context, base_url):
    page, errors = open_editor(context, base_url)
    upload(page, "tw", "raute-mit-script.svg")
    assert status(page, "tw") == "Logo gespeichert ✓"
    # Weder <script> noch onload liefen – weder in der Seite noch in der Vorschau
    assert page.evaluate("window.__svgRan") is None
    assert page.frame_locator("#preview").locator("body").evaluate("() => window.__svgRan") is None
    assert page.locator("svg[onload], script:not([src])").count() == 0
    # Gespeichert ist nur ein sauberes PNG
    value = saved(page, "tw")
    assert value.startswith(PREFIX) and "svg" not in value and "script" not in value
    assert page.evaluate(MASK_JS, value)["nonWhite"] == 0
    assert errors == []


@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("leer.png", "Bitte eine Version mit transparentem Hintergrund verwenden."),
        ("vollflaechig.png", "Bitte eine Version mit transparentem Hintergrund verwenden."),
    ],
)
def test_empty_or_full_images_are_rejected(context, base_url, name, message):
    page, errors = open_editor(context, base_url)
    upload(page, "tw", name)
    assert status(page, "tw") == message
    assert saved(page, "tw") is None
    assert errors == []


def test_too_large_file_is_rejected(context, base_url):
    page, errors = open_editor(context, base_url)
    big = {
        "name": "gross.png",
        "mimeType": "image/png",
        "buffer": b"\x89PNG" + b"\0" * (300 * 1024),
    }
    upload(page, "tw", files=big)
    assert status(page, "tw") == "Die Datei ist größer als 300 KB."
    assert saved(page, "tw") is None
    assert errors == []


def test_wrong_file_type_is_rejected(context, base_url):
    page, errors = open_editor(context, base_url)
    upload(
        page, "tw", files={"name": "bild.jpg", "mimeType": "image/jpeg", "buffer": b"\xff\xd8\xff"}
    )
    assert status(page, "tw") == "Nur PNG, SVG oder WebP."
    assert saved(page, "tw") is None
    assert errors == []


def test_remove_logo(context, base_url):
    data = {"socialIcons": {ICON_UID: {"tw": icon_data_url(), "yt": icon_data_url()}}}
    page, errors = open_editor(context, base_url, data=data)
    row(page, "tw").locator(".icon-mark").wait_for()
    row(page, "tw").locator(".icon-remove").click()
    page.wait_for_function(
        "() => document.querySelector('.icon-row[data-social=\"tw\"] .icon-status').textContent.trim() !== ''"
    )
    assert status(page, "tw") == "Logo entfernt."
    assert saved(page, "tw") is None and saved(page, "yt") is not None
    assert row(page, "tw").locator(".icon-mark").count() == 0
    assert errors == []


def test_upload_permission_denied(context, base_url):
    page, _ = open_editor(context, base_url)
    page.evaluate("window.__deny = true")
    upload(page, "tw", "kreis-transparent.png")
    assert status(page, "tw") == (
        "Das Hochladen wird gerade eingerichtet. Bitte versuch es später noch einmal."
    )
    assert row(page, "tw").locator(".icon-status").get_attribute("data-type") == "error"


def test_upload_texts_in_english(context, base_url):
    page, _ = open_editor(context, base_url)
    page.select_option("[data-sge-language] >> nth=0", "en")
    page.wait_for_function("() => document.documentElement.lang === 'en'")
    upload(page, "tw", "leer.png")
    assert status(page, "tw") == "Please use a version with a transparent background."
    hint = page.locator("#icon-upload .cam-hint").text_content()
    assert "You are responsible for any images you upload." in hint
    assert page.locator("#icon-upload .cam-sub").text_content() == "Your own logos (optional)"


# ---------------------------------------------------------------------------
# uid nur in Overlay-Links, nie in Teilen-Link oder Profil
# ---------------------------------------------------------------------------


def query_of(url):
    return parse_qs(urlsplit(url).query)


def test_uid_only_in_overlay_links(context, base_url):
    data = {
        "profiles": {
            ICON_UID: {
                "name": "Anna",
                "username": "anna",
                "usernameLower": "anna",
                "nameLower": "anna",
                "createdAt": 1,
            }
        },
        "usernames": {"anna": ICON_UID},
    }
    page, errors = open_editor(context, base_url, data=data)
    page.check("#fi")
    page.wait_for_function(
        "uid => document.getElementById('preview').src.includes('u=' + uid)", arg=ICON_UID
    )
    links = [i.input_value() for i in page.locator("#link-list input").all()]
    assert links and all(query_of(u)["u"] == [ICON_UID] for u in links)
    export = page.evaluate("SGE_LAYOUT_EXPORT.overlayUrl(SGE_LAYOUT_EXPORT.read(), 'live')")
    assert query_of(export)["u"] == [ICON_UID]

    share = page.evaluate("SGE_LAYOUT_EXPORT.shareUrl(SGE_LAYOUT_EXPORT.read())")
    assert "u" not in query_of(share)

    # „Im Profil zeigen“ speichert keine uid; die Profilseite gibt also auch keine weiter
    page.click("#profile-save")
    page.wait_for_function(
        "() => document.getElementById('profile-status').dataset.type === 'success'"
    )
    params = read_db(page)["layouts"][ICON_UID]["params"]
    assert "u" not in parse_qs(params) and ICON_UID not in params

    # Ohne „Logos anzeigen“ keine uid in den Overlay-Links
    page.uncheck("#fi")
    page.wait_for_function("() => !document.getElementById('preview').src.includes('u=')")
    assert errors == []


def test_profile_take_over_has_no_uid(make_context, base_url):
    data = {
        "profiles": {
            ICON_UID: {
                "name": "Anna",
                "username": "anna",
                "usernameLower": "anna",
                "nameLower": "anna",
                "createdAt": 1,
            }
        },
        "usernames": {"anna": ICON_UID},
        # Selbst ein manipulierter Eintrag mit u= wird beim Anzeigen bereinigt
        "layouts": {
            ICON_UID: {"params": f"frame=plain&fs=1&fi=1&tw=anna&u={ICON_UID}", "updatedAt": 1}
        },
    }
    context = make_context()
    set_language(context, "de")
    seed_db(context, data)
    page = context.new_page()
    page.goto(f"{base_url}/profil.html?u=anna", wait_until="load")
    wait_for_auth(page)
    block = page.locator(".profile-layout")
    block.wait_for(state="attached")
    href = block.locator("a.btn").get_attribute("href")
    src = block.locator("iframe").get_attribute("src")
    assert "u" not in query_of(href) and "u" not in query_of(src)
    assert "fi" in query_of(href)  # die Option selbst bleibt, nur ohne fremde Logos


# ---------------------------------------------------------------------------
# Overlay: Logos über die Datenbank-Adresse
# ---------------------------------------------------------------------------

ITEMS_JS = """[...document.querySelectorAll('.fs-item')].map(e => {
  const icon = e.querySelector('.fs-icon');
  return { key: e.dataset.social, text: e.textContent.trim(),
           mask: icon ? (icon.style.maskImage || icon.style.webkitMaskImage) : null,
           h: icon ? icon.getBoundingClientRect().height : 0 }; })"""


def open_live(context, base_url, extra, icons=None, status=200):
    requested = route_db_icons(context, icons or {}, status=status)
    page = context.new_page()
    page.set_viewport_size({"width": 1920, "height": 1080})
    errors = collect_errors(page)
    page.goto(f"{base_url}/overlay.html?s=live&frame=plain&fs=1&fi=1&{extra}", wait_until="load")
    page.evaluate("document.fonts.ready.then(() => true)")
    return page, errors, requested


def test_overlay_loads_logos_from_database(context, base_url):
    icons = {
        "tw": icon_data_url(),
        "yt": icon_data_url("dreieck-ohne-transparenz.png"),
        "tt": icon_data_url(),
    }
    page, errors, requested = open_live(
        context, base_url, f"tw=luna&yt=luna&tt=luna&u={ICON_UID}", icons
    )
    page.wait_for_function("() => document.querySelectorAll('.fs-icon').length === 3")
    entries = page.evaluate(ITEMS_JS)
    assert [e["text"] for e in entries] == ["/luna", "/@luna", "@luna"]  # ohne Plattformwort
    assert all(e["mask"].startswith('url("data:image/png;base64,') for e in entries)
    assert all(e["h"] >= 24 for e in entries)
    assert (
        page.evaluate("getComputedStyle(document.querySelector('.fs-icon')).backgroundColor")
        == "rgb(255, 255, 255)"
    )
    assert page.locator(".cam-frame img, .cam-frame svg").count() == 0
    assert len(requested) == 1
    assert requested[0].endswith(f"/socialIcons/{ICON_UID}.json")
    assert requested[0].startswith("https://streaminggrowthengine-default-rtdb.")
    assert errors == []


def test_overlay_falls_back_to_text(context, base_url):
    page, errors, _ = open_live(
        context, base_url, f"tw=luna&ig=luna&u={ICON_UID}", {"tw": icon_data_url()}
    )
    page.wait_for_function("() => document.querySelectorAll('.fs-icon').length === 1")
    entries = page.evaluate(ITEMS_JS)
    assert entries[0]["text"] == "/luna" and entries[0]["mask"]
    assert entries[1] == {"key": "ig", "text": "Instagram @luna", "mask": None, "h": 0}
    assert len(entries) == 2  # gemischt: Text-Regel, höchstens 2
    assert errors == []


@pytest.mark.parametrize("status", [404, 500])
def test_overlay_text_when_request_fails(context, base_url, status):
    page, errors, requested = open_live(context, base_url, f"tw=luna&u={ICON_UID}", status=status)
    page.wait_for_timeout(400)
    assert requested
    assert page.evaluate(ITEMS_JS) == [{"key": "tw", "text": "Twitch /luna", "mask": None, "h": 0}]
    assert real_errors(errors) == []


@pytest.mark.parametrize(
    "uid", ["abc", "user-anna-0000000", "a" * 129, "%3Cimg%3E0000000000", "../x000000000"]
)
def test_invalid_uid_is_ignored(context, base_url, uid):
    page, errors, requested = open_live(
        context, base_url, f"tw=luna&u={uid}", {"tw": icon_data_url()}
    )
    page.wait_for_timeout(400)
    assert requested == []
    assert page.evaluate(ITEMS_JS)[0]["text"] == "Twitch /luna"
    assert errors == []


def test_overlay_ignores_values_that_are_not_png_data_urls(context, base_url):
    svg = "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4="
    icons = {
        "tw": svg,
        "yt": "javascript:alert(1)",
        "tt": icon_data_url().replace("base64,", "base64,<b>"),
        "ig": {"nested": True},
    }
    page, errors, _ = open_live(
        context, base_url, f"tw=luna&yt=luna&tt=luna&ig=luna&u={ICON_UID}", icons
    )
    page.wait_for_timeout(400)
    assert page.locator(".fs-icon").count() == 0
    assert page.evaluate(ITEMS_JS)[0]["text"] == "Twitch /luna"
    assert errors == []


def test_database_rules_for_social_icons():
    from pathlib import Path

    rules = json.loads((Path(__file__).resolve().parents[2] / "database.rules.json").read_text())[
        "rules"
    ]
    icons = rules["socialIcons"]
    assert icons[".read"] is True
    user = icons["$uid"]
    assert user[".write"] == "auth != null && auth.uid === $uid"
    assert set(user) == {".write", "tw", "yt", "tt", "ig", "x", "$other"}
    for key in ("tw", "yt", "tt", "ig", "x"):
        rule = user[key][".validate"]
        assert "beginsWith('data:image/png;base64,')" in rule and "length <= 40000" in rule
    assert user["$other"][".validate"] is False
