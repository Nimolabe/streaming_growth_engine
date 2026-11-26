"""Wochenplan-Seite (wochenplan.html): Formular → Plan über js/strategist-core.js.

Der Rechenkern selbst ist per Paritätstest an Python gebunden (test_strategist_parity.py);
hier geht es um die Seite: Formular, Fehler, Sprache, Teilen, Kalender, Kopieren, Handy.
"""

from __future__ import annotations

import re
from datetime import date

import pytest
from conftest import collect_errors, set_language

LANGUAGES = ["de", "en"]
PAGE = "wochenplan.html"
GAMBLING_DE = "Glücksspiel-Kategorien werden von der Streaming Growth Engine nicht unterstützt"


def open_planner(context, base_url, language="de", path=PAGE):
    set_language(context, language)
    page = context.new_page()
    errors = collect_errors(page)
    requests: list[str] = []
    page.on("request", lambda request: requests.append(request.url))
    page.goto(f"{base_url}/{path}")
    page.wait_for_selector("html[data-wochenplan=ready]")
    page.requests = requests  # für die Prüfung auf fremde Hosts
    return page, errors


def fill_basic(page, games=("Valorant",), hours="8", streams="3"):
    inputs = page.locator("#wp-games input")
    for index, game in enumerate(games):
        if index >= inputs.count():
            page.click("#wp-add-game")
        page.locator("#wp-games input").nth(index).fill(game)
    page.click("[data-quick=evenings]")
    page.fill("#wp-hours", hours)
    page.fill("#wp-streams", streams)


def submit(page):
    page.click("#wp-submit")


def plan(page):
    return page.evaluate("window.SGE_WOCHENPLAN.plan()")


@pytest.mark.parametrize("language", LANGUAGES)
def test_form_creates_plan(context, base_url, language):
    page, errors = open_planner(context, base_url, language)
    fill_basic(page)
    submit(page)
    page.wait_for_selector(".wp-card")
    data = plan(page)
    assert data["language"] == language and len(data["streams"]) == 3
    cards = page.locator(".wp-card")
    assert cards.count() == 3
    first = data["streams"][0]
    card = cards.first
    assert card.locator("h3").text_content() == "Valorant"
    assert card.locator(".wp-title-main span").text_content() == first["title"]
    assert card.locator(".wp-title:not(.wp-title-main) span").all_text_contents() == first["title_alternatives"]
    assert card.locator(".wp-tag").all_text_contents() == first["tags"]
    heading = {"de": "Dein Wochenplan", "en": "Your weekly plan"}[language]
    assert page.locator("#wp-result-title").text_content() == heading
    # Ehrlicher Hinweis ohne Messungen – ohne Kommandozeilen-Befehl
    notes = " ".join(page.locator(".wp-notes li").all_text_contents())
    assert {"de": "kommen später dazu", "en": "will come later"}[language] in notes
    assert "python" not in page.locator("#wp-result").text_content()
    assert {"de": "Vorbereitung", "en": "Preparation"}[language] in card.text_content()
    assert errors == []


def test_language_switch_recomputes(context, base_url):
    page, errors = open_planner(context, base_url, "de")
    fill_basic(page)
    submit(page)
    page.wait_for_selector(".wp-card")
    german = plan(page)["streams"][0]["title"]
    page.select_option("[data-sge-language] >> nth=0", "en")
    page.wait_for_function("window.SGE_WOCHENPLAN.plan().language === 'en'")
    english = plan(page)["streams"][0]
    assert english["title"] != german
    assert page.locator(".wp-card .wp-title-main span").first.text_content() == english["title"]
    assert page.locator("#wp-result-title").text_content() == "Your weekly plan"
    assert page.locator("#wp-goal option").first.text_content() == "Find new viewers"
    assert page.locator("#wp-windows select").first.locator("option").first.text_content() == "Monday"
    page.select_option("[data-sge-language] >> nth=0", "de")
    page.wait_for_function("window.SGE_WOCHENPLAN.plan().language === 'de'")
    assert page.locator("#wp-goal option").first.text_content() == "Neue Zuschauer finden"
    assert errors == []


def test_validation_errors_are_shown_at_the_field(context, base_url):
    page, errors = open_planner(context, base_url, "de")
    fill_basic(page, hours="")
    submit(page)
    alert = page.locator("#wp-errors")
    assert alert.is_visible() and alert.get_attribute("role") == "alert"
    assert "markierten Felder" in alert.text_content()
    assert page.locator("#wp-hours-error").text_content() == "Bitte 2 bis 60 Stunden angeben."
    assert page.locator("#wp-hours").get_attribute("aria-invalid") == "true"
    assert page.locator("#wp-result").is_hidden()

    # Zeitfenster ohne Dauer
    page.fill("#wp-hours", "8")
    row = page.locator("#wp-windows .wp-row").first
    row.locator("input").nth(1).fill("18:00")
    submit(page)
    assert "braucht eine Dauer" in page.locator("#wp-windows-error").text_content()
    assert row.locator("input").nth(1).get_attribute("aria-invalid") == "true"

    # Zu kurzer Spielname, danach wieder alles gut
    row.locator("input").nth(1).fill("22:00")
    page.locator("#wp-games input").first.fill("X")
    submit(page)
    assert "2 bis 80 Zeichen" in page.locator("#wp-games-error").text_content()
    page.locator("#wp-games input").first.fill("Minecraft")
    submit(page)
    page.wait_for_selector(".wp-card")
    assert page.locator("#wp-errors").is_hidden()
    assert page.locator("[aria-invalid=true]").count() == 0
    assert errors == []


def test_validation_message_in_english(context, base_url):
    page, errors = open_planner(context, base_url, "en")
    fill_basic(page, streams="9")
    submit(page)
    assert page.locator("#wp-streams-error").text_content() == "Please enter 1 to 7 streams."
    assert errors == []


@pytest.mark.parametrize("language", LANGUAGES)
def test_gambling_alone_is_refused(context, base_url, language):
    page, errors = open_planner(context, base_url, language)
    fill_basic(page, games=("Slots",))
    submit(page)
    message = {"de": GAMBLING_DE, "en": "Gambling categories are not supported"}[language]
    assert message in page.locator("#wp-errors").text_content()
    assert message in page.locator("#wp-games-error").text_content()
    assert page.locator("#wp-games input").first.get_attribute("aria-invalid") == "true"
    assert page.locator("#wp-result").is_hidden()
    # Die Meldung landet sichtbar unter der festen Navigation (html scrollt weich, daher warten)
    page.wait_for_function("""() => { const top = document.querySelector('#wp-errors').getBoundingClientRect().top;
      return top >= document.querySelector('.nav').getBoundingClientRect().bottom && top < innerHeight; }""")
    assert errors == []


def test_gambling_next_to_a_game_is_removed_with_note(context, base_url):
    page, errors = open_planner(context, base_url, "de")
    fill_basic(page, games=("Slots", "Valorant"))
    submit(page)
    page.wait_for_selector(".wp-card")
    assert set(page.locator(".wp-card h3").all_text_contents()) == {"Valorant"}
    assert GAMBLING_DE in page.locator(".wp-notes").text_content()
    # Vorschläge enthalten nie Glücksspiel
    options = page.locator("#wp-game-list option").evaluate_all("els => els.map(e => e.value)")
    assert "Minecraft" in options and "Counter-Strike" in options
    assert not {"Slots", "Poker", "Virtual Casino"} & set(options)
    assert errors == []


def test_not_enough_time(context, base_url):
    page, errors = open_planner(context, base_url, "de")
    fill_basic(page, hours="2", streams="3")
    submit(page)
    assert page.locator("#wp-errors").text_content().startswith("Zu wenig Zeit")
    assert page.locator("#wp-hours-error").text_content().startswith("Zu wenig Zeit")
    assert errors == []


def test_shared_link_gives_the_same_plan(make_context, base_url):
    context = make_context(permissions=["clipboard-read", "clipboard-write"])
    page, errors = open_planner(context, base_url, "de")
    fill_basic(page, games=("Valorant", "Stardew Valley"), hours="12", streams="4")
    page.click("#wp-more summary")
    page.select_option("#wp-mood", "funny")
    page.fill("#wp-rank-goal", "Platin")
    page.fill("#wp-commands", "!discord !insta")
    page.check("#wp-first-time")
    submit(page)
    page.wait_for_selector(".wp-card")
    original = plan(page)
    page.click("#wp-share")
    share = page.locator(".wp-share input")
    page.wait_for_function("document.querySelector('.wp-share input').value.includes('#p=')")
    url = share.input_value()
    assert url.startswith(f"{base_url}/wochenplan.html#p=") and len(url) < 2000
    assert page.evaluate("navigator.clipboard.readText()") == url

    other = make_context()
    page2, errors2 = open_planner(other, base_url, "de", path=url.removeprefix(base_url + "/"))
    page2.wait_for_selector(".wp-card")
    assert plan(page2) == original
    assert page2.locator("#wp-mood").input_value() == "funny"
    assert page2.locator("#wp-more").get_attribute("open") is not None
    assert errors == [] and errors2 == []


def test_broken_link_shows_friendly_message(context, base_url):
    page, errors = open_planner(context, base_url, "de", path=f"{PAGE}#p=kaputt!!")
    assert "ungültig oder beschädigt" in page.locator("#wp-errors").text_content()
    assert page.locator("#wp-result").is_hidden()
    assert errors == []


def test_calendar_file_has_the_right_events(context, base_url):
    page, errors = open_planner(context, base_url, "de")
    fill_basic(page, games=("Minecraft",), hours="8", streams="3")
    submit(page)
    page.wait_for_selector(".wp-card")
    data = plan(page)
    with page.expect_download() as download:
        page.click("#wp-ics")
    assert download.value.suggested_filename == "wochenplan.ics"
    text = open(download.value.path(), encoding="utf-8", newline="").read()
    assert text.startswith("BEGIN:VCALENDAR\r\n") and text.endswith("END:VCALENDAR\r\n")
    assert text.count("BEGIN:VEVENT") == 2 * len(data["streams"])  # Stream + Vorbereitung
    unfolded = text.replace("\r\n ", "")
    starts = re.findall(r"DTSTART:(\d{8})T(\d{4})00", unfolded)
    assert "Z" not in "".join(re.findall(r"DTSTART:\S+", unfolded))  # Ortszeit ohne Zeitzone
    stream_starts = starts[1::2]
    for stream, (day, clock) in zip(data["streams"], stream_starts, strict=True):
        assert clock == stream["stream"]["start"].replace(":", "")
        assert date(int(day[:4]), int(day[4:6]), int(day[6:])).weekday() == stream["stream"]["day"]
    prep_starts = starts[0::2]
    for stream, (_, clock) in zip(data["streams"], prep_starts, strict=True):
        assert clock == stream["preparation"]["start"].replace(":", "")
    assert "SUMMARY:Stream: Minecraft" in unfolded
    assert "heruntergeladen" in page.locator(".wp-action-status").text_content()
    assert errors == []


def test_copy_buttons(make_context, base_url):
    context = make_context(permissions=["clipboard-read", "clipboard-write"])
    page, errors = open_planner(context, base_url, "de")
    fill_basic(page)
    submit(page)
    page.wait_for_selector(".wp-card")
    stream = plan(page)["streams"][0]
    card = page.locator(".wp-card").first
    card.locator(".wp-title-main .wp-copy").click()
    page.wait_for_function("document.querySelector('.wp-title-main .wp-copy').textContent === 'Kopiert ✓'")
    assert page.evaluate("navigator.clipboard.readText()") == stream["title"]
    card.locator(".wp-title:not(.wp-title-main) .wp-copy").nth(1).click()
    page.wait_for_timeout(100)
    assert page.evaluate("navigator.clipboard.readText()") == stream["title_alternatives"][1]
    card.locator(".wp-tags .wp-copy").click()
    page.wait_for_timeout(100)
    assert page.evaluate("navigator.clipboard.readText()") == ", ".join(stream["tags"])
    assert errors == []


def test_xss_in_game_name_stays_text(context, base_url):
    page, errors = open_planner(context, base_url, "de")
    attack = '<img src=x onerror="window.__xss=1"><script>window.__xss=2</script>'
    fill_basic(page, games=(attack[:80],))
    submit(page)
    page.wait_for_selector(".wp-card")
    assert page.locator("#wp-result img, #wp-result script").count() == 0
    assert page.locator(".wp-card h3").first.text_content() == attack[:80]
    assert page.evaluate("window.__xss") is None
    assert errors == []


def test_last_inputs_are_remembered(context, base_url):
    page, errors = open_planner(context, base_url, "de")
    fill_basic(page, games=("Phasmophobia",), hours="10")
    submit(page)
    page.wait_for_selector(".wp-card")
    page.reload()
    page.wait_for_selector("html[data-wochenplan=ready]")
    assert page.locator("#wp-games input").first.input_value() == "Phasmophobia"
    assert page.locator("#wp-hours").input_value() == "10"
    assert page.locator("#wp-windows .wp-row").count() == 5
    assert errors == []


def test_works_without_local_storage(make_context, base_url):
    context = make_context()
    context.add_init_script(
        "Object.defineProperty(window, 'localStorage', { get() { throw new Error('gesperrt'); } });")
    page = context.new_page()
    page_errors: list[str] = []
    page.on("pageerror", lambda exc: page_errors.append(str(exc)))
    page.goto(f"{base_url}/{PAGE}")
    page.wait_for_selector("html[data-wochenplan=ready]")
    fill_basic(page)
    submit(page)
    page.wait_for_selector(".wp-card")
    # i18n.js liest den Speicher selbst ohne try/catch – das ist ein bekannter, älterer Punkt;
    # der Wochenplan darf trotzdem nicht ausfallen.
    assert page.locator(".wp-card").count() == 3


def test_no_foreign_requests_while_planning(context, base_url):
    page, errors = open_planner(context, base_url, "de")
    fill_basic(page)
    submit(page)
    page.wait_for_selector(".wp-card")
    foreign = [url for url in page.requests
               if not url.startswith((base_url, "data:", "blob:")) and "gstatic.com/firebasejs/" not in url]
    assert foreign == []
    assert f"{base_url}/data/content-strategist.json" in page.requests
    assert errors == []


@pytest.mark.parametrize("width", [390, 360])
@pytest.mark.parametrize("language", LANGUAGES)
def test_phone_without_horizontal_scroll_with_plan(make_context, base_url, width, language):
    context = make_context(viewport={"width": width, "height": 844}, is_mobile=True, has_touch=True)
    context.add_init_script("""
document.addEventListener("DOMContentLoaded", () => {
  const style = document.createElement("style");
  style.textContent = '* { font-family: "DejaVu Sans", Verdana, sans-serif !important; }';
  document.head.appendChild(style);
});""")
    page, errors = open_planner(context, base_url, language)
    fill_basic(page, games=("Warhammer 40,000: Darktide – Ultimate Edition", "Stardew Valley"))
    page.click("#wp-more summary")
    page.fill("#wp-commands", "!discord !insta")
    submit(page)
    page.wait_for_selector(".wp-card")
    page.locator("#wp-share").click()
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(200)
    widths = page.evaluate(
        "({ scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth })")
    assert widths["scroll"] <= widths["client"] == width, widths
    assert errors == []


def test_growth_tile_links_to_wochenplan(context, base_url):
    set_language(context, "de")
    page = context.new_page()
    page.goto(f"{base_url}/index.html")
    link = page.locator('#features a.card-link[href="wochenplan.html"]')
    assert link.count() == 1
    assert link.text_content().strip() == "Wochenplan erstellen →"


def test_print_styles_hide_the_form(context, base_url):
    page, errors = open_planner(context, base_url, "de")
    fill_basic(page)
    submit(page)
    page.wait_for_selector(".wp-card")
    page.emulate_media(media="print")
    assert page.locator("#wp-form").is_hidden()
    assert page.locator(".nav").is_hidden()
    assert page.locator(".wp-actions").is_hidden()
    assert page.locator(".wp-card").first.is_visible()
    assert errors == []


def test_works_when_logged_in(context, base_url):
    from conftest import login, profile, seed_db

    uid = "uid-wochenplan-1"
    seed_db(context, {"profiles": {uid: profile(uid, "planer")}, "usernames": {"planer": uid}})
    page, errors = open_planner(context, base_url, "de")
    login(page, "uid-wochenplan-1", "Planer")
    fill_basic(page)
    submit(page)
    page.wait_for_selector(".wp-card")
    assert page.locator(".wp-card").count() == 3
    assert errors == []
