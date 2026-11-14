"""Preisregeln (VERIFIZIERUNG.md, Abschnitt 5).

Diese Funktionen verändern ausschließlich Preis- und Händlerdaten, nie Setup-Angaben.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from .models import Availability, Money, Offer, PriceObservation

STALE_AFTER = timedelta(days=14)
REVIEW_AFTER_FAILURES = 3


class PriceState(StrEnum):
    CURRENT = "current"
    STALE = "stale"
    UNKNOWN = "unknown"


def price_state(offer: Offer, now: datetime) -> PriceState:
    if offer.price is None or offer.last_success_at is None:
        return PriceState.UNKNOWN
    if now - offer.last_success_at > STALE_AFTER:
        return PriceState.STALE
    return PriceState.CURRENT


def needs_review(offer: Offer) -> bool:
    return offer.failed_checks >= REVIEW_AFTER_FAILURES


@dataclass(frozen=True)
class PriceChange:
    offer_id: str
    old_price: Money | None
    new_price: Money | None
    old_availability: Availability
    new_availability: Availability


@dataclass(frozen=True)
class CheckResult:
    offer: Offer
    change: PriceChange | None
    observation: PriceObservation | None  # None = nichts Neues für den Verlauf


def apply_observation(offer: Offer, price: Money | None, availability: Availability, at: datetime, source: str) -> CheckResult:
    """Erfolgreicher Abruf. Gleicher Preis und gleiche Verfügbarkeit erzeugen keine neue Beobachtung."""
    changed = offer.price != price or offer.availability != availability
    updated = offer.model_copy(
        update={
            "price": price,
            "availability": availability,
            "checked_at": at,
            "last_success_at": at,
            "failed_checks": 0,
            "price_source": source,
            "version": offer.version + (1 if changed else 0),
            "updated_at": at if changed else offer.updated_at,
        }
    )
    if not changed:
        return CheckResult(updated, None, None)
    change = PriceChange(offer.id, offer.price, price, offer.availability, availability)
    obs = PriceObservation(offer_id=offer.id, price=price, availability=availability, observed_at=at, price_source=source)
    return CheckResult(updated, change, obs)


def apply_check_failure(offer: Offer, at: datetime) -> Offer:
    """Abruf fehlgeschlagen: letzter bekannter Preis bleibt, nichts wird erfunden."""
    return offer.model_copy(update={"checked_at": at, "failed_checks": offer.failed_checks + 1})
