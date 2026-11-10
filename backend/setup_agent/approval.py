"""Approval Manager und Audit Logger.

Alle Änderungen an Fakten laufen hier durch: Vorschlag → Entscheidung (nur Admin) → Anwendung.
Jede Anwendung erzeugt einen Audit-Eintrag mit Begründung. Siehe docs/setup-agent/DATENMODELL.md (E, F).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from pydantic import BaseModel, ValidationError

from . import repository as R
from .models import (
    Actor,
    ActorType,
    AuditAction,
    AuditEntry,
    Availability,
    ChangeProposal,
    Money,
    Offer,
    Operation,
    Product,
    ProposalStatus,
    SetupClaim,
    Source,
    SourceRegistryEntry,
    Streamer,
    VerificationStatus,
    utcnow,
)
from .pricing import apply_observation
from .verification import PUBLIC_STATUSES, analyze_slots, evaluate_claim

ENTITIES: dict[str, tuple[str, type[BaseModel]]] = {
    "streamer": (R.STREAMERS, Streamer),
    "setup_claim": (R.CLAIMS, SetupClaim),
    "product": (R.PRODUCTS, Product),
    "offer": (R.OFFERS, Offer),
    "source": (R.SOURCES, Source),
    "source_registry": (R.REGISTRY, SourceRegistryEntry),
}
NEW = "new"  # entity_id für Neuanlagen, deren ID erst aus den Daten berechnet wird
_IGNORED_IN_DIFF = {"version", "updated_at", "created_at"}


class InvalidInput(ValueError):
    code = "invalid_input"


class AuditLogger:
    def __init__(self, repo: R.Repository) -> None:
        self.repo = repo

    @staticmethod
    def diff(before: dict[str, Any] | None, after: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
        before, after = before or {}, after or {}
        keys = (set(before) | set(after)) - _IGNORED_IN_DIFF
        return {k: {"from": before.get(k), "to": after.get(k)} for k in sorted(keys) if before.get(k) != after.get(k)}

    def record(self, *, at: datetime, actor: Actor, action: AuditAction, entity_type: str, entity_id: str, reason: str,
               before: BaseModel | None = None, after: BaseModel | None = None, proposal_id: str | None = None) -> AuditEntry:
        entry = AuditEntry(
            at=at, actor=actor, action=action, entity_type=entity_type, entity_id=entity_id,
            from_version=getattr(before, "version", None), to_version=getattr(after, "version", None),
            changes=self.diff(R.dump(before) if before else None, R.dump(after) if after else None),
            reason=reason, proposal_id=proposal_id,
        )
        self.repo.append_audit(entry)
        return entry


@dataclass
class ApplyReport:
    applied: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)


class ApprovalManager:
    def __init__(self, repo: R.Repository, clock: Callable[[], datetime] = utcnow) -> None:
        self.repo = repo
        self.clock = clock
        self.audit = AuditLogger(repo)

    # ------------------------------------------------------------ Vorschlagen

    def propose(self, *, entity_type: str, entity_id: str, operation: Operation, payload: dict[str, Any], reason: str,
                actor: Actor, origin: str, base_version: int | None = None,
                evidence_source_ids: list[str] | None = None) -> tuple[ChangeProposal, bool]:
        if entity_type not in ENTITIES:
            raise InvalidInput(f"Unbekannter Typ: {entity_type}")
        proposal = ChangeProposal(
            entity_type=entity_type, entity_id=entity_id, operation=operation, payload=payload, base_version=base_version,
            reason=reason, evidence_source_ids=evidence_source_ids or [], origin=origin, created_by=actor,
            created_at=self.clock(),
        )
        self._dry_run(proposal)  # ungültige Eingaben gar nicht erst speichern
        return self.repo.add_proposal(proposal)

    def _dry_run(self, p: ChangeProposal) -> None:
        collection, model = ENTITIES[p.entity_type]
        try:
            if p.operation == Operation.CREATE:
                entity = model.model_validate(p.payload)
                if p.entity_id not in (NEW, getattr(entity, "id")):
                    raise InvalidInput(f"entity_id passt nicht zu den Daten (berechnet: {getattr(entity, 'id')}).")
                self._check_references(entity)
            elif p.operation == Operation.UPDATE:
                current = self.repo.get(collection, p.entity_id, model)
                self._check_references(self._merged(current, p.payload))
            else:
                self.repo.get(collection, p.entity_id, model)
        except ValidationError as e:
            raise InvalidInput(_short(e)) from None

    # ------------------------------------------------------------ Entscheiden

    def decide(self, proposal_id: str, status: ProposalStatus, actor: Actor, note: str | None = None) -> ChangeProposal:
        current = self.repo.get(R.PROPOSALS, proposal_id, ChangeProposal)
        decided = current.decide(status, actor, self.clock(), note)
        self.repo.update_proposal(decided, expected_status=ProposalStatus.PENDING, expected_applied=False)
        if status in (ProposalStatus.APPROVED, ProposalStatus.REJECTED):
            self.audit.record(
                at=self.clock(), actor=actor,
                action=AuditAction.APPROVE if status == ProposalStatus.APPROVED else AuditAction.REJECT,
                entity_type=decided.entity_type, entity_id=decided.entity_id,
                reason=decided.reason + (f" – Notiz: {note.strip()}" if note and note.strip() else ""), proposal_id=decided.id,
            )
        if status == ProposalStatus.APPROVED:
            return self.apply(decided)
        return decided

    def apply_pending_approvals(self) -> ApplyReport:
        """Wendet freigegebene, noch nicht angewendete Vorschläge an (z. B. aus der Admin-Seite)."""
        report = ApplyReport()
        for p in sorted(self.repo.list_proposals(ProposalStatus.APPROVED), key=lambda p: p.created_at):
            if p.applied_at is not None:
                continue
            result = self.apply(p)
            if result.applied_at:
                report.applied.append(p.id)
            elif result.apply_error:
                report.failed[p.id] = result.apply_error
        return report

    # ------------------------------------------------------------ Anwenden

    def apply(self, p: ChangeProposal) -> ChangeProposal:
        if p.status != ProposalStatus.APPROVED or p.applied_at is not None:
            raise InvalidInput("Nur freigegebene, noch nicht angewendete Vorschläge können angewendet werden.")
        if p.decided_by is None or p.decided_by.type != ActorType.ADMIN:
            raise InvalidInput("Freigabe ohne Admin wird nicht angewendet.")
        now = self.clock()
        try:
            self._apply(p, now)
            done = p.model_copy(update={"applied_at": now, "apply_error": None})
        except (ValidationError, R.RepositoryError, InvalidInput, ValueError) as e:
            if isinstance(e, R.StorageUnavailable):
                raise  # nichts ändern, später erneut versuchen
            done = p.model_copy(update={"apply_error": (_short(e) if isinstance(e, ValidationError) else str(e))[:500]})
        self.repo.update_proposal(done, expected_status=ProposalStatus.APPROVED, expected_applied=False)
        return done

    def _apply(self, p: ChangeProposal, now: datetime) -> None:
        collection, model = ENTITIES[p.entity_type]
        actor = p.decided_by
        assert actor is not None

        if p.operation == Operation.CREATE:
            stamps = {k: v for k, v in {"created_at": now, "updated_at": now, "version": 1}.items() if k in model.model_fields}
            entity = model.model_validate({**p.payload, **stamps})
            if p.entity_id not in (NEW, getattr(entity, "id")):
                raise InvalidInput("entity_id passt nicht zu den Daten.")
            self._check_references(entity)
            if isinstance(entity, SetupClaim):
                entity = self._finalize_claim(entity, now, p)
            self.repo.save(collection, entity, expected_version=None)
            self.audit.record(at=now, actor=actor, action=AuditAction.CREATE, entity_type=p.entity_type,
                              entity_id=getattr(entity, "id"), after=entity, reason=p.reason, proposal_id=p.id)
            return

        current = self.repo.get(collection, p.entity_id, model)
        if p.base_version is not None and getattr(current, "version", None) != p.base_version:
            raise InvalidInput(
                f"Datensatz wurde inzwischen geändert (v{getattr(current, 'version', '?')} statt v{p.base_version}). "
                "Bitte neu prüfen."
            )

        if p.operation == Operation.UPDATE and isinstance(current, Offer) and set(p.payload) <= {"price", "availability"}:
            self._apply_price(p, current, now, actor)
            return

        if p.operation == Operation.UPDATE:
            updated = self._merged(current, p.payload)
            action = AuditAction.UPDATE
        else:
            updated = self._retired(current)
            action = AuditAction.RETIRE
        updated = updated.model_copy(update={"version": current.version + 1, "updated_at": now})  # type: ignore[attr-defined]
        if isinstance(updated, SetupClaim) and action == AuditAction.UPDATE:
            updated = self._finalize_claim(updated, now, p)
        if getattr(updated, "id") != getattr(current, "id"):
            raise InvalidInput("Diese Änderung würde die ID verändern. Bitte als neuen Datensatz anlegen und den alten zurückziehen.")
        self.repo.save(collection, updated, expected_version=current.version)  # type: ignore[attr-defined]
        self.audit.record(at=now, actor=actor, action=action, entity_type=p.entity_type, entity_id=p.entity_id,
                          before=current, after=updated, reason=p.reason, proposal_id=p.id)

    def _apply_price(self, p: ChangeProposal, offer: Offer, now: datetime, actor: Actor) -> None:
        price = Money.model_validate(p.payload["price"]) if p.payload.get("price") is not None else None
        availability = Availability(p.payload.get("availability", offer.availability))
        result = apply_observation(offer, price, availability, now, "manual")
        updated = result.offer if result.change else result.offer.model_copy(update={"version": offer.version + 1})
        self.repo.save(R.OFFERS, updated, expected_version=offer.version)
        if result.observation:
            self.repo.add_observation(result.observation)
        self.audit.record(at=now, actor=actor, action=AuditAction.UPDATE, entity_type="offer", entity_id=offer.id,
                          before=offer, after=updated, reason=p.reason, proposal_id=p.id)

    def _check_references(self, entity: BaseModel) -> None:
        """Verweise müssen auf existierende Datensätze zeigen (keine verwaisten Angaben)."""
        refs: list[tuple[str, str, type[BaseModel]]] = []
        if isinstance(entity, SetupClaim):
            refs.append((R.STREAMERS, entity.streamer_id, Streamer))
            if entity.product_id is not None:
                refs.append((R.PRODUCTS, entity.product_id, Product))
        if isinstance(entity, Offer):
            refs.append((R.PRODUCTS, entity.product_id, Product))
        for collection, ref_id, model in refs:
            if self.repo.find(collection, ref_id, model) is None:
                raise InvalidInput(f"Verweis auf unbekannten Datensatz: {collection}/{ref_id}")

    @staticmethod
    def _merged(current: BaseModel, payload: dict[str, Any]) -> BaseModel:
        data = R.dump(current)
        data.update(payload)
        return type(current).model_validate(data)

    @staticmethod
    def _retired(current: BaseModel) -> BaseModel:
        changes: dict[type, dict[str, Any]] = {
            SetupClaim: {"published": False, "status": VerificationStatus.OUTDATED, "reason": "Zurückgezogen."},
            Streamer: {"active": False},
            Product: {"discontinued": True},
            Offer: {"availability": Availability.DISCONTINUED},
            SourceRegistryEntry: {"enabled": False},
        }
        if type(current) not in changes:
            raise InvalidInput(f"Zurückziehen ist für {type(current).__name__} nicht vorgesehen.")
        return type(current).model_validate({**R.dump(current), **changes[type(current)]})

    def _finalize_claim(self, claim: SetupClaim, now: datetime, p: ChangeProposal) -> SetupClaim:
        """Bewertet die Angabe neu (inkl. Slot-Prüfung) und setzt 'published' – das ist der Akt der Freigabe.
        Enthält der Vorschlag einen Status (Change Detector oder manuelle Korrektur), gilt dieser."""
        if "status" in p.payload:
            status = claim.status
            reason = claim.reason if "reason" in p.payload else f"Status manuell gesetzt: {p.reason}"
            verdict = evaluate_claim(claim, now)
            confidence, level = verdict.confidence, verdict.level
        else:
            others = [c for c in self.repo.list(R.CLAIMS, SetupClaim) if c.streamer_id == claim.streamer_id and c.id != claim.id]
            flags = analyze_slots(others + [claim], now)
            verdict = evaluate_claim(claim, now, conflicting=claim.id in flags.conflicting, superseded=claim.id in flags.superseded)
            status, reason, confidence, level = verdict.status, verdict.reason, verdict.confidence, verdict.level
        return claim.model_copy(update={
            "status": status, "reason": reason, "confidence": confidence, "confidence_level": level,
            "last_verified_at": now,
            "published": status in PUBLIC_STATUSES and claim.product_id is not None,
        })


def _short(e: ValidationError) -> str:
    parts = [f"{'.'.join(str(x) for x in err['loc']) or 'eingabe'}: {err['msg']}" for err in e.errors()[:5]]
    return "; ".join(parts)
