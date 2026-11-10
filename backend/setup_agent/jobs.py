"""Update Scheduler: die geplanten Läufe. Aufgerufen über die Kommandozeile (cli.py) bzw. GitHub Actions.

| Job      | Takt (Vorschlag) | Inhalt |
| apply    | stündlich        | Freigaben aus der Admin-Seite anwenden, danach Export |
| weekly   | wöchentlich      | Quellen prüfen (Source Monitor), Regeln neu bewerten (Change Detector) |
| prices   | täglich          | Preise aus zulässigen Preisquellen aktualisieren |
| export   | nach Bedarf      | statische JSON-API schreiben |

Jeder Lauf schreibt sein Ergebnis nach meta/agent (für die Warnung im Admin-Bereich).
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from . import exporter
from . import repository as R
from .approval import ApprovalManager
from .detector import ChangeDetector
from .fetcher import Fetcher
from .models import utcnow
from .monitors import PriceMonitor, PriceSource, SourceMonitor

JOBS = ("apply", "weekly", "prices", "export")


def _summary(report: Any) -> dict[str, Any]:
    data = asdict(report) if is_dataclass(report) else dict(report)
    return {k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in data.items()}


def record_run(repo: R.Repository, job: str, at: datetime, ok: bool, summary: dict[str, Any]) -> None:
    meta = repo.get_meta("agent")
    runs = meta.get("runs", {})
    runs[job] = {"at": at.isoformat().replace("+00:00", "Z"), "ok": ok, "summary": summary}
    meta["runs"] = runs
    repo.set_meta("agent", meta)


def run_job(job: str, repo: R.Repository, *, out_dir: Path | None = None, fetcher: Fetcher | None = None,
            price_sources: list[PriceSource] | None = None, clock: Callable[[], datetime] = utcnow) -> dict[str, Any]:
    if job not in JOBS:
        raise ValueError(f"Unbekannter Job {job!r}. Möglich: {', '.join(JOBS)}")
    now = clock()
    approvals = ApprovalManager(repo, clock=clock)
    result: dict[str, Any] = {}
    try:
        if job == "apply":
            result["apply"] = _summary(approvals.apply_pending_approvals())
            invalid = getattr(repo, "invalid_proposals", {})
            if invalid:
                result["invalid_proposals"] = sorted(invalid)  # fehlerhafte Dokumente aus der Admin-Seite
        if job == "weekly":
            if fetcher is not None:
                result["sources"] = _summary(SourceMonitor(repo, approvals, fetcher, clock).run())
            result["detector"] = _summary(ChangeDetector(repo, approvals, clock).run())
        if job == "prices":
            result["prices"] = _summary(PriceMonitor(repo, price_sources or [], clock).run())
        if out_dir is not None and job in ("apply", "export"):
            result["export"] = _summary(exporter.write(repo, out_dir, now))
    except R.StorageUnavailable as e:
        # Nichts wurde überschrieben; der nächste Lauf versucht es erneut.
        result["error"] = str(e)
        return result
    record_run(repo, job, now, "error" not in result, result)
    return result
