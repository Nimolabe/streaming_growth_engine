import pytest

from streaming_agents.clip_hunter.chat_log import ChatLogWriter, read_chat_log
from streaming_agents.clip_hunter.models import ChatLogHeader
from streaming_agents.clip_hunter.twitch_irc import (
    ChannelNameError,
    Pseudonymizer,
    TwitchChatRecorder,
    normalize_channel,
    parse_irc_line,
    to_chat_message,
)

PRIVMSG = (
    "@badge-info=;badges=subscriber/12,premium/1;color=#FF0000;display-name=Max\\sMuster;"
    "emotes=;id=abc;mod=0;room-id=1;subscriber=1;tmi-sent-ts=1760000000123;user-id=4242 "
    ":maxmuster!maxmuster@maxmuster.tmi.twitch.tv PRIVMSG #kanal :KEKW das war gut"
)
RAID = (
    "@badges=;display-name=Freund;login=freund;msg-id=raid;msg-param-viewerCount=50;"
    "system-msg=50\\sraiders\\sfrom\\sFreund\\shave\\sjoined!;tmi-sent-ts=1760000100000;"
    "user-id=99 :tmi.twitch.tv USERNOTICE #kanal"
)


def key_pseudo():
    return Pseudonymizer(b"0123456789abcdef")


def test_parse_privmsg_with_tags_and_escapes():
    line = parse_irc_line(PRIVMSG)
    assert line.command == "PRIVMSG"
    assert line.params == ["#kanal"]
    assert line.trailing == "KEKW das war gut"
    assert line.tags["display-name"] == "Max Muster"
    assert line.login == "maxmuster"


def test_tag_unescaping_covers_all_sequences():
    line = parse_irc_line("@a=x\\:y\\sz\\\\w\\n :tmi.twitch.tv NOTICE #k :hi")
    assert line.tags["a"] == "x;y z\\w\n"


def test_message_is_pseudonymized_and_flags_are_read():
    message = to_chat_message(parse_irc_line(PRIVMSG), key_pseudo())
    assert message.ts == pytest.approx(1760000000.123)
    assert message.text == "KEKW das war gut"
    assert message.subscriber and not message.mod and not message.bot
    assert "max" not in message.user.casefold() and message.user != "4242"
    assert message.user == key_pseudo()("4242")
    assert message.user != Pseudonymizer(b"another-key-1234")("4242")


def test_usernotice_raid_and_sub_are_events():
    raid = to_chat_message(parse_irc_line(RAID), key_pseudo())
    assert raid.kind == "raid"
    sub = to_chat_message(parse_irc_line(RAID.replace("msg-id=raid", "msg-id=resub")),
                          key_pseudo())
    assert sub.kind == "sub"
    gift = to_chat_message(parse_irc_line(RAID.replace("msg-id=raid", "msg-id=submysterygift")),
                           key_pseudo())
    assert gift.kind == "gift"
    other = to_chat_message(parse_irc_line(RAID.replace("msg-id=raid", "msg-id=ritual")),
                            key_pseudo())
    assert other.kind == "event"


def test_cheer_bot_broadcaster_and_action_messages():
    cheer = to_chat_message(parse_irc_line(PRIVMSG.replace("id=abc;", "bits=100;id=abc;")),
                            key_pseudo())
    assert cheer.kind == "cheer"
    bot = to_chat_message(parse_irc_line(PRIVMSG.replace("maxmuster", "nightbot")), key_pseudo())
    assert bot.bot
    owner = to_chat_message(parse_irc_line(PRIVMSG.replace("subscriber/12", "broadcaster/1")),
                            key_pseudo())
    assert owner.broadcaster
    action = to_chat_message(parse_irc_line(PRIVMSG.replace(
        ":KEKW das war gut", ":\x01ACTION tanzt\x01")), key_pseudo())
    assert action.text == "tanzt"


def test_non_chat_lines_are_ignored():
    assert to_chat_message(parse_irc_line(":tmi.twitch.tv 001 justinfan1 :Welcome"),
                           key_pseudo()) is None
    assert parse_irc_line("") is None


@pytest.mark.parametrize("raw,expected", [
    ("MeinKanal", "meinkanal"), ("#kanal_1", "kanal_1"),
    ("https://www.twitch.tv/Some_Streamer/", "some_streamer"), ("twitch.tv/abc", "abc"),
])
def test_normalize_channel(raw, expected):
    assert normalize_channel(raw) == expected


@pytest.mark.parametrize("raw", ["ab", "kanal mit leerzeichen", "x" * 26, "böse"])
def test_invalid_channel_rejected(raw):
    with pytest.raises(ChannelNameError):
        normalize_channel(raw)


class FakeConnection:
    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.sent: list[str] = []
        self.closed = False

    def sendall(self, data: bytes) -> None:
        self.sent.append(data.decode())

    def settimeout(self, value: float) -> None:
        pass

    def recv(self, size: int) -> bytes:
        if not self.chunks:
            return b""
        item = self.chunks.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    def close(self) -> None:
        self.closed = True


class Clock:
    def __init__(self):
        self.now = 1_760_000_000.0

    def __call__(self) -> float:
        self.now += 0.01
        return self.now


def make_writer(tmp_path):
    return ChatLogWriter(tmp_path / "chat.jsonl",
                         ChatLogHeader(channel="kanal", started_at=1_760_000_000))


def test_recorder_handshake_ping_split_lines_and_reconnect(tmp_path):
    raw = (PRIVMSG + "\r\n").encode()
    first = FakeConnection([
        b":tmi.twitch.tv 001 justinfan :Welcome\r\nPING :tmi.twitch.tv\r\n",
        raw[:40], raw[40:],
        b":tmi.twitch.tv RECONNECT\r\n",
    ])
    second = FakeConnection([(RAID + "\r\n").encode(), KeyboardInterrupt()])
    connections = iter([first, second])
    sleeps: list[float] = []
    writer = make_writer(tmp_path)
    recorder = TwitchChatRecorder("Kanal", writer, connect=lambda: next(connections),
                                  sleep=sleeps.append, clock=Clock(), log=lambda _: None,
                                  pseudonymizer=key_pseudo())
    stats = recorder.run()
    writer.close()
    assert stats.messages == 1 and stats.events == 1
    assert stats.stopped_by == "Strg+C"
    assert any(cmd.startswith("CAP REQ :twitch.tv/tags twitch.tv/commands") for cmd in first.sent)
    assert any(cmd.startswith("NICK justinfan") for cmd in first.sent)
    assert "JOIN #kanal\r\n" in first.sent
    assert "PONG :tmi.twitch.tv\r\n" in first.sent
    assert first.closed
    assert sleeps == [1.0]
    log = read_chat_log(tmp_path / "chat.jsonl")
    assert [item.kind for item in log.messages] == ["message", "raid"]
    assert "maxmuster" not in (tmp_path / "chat.jsonl").read_text()


def test_recorder_backs_off_and_gives_up(tmp_path):
    def broken():
        raise ConnectionRefusedError

    sleeps: list[float] = []
    writer = make_writer(tmp_path)
    stats = TwitchChatRecorder("kanal", writer, connect=broken, sleep=sleeps.append,
                               clock=Clock(), log=lambda _: None, max_reconnects=8).run()
    writer.close()
    assert stats.stopped_by.startswith("zu viele Verbindungsfehler")
    assert sleeps == [1, 2, 4, 8, 16, 32, 60, 60]


def test_recorder_stops_for_suspended_channel(tmp_path):
    notice = (b"@msg-id=msg_channel_suspended :tmi.twitch.tv NOTICE #kanal "
              b":This channel does not exist or has been suspended.\r\n")
    conn = FakeConnection([notice])
    writer = make_writer(tmp_path)
    stats = TwitchChatRecorder("kanal", writer, connect=lambda: conn, sleep=lambda _: None,
                               clock=Clock(), log=lambda _: None).run()
    writer.close()
    assert stats.stopped_by == "Kanal nicht verfügbar"
    assert stats.notices


def test_recorder_respects_time_limit(tmp_path):
    class SlowClock(Clock):
        def __call__(self):
            self.now += 30
            return self.now

    conn = FakeConnection([(PRIVMSG + "\r\n").encode()] * 100)
    writer = make_writer(tmp_path)
    stats = TwitchChatRecorder("kanal", writer, connect=lambda: conn, sleep=lambda _: None,
                               clock=SlowClock(), log=lambda _: None, max_seconds=120).run()
    writer.close()
    assert stats.stopped_by == "Zeitlimit erreicht"
    assert 0 < stats.messages < 100
