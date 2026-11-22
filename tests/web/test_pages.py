"""Alle Seiten laden auf Deutsch und Englisch ohne JS-Fehler; Handy-Breite ohne seitliches Scrollen."""

from __future__ import annotations

from urllib.parse import urlsplit

import pytest
from conftest import MAIN_PAGES, OVERLAY_PAGE, collect_errors, set_language, wait_for_auth

LANGUAGES = ["de", "en"]


def open_page(context, base_url, path, language):
    set_language(context, language)
    page = context.new_page()
    errors = collect_errors(page)
    page.goto(f"{base_url}/{path}", wait_until="load")
    if not path.startswith("overlay.html"):  # das Overlay hat keine Anmeldung
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


PHONE_WIDTHS = [390, 360]

# Die Webfonts sind im Test geblockt, also entscheidet die installierte Ersatzschrift über die
# Textbreite. Damit lokal dieselben Fehler auftreten wie in der CI (Ubuntu: DejaVu Sans),
# wird eine breite Ersatzschrift erzwungen.
WIDE_FONT = """
document.addEventListener("DOMContentLoaded", () => {
  const style = document.createElement("style");
  style.textContent = '* { font-family: "DejaVu Sans", Verdana, sans-serif !important; }';
  document.head.appendChild(style);
});
"""


# Zusätzlich sehr schmale Handys (320 px) für Seiten, die dort schon geprüft sind
EXTRA_PHONE_CASES = [("setups.html", 320)]


def phone_cases():
    for path in MAIN_PAGES:
        widths = PHONE_WIDTHS + [w for page, w in EXTRA_PHONE_CASES if page == path]
        for width in widths:
            for language in LANGUAGES:
                yield pytest.param(path, language, width, id=f"{path}-{language}-{width}")


@pytest.mark.parametrize(("path", "language", "width"), list(phone_cases()))
def test_no_horizontal_scroll_on_phone(make_context, base_url, path, language, width):
    context = make_context(viewport={"width": width, "height": 844}, is_mobile=True, has_touch=True)
    context.add_init_script(WIDE_FONT)
    page, errors = open_page(context, base_url, path, language)
    # Einmal ganz nach unten scrollen, damit alle Einblendungen (GSAP) ausgelöst werden
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(300)
    widths = page.evaluate(
        "({ scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth })"
    )
    assert widths["client"] == width
    assert widths["scroll"] <= widths["client"], f"seitliches Scrollen: {widths}"
    assert errors == []


@pytest.mark.parametrize("language", LANGUAGES)
def test_guides_link_to_clip_hunter_beta(context, base_url, language):
    page, errors = open_page(context, base_url, "guides.html", language)
    link = page.locator('a.guide-link[href="index.html#clip-hunter"]')
    assert link.count() >= 1
    expected = {
        "de": "Highlights automatisch finden: für die Clip-Hunter-Beta vormerken →",
        "en": "Find highlights automatically: join the Clip Hunter beta →",
    }[language]
    assert expected in [t.strip() for t in link.all_text_contents()]

    link.filter(has_text=expected).click()
    page.wait_for_url("**/index.html#clip-hunter")
    tile = page.locator("#clip-hunter")
    assert tile.locator('[data-waitlist="clipHunter"] [data-waitlist-join]').count() == 1
    assert errors == []


GOOGLE_FONT_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com")


@pytest.mark.parametrize("path", [*MAIN_PAGES, OVERLAY_PAGE])
def test_no_requests_to_google_fonts(context, base_url, path):
    """Schriften kommen selbst gehostet aus fonts/ (css/fonts.css bzw. css/overlay.css)."""
    requests = []
    context.on("request", lambda r: requests.append(r.url))
    statuses = {}
    context.on("response", lambda r: statuses.__setitem__(r.url, r.status))
    page, errors = open_page(context, base_url, path, "de")
    # Einmal durchscrollen, damit alle Inhalte (und damit alle Schriftschnitte) gebraucht werden
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.evaluate("document.fonts.ready.then(() => true)")
    page.wait_for_timeout(300)

    google = [u for u in requests if any(host in u for host in GOOGLE_FONT_HOSTS)]
    assert google == []
    # Keine Verweise mehr im HTML (auch kein preconnect)
    html = page.content()
    assert not any(host in html for host in GOOGLE_FONT_HOSTS)
    own = {u: s for u, s in statuses.items() if "/fonts/" in u and u.endswith(".woff2")}
    assert own and all(s == 200 for s in own.values()), own
    assert errors == []


# ---------------------------------------------------------------------------
# Fremde Hosts: Die Website lädt nichts von Dritten außer Firebase
# ---------------------------------------------------------------------------

# Zentrale Liste der erlaubten fremden Adressen (Host, Pfad-Anfang). Alles andere – auch
# Google Fonts oder Bild-CDNs – ist verboten, weil dabei die IP-Adresse an Dritte geht.
ALLOWED_FOREIGN = [
    ("www.gstatic.com", "/firebasejs/"),  # Firebase-SDK
    ("*.firebaseio.com", "/"),  # Realtime Database (ältere Adressen)
    ("*.firebasedatabase.app", "/"),  # Realtime Database (u. a. Logos fürs Overlay)
    ("identitytoolkit.googleapis.com", "/"),  # Firebase Auth (Anmelden)
    ("securetoken.googleapis.com", "/"),  # Firebase Auth (Token erneuern)
]


def foreign_allowed(url: str) -> bool:
    parts = urlsplit(url)
    for host, prefix in ALLOWED_FOREIGN:
        ok_host = parts.hostname == host or (
            host.startswith("*.") and (parts.hostname or "").endswith(host[1:])
        )
        if ok_host and parts.path.startswith(prefix):
            return True
    return False


def test_allowlist_itself():
    assert foreign_allowed("https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js")
    assert foreign_allowed("https://x-default-rtdb.europe-west1.firebasedatabase.app/a.json")
    assert not foreign_allowed("https://fonts.googleapis.com/css2?family=Inter")
    assert not foreign_allowed("https://fonts.gstatic.com/s/inter/v20/a.woff2")
    assert not foreign_allowed("https://www.gstatic.com/other/thing.js")
    assert not foreign_allowed("https://images.unsplash.com/photo-1?w=900")
    assert not foreign_allowed("https://evil.firebasedatabase.app.example.com/")


@pytest.mark.parametrize(
    "path",
    [
        *MAIN_PAGES,
        OVERLAY_PAGE,
        "overlay.html?s=live&frame=plain&fs=1&fi=1&tw=a&u=AnnaUid000000000001",
    ],
)
def test_no_requests_to_foreign_hosts(context, base_url, path):
    requests = []
    context.on("request", lambda r: requests.append(r.url))
    page, errors = open_page(context, base_url, path, "de")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(400)
    page.evaluate("window.scrollTo(0, 0)")
    foreign = [u for u in requests if not u.startswith(base_url) and not u.startswith("data:")]
    assert [u for u in foreign if not foreign_allowed(u)] == []
    assert errors == []


def test_homepage_images_are_local(context, base_url):
    page, errors = open_page(context, base_url, "index.html", "de")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_function(
        "() => [...document.querySelectorAll('main img')].every(i => i.complete && i.naturalWidth > 0)"
    )
    imgs = page.evaluate(
        """[...document.querySelectorAll('main img')].map(i => ({
             src: i.getAttribute('src'), srcset: i.getAttribute('srcset'), sizes: i.getAttribute('sizes'),
             w: i.getAttribute('width'), h: i.getAttribute('height'), lazy: i.getAttribute('loading'),
             alt: i.getAttribute('alt') }))"""
    )
    assert len(imgs) == 7
    for i, img in enumerate(imgs):
        assert img["src"].startswith("images/") and img["src"].endswith(".webp")
        assert "-600.webp 600w" in img["srcset"] and img["sizes"]
        assert img["w"] and img["h"] and img["alt"]
        assert img["lazy"] == (None if i == 0 else "lazy")  # Hero-Bild nicht lazy
    assert errors == []
