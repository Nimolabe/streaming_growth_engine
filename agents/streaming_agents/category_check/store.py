"""Messungen als JSON Lines: eine Messung pro Zeile, Datei wird nur ergänzt."""
import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from .models import CategorySnapshot

MAX_FILE_BYTES = 200 * 1024 * 1024


class StoreError(ValueError):
    pass


@dataclass
class LoadedSnapshots:
    snapshots: list[CategorySnapshot]
    skipped_lines: int


def append_snapshots(path: str | Path, snapshots: list[CategorySnapshot]) -> Path:
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8", newline="\n") as handle:
        for item in snapshots:
            handle.write(item.model_dump_json() + "\n")
    return target


def load_snapshots(*paths: str | Path) -> LoadedSnapshots:
    snapshots: list[CategorySnapshot] = []
    skipped = 0
    for path in paths:
        source = Path(path).expanduser()
        if not source.is_file():
            raise StoreError(f"Datei nicht gefunden: {source}")
        if source.stat().st_size > MAX_FILE_BYTES:
            raise StoreError(f"Datei ist zu groß: {source}")
        with source.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    snapshots.append(CategorySnapshot.model_validate(json.loads(line)))
                except (json.JSONDecodeError, ValidationError, TypeError):
                    skipped += 1
    if not snapshots:
        raise StoreError("Keine gültigen Messungen gefunden.")
    return LoadedSnapshots(snapshots, skipped)
