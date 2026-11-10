"""Framework-unabhängiger Kern der REST-API v1 (API.md).

Die gesamte Logik – Filter, Rechteprüfung, Fehlercodes – steckt hier und wird ohne Webserver getestet.
api.py verbindet sie nur mit FastAPI-Routen.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Protocol

from pydantic import ValidationError

from . import repository as R
from .approval import NEW, ApprovalManager, InvalidInput
from .models import (
    Actor,
    ActorType,
    AuditEntry,
    ChangeProposal,
    InvalidTransition,
    Offer,
    Operation,
    ProposalStatus,
    Source,
    SourceRegistryEntry,
    utcnow,
)
from .public_views import PublicData


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.status, self.code, self.message, self.details = status, code, message, details or {}

    def body(self) -> dict[str, Any]:
        return {"error": {"code": self.code, "message": self.message, "details": self.details}}


class TokenVerifier(Protocol):
    def verify(self, token: str) -> dict[str, Any]:
        """Gibt die Claims zurück (mind. 'uid'); wirft eine Exception bei ungültigem Token."""
        ...


class FirebaseTokenVerifier:
    def __init__(self, app: Any = None) -> None:
        self.app = app

    def verify(self, token: str) -> dict[str, Any]:
        from firebase_admin import auth  # type: ignore[import-not-found]

        return auth.verify_id_token(token, app=self.app, check_revoked=True)


def _translate(e: Exception) -> ApiError:
    if isinstance(e, ApiError):
        return e
    if isinstance(e, R.NotFound):
        return ApiError(404, "not_found", "Datensatz nicht gefunden.", {"detail": str(e)})
    if isinstance(e, R.VersionConflict):
        return ApiError(409, "version_conflict", "Datensatz wurde zwischenzeitlich geändert.", {"detail": str(e)})
    if isinstance(e, R.Duplicate):
        return ApiError(409, "duplicate", "Datensatz existiert bereits.", {"detail": str(e)})
    if isinstance(e, R.StorageUnavailable):
        return ApiError(503, "storage_unavailable", "Datenbank nicht erreichbar. Nichts wurde geändert.")
    if isinstance(e, InvalidTransition):
        return ApiError(422, "invalid_transition", str(e))
    if isinstance(e, (InvalidInput, ValidationError, ValueError)):
        return ApiError(400, "invalid_input", str(e)[:500])
    raise e


ADMIN_ENTITY = {"streamers": "streamer", "products": "product", "claims": "setup_claim", "offers": "offer",
                "sources": "source", "source-registry": "source_registry"}


class SetupApi:
    def __init__(self, repo: R.Repository, verifier: TokenVerifier, clock: Callable[[], datetime] = utcnow) -> None:
        self.repo, self.verifier, self.clock = repo, verifier, clock
        self.approvals = ApprovalManager(repo, clock=clock)

    def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[int, Any]:
        """Führt eine Operation aus und übersetzt Fehler in (Status, Fehler-JSON)."""
        try:
            return 200, fn(*args, **kwargs)
        except Exception as e:  # noqa: BLE001
            err = _translate(e)
            return err.status, err.body()

    # ------------------------------------------------------------ öffentlich

    def _data(self) -> PublicData:
        return PublicData(self.repo, self.clock())

    @staticmethod
    def _found(value: Any, what: str) -> Any:
        if value is None:
            raise ApiError(404, "not_found", f"{what} nicht gefunden.")
        return value

    def list_streamers(self, *, category=None, platform=None, language=None, q=None, page: int = 1, page_size: int = 50):
        if page < 1 or not 1 <= page_size <= 100:
            raise ApiError(400, "invalid_input", "page ≥ 1 und page_size zwischen 1 und 100.")
        items = self._data().list_streamers(category, platform, language, q)
        start = (page - 1) * page_size
        return {"items": items[start:start + page_size], "page": page, "page_size": page_size, "total": len(items)}

    def streamer(self, streamer_id: str):
        return self._found(self._data().streamer(streamer_id), "Streamer")

    def setup(self, streamer_id: str, category: str | None = None):
        data = self._data()
        result = self._found(data.setup(streamer_id, category), "Streamer")
        return {**result, "generated_at": data.now.isoformat().replace("+00:00", "Z")}

    def list_products(self, *, category=None, min_price=None, max_price=None, currency="EUR", q=None):
        if min_price is not None and max_price is not None and min_price > max_price:
            raise ApiError(400, "invalid_input", "min_price darf nicht größer als max_price sein.")
        return {"items": self._data().list_products(category, min_price, max_price, currency, q)}

    def product(self, product_id: str):
        return self._found(self._data().product(product_id), "Produkt")

    def offers(self, product_id: str):
        return {"items": self._found(self._data().offers_for(product_id), "Produkt")}

    def alternatives(self, product_id: str, *, max_price: int | None = None, limit: int = 5):
        if not 1 <= limit <= 20:
            raise ApiError(400, "invalid_input", "limit zwischen 1 und 20.")
        return {"items": self._found(self._data().alternatives(product_id, max_price, limit), "Produkt")}

    def meta(self):
        meta = self._data().meta()
        runs = self.repo.get_meta("agent").get("runs", {})
        return {**meta, "last_runs": {k: v.get("at") for k, v in runs.items()}}

    # ------------------------------------------------------------ Admin

    def admin(self, authorization: str | None) -> Actor:
        if not authorization or not authorization.startswith("Bearer "):
            raise ApiError(401, "unauthenticated", "Anmeldung erforderlich.")
        try:
            claims = self.verifier.verify(authorization[7:].strip())
        except Exception:  # noqa: BLE001 – Details nicht nach außen geben
            raise ApiError(401, "unauthenticated", "Token ungültig oder abgelaufen.") from None
        if claims.get("admin") is not True or not claims.get("uid"):
            raise ApiError(403, "forbidden", "Keine Admin-Berechtigung.")
        return Actor(type=ActorType.ADMIN, id=str(claims["uid"]))

    def _admin_apply(self, actor: Actor, entity_type: str, operation: Operation, payload: dict, reason: str,
                     entity_id: str = NEW, base_version: int | None = None) -> dict:
        if not isinstance(payload, dict):
            raise ApiError(400, "invalid_input", "Erwartet ein JSON-Objekt.")
        proposal, created = self.approvals.propose(entity_type=entity_type, entity_id=entity_id, operation=operation,
                                                   payload=payload, reason=reason, actor=actor, origin="admin_api",
                                                   base_version=base_version)
        if not created and proposal.status != ProposalStatus.PENDING:
            raise ApiError(409, "duplicate", "Genau diese Änderung wurde bereits entschieden.", {"proposal_id": proposal.id})
        done = self.approvals.decide(proposal.id, ProposalStatus.APPROVED, actor, "Direkt durch Admin")
        if done.apply_error:
            raise ApiError(409 if "existiert" in done.apply_error or "geändert" in done.apply_error else 400,
                           "apply_failed", done.apply_error, {"proposal_id": done.id})
        return {"proposal_id": done.id, "applied_at": done.applied_at.isoformat() if done.applied_at else None}

    def admin_create(self, authorization: str | None, kind: str, body: dict) -> dict:
        actor = self.admin(authorization)
        if kind not in ADMIN_ENTITY:
            raise ApiError(404, "not_found", f"Unbekannter Bereich {kind}.")
        reason = str((body or {}).pop("reason", "") or "Admin-Eingabe")
        return self._admin_apply(actor, ADMIN_ENTITY[kind], Operation.CREATE, body, reason)

    def admin_update(self, authorization: str | None, kind: str, entity_id: str, body: dict, *, retire: bool = False) -> dict:
        actor = self.admin(authorization)
        if kind not in ADMIN_ENTITY:
            raise ApiError(404, "not_found", f"Unbekannter Bereich {kind}.")
        body = dict(body or {})
        version = body.pop("expected_version", None)
        reason = str(body.pop("reason", "") or "")
        if not isinstance(version, int):
            raise ApiError(400, "invalid_input", "expected_version (Zahl) ist Pflicht.")
        if len(reason.strip()) < 3:
            raise ApiError(400, "invalid_input", "reason (Begründung) ist Pflicht.")
        changes = body.pop("changes", {}) if not retire else {}
        if body:
            raise ApiError(400, "invalid_input", f"Unbekannte Felder: {', '.join(sorted(body))}")
        return self._admin_apply(actor, ADMIN_ENTITY[kind], Operation.RETIRE if retire else Operation.UPDATE, changes,
                                 reason, entity_id=entity_id, base_version=version)

    def admin_set_price(self, authorization: str | None, offer_id: str, body: dict) -> dict:
        actor = self.admin(authorization)
        body = dict(body or {})
        version = body.pop("expected_version", None)
        reason = str(body.pop("reason", "") or "Preis manuell aktualisiert")
        unknown = set(body) - {"price", "availability"}
        if unknown or "price" not in body:
            raise ApiError(400, "invalid_input", "Erwartet price (oder null), optional availability, expected_version.")
        if version is None:
            version = self.repo.get(R.OFFERS, offer_id, Offer).version
        return self._admin_apply(actor, "offer", Operation.UPDATE, body, reason, entity_id=offer_id, base_version=version)

    def admin_proposals(self, authorization: str | None, *, status: str | None = "pending", entity_type: str | None = None):
        self.admin(authorization)
        st = ProposalStatus(status) if status else None
        items = [p for p in self.repo.list_proposals(st) if entity_type is None or p.entity_type == entity_type]
        return {"items": [R.dump(p) for p in items]}

    def admin_decide(self, authorization: str | None, proposal_id: str, approve: bool, note: str | None) -> dict:
        actor = self.admin(authorization)
        status = ProposalStatus.APPROVED if approve else ProposalStatus.REJECTED
        decided: ChangeProposal = self.approvals.decide(proposal_id, status, actor, note)
        return R.dump(decided)

    def admin_sources(self, authorization: str | None) -> dict:
        self.admin(authorization)
        return {"sources": [R.dump(s) for s in self.repo.list(R.SOURCES, Source)],
                "registry": [R.dump(r) for r in self.repo.list(R.REGISTRY, SourceRegistryEntry)]}

    def admin_audit(self, authorization: str | None, *, entity_type=None, entity_id=None, since: datetime | None = None) -> dict:
        self.admin(authorization)
        entries: list[AuditEntry] = self.repo.audit_log(entity_type, entity_id)
        if since is not None:
            entries = [e for e in entries if e.at >= since]
        return {"items": [R.dump(e) for e in entries]}
