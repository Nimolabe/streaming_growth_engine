"""Product Resolver: ordnet Bezeichnungen aus Quellen eindeutig einem Katalogprodukt zu.

Regel (VERIFIZIERUNG.md, Abschnitt 4): Zuordnung nur bei genau einem exakten Treffer nach Normalisierung.
Ähnliche Namen werden höchstens als Vorschlag für die manuelle Prüfung genannt, nie automatisch zugeordnet.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

from .identity import compact
from .models import Product, ProductCategory


@dataclass(frozen=True)
class Resolution:
    product_id: str | None
    reason: str
    suggestions: list[str] = field(default_factory=list)  # nur Hinweise für Admins


class ProductResolver:
    def __init__(self, products: list[Product]) -> None:
        self.products = [p for p in products]
        self._full: dict[str, set[str]] = {}   # "shuresm7b" -> {product_id}
        self._model: dict[str, set[str]] = {}  # "sm7b" -> {product_id}
        for p in self.products:
            names = {p.model, *p.aliases}
            for n in names:
                self._full.setdefault(compact(p.manufacturer + n), set()).add(p.id)
                self._model.setdefault(compact(n), set()).add(p.id)
            for a in p.aliases:  # Aliase dürfen den Hersteller schon enthalten ("Shure SM-7B")
                if compact(a).startswith(compact(p.manufacturer)):
                    self._full.setdefault(compact(a), set()).add(p.id)
        self._by_id = {p.id: p for p in self.products}

    def resolve(self, raw_name: str, category: ProductCategory | None = None) -> Resolution:
        key = compact(raw_name)
        if not key:
            return Resolution(None, "Leere Bezeichnung.")
        hits = self._filter(self._full.get(key, set()), category)
        if not hits:
            hits = self._filter(self._model.get(key, set()), category)
        if len(hits) == 1:
            pid = next(iter(hits))
            return Resolution(pid, f"Eindeutig zugeordnet: {self._label(pid)}.")
        if len(hits) > 1:
            names = sorted(self._label(h) for h in hits)
            return Resolution(None, f"Mehrdeutig: passt auf {', '.join(names)}.", sorted(hits))
        return Resolution(None, "Kein Katalogprodukt gefunden.", self._similar(key, category))

    def find_mentions(self, text: str, categories: set[ProductCategory] | None = None) -> list[str]:
        """Regelbasierter Extraktor: Produkte, deren Hersteller+Modell oder Alias wörtlich im Text steht.
        Modellnamen allein reichen nicht (zu viele Fehltreffer)."""
        hay = " " + re.sub(r"[^a-z0-9]+", " ", text.lower()) + " "
        found: list[str] = []
        for p in self.products:
            if categories and p.category not in categories:
                continue
            candidates = [f"{p.manufacturer} {n}" for n in (p.model, *p.aliases)] + [a for a in p.aliases if compact(p.manufacturer) in compact(a)]
            for c in candidates:
                needle = " " + re.sub(r"[^a-z0-9]+", " ", c.lower()).strip() + " "
                if needle.strip() and needle in hay:
                    found.append(p.id)
                    break
        # Bei Treffern wie "sm7b" und "sm7db" gewinnt die genauere Übereinstimmung automatisch,
        # weil nur ganze Wörter verglichen werden.
        return sorted(set(found))

    def _filter(self, ids: set[str], category: ProductCategory | None) -> set[str]:
        return {i for i in ids if category is None or self._by_id[i].category == category}

    def _label(self, pid: str) -> str:
        p = self._by_id[pid]
        return f"{p.manufacturer} {p.model}"

    def _similar(self, key: str, category: ProductCategory | None) -> list[str]:
        pool = {compact(p.manufacturer + p.model): p.id for p in self.products if category is None or p.category == category}
        return [pool[k] for k in difflib.get_close_matches(key, list(pool), n=3, cutoff=0.75)]
