"""Gemeinsame Bausteine für die Browser-Tests der Website.

- Ein lokaler HTTP-Server liefert die Repo-Wurzel aus (zufälliger Port).
- Anfragen nach außen (Google Fonts, CDNs, Bilder) werden mit Status 204 beantwortet.
- Firebase wird durch die Module in ``stubs/`` ersetzt (siehe README.md).
"""

from __future__ import annotations

import functools
import json
import os
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
STUBS = Path(__file__).resolve().parent / "stubs"
FIREBASE_PREFIX = "https://www.gstatic.com/firebasejs/"

# Hauptseiten mit Navigation (overlay.html ist eine OBS-Quelle ohne Navigation)
MAIN_PAGES = [
    "index.html",
    "setups.html",
    "guides.html",
    "layouts.html",
    "community.html",
    "profil.html",
]
OVERLAY_PAGE = "overlay.html?s=live&n=Test"


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


@pytest.fixture(scope="session")
def base_url() -> str:
    handler = functools.partial(_QuietHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


@pytest.fixture(scope="session")
def playwright_instance() -> Playwright:
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright) -> Browser:
    # SGE_CHROMIUM: optional eigener Chromium-Pfad (z. B. wenn die installierte
    # Playwright-Version nicht zum vorhandenen Browser passt).
    executable = os.environ.get("SGE_CHROMIUM") or None
    browser = playwright_instance.chromium.launch(headless=True, executable_path=executable)
    yield browser
    browser.close()


def _stub_body(url: str) -> str | None:
    name = url.split("?")[0].rsplit("/", 1)[-1]
    path = STUBS / name
    return path.read_text(encoding="utf-8") if path.is_file() else None


def new_context(browser: Browser, base_url: str, **options) -> BrowserContext:
    """Neuer Browser-Kontext: nur der lokale Server ist erreichbar, Firebase ist nachgebaut."""
    context = browser.new_context(accept_downloads=True, **options)

    def handle(route):
        url = route.request.url
        if url.startswith(base_url):
            route.continue_()
        elif url.startswith(FIREBASE_PREFIX):
            body = _stub_body(url)
            if body is None:
                route.fulfill(status=404, body="unbekanntes Firebase-Modul")
            else:
                route.fulfill(
                    status=200,
                    body=body,
                    content_type="text/javascript; charset=utf-8",
                    headers={"Access-Control-Allow-Origin": "*"},
                )
        else:
            route.fulfill(status=204, body="")

    context.route("**/*", handle)
    return context


@pytest.fixture
def context(browser: Browser, base_url: str) -> BrowserContext:
    context = new_context(browser, base_url)
    yield context
    context.close()


@pytest.fixture
def make_context(browser: Browser, base_url: str):
    """Für Tests, die mehrere Kontexte oder eigene Optionen (z. B. Handy-Breite) brauchen."""
    created: list[BrowserContext] = []

    def factory(**options) -> BrowserContext:
        context = new_context(browser, base_url, **options)
        created.append(context)
        return context

    yield factory
    for context in created:
        context.close()


def set_language(context: BrowserContext, language: str) -> None:
    """Sprache vor dem ersten Laden festlegen (wie eine gespeicherte Auswahl)."""
    context.add_init_script(f"localStorage.setItem('sge-language', {json.dumps(language)});")


def seed_db(context: BrowserContext, data: dict) -> None:
    """Startdaten der nachgebauten Datenbank (nur beim ersten Laden im Kontext)."""
    payload = json.dumps(json.dumps(data))
    context.add_init_script(
        "if (!sessionStorage.getItem('__sgeSeeded')) {"
        f"  localStorage.setItem('__sgeDb', {payload});"
        "  sessionStorage.setItem('__sgeSeeded', '1');"
        "}"
    )


def read_db(page: Page) -> dict:
    return page.evaluate("JSON.parse(localStorage.getItem('__sgeDb') || '{}')")


def write_db(page: Page, data: dict) -> None:
    page.evaluate("data => localStorage.setItem('__sgeDb', JSON.stringify(data))", data)


def collect_errors(page: Page) -> list[str]:
    """Sammelt JS-Fehler (nicht abgefangene Ausnahmen und console.error)."""
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
    page.on(
        "console",
        lambda msg: errors.append(f"console.error: {msg.text}") if msg.type == "error" else None,
    )
    return errors


def wait_for_auth(page: Page) -> None:
    """Wartet, bis auth.js Firebase (nachgebaut) geladen und den Anmeldestand gemeldet hat."""
    page.wait_for_function("window.sgeAuth !== undefined && typeof window.__setUser === 'function'")


def login(page: Page, uid: str, name: str = "Test") -> None:
    wait_for_auth(page)
    page.evaluate(
        "([uid, name]) => window.__setUser({ uid, displayName: name, email: uid + '@example.test' })",
        [uid, name],
    )
    page.wait_for_function(
        "uid => window.sgeAuth && window.sgeAuth.user && window.sgeAuth.user.uid === uid", arg=uid
    )


def profile(uid: str, username: str, platform: str = "twitch", **extra) -> dict:
    """Ein öffentliches Profil wie von social.js gespeichert."""
    data = {
        "name": extra.pop("name", username),
        "username": username,
        "usernameLower": username.lower(),
        "bio": "",
        "platform": platform,
        "channel": "",
        "games": "",
        "createdAt": 1_700_000_000_000,
        **extra,
    }
    data["nameLower"] = data["name"].lower()
    return data
