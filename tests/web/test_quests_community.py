"""Erste Quests (js/quests.js) nur per Klick und ehrlicher Leer-Zustand der Community."""

from __future__ import annotations

import pytest
from conftest import collect_errors, login, profile, seed_db, set_language, wait_for_auth

QUEST = '.quests li[data-quest="{}"]'
CHECK = QUEST + " .quest-check"


def open_index(context, base_url, language="de"):
    set_language(context, language)
    page = context.new_page()
    errors = collect_errors(page)
    page.goto(f"{base_url}/index.html", wait_until="load")
    wait_for_auth(page)
    page.locator("#start").scroll_into_view_if_needed()
    return page, errors


def xp(page) -> int:
    return int(page.locator("[data-xp]").text_content())


def level(page) -> int:
    return int(page.locator("[data-level]").text_content())


def checked(page) -> list[str]:
    return page.eval_on_selector_all(
        ".quests .quest-check", "els => els.map(el => el.getAttribute('aria-checked'))"
    )


def bar_value(page) -> str:
    return page.eval_on_selector(".xp-bar span", "el => el.style.getPropertyValue('--xp')")


# ------------------------------------------------------------------ Quests
def test_scrolling_never_ticks_quests(context, base_url):
    page, errors = open_index(context, base_url)
    # Langsam durch die Quests und bis ganz nach unten scrollen (früher hakten sie sich dabei ab)
    for li in page.locator(".quests li").all():
        li.scroll_into_view_if_needed()
        page.wait_for_timeout(150)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(600)
    assert xp(page) == 0 and level(page) == 1
    assert checked(page) == ["false"] * 4
    assert page.locator(".quests li.is-done").count() == 0
    assert bar_value(page) == "0"
    assert page.locator("[data-quest-reset]").is_hidden()
    assert errors == []


def test_ticking_raises_xp_survives_reload_and_resets(context, base_url):
    page, errors = open_index(context, base_url)
    page.locator(CHECK.format("platform")).click()
    assert xp(page) == 100 and checked(page) == ["true", "false", "false", "false"]
    assert page.locator(QUEST.format("platform")).evaluate("el => el.classList.contains('is-done')")
    # Tastatur: Fokus auf die Checkbox, Leertaste bzw. Enter
    page.locator(CHECK.format("schedule")).focus()
    page.keyboard.press("Space")
    assert xp(page) == 400
    page.locator(CHECK.format("schedule")).focus()
    page.keyboard.press("Enter")
    assert xp(page) == 100
    page.keyboard.press("Enter")
    assert xp(page) == 400
    assert abs(float(bar_value(page)) - 400 / 1100) < 1e-6
    assert page.evaluate("localStorage.getItem('sge-quests')") == '["platform","schedule"]'

    page.reload(wait_until="load")
    page.locator("#start").scroll_into_view_if_needed()
    assert xp(page) == 400 and checked(page) == ["true", "false", "true", "false"]

    reset = page.locator("[data-quest-reset]")
    assert reset.is_visible()
    reset.click()
    assert xp(page) == 0 and checked(page) == ["false"] * 4
    assert reset.is_hidden()
    assert page.evaluate("localStorage.getItem('sge-quests')") is None
    page.reload(wait_until="load")
    assert xp(page) == 0
    assert errors == []


def test_level_two_only_with_all_quests_ticked(context, base_url):
    page, errors = open_index(context, base_url)
    for quest in ("platform", "setup", "schedule"):
        page.locator(CHECK.format(quest)).click()
    assert xp(page) == 600 and level(page) == 1
    page.locator(CHECK.format("golive")).click()
    assert xp(page) == 1100 and level(page) == 2
    page.locator(CHECK.format("setup")).click()
    assert xp(page) == 900 and level(page) == 1
    assert errors == []


def test_without_storage_quests_work_in_memory(context, base_url):
    # Gesperrter Speicher (z. B. strenge Datenschutz-Einstellungen) nur für die Quests
    context.add_init_script(
        """
        for (const name of ['getItem', 'setItem', 'removeItem']) {
          const original = Storage.prototype[name];
          Storage.prototype[name] = function (key, ...rest) {
            if (key === 'sge-quests') throw new DOMException('blocked', 'SecurityError');
            return original.call(this, key, ...rest);
          };
        }
        """
    )
    page, errors = open_index(context, base_url)
    page.locator(CHECK.format("golive")).click()
    assert xp(page) == 500 and checked(page)[3] == "true"
    page.locator("[data-quest-reset]").click()
    assert xp(page) == 0
    assert errors == []


def test_quests_link_to_matching_help(context, base_url):
    page, _ = open_index(context, base_url)
    links = {
        quest: page.eval_on_selector_all(
            QUEST.format(quest) + " .quest-links a", "els => els.map(el => el.getAttribute('href'))"
        )
        for quest in ("platform", "setup", "schedule", "golive")
    }
    assert links == {
        "platform": ["guides.html#plattform"],
        "setup": ["setups.html", "guides.html#obs"],
        "schedule": ["guides.html#zeitplan"],
        "golive": ["guides.html#erster-stream"],
    }
    page.locator(QUEST.format("schedule") + " .quest-links a").click()
    page.wait_for_url("**/guides.html#zeitplan")
    assert page.locator("#zeitplan").count() == 1


def test_quests_in_english(context, base_url):
    page, errors = open_index(context, base_url, "en")
    section = page.locator("#start")
    text = section.text_content()
    assert "Tick off a quest once you've done it." in text
    assert "Guide: Choosing a platform →" in text and "Setup finder →" in text
    assert not any(ch in text for ch in "äöüß"), text
    labels = page.eval_on_selector_all(
        ".quests .quest-check", "els => els.map(el => el.getAttribute('aria-label'))"
    )
    assert labels == ["Done: Choose a platform", "Done: Set up your gear", "Done: Set a schedule",
                      "Done: Go live!"]
    page.locator(CHECK.format("setup")).click()
    assert page.locator("[data-quest-reset]").text_content().strip() == "Reset"
    # Umschalten zurück auf Deutsch übersetzt auch die Bedienelemente zurück
    page.select_option("[data-sge-language] >> nth=0", "de")
    assert page.locator("[data-quest-reset]").text_content().strip() == "Zurücksetzen"
    assert page.locator(CHECK.format("setup")).get_attribute("aria-label") == \
        "Erledigt: Setup einrichten"
    assert xp(page) == 200
    assert errors == []


@pytest.mark.parametrize("width", [390, 360])
def test_quests_on_phone(make_context, base_url, width):
    context = make_context(viewport={"width": width, "height": 800}, is_mobile=True, has_touch=True)
    page, errors = open_index(context, base_url)
    check = page.locator(CHECK.format("setup"))
    check.tap()
    assert xp(page) == 200
    box = check.bounding_box()
    assert box["x"] >= 0 and box["x"] + box["width"] <= width
    links = page.locator(QUEST.format("setup") + " .quest-links a").all()
    assert all(link.bounding_box()["x"] + link.bounding_box()["width"] <= width for link in links)
    assert errors == []


def test_community_card_says_just_starting(context, base_url):
    page, _ = open_index(context, base_url)
    card = page.locator(".card", has=page.locator("h3", has_text="Community"))
    assert card.locator(".card-badge").text_content().strip() == "Im Aufbau"
    assert card.locator('a[href="community.html"]').count() == 1
    page.select_option("[data-sge-language] >> nth=0", "en")
    assert card.locator(".card-badge").text_content().strip() == "Just starting"


# ------------------------------------------------------------------ Community
def open_community(context, base_url, data=None, language="de"):
    set_language(context, language)
    if data is not None:
        seed_db(context, data)
    page = context.new_page()
    errors = collect_errors(page)
    page.goto(f"{base_url}/community.html", wait_until="load")
    wait_for_auth(page)
    return page, errors


def wait_loaded(page):
    page.wait_for_function(
        "() => !['Wird geladen …', 'Loading …'].includes("
        "document.getElementById('results-status').textContent)"
    )


def profiles(count: int) -> dict:
    data = {"profiles": {}, "usernames": {}}
    for i in range(count):
        uid = f"user-{i}"
        data["profiles"][uid] = profile(uid, f"streamer{i}", createdAt=1_700_000_000_000 + i)
        data["usernames"][f"streamer{i}"] = uid
    return data


def test_empty_community_explains_and_invites(context, base_url):
    page, errors = open_community(context, base_url, {})
    wait_loaded(page)
    empty = page.locator("#community-empty")
    assert empty.is_visible()
    assert "Die Community startet gerade" in empty.text_content()
    assert page.locator("#results > *").count() == 0
    assert page.locator("#results-title").is_hidden()  # keine Überschrift über leerer Liste
    join = empty.locator("[data-community-join]")
    assert join.is_visible() and join.text_content().strip() == "Profil anlegen"
    join.click()
    assert page.locator("#auth-modal").is_visible()
    assert errors == []


def test_small_community_shows_profiles_and_hint(context, base_url):
    page, errors = open_community(context, base_url, profiles(2))
    wait_loaded(page)
    assert page.locator("#results > *").count() == 2
    assert page.locator("#results-title").is_visible()
    assert page.locator("#community-empty").is_visible()
    # Bei einer Suche passt der Hinweis nicht – er verschwindet
    page.fill("#search-input", "streamer1")
    page.wait_for_function(
        "() => document.getElementById('results-title').textContent !== 'Neu dabei'"
    )
    assert page.locator("#community-empty").is_hidden()
    assert errors == []


def test_bigger_community_has_no_empty_state(context, base_url):
    page, errors = open_community(context, base_url, profiles(6))
    wait_loaded(page)
    assert page.locator("#results > *").count() == 6
    assert page.locator("#community-empty").is_hidden()
    assert errors == []


def test_logged_in_member_sees_no_join_button(context, base_url):
    page, errors = open_community(context, base_url, profiles(1))
    wait_loaded(page)
    login(page, "user-0")
    page.wait_for_selector("[data-community-me]", state="visible")
    assert page.locator("[data-community-join]").is_hidden()
    assert errors == []


def test_empty_community_in_english(context, base_url):
    page, errors = open_community(context, base_url, {}, language="en")
    wait_loaded(page)
    text = page.locator("#community-empty").text_content()
    assert "The community is just starting" in text and "Create your profile" in text
    assert not any(ch in text for ch in "äöüß"), text
    assert errors == []


def test_permission_denied_keeps_friendly_message(context, base_url):
    set_language(context, "de")
    context.add_init_script("window.__deny = true;")
    page = context.new_page()
    page.goto(f"{base_url}/community.html", wait_until="load")
    wait_for_auth(page)
    wait_loaded(page)
    assert page.locator("#results-status").text_content() == (
        "Profile konnten gerade nicht geladen werden. Lade die Seite neu."
    )
    assert page.locator("#community-empty").is_hidden()


@pytest.mark.parametrize("width", [390, 360])
def test_empty_community_on_phone(make_context, base_url, width):
    context = make_context(viewport={"width": width, "height": 800}, is_mobile=True, has_touch=True)
    page, errors = open_community(context, base_url, {})
    wait_loaded(page)
    assert page.locator("#community-empty").is_visible()
    scroll = page.evaluate("document.documentElement.scrollWidth")
    assert scroll <= width
    assert errors == []


def test_quests_work_with_reduced_motion(make_context, base_url):
    # Ohne Animationen (motion.js läuft dann nicht) bleibt alles bedienbar und ehrlich
    context = make_context(reduced_motion="reduce")
    page, errors = open_index(context, base_url)
    assert xp(page) == 0 and bar_value(page) == "0"
    page.locator(CHECK.format("golive")).click()
    assert xp(page) == 500 and checked(page)[3] == "true"
    assert errors == []
