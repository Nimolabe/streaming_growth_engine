"""Beta-Warteliste an der Clip-Hunter-Kachel (js/waitlist.js)."""

from __future__ import annotations

from conftest import collect_errors, login, profile, read_db, seed_db, set_language, wait_for_auth

UID = "user-anna"
BOX = '[data-waitlist="clipHunter"]'


def open_index(context, base_url, platform="twitch"):
    set_language(context, "de")
    seed_db(
        context, {"profiles": {UID: profile(UID, "anna", platform)}, "usernames": {"anna": UID}}
    )
    page = context.new_page()
    errors = collect_errors(page)
    page.goto(f"{base_url}/index.html", wait_until="load")
    wait_for_auth(page)
    page.locator(BOX).scroll_into_view_if_needed()
    return page, errors


def status(page) -> str:
    return page.locator(f"{BOX} [data-waitlist-status]").text_content().strip()


def entry(page):
    return read_db(page).get("waitlist", {}).get("clipHunter", {}).get(UID)


def test_logged_out_click_opens_login_then_joins_automatically(context, base_url):
    page, errors = open_index(context, base_url)
    assert status(page) == "Kostenlos. Du brauchst nur einen Account."
    assert page.locator("#auth-modal").is_hidden()

    page.locator(f"{BOX} [data-waitlist-join]").click()
    assert page.locator("#auth-modal").is_visible()
    assert status(page) == "Melde dich an – danach wirst du automatisch vorgemerkt."
    assert entry(page) is None

    login(page, UID, "Anna")
    page.wait_for_function("() => document.querySelector('[data-waitlist-leave]').hidden === false")
    saved = entry(page)
    assert set(saved) == {"createdAt", "platform"}
    assert isinstance(saved["createdAt"], int) and saved["createdAt"] > 1_700_000_000_000
    assert saved["platform"] == "twitch"
    assert status(page) == "✓ Du bist vorgemerkt. Wir melden uns, sobald die Beta startet."
    assert page.locator(f"{BOX} [data-waitlist-join]").is_hidden()
    assert errors == []


def test_platform_is_left_out_when_profile_has_none(context, base_url):
    page, _ = open_index(context, base_url, platform="")
    login(page, UID)
    page.locator(f"{BOX} [data-waitlist-join]").click()
    page.wait_for_function("() => document.querySelector('[data-waitlist-leave]').hidden === false")
    assert set(entry(page)) == {"createdAt"}


def test_leave_removes_entry(context, base_url):
    page, errors = open_index(context, base_url)
    login(page, UID)
    page.locator(f"{BOX} [data-waitlist-join]").click()
    leave = page.locator(f"{BOX} [data-waitlist-leave]")
    leave.wait_for(state="visible")
    assert entry(page) is not None

    leave.click()
    page.locator(f"{BOX} [data-waitlist-join]").wait_for(state="visible")
    assert entry(page) is None
    assert status(page) == "Du bist ausgetragen."
    assert errors == []


def test_joined_state_survives_reload(context, base_url):
    page, _ = open_index(context, base_url)
    login(page, UID)
    page.locator(f"{BOX} [data-waitlist-join]").click()
    page.locator(f"{BOX} [data-waitlist-leave]").wait_for(state="visible")

    page.reload(wait_until="load")
    wait_for_auth(page)
    # Nach dem Neuladen blendet GSAP die Kachel erst beim Scrollen ein → hidden-Attribut prüfen
    page.wait_for_function("() => document.querySelector('[data-waitlist-leave]').hidden === false")
    assert status(page) == "✓ Du bist vorgemerkt. Wir melden uns, sobald die Beta startet."


def test_permission_denied_shows_friendly_message(context, base_url):
    page, _ = open_index(context, base_url)
    page.evaluate("window.__deny = true")
    login(page, UID)
    page.locator(f"{BOX} [data-waitlist-join]").click()
    page.wait_for_function(
        "() => document.querySelector('[data-waitlist-status]').dataset.type === 'error'"
    )
    assert status(page) == (
        "Die Warteliste wird gerade eingerichtet. Bitte versuch es später noch einmal."
    )
    assert entry(page) is None
    # Der Knopf bleibt nutzbar, man kann es später erneut versuchen
    join = page.locator(f"{BOX} [data-waitlist-join]")
    assert join.is_visible() and join.is_enabled()


def test_permission_denied_message_in_english(context, base_url):
    page, _ = open_index(context, base_url)
    page.select_option("[data-sge-language] >> nth=0", "en")
    page.evaluate("window.__deny = true")
    login(page, UID)
    page.locator(f"{BOX} [data-waitlist-join]").click()
    page.wait_for_function(
        "() => document.querySelector('[data-waitlist-status]').dataset.type === 'error'"
    )
    text = status(page)
    assert text and not any(ch in text for ch in "äöüß"), text
