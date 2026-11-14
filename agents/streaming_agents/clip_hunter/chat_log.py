"""Chat-Mitschnitte als JSON Lines: erste Zeile Kopf, danach eine Nachricht pro Zeile.

Das Format ist bewusst einfach, damit ein abgebrochener Mitschnitt lesbar bleibt
(eine halbe letzte Zeile wird übersprungen) und Dateien in jedem Editor prüfbar sind.
"""
import json
from pathlib import Path
from typing import IO, Self

from pydantic import ValidationError

from .models import MAX_CHAT_MESSAGES, ChatLog, ChatLogHeader, ChatMessage

MAX_LINE_CHARS = 4000


class ChatLogError(ValueError):
    """Verständlicher Grund, warum ein Mitschnitt nicht gelesen werden kann."""


class ChatLogWriter:
    """Schreibt Zeile für Zeile und leert den Puffer, damit bei Abbruch nichts verloren geht."""

    def __init__(self, path: str | Path, header: ChatLogHeader, *, overwrite: bool = False):
        self.path = Path(path)
        if self.path.exists() and not overwrite:
            raise ChatLogError(f"{self.path} existiert bereits; bitte einen neuen Dateinamen wählen.")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file: IO[str] = self.path.open("w", encoding="utf-8", newline="\n")
        self.count = 0
        self._write(header.model_dump(mode="json"))

    def _write(self, payload: dict) -> None:
        self._file.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
        self._file.flush()

    def write(self, message: ChatMessage) -> None:
        # Pflichtfelder (ts, user) haben keinen Standardwert und bleiben immer erhalten.
        self._write(message.model_dump(mode="json", exclude_defaults=True))
        self.count += 1

    def close(self) -> None:
        if not self._file.closed:
            self._file.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_exc) -> None:
        self.close()


def read_chat_log(path: str | Path) -> ChatLog:
    source = Path(path)
    if not source.is_file():
        raise ChatLogError(f"Chat-Mitschnitt {source} wurde nicht gefunden.")
    with source.open("r", encoding="utf-8", errors="replace") as handle:
        return parse_chat_lines(handle)


def parse_chat_lines(lines) -> ChatLog:
    header: ChatLogHeader | None = None
    messages: list[ChatMessage] = []
    skipped = 0
    for number, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            continue
        if len(line) > MAX_LINE_CHARS:
            skipped += 1
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        if header is None:
            try:
                header = ChatLogHeader.model_validate(payload)
            except ValidationError as exc:
                raise ChatLogError(
                    "Die erste Zeile ist kein gültiger Kopf eines sge-chat-log-Mitschnitts."
                ) from exc
            continue
        try:
            messages.append(ChatMessage.model_validate(payload))
        except ValidationError:
            skipped += 1
            continue
        if len(messages) > MAX_CHAT_MESSAGES:
            raise ChatLogError(
                f"Der Mitschnitt ist zu groß (mehr als {MAX_CHAT_MESSAGES:,} Nachrichten). "
                "Bitte in kürzere Abschnitte aufteilen."
            )
    if header is None:
        raise ChatLogError("Der Chat-Mitschnitt ist leer.")
    messages.sort(key=lambda item: item.ts)
    return ChatLog(header=header, messages=messages, skipped_lines=skipped)
