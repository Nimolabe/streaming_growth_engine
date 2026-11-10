"""Speicher-Schnittstelle. Die Geschäftslogik kennt nur dieses Protokoll.

Umsetzungen: InMemoryRepository (Tests, lokale Entwicklung) und
FirestoreRepository (firestore_repo.py, Produktion). Beide erfüllen dieselben Tests.
"""

from __future__ import annotations

import copy
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

from .models import AuditEntry, ChangeProposal, PriceObservation, Product, ProposalStatus

T = TypeVar("T", bound=BaseModel)

# Collection-Namen (identisch in Firestore)
STREAMERS = "streamers"
CLAIMS = "setup_claims"
PRODUCTS = "products"
OFFERS = "offers"
SOURCES = "sources"
REGISTRY = "source_registry"
PROPOSALS = "change_proposals"
AUDIT = "audit_log"
META = "meta"
OBSERVATIONS = "observations"  # Unter-Collection von offers/{id}


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

    def find(self, collection: str, entity_id: str, model: type[T]) -> T | None: ...

    def list(self, collection: str, model: type[T]) -> list[T]: ...

    def save(self, collection: str, entity: BaseModel, *, expected_version: int | None) -> None:
        """expected_version=None heißt Neuanlage (darf nicht existieren), sonst optimistisches Sperren."""
        ...

    def add_proposal(self, proposal: ChangeProposal) -> tuple[ChangeProposal, bool]:
        """(Vorschlag, neu_angelegt). Gleiche ID → bestehender Vorschlag, nichts wird doppelt angelegt."""
        ...

    def update_proposal(self, proposal: ChangeProposal, *, expected_status: ProposalStatus, expected_applied: bool) -> None:
        """Nur wenn der gespeicherte Vorschlag noch den erwarteten Zustand hat (sonst VersionConflict)."""
        ...

    def list_proposals(self, status: ProposalStatus | None = None) -> list[ChangeProposal]: ...

    def append_audit(self, entry: AuditEntry) -> None: ...

    def audit_log(self, entity_type: str | None = None, entity_id: str | None = None) -> list[AuditEntry]: ...

    def add_observation(self, observation: PriceObservation) -> None: ...

    def observations(self, offer_id: str) -> list[PriceObservation]: ...

    def get_meta(self, key: str) -> dict[str, Any]: ...

    def set_meta(self, key: str, value: dict[str, Any]) -> None: ...


def dump(entity: BaseModel) -> dict[str, Any]:
    """Speicherformat: JSON-kompatibel, inkl. abgeleiteter Felder (für Abfragen in Firestore)."""
    return entity.model_dump(mode="json")


class InMemoryRepository:
    """Für Tests und lokale Entwicklung. Speichert JSON-Kopien, damit nichts von außen mutiert."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, dict]] = {}
        self._audit: list[AuditEntry] = []
        self._observations: dict[str, list[dict]] = {}
        self._meta: dict[str, dict] = {}
        self.available = True

    def _check(self) -> None:
        if not self.available:
            raise StorageUnavailable("Speicher nicht erreichbar.")

    def get(self, collection: str, entity_id: str, model: type[T]) -> T:
        found = self.find(collection, entity_id, model)
        if found is None:
            raise NotFound(f"{collection}/{entity_id}")
        return found

    def find(self, collection: str, entity_id: str, model: type[T]) -> T | None:
        self._check()
        raw = self._data.get(collection, {}).get(entity_id)
        return None if raw is None else model.model_validate(raw)

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
            if isinstance(entity, Product) and any(v.get("match_key") == entity.match_key for v in coll.values()):
                raise Duplicate(f"Produkt mit match_key {entity.match_key} existiert bereits.")
        else:
            if current is None:
                raise NotFound(f"{collection}/{entity_id}")
            if current.get("version") != expected_version:
                raise VersionConflict(
                    f"{collection}/{entity_id}: erwartet v{expected_version}, gespeichert v{current.get('version')}."
                )
            if getattr(entity, "version", None) != expected_version + 1:
                raise VersionConflict("Neue Version muss expected_version + 1 sein.")
        coll[entity_id] = dump(entity)

    def add_proposal(self, proposal: ChangeProposal) -> tuple[ChangeProposal, bool]:
        self._check()
        coll = self._data.setdefault(PROPOSALS, {})
        existing = coll.get(proposal.id)
        if existing is not None:
            return ChangeProposal.model_validate(existing), False
        coll[proposal.id] = dump(proposal)
        return proposal, True

    def update_proposal(self, proposal: ChangeProposal, *, expected_status: ProposalStatus, expected_applied: bool) -> None:
        self._check()
        coll = self._data.setdefault(PROPOSALS, {})
        current = coll.get(proposal.id)
        if current is None:
            raise NotFound(f"{PROPOSALS}/{proposal.id}")
        if current["status"] != expected_status.value or (current.get("applied_at") is not None) != expected_applied:
            raise VersionConflict(f"Vorschlag {proposal.id} wurde zwischenzeitlich geändert.")
        coll[proposal.id] = dump(proposal)

    def list_proposals(self, status: ProposalStatus | None = None) -> list[ChangeProposal]:
        return [p for p in self.list(PROPOSALS, ChangeProposal) if status is None or p.status == status]

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

    def add_observation(self, observation: PriceObservation) -> None:
        self._check()
        self._observations.setdefault(observation.offer_id, []).append(dump(observation))

    def observations(self, offer_id: str) -> list[PriceObservation]:
        self._check()
        return [PriceObservation.model_validate(o) for o in self._observations.get(offer_id, [])]

    def get_meta(self, key: str) -> dict[str, Any]:
        self._check()
        return copy.deepcopy(self._meta.get(key, {}))

    def set_meta(self, key: str, value: dict[str, Any]) -> None:
        self._check()
        self._meta[key] = copy.deepcopy(value)
