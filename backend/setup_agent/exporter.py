"""Statischer JSON-Export der freigegebenen Daten (öffentliche API ohne Server, ARCHITEKTUR.md 3.3).

Pfade entsprechen den API-Endpunkten:
  /api/v1/streamers                → v1/streamers.json
  /api/v1/streamers/{id}           → v1/streamers/{id}.json
  /api/v1/streamers/{id}/setup     → v1/streamers/{id}/setup.json
  /api/v1/products                 → v1/products.json
  /api/v1/products/{id}            → v1/products/{id}.json
  /api/v1/products/{id}/offers     → v1/products/{id}/offers.json
  /api/v1/products/{id}/alternatives → v1/products/{id}/alternatives.json
  /api/v1/meta                     → v1/meta.json

Der Export ist deterministisch: gleiche Daten → identische Dateien. Unveränderte Dateien werden nicht
neu geschrieben, verschwundene Einträge werden entfernt.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from . import repository as R
from .public_views import API_VERSION, PublicData


def build(repo: R.Repository, now: datetime) -> dict[str, Any]:
    data = PublicData(repo, now)
    files: dict[str, Any] = {
        "streamers.json": {"items": data.list_streamers()},
        "products.json": {"items": data.list_products()},
        "meta.json": data.meta(),
    }
    for sid in data.streamers:
        files[f"streamers/{sid}.json"] = data.streamer(sid)
        files[f"streamers/{sid}/setup.json"] = data.setup(sid)
    for pid in data.products:
        files[f"products/{pid}.json"] = data.product(pid)
        files[f"products/{pid}/offers.json"] = {"items": data.offers_for(pid)}
        files[f"products/{pid}/alternatives.json"] = {"items": data.alternatives(pid)}
    return {f"{API_VERSION}/{k}": v for k, v in files.items()}


def render(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


@dataclass
class ExportReport:
    written: list[str] = field(default_factory=list)
    unchanged: int = 0
    removed: list[str] = field(default_factory=list)


def write(repo: R.Repository, out_dir: Path, now: datetime) -> ExportReport:
    out_dir = Path(out_dir)
    report = ExportReport()
    files = build(repo, now)
    for rel, value in sorted(files.items()):
        path = out_dir / rel
        text = render(value)
        if path.exists() and path.read_text(encoding="utf-8") == text:
            report.unchanged += 1
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        report.written.append(rel)
    version_dir = out_dir / API_VERSION
    if version_dir.exists():
        for path in sorted(version_dir.rglob("*.json")):
            rel = path.relative_to(out_dir).as_posix()
            if rel not in files:
                path.unlink()
                report.removed.append(rel)
    return report
