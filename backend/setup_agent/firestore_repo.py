"""Firestore-Adapter für das Repository-Protokoll.

Nutzt den offiziellen Python-Client (über firebase-admin). Gleichzeitige Änderungen werden über
Vorbedingungen abgesichert: Neuanlage mit create() (schlägt fehl, wenn es das Dokument gibt),
Änderungen mit update(..., option=last_update_time), damit nichts unbemerkt überschrieben wird.

Lokal getestet mit einem nachgebauten Client (tests/fake_firestore.py), nicht gegen echtes Firestore.
"""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from . import repository as R
from .models import AuditEntry, ChangeProposal, PriceObservation, Product, ProposalStatus

T = TypeVar("T", bound=BaseModel)

_UNAVAILABLE = {"ServiceUnavailable", "DeadlineExceeded", "RetryError", "InternalServerError", "TooManyRequests",
                "ResourceExhausted", "GatewayTimeout", "Unknown", "ConnectionError", "TransportError"}


def _translate(e: Exception) -> Exception:
    name = type(e).__name__
    if name == "AlreadyExists":
        return R.Duplicate(str(e))
    if name == "FailedPrecondition":
        return R.VersionConflict("Datensatz wurde zwischenzeitlich geändert.")
    if name == "NotFound":
        return R.NotFound(str(e))
    if name in _UNAVAILABLE:
        return R.StorageUnavailable(f"Firestore nicht erreichbar ({name}).")
    return e


class FirestoreRepository:
    def __init__(self, client: Any) -> None:
        self.db = client
        self.invalid_proposals: dict[str, str] = {}

    @classmethod
    def from_service_account(cls, credentials_json: str | dict, project_id: str | None = None) -> "FirestoreRepository":
        import json

        import firebase_admin  # type: ignore[import-not-found]
        from firebase_admin import credentials, firestore  # type: ignore[import-not-found]

        info = json.loads(credentials_json) if isinstance(credentials_json, str) else credentials_json
        app = firebase_admin.initialize_app(credentials.Certificate(info), {"projectId": project_id or info.get("project_id")},
                                            name="setup-agent")
        return cls(firestore.client(app))

    def _call(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:  # noqa: BLE001 – wird übersetzt
            translated = _translate(e)
            if translated is e:
                raise
            raise translated from e

    # ------------------------------------------------------------ Entitäten

    def find(self, collection: str, entity_id: str, model: type[T]) -> T | None:
        snap = self._call(self.db.collection(collection).document(entity_id).get)
        if not snap.exists:
            return None
        data = snap.to_dict()
        if collection == R.PROPOSALS:
            data["id"] = snap.id  # Admin-Seite speichert die ID nur als Dokument-ID
        return model.model_validate(data)

    def get(self, collection: str, entity_id: str, model: type[T]) -> T:
        found = self.find(collection, entity_id, model)
        if found is None:
            raise R.NotFound(f"{collection}/{entity_id}")
        return found

    def list(self, collection: str, model: type[T]) -> list[T]:
        docs = self._call(lambda: list(self.db.collection(collection).stream()))
        extra = (lambda d: {"id": d.id}) if collection == R.PROPOSALS else (lambda d: {})
        return [model.model_validate({**d.to_dict(), **extra(d)}) for d in sorted(docs, key=lambda d: d.id)]

    def save(self, collection: str, entity: BaseModel, *, expected_version: int | None) -> None:
        entity_id = getattr(entity, "id")
        ref = self.db.collection(collection).document(entity_id)
        data = R.dump(entity)
        if expected_version is None:
            if isinstance(entity, Product):
                dup = self._call(lambda: list(self.db.collection(collection).where("match_key", "==", entity.match_key).limit(1).stream()))
                if dup:
                    raise R.Duplicate(f"Produkt mit match_key {entity.match_key} existiert bereits.")
            self._call(ref.create, data)
            return
        snap = self._call(ref.get)
        if not snap.exists:
            raise R.NotFound(f"{collection}/{entity_id}")
        stored = snap.to_dict().get("version")
        if stored != expected_version:
            raise R.VersionConflict(f"{collection}/{entity_id}: erwartet v{expected_version}, gespeichert v{stored}.")
        if getattr(entity, "version", None) != expected_version + 1:
            raise R.VersionConflict("Neue Version muss expected_version + 1 sein.")
        self._call(ref.update, data, option=self.db.write_option(last_update_time=snap.update_time))

    # ------------------------------------------------------------ Vorschläge

    def add_proposal(self, proposal: ChangeProposal) -> tuple[ChangeProposal, bool]:
        ref = self.db.collection(R.PROPOSALS).document(proposal.id)
        try:
            self._call(ref.create, R.dump(proposal))
            return proposal, True
        except R.Duplicate:
            return self.get(R.PROPOSALS, proposal.id, ChangeProposal), False

    def update_proposal(self, proposal: ChangeProposal, *, expected_status: ProposalStatus, expected_applied: bool) -> None:
        ref = self.db.collection(R.PROPOSALS).document(proposal.id)
        snap = self._call(ref.get)
        if not snap.exists:
            raise R.NotFound(f"{R.PROPOSALS}/{proposal.id}")
        current = snap.to_dict()
        if current.get("status") != expected_status.value or (current.get("applied_at") is not None) != expected_applied:
            raise R.VersionConflict(f"Vorschlag {proposal.id} wurde zwischenzeitlich geändert.")
        self._call(ref.update, R.dump(proposal), option=self.db.write_option(last_update_time=snap.update_time))

    def list_proposals(self, status: ProposalStatus | None = None) -> list[ChangeProposal]:
        coll = self.db.collection(R.PROPOSALS)
        query = coll.where("status", "==", status.value) if status else coll
        docs = self._call(lambda: list(query.stream()))
        # Admin-Seite legt Vorschläge mit eigener Dokument-ID an → ID aus dem Dokument übernehmen.
        # Ein fehlerhaftes Dokument (z. B. falsche Uhrzeit im Browser) darf nicht alle Läufe blockieren.
        out = []
        for d in docs:
            try:
                out.append(ChangeProposal.model_validate({**d.to_dict(), "id": d.id}))
            except ValidationError as e:
                self.invalid_proposals[d.id] = str(e)[:300]
        return sorted(out, key=lambda p: p.created_at)

    # ------------------------------------------------------------ Audit, Preise, Meta

    def append_audit(self, entry: AuditEntry) -> None:
        self._call(self.db.collection(R.AUDIT).add, R.dump(entry))

    def audit_log(self, entity_type: str | None = None, entity_id: str | None = None) -> list[AuditEntry]:
        query = self.db.collection(R.AUDIT)
        if entity_type:
            query = query.where("entity_type", "==", entity_type)
        if entity_id:
            query = query.where("entity_id", "==", entity_id)
        docs = self._call(lambda: list(query.stream()))
        return sorted((AuditEntry.model_validate(d.to_dict()) for d in docs), key=lambda e: e.at)

    def add_observation(self, observation: PriceObservation) -> None:
        coll = self.db.collection(R.OFFERS).document(observation.offer_id).collection(R.OBSERVATIONS)
        self._call(coll.add, R.dump(observation))

    def observations(self, offer_id: str) -> list[PriceObservation]:
        coll = self.db.collection(R.OFFERS).document(offer_id).collection(R.OBSERVATIONS)
        docs = self._call(lambda: list(coll.stream()))
        return sorted((PriceObservation.model_validate(d.to_dict()) for d in docs), key=lambda o: o.observed_at)

    def get_meta(self, key: str) -> dict[str, Any]:
        snap = self._call(self.db.collection(R.META).document(key).get)
        return snap.to_dict() if snap.exists else {}

    def set_meta(self, key: str, value: dict[str, Any]) -> None:
        self._call(self.db.collection(R.META).document(key).set, value)
