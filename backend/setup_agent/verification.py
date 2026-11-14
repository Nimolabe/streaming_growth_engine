"""Confidence Evaluator und Setup-Verifier-Regeln.

Regeln und Zahlen: docs/setup-agent/VERIFIZIERUNG.md, Abschnitte 1–3 und 6.
Alle Funktionen sind rein: Sie lesen nichts, schreiben nichts und bekommen die Uhrzeit übergeben.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .models import ConfidenceLevel, Evidence, SetupClaim, SourceType, VerificationStatus

SOURCE_WEIGHTS: dict[SourceType, float] = {
    SourceType.OFFICIAL_STATEMENT: 0.95,
    SourceType.OWN_SETUP_PAGE: 0.90,
    SourceType.VIDEO_STATEMENT: 0.85,
    SourceType.MANUFACTURER: 0.80,
    SourceType.VIDEO_VISUAL: 0.60,
    SourceType.THIRD_PARTY: 0.40,
}

FRESH_DAYS = 365
AGING_DAYS = 730
FRESH_FACTOR, AGING_FACTOR, STALE_FACTOR = 1.0, 0.7, 0.4
CORROBORATION_BONUS = 0.05
MAX_CONFIDENCE = 0.99
CONFLICT_WINDOW = timedelta(days=30)


def freshness_factor(evidence: Evidence, now: datetime) -> float:
    age = (now - evidence.observed_at).days
    if age <= FRESH_DAYS:
        return FRESH_FACTOR
    if age <= AGING_DAYS:
        return AGING_FACTOR
    return STALE_FACTOR


def confidence_score(evidence: list[Evidence], now: datetime) -> float:
    if not evidence:
        return 0.0
    scored = sorted(
        ((SOURCE_WEIGHTS[e.source_type] * freshness_factor(e, now), e) for e in evidence),
        key=lambda t: t[0],
        reverse=True,
    )
    best_score, best = scored[0]
    fresh_domains = {e.domain for e in evidence if freshness_factor(e, now) == FRESH_FACTOR}
    fresh_domains.discard(best.domain)
    score = best_score + CORROBORATION_BONUS * len(fresh_domains)
    return round(min(score, MAX_CONFIDENCE), 4)


def confidence_level(score: float) -> ConfidenceLevel:
    if score >= 0.8:
        return ConfidenceLevel.HIGH
    if score >= 0.5:
        return ConfidenceLevel.MEDIUM
    if score > 0:
        return ConfidenceLevel.LOW
    return ConfidenceLevel.NONE


@dataclass(frozen=True)
class Verdict:
    status: VerificationStatus
    confidence: float
    level: ConfidenceLevel
    reasons: list[str] = field(default_factory=list)

    @property
    def reason(self) -> str:
        return " ".join(self.reasons)


def evaluate_claim(
    claim: SetupClaim, now: datetime, *, conflicting: bool = False, superseded: bool = False
) -> Verdict:
    """Empfohlener Status für eine Angabe. Ändert die Angabe nicht."""
    ev = claim.evidence
    score = confidence_score(ev, now)
    level = confidence_level(score)

    def verdict(status: VerificationStatus, *reasons: str) -> Verdict:
        return Verdict(status, score, level, list(reasons))

    if not ev:  # Regel 1 (durch das Modell eigentlich ausgeschlossen)
        return Verdict(VerificationStatus.UNKNOWN, 0.0, ConfidenceLevel.NONE, ["Kein Beleg vorhanden."])
    if claim.product_id is None:  # Regel 2
        return verdict(VerificationStatus.UNKNOWN, f"Produkt „{claim.raw_name}“ ist nicht eindeutig zugeordnet.")
    if conflicting:  # Regel 3
        return verdict(VerificationStatus.CONFLICTING, "Widersprüchliche aktuelle Belege im selben Slot, manuelle Prüfung nötig.")
    if superseded:  # Regel 4
        return verdict(VerificationStatus.OUTDATED, "Durch einen neueren Primärbeleg für ein anderes Produkt abgelöst.")

    ages = [(now - e.observed_at).days for e in ev]
    if min(ages) > AGING_DAYS:  # Regel 5
        return verdict(VerificationStatus.OUTDATED, f"Alle Belege sind älter als {AGING_DAYS} Tage.")

    fresh_primary = [e for e in ev if e.is_primary and (now - e.observed_at).days <= FRESH_DAYS]
    if fresh_primary:  # Regel 6
        types = ", ".join(sorted({e.source_type.value for e in fresh_primary}))
        return verdict(VerificationStatus.CONFIRMED, f"Aktueller Primärbeleg ({types}).")

    if any(e.is_primary for e in ev):  # Regel 7
        return verdict(VerificationStatus.PROBABLE, f"Primärbeleg ist älter als {FRESH_DAYS} Tage, aktueller Stand unklar.")
    return verdict(VerificationStatus.PROBABLE, "Nur Sekundärquellen, keine Aussage des Streamers oder Herstellers.")


def _newest_primary(claim: SetupClaim) -> datetime | None:
    dates = [e.observed_at for e in claim.evidence if e.is_primary]
    return max(dates) if dates else None


@dataclass(frozen=True)
class SlotFlags:
    conflicting: set[str]
    superseded: set[str]


def analyze_slots(claims: list[SetupClaim], now: datetime) -> SlotFlags:
    """Erkennt Widersprüche und Ablösungen pro Streamer und Slot (VERIFIZIERUNG.md, Abschnitt 3)."""
    conflicting: set[str] = set()
    superseded: set[str] = set()
    by_slot: dict[tuple[str, str], list[SetupClaim]] = defaultdict(list)
    for c in claims:
        if c.product_id is None:
            continue
        if min((now - e.observed_at).days for e in c.evidence) > AGING_DAYS:
            continue  # ohnehin veraltet
        by_slot[(c.streamer_id, c.slot)].append(c)

    for group in by_slot.values():
        dated = [(d, c) for c in group if (d := _newest_primary(c)) is not None]
        if len({c.product_id for _, c in dated}) < 2:
            continue
        # Neuester Primärbeleg je Produkt
        newest: dict[str, tuple[datetime, SetupClaim]] = {}
        for d, c in dated:
            if c.product_id not in newest or d > newest[c.product_id][0]:
                newest[c.product_id] = (d, c)
        ranked = sorted(newest.values(), key=lambda t: t[0], reverse=True)
        lead_date = ranked[0][0]
        close = [c for d, c in ranked if lead_date - d <= CONFLICT_WINDOW]
        if len(close) > 1:
            conflicting.update(c.id for c in close)
        for d, c in ranked:
            if lead_date - d > CONFLICT_WINDOW:
                superseded.add(c.id)
    return SlotFlags(conflicting, superseded)


PUBLIC_STATUSES = frozenset({VerificationStatus.CONFIRMED, VerificationStatus.PROBABLE})


def is_publishable(claim: SetupClaim) -> bool:
    """Öffentlich nur mit Admin-Freigabe und Status bestätigt oder (gekennzeichnet) wahrscheinlich."""
    return claim.published and claim.status in PUBLIC_STATUSES and claim.product_id is not None
