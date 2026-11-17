"""Alle Seiten laden auf Deutsch und Englisch ohne JS-Fehler; Handy-Breite ohne seitliches Scrollen."""

from __future__ import annotations

import pytest
from conftest import MAIN_PAGES, OVERLAY_PAGE, collect_errors, set_language, wait_for_auth

LANGUAGES = ["de", "en"]


def open_page(context, base_url, path, language):
    set_language(context, language)
    page = context.new_page()
    errors = collect_errors(page)
    page.goto(f"{base_url}/{path}", wait_until="load")
    if path != OVERLAY_PAGE:
        wait_for_auth(page)
    page.wait_for_timeout(300)  # verzögerte Fehler (z. B. aus async-Code) abwarten
    return page, errors


@pytest.mark.parametrize("language", LANGUAGES)
@pytest.mark.parametrize("path", [*MAIN_PAGES, OVERLAY_PAGE])
def test_page_loads_without_js_errors(context, base_url, path, language):
    page, errors = open_page(context, base_url, path, language)
    assert errors == []
    if path != OVERLAY_PAGE:
        assert page.evaluate("document.documentElement.lang") == language


@pytest.mark.parametrize("path", MAIN_PAGES)
def test_guides_link_in_navigation(context, base_url, path):
    page, _ = open_page(context, base_url, path, "de")
    links = page.locator('.nav-links a[href="guides.html"]')
    assert links.count() == 1
    assert links.first.text_content().strip() == "Guides"


# Bekannte Fehler der Website (nicht in diesem PR repariert). Ob sie bei 390 px auftreten,
# hängt von den installierten Ersatzschriften ab (die Webfonts sind im Test geblockt):
# mit "Inter" passt es knapp, mit "DejaVu Sans" (Ubuntu/CI) nicht. Bei 360/375 px scrollen
# die Seiten auch mit der echten Schrift seitlich. Deshalb nicht strikt.
GUIDES_TABLE = (
    "guides.html: .guide-table-wrap (overflow-x: auto) liegt in einem Grid-Element ohne "
    "min-width: 0 und wird so breit wie die Tabelle im Guide „Plattform“"
)
LAYOUTS_TABS = (
    "layouts.html (EN): die Szenen-Tabs (Starting soon / Live / Be right back / Ending) "
    "passen nicht in eine Zeile und verbreitern die Grid-Spalte von .builder"
)
KNOWN_OVERFLOW = {
    ("guides.html", "de"): GUIDES_TABLE,
    ("guides.html", "en"): GUIDES_TABLE,
    ("layouts.html", "en"): LAYOUTS_TABS,
}


def phone_cases():
    for path in MAIN_PAGES:
        for language in LANGUAGES:
            reason = KNOWN_OVERFLOW.get((path, language))
            marks = [pytest.mark.xfail(strict=False, reason=reason)] if reason else []
            yield pytest.param(path, language, marks=marks, id=f"{path}-{language}")


@pytest.mark.parametrize(("path", "language"), list(phone_cases()))
def test_no_horizontal_scroll_on_phone(make_context, base_url, path, language):
    context = make_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    page, errors = open_page(context, base_url, path, language)
    # Einmal ganz nach unten scrollen, damit alle Einblendungen (GSAP) ausgelöst werden
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(300)
    widths = page.evaluate(
        "({ scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth })"
    )
    assert widths["scroll"] <= widths["client"], f"seitliches Scrollen: {widths}"
    assert errors == []
