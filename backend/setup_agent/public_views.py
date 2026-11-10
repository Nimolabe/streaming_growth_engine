"""Öffentliche Sicht auf die Daten (nur freigegebene Angaben).

Dieselben Funktionen erzeugen die statischen JSON-Dateien (exporter.py) und die API-Antworten (api.py),
damit beide garantiert gleich aussehen (API.md).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from . import repository as R
from .models import Offer, Product, ProductCategory, SetupClaim, Streamer
from .pricing import price_state
from .verification import is_publishable

API_VERSION = "v1"


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat().replace("+00:00", "Z") if dt else None


class PublicData:
    """Lädt alles einmal und beantwortet dann alle öffentlichen Abfragen."""

    def __init__(self, repo: R.Repository, now: datetime) -> None:
        self.now = now
        self.streamers = {s.id: s for s in repo.list(R.STREAMERS, Streamer) if s.active}
        self.products = {p.id: p for p in repo.list(R.PRODUCTS, Product)}
        self.offers: dict[str, list[Offer]] = {}
        for o in repo.list(R.OFFERS, Offer):
            self.offers.setdefault(o.product_id, []).append(o)
        self.claims: dict[str, list[SetupClaim]] = {}
        for c in repo.list(R.CLAIMS, SetupClaim):
            if is_publishable(c) and c.streamer_id in self.streamers and c.product_id in self.products:
                self.claims.setdefault(c.streamer_id, []).append(c)

    # ---------------------------------------------------------- Bausteine

    def product_summary(self, p: Product) -> dict[str, Any]:
        best = self.best_price(p.id)
        return {"id": p.id, "manufacturer": p.manufacturer, "model": p.model, "category": p.category.value,
                "variant": p.variant, "discontinued": p.discontinued, "best_price": best}

    def offer_view(self, o: Offer) -> dict[str, Any]:
        return {"id": o.id, "retailer": o.retailer, "url": str(o.url),
                "price": o.price.model_dump() if o.price else None, "availability": o.availability.value,
                "price_state": price_state(o, self.now).value, "last_success_at": _iso(o.last_success_at)}

    def best_price(self, product_id: str) -> dict[str, Any] | None:
        """Günstigstes aktuelles Angebot (nur Preise, die nicht veraltet sind)."""
        current = [o for o in self.offers.get(product_id, []) if o.price and price_state(o, self.now).value == "current"
                   and o.availability.value not in ("out_of_stock", "discontinued")]
        if not current:
            return None
        o = min(current, key=lambda o: (o.price.currency, o.price.amount_minor))  # type: ignore[union-attr]
        return {**o.price.model_dump(), "retailer": o.retailer, "offer_id": o.id}  # type: ignore[union-attr]

    def streamer_summary(self, s: Streamer) -> dict[str, Any]:
        return {"id": s.id, "display_name": s.display_name, "categories": [c.value for c in s.categories],
                "platforms": [{"platform": a.platform.value, "handle": a.handle, "url": str(a.url)} for a in s.platforms],
                "primary_language": s.primary_language, "setup_items": len(self.claims.get(s.id, []))}

    # ---------------------------------------------------------- Endpunkte

    def list_streamers(self, category: str | None = None, platform: str | None = None, language: str | None = None,
                       q: str | None = None) -> list[dict[str, Any]]:
        out = []
        for s in sorted(self.streamers.values(), key=lambda s: s.display_name.lower()):
            if category and category not in [c.value for c in s.categories]:
                continue
            if platform and platform not in [a.platform.value for a in s.platforms]:
                continue
            if language and s.primary_language != language:
                continue
            if q and q.lower() not in s.display_name.lower():
                continue
            out.append(self.streamer_summary(s))
        return out

    def streamer(self, streamer_id: str) -> dict[str, Any] | None:
        s = self.streamers.get(streamer_id)
        return None if s is None else {**self.streamer_summary(s), "profile_links": [str(u) for u in s.profile_links]}

    def setup(self, streamer_id: str, category: str | None = None) -> dict[str, Any] | None:
        if streamer_id not in self.streamers:
            return None
        items = []
        for c in sorted(self.claims.get(streamer_id, []), key=lambda c: (c.category.value, c.role)):
            if category and c.category.value != category:
                continue
            items.append({
                "claim_id": c.id, "category": c.category.value, "role": c.role,
                "product": self.product_summary(self.products[c.product_id]),  # type: ignore[index]
                "status": c.status.value, "confidence_level": c.confidence_level.value, "reason": c.reason,
                "last_verified_at": _iso(c.last_verified_at),
                "sources": [{"url": str(e.source_url), "source_type": e.source_type.value, "observed_at": _iso(e.observed_at),
                             "media_timestamp": e.media_timestamp} for e in sorted(c.evidence, key=lambda e: e.observed_at, reverse=True)],
            })
        return {"streamer_id": streamer_id, "items": items}

    def list_products(self, category: str | None = None, min_price: int | None = None, max_price: int | None = None,
                      currency: str = "EUR", q: str | None = None) -> list[dict[str, Any]]:
        out = []
        for p in sorted(self.products.values(), key=lambda p: (p.category.value, p.manufacturer.lower(), p.model.lower())):
            if category and p.category.value != category:
                continue
            if q and q.lower() not in f"{p.manufacturer} {p.model}".lower():
                continue
            summary = self.product_summary(p)
            if min_price is not None or max_price is not None:
                best = summary["best_price"]
                if best is None or best["currency"] != currency:
                    continue
                if min_price is not None and best["amount_minor"] < min_price:
                    continue
                if max_price is not None and best["amount_minor"] > max_price:
                    continue
            out.append(summary)
        return out

    def product(self, product_id: str) -> dict[str, Any] | None:
        p = self.products.get(product_id)
        if p is None:
            return None
        return {**self.product_summary(p), "aliases": p.aliases, "gtin": p.gtin, "specs": p.specs}

    def offers_for(self, product_id: str) -> list[dict[str, Any]] | None:
        if product_id not in self.products:
            return None
        offers = sorted(self.offers.get(product_id, []), key=lambda o: (o.price is None, o.price.amount_minor if o.price else 0))
        return [self.offer_view(o) for o in offers]

    def alternatives(self, product_id: str, max_price: int | None = None, limit: int = 5) -> list[dict[str, Any]] | None:
        p = self.products.get(product_id)
        if p is None:
            return None
        own = self.best_price(product_id)
        ceiling = max_price if max_price is not None else (own["amount_minor"] if own else None)
        alts = []
        for other in self.products.values():
            if other.id == p.id or other.category != p.category or other.discontinued:
                continue
            best = self.best_price(other.id)
            if best is None or (own and best["currency"] != own["currency"]):
                continue
            if ceiling is not None and best["amount_minor"] > ceiling:
                continue
            alts.append(self.product_summary(other))
        alts.sort(key=lambda a: a["best_price"]["amount_minor"])
        return alts[: max(1, min(limit, 20))]

    def data_as_of(self) -> str | None:
        stamps = [s.updated_at for s in self.streamers.values()] + [p.updated_at for p in self.products.values()]
        stamps += [c.updated_at for cs in self.claims.values() for c in cs]
        stamps += [o.updated_at for os in self.offers.values() for o in os]
        return _iso(max(stamps)) if stamps else None

    def meta(self) -> dict[str, Any]:
        return {"api_version": API_VERSION, "data_as_of": self.data_as_of(),
                "counts": {"streamers": len(self.streamers), "products": len(self.products),
                           "published_setup_items": sum(len(v) for v in self.claims.values())},
                "categories": [c.value for c in ProductCategory]}
