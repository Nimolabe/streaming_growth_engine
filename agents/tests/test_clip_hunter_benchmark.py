"""Messwerkzeug mit einem nachgebauten Datensatz im LIGHTOR-Format (keine echten Daten)."""
import json

import pytest
from chat_fixtures import START, Burst, ChatScenario, build_chat

from streaming_agents.clip_hunter.benchmark import BenchmarkError, evaluate, load_lightor
from streaming_agents.clip_hunter.cli import main

EVENTS = [600, 1300, 2100, 2900]


def mmss(seconds: int) -> str:
    return f"{seconds // 60:03d}-{seconds % 60:02d}"


def write_stream(folder, key, seed, start_ms=1_300_000, events=EVENTS, labels=True):
    log = build_chat(ChatScenario(seed=seed, bursts=[Burst(e, "funny", 40) for e in events],
                                  bot_spam_every=0))
    chat_dir = folder / "chat"
    label_dir = folder / "labels"
    chat_dir.mkdir(parents=True, exist_ok=True)
    label_dir.mkdir(parents=True, exist_ok=True)
    lines = []
    for index, message in enumerate(log.messages):
        ms = start_ms + round((message.ts - START) * 1000)
        text = message.text.replace("\t", " ")
        lines.append(f"{index}\t{key}\t{message.user}\t{text}\t0\t{ms}")
    lines.append("kaputt\tzeile")
    (chat_dir / f"{key} {start_ms}.csv").write_text("\n".join(lines), encoding="utf-8")
    if labels:
        rows = [f"000-00 {mmss(e)} {mmss(e + 12)}" for e in events] + ["001-00 000-00 000-00"]
        (label_dir / f"{key}.csv").write_text("\n".join(rows), encoding="utf-8")


@pytest.fixture
def dataset(tmp_path):
    root = tmp_path / "Lightor_Exp" / "dataset"
    for index in range(3):
        write_stream(root / "Dota2" / "test", f"100{index}", seed=index + 1)
    write_stream(root / "Dota2" / "test", "9999", seed=9, labels=False)  # ohne Markierungen
    write_stream(root / "LOL" / "test", "nalcs_w1d1_A_B_g1", seed=11, start_ms=1485644238533)
    (root / "Dota2" / "train" / "chat").mkdir(parents=True)
    (root / "LOL" / "train" / "chat").mkdir(parents=True)
    return tmp_path / "Lightor_Exp"


def test_loader_parses_chat_and_labels(dataset):
    streams = load_lightor(dataset, game="dota2", split="test")
    assert [s.key for s in streams] == ["1000", "1001", "1002"]  # 9999 hat keine Markierungen
    first = streams[0]
    assert first.highlights == [(e, e + 12) for e in EVENTS]
    assert first.chat.messages[0].ts >= 1_700_000_000
    assert 3500 < first.duration < 3700
    assert all(len(m.user) == 12 for m in first.chat.messages)  # Namen pseudonymisiert
    lol = load_lightor(dataset / "dataset", game="lol", split="test")
    assert len(lol) == 1 and lol[0].game == "lol"
    assert len(load_lightor(dataset, game="all", split="test")) == 4


def test_evaluation_finds_marked_highlights_and_beats_baselines(dataset):
    result = evaluate(load_lightor(dataset, game="all", split="test"))
    assert result.streams == 4 and result.highlights == 16
    assert result.coverage_top15 == 1.0
    assert result.top10_clip_contains >= result.top10_hits > result.random_top10_hits
    assert 0 <= result.count_top10_hits <= 1


@pytest.mark.parametrize("kwargs", [{"game": "fortnite"}, {"split": "valid"}])
def test_invalid_selection(dataset, kwargs):
    with pytest.raises(BenchmarkError):
        load_lightor(dataset, **kwargs)


def test_missing_or_empty_folders(tmp_path, dataset):
    with pytest.raises(BenchmarkError):
        load_lightor(tmp_path / "gibt-es-nicht")
    with pytest.raises(BenchmarkError):
        load_lightor(dataset, game="dota2", split="train")  # Ordner leer


def test_cli_benchmark(dataset, tmp_path, capsys):
    out = tmp_path / "messung.json"
    assert main(["benchmark", "--lightor", str(dataset), "--game", "dota2",
                 "--out", str(out)]) == 0
    printed = capsys.readouterr().out
    assert "Clip enthält ein Highlight" in printed and "Zufall" in printed
    assert json.loads(out.read_text())["streams"] == 3
    assert main(["benchmark", "--lightor", str(tmp_path / "fehlt")]) == 2
