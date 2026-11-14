"""Abruf öffentlicher Seiten – nur für Quellen, die die Source Registry freigegeben hat.

- respektiert robots.txt (nicht lesbar = kein Abruf)
- kein Login, keine Cookies, kein Umgehen von Sperren, kein JavaScript-Rendering
- Größen- und Zeitlimit, nur Text-Inhalte
Gespeichert wird später nur ein Hash des Inhalts, nie der Text selbst.
"""

from __future__ import annotations

import urllib.error
import urllib.request
import urllib.robotparser
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit

USER_AGENT = "SGE-SetupAgent/0.1 (+https://github.com/Nimolabe/streaming_growth_engine)"
MAX_BYTES = 2_000_000
TIMEOUT_S = 15
ALLOWED_TYPES = ("text/html", "text/plain", "application/json", "application/xml", "text/xml", "application/rss+xml")


@dataclass(frozen=True)
class FetchResult:
    ok: bool
    text: str = ""
    status: int | None = None
    error: str | None = None
    final_url: str | None = None


class Fetcher(Protocol):
    def fetch(self, url: str) -> FetchResult: ...


class HttpFetcher:
    def __init__(self, user_agent: str = USER_AGENT, timeout: float = TIMEOUT_S) -> None:
        self.user_agent, self.timeout = user_agent, timeout
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    def _robots_allows(self, url: str) -> bool:
        parts = urlsplit(url)
        base = f"{parts.scheme}://{parts.netloc}"
        if base not in self._robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                req = urllib.request.Request(base + "/robots.txt", headers={"User-Agent": self.user_agent})
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310 (nur http/https, siehe fetch)
                    rp.parse(resp.read(200_000).decode("utf-8", "replace").splitlines())
            except urllib.error.HTTPError as e:
                if e.code in (401, 403):
                    rp.disallow_all = True
                elif 400 <= e.code < 500:
                    rp.allow_all = True  # keine robots.txt vorhanden
                else:
                    self._robots[base] = None
                    return False
            except Exception:  # noqa: BLE001 – Netzwerkfehler: vorsichtshalber nicht abrufen
                self._robots[base] = None
                return False
            self._robots[base] = rp
        rp = self._robots[base]
        return rp is not None and rp.can_fetch(self.user_agent, url)

    def fetch(self, url: str) -> FetchResult:
        if urlsplit(url).scheme not in ("http", "https"):
            return FetchResult(False, error="Nur http/https.")
        if not self._robots_allows(url):
            return FetchResult(False, error="robots.txt erlaubt keinen Abruf (oder ist nicht lesbar).")
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent, "Accept": "text/html,application/json;q=0.9,*/*;q=0.1"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
                ctype = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()
                if ctype and ctype not in ALLOWED_TYPES:
                    return FetchResult(False, status=resp.status, error=f"Inhaltstyp {ctype} wird nicht verarbeitet.")
                raw = resp.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    return FetchResult(False, status=resp.status, error="Seite ist zu groß.")
                charset = resp.headers.get_content_charset() or "utf-8"
                return FetchResult(True, raw.decode(charset, "replace"), resp.status, final_url=resp.geturl())
        except urllib.error.HTTPError as e:
            return FetchResult(False, status=e.code, error=f"HTTP {e.code}")
        except Exception as e:  # noqa: BLE001
            return FetchResult(False, error=f"{type(e).__name__}: {e}"[:300])
