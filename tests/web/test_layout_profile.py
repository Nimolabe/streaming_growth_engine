"""Layout im Profil zeigen (js/layouts-share.js, js/layout-profile.js, js/profil.js)."""

from __future__ import annotations

from urllib.parse import parse_qs, urlsplit

from conftest import (
    collect_errors,
    login,
    profile,
    read_db,
    seed_db,
    set_language,
    wait_for_auth,
)

OWNER = "user-anna"
VIEWER = "user-ben"
ALLOWED_KEYS = {"t", "c", "l", "n", "ms", "mp", "me", "nx", "cd", "tw", "yt", "tt", "ig", "x"}


def base_data():
    return {
        "profiles": {OWNER: profile(OWNER, "anna"), VIEWER: profile(VIEWER, "ben")},
        "usernames": {"anna": OWNER, "ben": VIEWER},
    }


def open_page(context, base_url, path, data):
    set_language(context, "de")
    seed_db(context, data)
    page = context.new_page()
    errors = collect_errors(page)
    page.goto(f"{base_url}/{path}", wait_until="load")
    wait_for_auth(page)
    return page, errors


def layout_block(page):
    block = page.locator(".profile-layout")
    block.wait_for(state="attached")
    frame = block.locator("iframe")
    link = block.locator("a.btn")
    return frame.get_attribute("src"), link.get_attribute("href"), link.text_content().strip()


def query_of(url):
    return {k: v[0] for k, v in parse_qs(urlsplit(url).query).items()}


def test_show_in_profile_saves_layout(context, base_url):
    page, errors = open_page(context, base_url, "layouts.html", base_data())
    login(page, OWNER, "Anna")
    page.fill("#name", "Anna live")
    page.check('input[name="theme"][value="minimal"]', force=True)
    page.wait_for_function("() => document.getElementById('preview').src.includes('n=Anna+live')")

    page.click("#profile-save")
    page.wait_for_function(
        "() => document.getElementById('profile-status').dataset.type === 'success'"
    )
    saved = read_db(page)["layouts"][OWNER]
    assert set(saved) == {"params", "updatedAt"}
    assert isinstance(saved["updatedAt"], int)
    assert query_of("?" + saved["params"]) == {"t": "minimal", "n": "Anna live"}
    assert page.locator("#profile-save").text_content() == "Im Profil aktualisieren"
    assert page.locator("#profile-remove").is_visible()

    page.click("#profile-remove")
    page.locator("#profile-remove").wait_for(state="hidden")
    assert "layouts" not in read_db(page)
    assert errors == []


def test_show_in_profile_logged_out_opens_login(context, base_url):
    page, _ = open_page(context, base_url, "layouts.html", base_data())
    page.click("#profile-save")
    assert page.locator("#auth-modal").is_visible()
    assert "layouts" not in read_db(page)


def test_show_in_profile_permission_denied(context, base_url):
    page, _ = open_page(context, base_url, "layouts.html", base_data())
    login(page, OWNER)
    page.evaluate("window.__deny = true")
    page.click("#profile-save")
    page.wait_for_function(
        "() => document.getElementById('profile-status').dataset.type === 'error'"
    )
    assert page.locator("#profile-status").text_content().strip() == (
        "Das Teilen im Profil wird gerade eingerichtet. Bitte versuch es später noch einmal."
    )


def test_foreign_profile_shows_preview_and_take_over(make_context, base_url):
    data = base_data()
    data["layouts"] = {OWNER: {"params": "t=bold&c=ff4655&n=Anna+live", "updatedAt": 1}}

    # Angemeldet als jemand anderes
    page, errors = open_page(make_context(), base_url, "profil.html?u=anna", data)
    login(page, VIEWER, "Ben")
    frame_src, href, label = layout_block(page)
    assert label == "Design übernehmen"
    assert href == "layouts.html?t=bold&c=ff4655&n=Anna+live"
    assert frame_src == "overlay.html?s=start&t=bold&c=ff4655&n=Anna+live"
    assert errors == []

    # Abgemeldet sieht man dasselbe
    page, errors = open_page(make_context(), base_url, "profil.html?u=anna", data)
    _, _, label = layout_block(page)
    assert label == "Design übernehmen"

    # „Design übernehmen“ füllt den Baukasten
    page.click(".profile-layout a.btn")
    page.wait_for_url("**/layouts.html?**")
    wait_for_auth(page)
    assert page.input_value("#name") == "Anna live"
    assert page.is_checked('input[name="theme"][value="bold"]')
    assert page.input_value("#color") == "#ff4655"
    assert errors == []


def test_own_profile_offers_edit_instead(context, base_url):
    data = base_data()
    data["layouts"] = {OWNER: {"params": "n=Anna", "updatedAt": 1}}
    page, _ = open_page(context, base_url, "profil.html", data)
    login(page, OWNER)
    _, _, label = layout_block(page)
    assert label == "Im Baukasten bearbeiten"


def test_manipulated_layout_is_cleaned_when_shown(context, base_url):
    data = base_data()
    evil = (
        "t=evil&c=zzzzzz&s=live&foo=bar&cd=999"
        "&n=%3Cimg%20src%3Dx%20onerror%3D__x%3D1%3E%0Aabc"
        "&tw=%40%40bad!!&ms=" + "A" * 100
    )
    data["layouts"] = {OWNER: {"params": evil, "updatedAt": 1}}
    page, errors = open_page(context, base_url, "profil.html?u=anna", data)
    frame_src, href, _ = layout_block(page)

    params = query_of(href)
    assert set(params) <= ALLOWED_KEYS, params
    assert "t" not in params and "c" not in params  # ungültig → Standardwert, fällt weg
    assert params["cd"] == "30"
    assert params["tw"] == "bad"
    # Zeilenumbruch → Leerzeichen, dann auf 25 Zeichen gekürzt; bleibt reiner Text
    assert params["n"] == "<img src=x onerror=__x=1>"
    assert params["ms"] == "A" * 60
    assert query_of(frame_src)["s"] == "start"
    assert page.locator(".profile-layout img").count() == 0
    assert page.evaluate("window.__x") is None
    assert errors == []


def test_non_string_layout_is_ignored(context, base_url):
    data = base_data()
    data["layouts"] = {OWNER: {"params": {"n": "x"}, "updatedAt": 1}}
    page, errors = open_page(context, base_url, "profil.html?u=anna", data)
    page.locator(".profile h1").wait_for()
    page.wait_for_timeout(300)
    assert page.locator(".profile-layout").count() == 0
    assert errors == []
