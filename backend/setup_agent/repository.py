"""Speicher-Schnittstelle. Die Geschäftslogik kennt nur dieses Protokoll.

Phase 1: Protokoll + In-Memory-Umsetzung für Tests.
Phase 2: Firestore-Adapter mit identischem Verhalten (gleiche Tests).
"""

from __future__ import annotations

from typing import Protocol, TypeVar

from pydantic import BaseModel

from .models import AuditEntry, ChangeProposal, Product

T = TypeVar("T", bound=BaseModel)


class RepositoryError(Exception):
    code = "storage_error"


class NotFound(RepositoryError):
    code = "not_found"


class VersionConflict(RepositoryError):
    code = "version_conflict"


class Duplicate(RepositoryError):
    code = "duplicate"


class StorageUnavailable(RepositoryError):
    code = "storage_unavailable"


class Repository(Protocol):
    def get(self, collection: str, entity_id: str, model: type[T]) -> T: ...

    def list(self, collection: str, model: type[T]) -> list[T]: ...

    def save(self, collection: str, entity: BaseModel, *, expected_version: int | None) -> None:
        """expected_version=None heißt: Datensatz darf noch nicht existieren (Neuanlage)."""
        ...

    def add_proposal(self, proposal: ChangeProposal) -> tuple[ChangeProposal, bool]:
        """Gibt (Vorschlag, neu_angelegt) zurück. Gleicher dedupe_key → bestehender Vorschlag."""
        ...

    def append_audit(self, entry: AuditEntry) -> None: ...

    def audit_log(self, entity_type: str | None = None, entity_id: str | None = None) -> list[AuditEntry]: ...


class InMemoryRepository:
    """Für Tests und lokale Entwicklung. Kopiert beim Lesen und Schreiben, damit nichts von außen mutiert."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, dict]] = {}
        self._audit: list[AuditEntry] = []
        self.available = True

    def _check(self) -> None:
        if not self.available:
            raise StorageUnavailable("Speicher nicht erreichbar.")

    def get(self, collection: str, entity_id: str, model: type[T]) -> T:
        self._check()
        try:
            return model.model_validate(self._data[collection][entity_id])
        except KeyError:
            raise NotFound(f"{collection}/{entity_id}") from None

    def list(self, collection: str, model: type[T]) -> list[T]:
        self._check()
        return [model.model_validate(v) for _, v in sorted(self._data.get(collection, {}).items())]

    def save(self, collection: str, entity: BaseModel, *, expected_version: int | None) -> None:
        self._check()
        entity_id = getattr(entity, "id")
        coll = self._data.setdefault(collection, {})
        current = coll.get(entity_id)
        if expected_version is None:
            if current is not None:
                raise Duplicate(f"{collection}/{entity_id} existiert bereits.")
            if isinstance(entity, Product):
                if any(v.get("match_key") == entity.match_key for v in coll.values()):
                    raise Duplicate(f"Produkt mit match_key {entity.match_key} existiert bereits.")
        else:
            if current is None:
                raise NotFound(f"{collection}/{entity_id}")
            if current.get("version") != expected_version:
                raise VersionConflict(f"{collection}/{entity_id}: erwartet v{expected_version}, gespeichert v{current.get('version')}.")
            if getattr(entity, "version", None) != expected_version + 1:
                raise VersionConflict("Neue Version muss expected_version + 1 sein.")
        # Gespeichert wird inkl. abgeleiteter Felder (für Abfragen); beim Lesen werden sie neu berechnet.
        coll[entity_id] = entity.model_dump(mode="json")

    def add_proposal(self, proposal: ChangeProposal) -> tuple[ChangeProposal, bool]:
        self._check()
        coll = self._data.setdefault("change_proposals", {})
        existing = coll.get(proposal.id)
        if existing is not None:
            return ChangeProposal.model_validate(existing), False
        coll[proposal.id] = proposal.model_dump(mode="json")
        return proposal, True

    def append_audit(self, entry: AuditEntry) -> None:
        self._check()
        self._audit.append(entry)

    def audit_log(self, entity_type: str | None = None, entity_id: str | None = None) -> list[AuditEntry]:
        self._check()
        return [
            e
            for e in self._audit
            if (entity_type is None or e.entity_type == entity_type) and (entity_id is None or e.entity_id == entity_id)
        ]

