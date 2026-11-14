"""Change Detector: vergleicht den gespeicherten Stand mit der aktuellen Regelbewertung.

Er ändert nie selbst Fakten, sondern erzeugt Vorschläge. Wiederholte Läufe erzeugen dank
dedupe_key keine doppelten Vorschläge. Überholte eigene Vorschläge werden als 'superseded' markiert.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from . import repository as R
from .approval import ApprovalManager
from .models import Actor, ActorType, Operation, ProposalStatus, SetupClaim, utcnow
from .verification import analyze_slots, evaluate_claim

ORIGIN = "change_detector"
AGENT = Actor(type=ActorType.AGENT, id=ORIGIN)


@dataclass
class DetectorReport:
    checked: int = 0
    created: list[str] = field(default_factory=list)
    already_known: list[str] = field(default_factory=list)
    superseded: list[str] = field(default_factory=list)


class ChangeDetector:
    def __init__(self, repo: R.Repository, approvals: ApprovalManager, clock: Callable[[], datetime] = utcnow) -> None:
        self.repo, self.approvals, self.clock = repo, approvals, clock

    def run(self) -> DetectorReport:
        now = self.clock()
        report = DetectorReport()
        claims = self.repo.list(R.CLAIMS, SetupClaim)
        flags = analyze_slots(claims, now)
        wanted: dict[str, dict] = {}

        for c in claims:
            report.checked += 1
            v = evaluate_claim(c, now, conflicting=c.id in flags.conflicting, superseded=c.id in flags.superseded)
            if v.status == c.status:
                continue
            payload = {"status": v.status.value, "reason": v.reason}
            wanted[c.id] = payload
            proposal, created = self.approvals.propose(
                entity_type="setup_claim", entity_id=c.id, operation=Operation.UPDATE, payload=payload,
                reason=f"Status {c.status.value} → {v.status.value}: {v.reason}", actor=AGENT, origin=ORIGIN,
                base_version=c.version, evidence_source_ids=[e.source_id for e in c.evidence],
            )
            (report.created if created else report.already_known).append(proposal.id)

        # Eigene offene Vorschläge, die nicht mehr zum aktuellen Stand passen, als überholt markieren
        current_versions = {c.id: c.version for c in claims}
        for p in self.repo.list_proposals(ProposalStatus.PENDING):
            if p.origin != ORIGIN or p.entity_type != "setup_claim":
                continue
            outdated = wanted.get(p.entity_id) != p.payload or current_versions.get(p.entity_id) != p.base_version
            if outdated:
                self.repo.update_proposal(p.decide(ProposalStatus.SUPERSEDED, AGENT, now, "Durch neueren Stand überholt."),
                                          expected_status=ProposalStatus.PENDING, expected_applied=False)
                report.superseded.append(p.id)
        return report
