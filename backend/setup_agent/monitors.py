"""Source Monitor und Price Monitor (Phase 4).

Source Monitor: prüft freigegebene Quellen auf Änderungen und schlägt neue oder geänderte
Setup-Angaben vor (regelbasiert über den Product Resolver). Ist eine Quelle nicht abrufbar,
bleibt alles beim letzten bestätigten Stand; nur der Fehlversuch wird protokolliert.

Price Monitor: aktualisiert Preise aus konfigurierten, zulässigen Preisquellen. Preise ändern nur
Preisdaten. Manuell gepflegte Angebote (price_source = "manual") werden nicht angefasst.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Protocol

from . import repository as R
from .approval import NEW, ApprovalManager, AuditLogger
from .fetcher import Fetcher
from .identity import url_domain
from .models import (
    Actor,
    ActorType,
    AuditAction,
    Availability,
    Evidence,
    Money,
    Offer,
    Operation,
    Product,
    SetupClaim,
    Source,
    utcnow,
)
from .pricing import apply_check_failure, apply_observation
from .registry import SourceRegistry
from .resolver import ProductResolver

SOURCE_AGENT = Actor(type=ActorType.AGENT, id="source_monitor")
PRICE_AGENT = Actor(type=ActorType.AGENT, id="price_monitor")


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    p = _TextExtractor()
    p.feed(html)
    return " ".join(p.parts)


def content_hash(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).encode("utf-8")).hexdigest()


@dataclass
class SourceReport:
    checked: int = 0
    skipped: int = 0
    unchanged: int = 0
    failed: dict[str, str] = field(default_factory=dict)
    proposals: list[str] = field(default_factory=list)


class SourceMonitor:
    def __init__(self, repo: R.Repository, approvals: ApprovalManager, fetcher: Fetcher,
                 clock: Callable[[], datetime] = utcnow) -> None:
        self.repo, self.approvals, self.fetcher, self.clock = repo, approvals, fetcher, clock
        self.audit = AuditLogger(repo)

    def run(self) -> SourceReport:
        from .models import SourceRegistryEntry

        now = self.clock()
        report = SourceReport()
        registry = SourceRegistry(self.repo.list(R.REGISTRY, SourceRegistryEntry))
        resolver = ProductResolver(self.repo.list(R.PRODUCTS, Product))
        claims = self.repo.list(R.CLAIMS, SetupClaim)

        for source in self.repo.list(R.SOURCES, Source):
            url = str(source.url)
            decision = registry.check_auto_fetch(url, source.last_checked_at, now)
            use = registry.check_use(url, source.source_type)
            if not decision.allowed or not use.allowed:
                report.skipped += 1
                continue
            report.checked += 1
            result = self.fetcher.fetch(url)
            if result.ok and result.final_url and not registry.check_use(result.final_url, source.source_type).allowed:
                result = type(result)(False, error=f"Weiterleitung auf nicht zugelassene Domain {url_domain(result.final_url)}.")
            if not result.ok:
                self._record_failure(source, now, result.error or "unbekannter Fehler")
                report.failed[source.id] = result.error or "unbekannter Fehler"
                continue

            text = html_to_text(result.text) if "<" in result.text else result.text
            new_hash = content_hash(text)
            changed = new_hash != source.content_hash
            self._save_source(source, now, ok=True, content_hash=new_hash)
            if not changed:
                report.unchanged += 1
                continue
            if source.streamer_id is None:
                continue  # ohne Streamer-Bezug keine Setup-Angaben
            report.proposals += self._propose_from_text(source, text, resolver, claims, now)
        return report

    def _propose_from_text(self, source: Source, text: str, resolver: ProductResolver, claims: list[SetupClaim],
                           now: datetime) -> list[str]:
        created: list[str] = []
        products = {p.id: p for p in resolver.products}
        mentioned = set(resolver.find_mentions(text))
        evidence = Evidence(source_url=source.url, source_type=source.source_type, observed_at=now, retrieved_at=now,
                            note="Automatisch in freigegebener Quelle gefunden (regelbasiert).")
        own = [c for c in claims if c.streamer_id == source.streamer_id]

        for pid in sorted(mentioned):
            existing = [c for c in own if c.product_id == pid]
            if existing:
                c = existing[0]
                others = [e.model_dump(mode="json") for e in c.evidence if e.source_id != source.id]
                payload = {"evidence": others + [evidence.model_dump(mode="json")]}
                p, new = self.approvals.propose(entity_type="setup_claim", entity_id=c.id, operation=Operation.UPDATE,
                                                payload=payload, base_version=c.version, actor=SOURCE_AGENT, origin="source_monitor",
                                                reason=f"Quelle {url_domain(str(source.url))} nennt das Produkt weiterhin/erneut.",
                                                evidence_source_ids=[source.id])
            else:
                prod = products[pid]
                payload = {"streamer_id": source.streamer_id, "category": prod.category.value, "role": "primary",
                           "product_id": pid, "raw_name": f"{prod.manufacturer} {prod.model}",
                           "evidence": [evidence.model_dump(mode="json")]}
                p, new = self.approvals.propose(entity_type="setup_claim", entity_id=NEW, operation=Operation.CREATE,
                                                payload=payload, actor=SOURCE_AGENT, origin="source_monitor",
                                                reason=f"Neu in Quelle {url_domain(str(source.url))} gefunden.",
                                                evidence_source_ids=[source.id])
            if new:
                created.append(p.id)

        # Produkte, die diese Quelle früher belegt hat, aber nicht mehr nennt → nur zur Prüfung vorlegen
        for c in own:
            if c.product_id and c.product_id not in mentioned and any(e.source_id == source.id for e in c.evidence) and c.published:
                p, new = self.approvals.propose(
                    entity_type="setup_claim", entity_id=c.id, operation=Operation.UPDATE,
                    payload={"status": "outdated", "reason": "Nicht mehr in der Quelle genannt (automatisch erkannt, bitte prüfen)."},
                    base_version=c.version, actor=SOURCE_AGENT, origin="source_monitor",
                    reason=f"Quelle {url_domain(str(source.url))} nennt das Produkt nicht mehr.", evidence_source_ids=[source.id])
                if new:
                    created.append(p.id)
        return created

    def _save_source(self, source: Source, now: datetime, *, ok: bool, content_hash: str | None = None) -> None:
        update = {"last_checked_at": now, "last_check_ok": ok, "version": source.version + 1, "updated_at": now}
        if content_hash is not None:
            update["content_hash"] = content_hash
        self.repo.save(R.SOURCES, source.model_copy(update=update), expected_version=source.version)

    def _record_failure(self, source: Source, now: datetime, error: str) -> None:
        self._save_source(source, now, ok=False)
        self.audit.record(at=now, actor=SOURCE_AGENT, action=AuditAction.CHECK_FAILED, entity_type="source",
                          entity_id=source.id, reason=f"Abruf fehlgeschlagen: {error}"[:300])


# ---------------------------------------------------------------- Preise


@dataclass(frozen=True)
class PriceQuote:
    price: Money | None
    availability: Availability


class PriceSourceError(Exception):
    pass


class PriceSource(Protocol):
    name: str

    def lookup(self, offer: Offer) -> PriceQuote | None:
        """None = Quelle kennt dieses Angebot nicht. PriceSourceError = Abruf fehlgeschlagen."""
        ...


class JsonFeedPriceSource:
    """Preis-Feed als JSON, z. B. ein Produkt-Feed aus einem Partnerprogramm, dessen Bedingungen die Nutzung erlauben.

    Format: [{"url": "https://…", "amount_minor": 39900, "currency": "EUR", "availability": "in_stock"}, …]
    """

    def __init__(self, name: str, path: Path | None = None, url: str | None = None, fetcher: Fetcher | None = None) -> None:
        self.name, self.path, self.url, self.fetcher = name, path, url, fetcher
        self._index: dict[str, dict] | None = None

    def _load(self) -> dict[str, dict]:
        if self._index is None:
            try:
                if self.path:
                    raw = Path(self.path).read_text(encoding="utf-8")
                elif self.url and self.fetcher:
                    res = self.fetcher.fetch(self.url)
                    if not res.ok:
                        raise PriceSourceError(res.error or "Feed nicht abrufbar")
                    raw = res.text
                else:
                    raise PriceSourceError("Feed ohne Pfad oder URL.")
                items = json.loads(raw)
                if not isinstance(items, list):
                    raise PriceSourceError("Feed muss eine Liste sein.")
            except (OSError, json.JSONDecodeError) as e:
                raise PriceSourceError(f"Feed ungültig: {e}") from e
            from .identity import normalize_url
            self._index = {}
            for it in items:
                try:
                    self._index[normalize_url(it["url"])] = it
                except (KeyError, TypeError, ValueError):
                    continue  # einzelne kaputte Zeilen ignorieren
        return self._index

    def lookup(self, offer: Offer) -> PriceQuote | None:
        from .identity import normalize_url
        item = self._load().get(normalize_url(str(offer.url)))
        if item is None:
            return None
        try:
            price = None if item.get("amount_minor") is None else Money(amount_minor=item["amount_minor"], currency=item.get("currency", "EUR"))
            return PriceQuote(price, Availability(item.get("availability", "unknown")))
        except Exception as e:  # noqa: BLE001
            raise PriceSourceError(f"Ungültiger Eintrag im Feed: {e}") from e


@dataclass
class PriceReport:
    checked: int = 0
    changed: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)
    skipped: int = 0


class PriceMonitor:
    def __init__(self, repo: R.Repository, sources: list[PriceSource], clock: Callable[[], datetime] = utcnow,
                 interval: timedelta = timedelta(hours=20)) -> None:
        self.repo, self.clock, self.interval = repo, clock, interval
        self.sources = {s.name: s for s in sources}
        self.audit = AuditLogger(repo)

    def run(self) -> PriceReport:
        now = self.clock()
        report = PriceReport()
        for offer in self.repo.list(R.OFFERS, Offer):
            source = self.sources.get(offer.price_source)
            due = offer.checked_at is None or now - offer.checked_at >= self.interval
            if source is None or not due or offer.availability == Availability.DISCONTINUED:
                report.skipped += 1
                continue
            report.checked += 1
            try:
                quote = source.lookup(offer)
                if quote is None:
                    raise PriceSourceError("Angebot nicht mehr im Feed.")
            except PriceSourceError as e:
                updated = apply_check_failure(offer, now).model_copy(update={"version": offer.version + 1})
                self.repo.save(R.OFFERS, updated, expected_version=offer.version)
                self.audit.record(at=now, actor=PRICE_AGENT, action=AuditAction.CHECK_FAILED, entity_type="offer",
                                  entity_id=offer.id, reason=f"Preisabruf fehlgeschlagen: {e}"[:300], before=offer, after=updated)
                report.failed[offer.id] = str(e)
                continue
            result = apply_observation(offer, quote.price, quote.availability, now, source.name)
            updated = result.offer if result.change else result.offer.model_copy(update={"version": offer.version + 1})
            self.repo.save(R.OFFERS, updated, expected_version=offer.version)
            if result.observation:
                self.repo.add_observation(result.observation)
                self.audit.record(at=now, actor=PRICE_AGENT, action=AuditAction.UPDATE, entity_type="offer", entity_id=offer.id,
                                  reason=f"Preis/Verfügbarkeit laut {source.name} geändert.", before=offer, after=updated)
                report.changed.append(offer.id)
        return report
