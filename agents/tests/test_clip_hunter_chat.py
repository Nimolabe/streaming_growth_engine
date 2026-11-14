import pytest
from chat_fixtures import START, Burst, ChatScenario, build_chat

from streaming_agents.clip_hunter.chat_log import (
    ChatLogError,
    ChatLogWriter,
    parse_chat_lines,
    read_chat_log,
)
from streaming_agents.clip_hunter.chat_signal import analyze_chat
from streaming_agents.clip_hunter.models import ChatLog, ChatLogHeader, ChatMessage, HuntSettings
from streaming_agents.clip_hunter.reactions import classify_message, is_alert_reaction

FULL = ChatScenario(
    bursts=[Burst(600, "funny", 45), Burst(1500, "hype", 60), Burst(2400, "shock", 30),
            Burst(3000, "tension", 25)],
    subs=[1000, 2700], raids=[2000], command_floods=[1200],
)
TRUE_EVENTS = [600, 1500, 2400, 3000]


# ---------- Mitschnitt-Datei ----------
def test_chat_log_roundtrip_is_compact(tmp_path):
    header = ChatLogHeader(channel="kanal", started_at=START)
    path = tmp_path / "chat.jsonl"
    with ChatLogWriter(path, header) as writer:
        writer.write(ChatMessage(ts=START + 1, user="a1", text="KEKW"))
        writer.write(ChatMessage(ts=START + 2, user="b2", kind="raid"))
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3 and '"bot"' not in lines[1]
    log = read_chat_log(path)
    assert log.header.channel == "kanal"
    assert [item.text for item in log.messages] == ["KEKW", ""]
    assert log.messages[1].kind == "raid"


def test_writer_never_overwrites(tmp_path):
    path = tmp_path / "chat.jsonl"
    path.write_text("x")
    with pytest.raises(ChatLogError):
        ChatLogWriter(path, ChatLogHeader(channel="kanal", started_at=START))


def test_truncated_or_broken_lines_are_skipped_and_sorted():
    log = parse_chat_lines([
        '{"format":"sge-chat-log","version":1,"channel":"k","started_at":1760000000}',
        '{"ts":1760000005,"user":"a","text":"zwei"}',
        '{"ts":1760000001,"user":"b","text":"eins"}',
        '{"ts":"kaputt","user":"c"}',
        '{"ts":1760000009,"user":"d","te',
    ])
    assert [item.text for item in log.messages] == ["eins", "zwei"]
    assert log.skipped_lines == 2


@pytest.mark.parametrize("lines", [[], ['{"hello":"world"}'], ["not json"]])
def test_invalid_logs_are_rejected(lines):
    with pytest.raises(ChatLogError):
        parse_chat_lines(lines)


# ---------- Reaktionen ----------
@pytest.mark.parametrize("text,expected", [
    ("KEKW KEKW KEKW", {"funny"}), ("hahahaha", {"funny"}), ("xDDD", {"funny"}),
    ("Pog", {"hype"}), ("W", {"hype"}), ("LETS GOOOO", {"hype"}), ("lets gooo", {"hype"}),
    ("WHAT", {"shock"}), ("??", {"shock"}), ("no way", {"shock"}), ("krass", {"shock"}),
    ("Sadge", {"fail"}), ("L", {"fail"}), ("F", {"fail"}),
    ("monkaS", {"tension"}), ("ICANT 😂", {"funny"}),
])
def test_reactions_are_classified(text, expected):
    assert classify_message(text) == expected


@pytest.mark.parametrize("text", [
    "what game is this", "w", "kurze Pause", "?", "welchen rang hast du", "ich bin L. aus Köln",
    "kekse sind lecker", "",
])
def test_normal_sentences_are_not_reactions(text):
    assert classify_message(text) == frozenset()


def test_alert_reactions():
    assert is_alert_reaction("Danke für den Raid <3")
    assert is_alert_reaction("ty for the gifted subs")
    assert not is_alert_reaction("KEKW")


# ---------- Chat-Ausschläge ----------
def test_detects_real_moments_with_types_and_timing():
    moments, stats = analyze_chat(build_chat(FULL), HuntSettings(), START)
    assert stats.level == "active"
    assert stats.events == {"sub": 2, "raid": 1}
    assert [m.dominant_category for m in moments] == ["funny", "hype", "shock", "tension"]
    for true_time, moment in zip(TRUE_EVENTS, moments):
        assert abs(moment.event_seconds - true_time) <= 4
        assert moment.onset_seconds > moment.event_seconds
        assert moment.reaction_share > 0.5
        assert moment.alert_nearby is None
        assert moment.sample_messages


@pytest.mark.parametrize("seed", range(1, 9))
def test_alerts_raids_commands_and_bots_never_become_moments(seed):
    scenario = ChatScenario(seed=seed, subs=[700, 1900], raids=[1300, 2600],
                            command_floods=[400, 3100], bot_spam_every=20)
    moments, _ = analyze_chat(build_chat(scenario), HuntSettings(), START)
    assert moments == []


@pytest.mark.parametrize("seed", range(1, 9))
def test_detection_is_stable_across_random_chats(seed):
    scenario = ChatScenario(seed=seed, bursts=FULL.bursts, subs=FULL.subs, raids=FULL.raids,
                            command_floods=FULL.command_floods)
    moments, _ = analyze_chat(build_chat(scenario), HuntSettings(), START)
    assert [m.dominant_category for m in moments] == ["funny", "hype", "shock", "tension"]


def test_single_spammer_is_not_a_moment():
    log = build_chat(ChatScenario(seed=3))
    spam = [ChatMessage(ts=START + 900 + index * 0.2, user="spammer", text="KEKW")
            for index in range(80)]
    log = ChatLog(header=log.header, messages=sorted(log.messages + spam, key=lambda m: m.ts))
    moments, _ = analyze_chat(log, HuntSettings(), START)
    assert moments == []


def test_broadcaster_messages_do_not_count():
    log = build_chat(ChatScenario(seed=4))
    own = [ChatMessage(ts=START + 1200 + index * 0.1, user=f"x{index}", text="KEKW",
                       broadcaster=True) for index in range(60)]
    log = ChatLog(header=log.header, messages=sorted(log.messages + own, key=lambda m: m.ts))
    assert analyze_chat(log, HuntSettings(), START)[0] == []


def test_vod_start_and_offset_shift_times():
    log = build_chat(ChatScenario(bursts=[Burst(600, "funny", 45)]))
    base, _ = analyze_chat(log, HuntSettings(), START)
    later_vod, _ = analyze_chat(log, HuntSettings(), START + 100)
    shifted, _ = analyze_chat(log, HuntSettings(chat_offset_seconds=30), START)
    assert later_vod[0].event_seconds == pytest.approx(base[0].event_seconds - 100, abs=1)
    assert shifted[0].event_seconds == pytest.approx(base[0].event_seconds + 30, abs=1)


def test_messages_outside_the_vod_are_ignored():
    log = build_chat(ChatScenario(bursts=[Burst(600, "funny", 45), Burst(3000, "hype", 50)]))
    moments, stats = analyze_chat(log, HuntSettings(), START, duration_seconds=1800)
    assert [m.dominant_category for m in moments] == ["funny"]
    assert stats.messages_ignored > 0


def test_small_chat_is_low_and_still_finds_clear_reactions():
    scenario = ChatScenario(seed=2, rate=0.12, audience=15, bot_spam_every=0,
                            bursts=[Burst(900, "funny", 8)])
    moments, stats = analyze_chat(build_chat(scenario), HuntSettings(), START)
    assert stats.level == "low"
    assert any(abs(m.event_seconds - 900) <= 6 for m in moments)


def test_almost_empty_chat_is_none():
    scenario = ChatScenario(seed=1, rate=0.004, audience=3, bot_spam_every=0)
    moments, stats = analyze_chat(build_chat(scenario), HuntSettings(), START)
    assert stats.level == "none" and moments == []


def test_empty_chat():
    log = ChatLog(header=ChatLogHeader(channel="k", started_at=START))
    moments, stats = analyze_chat(log, HuntSettings(), START)
    assert moments == [] and stats.messages_used == 0
