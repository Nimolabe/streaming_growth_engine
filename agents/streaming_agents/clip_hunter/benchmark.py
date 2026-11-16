"""Messung der Chat-Erkennung an echten Twitch-Streams mit markierten Highlights.

Datengrundlage ist der öffentliche Forschungsdatensatz LIGHTOR (Simon Fraser University):
echte Twitch-Chats von Dota-2- und League-of-Legends-Streams, Highlights von Menschen als
Zeitintervalle markiert. Der Datensatz liegt NICHT im Repository; Bezug:
``git clone https://github.com/sfu-db/Lightor_Exp`` (Ordner ``dataset``).

Gemessen werden drei Zahlen, jeweils gemittelt über die Streams:

- ``top10_hits``: Anteil der 10 besten Kandidaten, deren geschätzter Zeitpunkt höchstens
  5 s neben einem markierten Highlight liegt.
- ``top10_clip_contains``: Anteil der 10 besten Kandidaten, deren Clip-Fenster ein
  markiertes Highlight enthält (mind. 3 s Überschneidung) – die Zahl, die für Nutzer zählt.
- ``coverage_top15``: Anteil der markierten Highlights, die unter den 15 besten
  Kandidaten getroffen werden.

Zum Vergleich: zufällige Zeitpunkte und „Nachrichten zählen“ (die Fenster mit den meisten
Nachrichten). Die Markierungen sind unvollständig; echte, aber unmarkierte Momente zählen
hier als Fehltreffer – die Werte sind also eher zu streng.
"""
import csv
import hashlib
import random
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from pydantic import BaseModel

from .hunter import hunt
from .models import ChatLog, ChatLogHeader, ChatMessage, HuntSettings

BASE_TS = 1_700_000_000.0  # künstlicher Startzeitpunkt; Zeiten im Datensatz sind relativ
GAMES = {"dota2": "Dota2", "lol": "LOL"}
SPLITS = ("train", "test")
HIT_TOLERANCE = 5.0
MIN_OVERLAP = 3.0


class BenchmarkError(ValueError):
    pass


@dataclass
class BenchmarkStream:
    key: str
    game: str
    split: str
    chat: ChatLog
    highlights: list[tuple[float, float]]
    duration: float


class BenchmarkResult(BaseModel):
    streams: int
    highlights: int
    top10_hits: float
    top10_clip_contains: float
    coverage_top15: float
    random_top10_hits: float
    count_top10_hits: float


def _seconds(value: str) -> int:
    minutes, seconds = value.split("-")
    return int(minutes) * 60 + int(seconds)


def _pseudonym(name: str) -> str:
    return hashlib.sha256(name.encode("utf-8")).hexdigest()[:12]


def load_lightor(root: str | Path, game: str = "all", split: str = "test") -> list[BenchmarkStream]:
    """Liest den LIGHTOR-Ordner ``dataset`` (oder das ganze Repository)."""
    base = Path(root).expanduser()
    if (base / "dataset").is_dir():
        base = base / "dataset"
    games = list(GAMES) if game == "all" else [game]
    splits = list(SPLITS) if split == "all" else [split]
    if any(name not in GAMES for name in games) or any(name not in SPLITS for name in splits):
        raise BenchmarkError("Spiel muss dota2, lol oder all sein; Teil train, test oder all.")
    streams: list[BenchmarkStream] = []
    for game_key in games:
        for split_key in splits:
            chat_dir = base / GAMES[game_key] / split_key / "chat"
            label_dir = base / GAMES[game_key] / split_key / "labels"
            if not chat_dir.is_dir():
                raise BenchmarkError(f"Ordner nicht gefunden: {chat_dir}")
            for chat_file in sorted(chat_dir.glob("*.csv")):
                parts = chat_file.stem.split()
                if len(parts) != 2 or not parts[1].isdigit():
                    continue
                key, start_ms = parts[0], int(parts[1])
                messages = []
                with chat_file.open(encoding="utf-8", errors="replace", newline="") as handle:
                    for row in csv.reader(handle, delimiter="\t"):
                        if len(row) < 6:
                            continue
                        try:
                            offset = int(row[5]) / 1000 - start_ms / 1000
                        except ValueError:
                            continue
                        if offset < 0:
                            continue
                        messages.append(ChatMessage(ts=BASE_TS + max(offset, 0.001),
                                                    user=_pseudonym(row[2] or "?"),
                                                    text=row[3][:600]))
                messages.sort(key=lambda item: item.ts)
                highlights = []
                label_file = label_dir / f"{key}.csv"
                if label_file.is_file():
                    with label_file.open(encoding="utf-8", newline="") as handle:
                        for row in csv.reader(handle, delimiter=" "):
                            if len(row) < 3 or (row[1] == "000-00" and row[2] == "000-00"):
                                continue
                            try:
                                highlights.append((_seconds(row[1]), _seconds(row[2])))
                            except ValueError:
                                continue
                if not messages or not highlights:
                    continue
                streams.append(BenchmarkStream(
                    key=key, game=game_key, split=split_key,
                    chat=ChatLog(header=ChatLogHeader(channel="lightor", started_at=BASE_TS,
                                                      source="lightor"), messages=messages),
                    highlights=sorted(set(highlights)),
                    duration=messages[-1].ts - BASE_TS,
                ))
    if not streams:
        raise BenchmarkError("Keine Streams mit Chat und Markierungen gefunden.")
    return streams


def _near(second: float, highlights: list[tuple[float, float]]) -> bool:
    return any(start - HIT_TOLERANCE <= second <= end + HIT_TOLERANCE
               for start, end in highlights)


def _random_hits(stream: BenchmarkStream, rng: random.Random, count: int = 10) -> float:
    picks = [rng.uniform(0, stream.duration) for _ in range(count)]
    return sum(_near(pick, stream.highlights) for pick in picks) / count


def _count_hits(stream: BenchmarkStream, settings: HuntSettings, count: int = 10) -> float:
    """Vergleichsverfahren: Fenster mit den meisten Nachrichten, gleiche Verzögerung."""
    size = int(stream.duration) + 1
    per_second = [0] * (size + 1)
    for message in stream.chat.messages:
        per_second[int(message.ts - BASE_TS)] += 1
    window = settings.chat_window_seconds
    sums = [sum(per_second[i:i + window]) for i in range(size)]
    chosen: list[int] = []
    for index in sorted(range(size), key=lambda i: -sums[i]):
        if all(abs(index - other) >= settings.chat_min_gap_seconds for other in chosen):
            chosen.append(index)
        if len(chosen) == count:
            break
    anchors = [max(0.0, index - settings.chat_reaction_lag_seconds) for index in chosen]
    return sum(_near(anchor, stream.highlights) for anchor in anchors) / max(len(anchors), 1)


def evaluate(streams: list[BenchmarkStream], settings: HuntSettings | None = None,
             seed: int = 1) -> BenchmarkResult:
    settings = (settings or HuntSettings()).model_copy(update={"max_candidates": 15})
    rng = random.Random(seed)
    hits, contains, coverage, random_hits, count_hits = [], [], [], [], []
    for stream in streams:
        candidates = hunt(chat_log=stream.chat, vod_start=BASE_TS, settings=settings).candidates
        top = candidates[:10]
        hits.append(sum(_near(c.anchor_seconds, stream.highlights) for c in top) / len(top)
                    if top else 0.0)
        contains.append(sum(
            any(min(c.end_seconds, end) - max(c.start_seconds, start) >= MIN_OVERLAP
                for start, end in stream.highlights) for c in top) / len(top) if top else 0.0)
        coverage.append(sum(
            any(start - HIT_TOLERANCE <= c.anchor_seconds <= end + HIT_TOLERANCE
                for c in candidates[:15]) for start, end in stream.highlights
        ) / len(stream.highlights))
        random_hits.append(_random_hits(stream, rng))
        count_hits.append(_count_hits(stream, settings))
    return BenchmarkResult(
        streams=len(streams),
        highlights=sum(len(stream.highlights) for stream in streams),
        top10_hits=round(mean(hits), 3),
        top10_clip_contains=round(mean(contains), 3),
        coverage_top15=round(mean(coverage), 3),
        random_top10_hits=round(mean(random_hits), 3),
        count_top10_hits=round(mean(count_hits), 3),
    )
