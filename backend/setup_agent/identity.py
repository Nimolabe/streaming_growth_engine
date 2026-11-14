"""Deterministische IDs und Normalisierung.

Gleiche fachliche Eingaben ergeben immer dieselbe ID. Dadurch erzeugen wiederholte
Agent-Läufe keine doppelten Datensätze (siehe docs/setup-agent/VERIFIZIERUNG.md, Abschnitt 7).
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_UMLAUTS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "ae", "Ö": "oe", "Ü": "ue",
                          "ø": "o", "Ø": "o", "æ": "ae", "Æ": "ae", "œ": "oe", "Œ": "oe", "ł": "l", "Ł": "l"})
_TRACKING_PARAMS = re.compile(r"^(utm_.*|fbclid|gclid|mc_cid|mc_eid|ref|ref_src|si)$", re.IGNORECASE)


def _ascii(text: str) -> str:
    text = text.translate(_UMLAUTS)
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def slugify(text: str) -> str:
    """'Shure SM7B' -> 'shure-sm7b'."""
    slug = re.sub(r"[^a-z0-9]+", "-", _ascii(text).lower()).strip("-")
    if not slug:
        raise ValueError(f"Aus {text!r} lässt sich keine ID bilden.")
    return slug


def compact(text: str) -> str:
    """Für Vergleiche: klein, ASCII, ohne Leer-, Binde- und Unterstriche. 'SM-7B' -> 'sm7b'."""
    return re.sub(r"[^a-z0-9]", "", _ascii(text).lower())


def product_id(manufacturer: str, model: str) -> str:
    return slugify(f"{manufacturer} {model}")


def product_match_key(manufacturer: str, model: str) -> str:
    """Zwei Produkte mit gleichem Schlüssel gelten als Duplikat."""
    m, mo = compact(manufacturer), compact(model)
    if not m or not mo:
        raise ValueError("Hersteller und Modell dürfen nicht leer sein.")
    return f"{m}:{mo}"


def normalize_url(url: str) -> str:
    """Klein geschriebener Host ohne 'www.', ohne Fragment, ohne Tracking-Parameter, ohne End-Slash."""
    parts = urlsplit(url.strip())
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValueError(f"Ungültige URL: {url!r}")
    host = parts.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    query = urlencode(sorted((k, v) for k, v in parse_qsl(parts.query) if not _TRACKING_PARAMS.match(k)))
    path = parts.path.rstrip("/") or ""
    # http und https gelten als dieselbe Quelle
    return urlunsplit(("https", host, path, query, ""))


def url_domain(url: str) -> str:
    return urlsplit(normalize_url(url)).netloc


def _hash(*parts: Any, length: int = 16) -> str:
    raw = json.dumps(parts, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:length]


def source_id(url: str) -> str:
    return "s_" + _hash(normalize_url(url))


def claim_id(streamer_id: str, slot: str, product_id_or_none: str | None, raw_name: str) -> str:
    target = product_id_or_none or "raw:" + compact(raw_name)
    return "c_" + _hash(streamer_id, slot, target)


def offer_id(product_id_: str, retailer: str, url: str) -> str:
    return "o_" + _hash(product_id_, compact(retailer), normalize_url(url))


def dedupe_key(entity_type: str, entity_id: str, operation: str, payload: dict[str, Any]) -> str:
    return _hash(entity_type, entity_id, operation, payload, length=24)


def gtin_is_valid(code: str) -> bool:
    """Prüfziffer für GTIN-8/12/13/14 (EAN, UPC)."""
    if not code.isdigit() or len(code) not in (8, 12, 13, 14):
        return False
    digits = [int(c) for c in code]
    body, check = digits[:-1], digits[-1]
    total = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return (10 - total % 10) % 10 == check
