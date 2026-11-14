"""Kompletter Ablauf über die Kommandozeile mit echtem FFmpeg (wird ohne FFmpeg übersprungen)."""
import json
import shutil
import subprocess
from datetime import UTC, datetime

import pytest
from chat_fixtures import START, Burst, ChatScenario, build_chat
from test_clip_hunter_audio import write_wav

from streaming_agents.clip_hunter.chat_log import ChatLogWriter
from streaming_agents.clip_hunter.cli import main

pytestmark = pytest.mark.skipif(
    not (shutil.which("ffmpeg") and shutil.which("ffprobe")), reason="FFmpeg nicht installiert")

VOD_START = datetime.fromtimestamp(START, UTC).isoformat()


@pytest.fixture(scope="module")
def stream(tmp_path_factory):
    folder = tmp_path_factory.mktemp("stream")
    wav = write_wav(folder / "audio.wav", seconds=240, spikes=((90, 2), (170, 1.5)))
    video = folder / "stream.mp4"
    subprocess.run([
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=10:duration=240", "-i", str(wav),
        "-shortest", "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", str(video),
    ], check=True, timeout=180)
    log = build_chat(ChatScenario(duration=240, rate=1.5, audience=80,
                                  bursts=[Burst(89, "funny", 40)], bot_spam_every=0))
    chat = folder / "chat.jsonl"
    with ChatLogWriter(chat, log.header) as writer:
        for message in log.messages:
            writer.write(message)
    return folder, video, chat


def ffprobe_size(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return tuple(int(value) for value in out.split(","))


def test_full_analysis_export_report_and_evaluation(stream, capsys):
    folder, video, chat = stream
    out, report, clips = folder / "ergebnis.json", folder / "bericht.html", folder / "clips"
    code = main(["analyze", "--video", str(video), "--chat", str(chat), "--vod-start", VOD_START,
                 "--out", str(out), "--report", str(report), "--export-dir", str(clips),
                 "--vertical", "--max", "5"])
    assert code == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    result = payload["result"]
    assert result["mode"] == "chat+audio" and result["version"] == "clip-hunter-v4"
    best = result["candidates"][0]
    assert best["signals"] == ["chat", "audio"] and best["category"] == "funny"
    assert abs(best["anchor_seconds"] - 91) <= 2
    assert result["alignment_note"] is None

    files = sorted(clips.glob("*.mp4"))
    assert len(files) == len(result["candidates"])
    assert files[0].name.startswith("clip_01_funny_") and files[0].name.endswith("_9x16.mp4")
    assert ffprobe_size(files[0]) == (1080, 1920)

    html = report.read_text(encoding="utf-8")
    assert "clip_01_funny_" in html and "Clip Hunter" in html
    capsys.readouterr()

    viewer = folder / "viewer.json"
    viewer.write_text(json.dumps([{"vod_offset": 70, "duration": 30, "view_count": 120,
                                   "title": "LOL"}]), encoding="utf-8")
    assert main(["evaluate", "--result", str(out), "--viewer-clips", str(viewer)]) == 0
    printed = capsys.readouterr().out
    assert "Abdeckung 100 %" in printed


def test_existing_outputs_are_not_overwritten(stream, capsys):
    folder, _, chat = stream
    target = folder / "schon_da.json"
    target.write_text("{}")
    code = main(["analyze", "--chat", str(chat), "--out", str(target)])
    assert code == 2
    assert "existiert bereits" in capsys.readouterr().err
    assert target.read_text() == "{}"


def test_chat_only_without_vod_start_warns(stream, capsys):
    folder, _, chat = stream
    out = folder / "nur_chat.json"
    assert main(["analyze", "--chat", str(chat), "--out", str(out), "--lang", "en"]) == 0
    result = json.loads(out.read_text())["result"]
    assert result["mode"] == "chat" and result["alignment_note"]
    assert result["candidates"][0]["category"] == "funny"


def test_audio_only_and_bad_arguments(stream, capsys):
    folder, video, _ = stream
    out = folder / "nur_audio.json"
    assert main(["analyze", "--video", str(video), "--out", str(out)]) == 0
    result = json.loads(out.read_text())["result"]
    assert result["mode"] == "audio" and len(result["candidates"]) == 2
    assert main(["analyze"]) == 2
    assert main(["analyze", "--chat", "fehlt.jsonl"]) == 2
    assert main(["analyze", "--video", str(video), "--vertical"]) == 2
    assert main(["analyze", "--video", str(video), "--max", "500"]) == 2
    assert main(["analyze", "--video", str(video), "--vod-start", "gestern"]) == 2
    err = capsys.readouterr().err
    assert "Traceback" not in err and err.count("Clip Hunter:") == 5
