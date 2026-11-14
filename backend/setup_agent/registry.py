"""Source Registry: welche Quellen sind zugelassen, und dürfen sie automatisch abgerufen werden?

Standard ist 'nur manuell'. Automatischer Abruf nur mit geprüften Nutzungsbedingungen,
technisch zulässiger Zugriffsart und Mindestabstand zwischen Abrufen (ARCHITEKTUR.md, Abschnitt 5).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .identity import url_domain
from .models import AccessMethod, SourceRegistryEntry, SourceType


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str
    entry: SourceRegistryEntry | None = None


class SourceRegistry:
    def __init__(self, entries: list[SourceRegistryEntry]) -> None:
        self.entries = {e.domain: e for e in entries}

    def lookup(self, url: str) -> SourceRegistryEntry | None:
        """Exakte Domain oder übergeordnete Domain (videos.beispiel.example → beispiel.example)."""
        host = url_domain(url)
        parts = host.split(".")
        for i in range(len(parts) - 1):
            entry = self.entries.get(".".join(parts[i:]))
            if entry:
                return entry
        return None

    def check_use(self, url: str, source_type: SourceType) -> Decision:
        entry = self.lookup(url)
        if entry is None:
            return Decision(False, f"Domain {url_domain(url)} ist nicht in der Source Registry.")
        if not entry.enabled:
            return Decision(False, f"Quelle {entry.domain} ist deaktiviert.", entry)
        if source_type not in entry.source_types:
            return Decision(False, f"Quellentyp {source_type.value} ist für {entry.domain} nicht zugelassen.", entry)
        return Decision(True, "Zugelassen.", entry)

    def check_auto_fetch(self, url: str, last_fetch: datetime | None, now: datetime) -> Decision:
        entry = self.lookup(url)
        if entry is None or not entry.enabled:
            return Decision(False, "Nicht registriert oder deaktiviert.", entry)
        if not entry.auto_fetch_allowed or entry.access_method == AccessMethod.MANUAL:
            return Decision(False, "Nur manuelle Prüfung erlaubt.", entry)
        if last_fetch is not None and now - last_fetch < timedelta(hours=entry.min_interval_hours):
            return Decision(False, f"Mindestabstand von {entry.min_interval_hours} h noch nicht erreicht.", entry)
        return Decision(True, "Automatischer Abruf erlaubt.", entry)
