"""Anonymer, nur lesender Twitch-Chat-Mitschnitt (IRC über TLS).

Twitch erlaubt das Lesen öffentlicher Chats ohne Konto (Nick ``justinfan<Zahl>``).
Es wird nichts in den Chat geschrieben. Nutzernamen werden nicht gespeichert,
sondern pro Mitschnitt mit einem zufälligen, nicht gespeicherten Schlüssel pseudonymisiert.
"""
import hashlib
import hmac
import re
import secrets
import socket
import ssl
import time
from collections.abc import Callable, Collection, Iterable
from dataclasses import dataclass, field

from .chat_log import ChatLogWriter
from .models import ChatMessage, EventKind

IRC_HOST = "irc.chat.twitch.tv"
IRC_PORT = 6697
CHANNEL_PATTERN = re.compile(r"^[a-z0-9_]{3,25}$")

# Häufige Chat-Bots; ihre Nachrichten sind keine Zuschauer-Reaktionen.
KNOWN_BOTS = frozenset({
    "nightbot", "streamelements", "streamlabs", "moobot", "fossabot", "wizebot",
    "sery_bot", "soundalerts", "botrixoficial", "kofistreambot", "blerp", "streamstickers",
    "pokemoncommunitygame", "frostytoolsdotcom", "tangiabot", "own3d", "lumiastream",
    "creatisbot", "deepbot", "coebot", "phantombot", "ankhbot", "streamholics",
})

_USERNOTICE_KINDS: dict[str, EventKind] = {
    "sub": "sub", "resub": "sub", "primepaidupgrade": "sub",
    "subgift": "gift", "submysterygift": "gift", "giftpaidupgrade": "gift",
    "anongiftpaidupgrade": "gift", "communitypayforward": "gift", "standardpayforward": "gift",
    "raid": "raid", "announcement": "announcement",
}

_TAG_ESCAPES = {"s": " ", ":": ";", "\\": "\\", "r": "\r", "n": "\n"}


class ChannelNameError(ValueError):
    pass


def normalize_channel(name: str) -> str:
    channel = name.strip().lstrip("#").casefold()
    if channel.startswith(("https://", "http://", "www.", "twitch.tv/")):
        channel = channel.rstrip("/").rsplit("/", 1)[-1]
    if not CHANNEL_PATTERN.fullmatch(channel):
        raise ChannelNameError(
            "Kanalname ungültig: 3–25 Zeichen, nur Buchstaben, Ziffern und Unterstrich."
        )
    return channel


def _unescape_tag(value: str) -> str:
    out: list[str] = []
    index = 0
    while index < len(value):
        char = value[index]
        if char == "\\" and index + 1 < len(value):
            out.append(_TAG_ESCAPES.get(value[index + 1], value[index + 1]))
            index += 2
            continue
        if char != "\\":
            out.append(char)
        index += 1
    return "".join(out)


@dataclass(frozen=True)
class IrcLine:
    tags: dict[str, str]
    prefix: str
    command: str
    params: list[str] = field(default_factory=list)
    trailing: str | None = None

    @property
    def login(self) -> str:
        return self.prefix.split("!", 1)[0] if "!" in self.prefix else ""


def parse_irc_line(line: str) -> IrcLine | None:
    """Zerlegt eine IRC-Zeile (IRCv3-Tags, Präfix, Befehl, Parameter)."""
    rest = line.rstrip("\r\n")
    if not rest:
        return None
    tags: dict[str, str] = {}
    if rest.startswith("@"):
        raw_tags, _, rest = rest[1:].partition(" ")
        for item in raw_tags.split(";"):
            key, _, value = item.partition("=")
            if key:
                tags[key] = _unescape_tag(value)
    prefix = ""
    if rest.startswith(":"):
        prefix, _, rest = rest[1:].partition(" ")
    trailing = None
    if " :" in rest:
        rest, _, trailing = rest.partition(" :")
    elif rest.startswith(":"):
        trailing = rest[1:]
        rest = ""
    parts = rest.split()
    if not parts:
        return None
    return IrcLine(tags=tags, prefix=prefix, command=parts[0].upper(), params=parts[1:],
                   trailing=trailing)


class Pseudonymizer:
    """Ersetzt Nutzerkennungen durch kurze Pseudonyme; der Schlüssel wird nie gespeichert."""

    def __init__(self, key: bytes | None = None):
        self._key = key or secrets.token_bytes(16)

    def __call__(self, identity: str) -> str:
        return hmac.new(self._key, identity.encode("utf-8"), hashlib.sha256).hexdigest()[:12]


def to_chat_message(line: IrcLine, pseudonymize: Callable[[str], str], *,
                    bot_names: Collection[str] = KNOWN_BOTS,
                    now: Callable[[], float] = time.time) -> ChatMessage | None:
    """Wandelt PRIVMSG/USERNOTICE in eine datensparsame ChatMessage; sonst None."""
    if line.command not in {"PRIVMSG", "USERNOTICE"}:
        return None
    tags = line.tags
    login = (tags.get("login") or line.login or tags.get("display-name", "")).casefold()
    identity = tags.get("user-id") or login
    if not identity:
        return None
    try:
        ts = int(tags["tmi-sent-ts"]) / 1000
    except (KeyError, ValueError):
        ts = now()
    badges = tags.get("badges", "")
    if line.command == "USERNOTICE":
        kind: EventKind = _USERNOTICE_KINDS.get(tags.get("msg-id", ""), "event")
    elif tags.get("bits", "").isdigit() and int(tags["bits"]) > 0:
        kind = "cheer"
    else:
        kind = "message"
    text = (line.trailing or "")[:600]
    if text.startswith("\x01ACTION ") and text.endswith("\x01"):
        text = text[8:-1]  # /me-Nachrichten
    return ChatMessage(
        ts=ts,
        user=pseudonymize(identity),
        text=text,
        kind=kind,
        bot=login in bot_names,
        mod=tags.get("mod") == "1" or "moderator/" in badges,
        broadcaster="broadcaster/" in badges,
        subscriber=tags.get("subscriber") == "1" or "subscriber/" in badges,
    )


class Connection:
    """Minimale Schnittstelle, damit Tests ohne Netzwerk laufen können."""

    def sendall(self, data: bytes) -> None: ...
    def recv(self, size: int) -> bytes: ...
    def settimeout(self, value: float) -> None: ...
    def close(self) -> None: ...


def tls_connect(host: str = IRC_HOST, port: int = IRC_PORT, timeout: float = 15) -> Connection:
    raw = socket.create_connection((host, port), timeout=timeout)
    return ssl.create_default_context().wrap_socket(raw, server_hostname=host)


@dataclass
class RecordStats:
    messages: int = 0
    events: int = 0
    reconnects: int = 0
    stopped_by: str = ""
    notices: list[str] = field(default_factory=list)


class TwitchChatRecorder:
    """Schneidet den Chat eines Kanals mit, bis Strg+C, Zeitlimit oder zu viele Fehler."""

    KEEPALIVE_SECONDS = 360

    def __init__(self, channel: str, writer: ChatLogWriter, *,
                 extra_bot_names: Iterable[str] = (),
                 connect: Callable[[], Connection] = tls_connect,
                 sleep: Callable[[float], None] = time.sleep,
                 clock: Callable[[], float] = time.time,
                 log: Callable[[str], None] = print,
                 max_seconds: float | None = None,
                 max_reconnects: int = 50,
                 pseudonymizer: Pseudonymizer | None = None):
        self.channel = normalize_channel(channel)
        self.writer = writer
        self.bot_names = KNOWN_BOTS | {name.casefold() for name in extra_bot_names}
        self._connect = connect
        self._sleep = sleep
        self._clock = clock
        self._log = log
        self.max_seconds = max_seconds
        self.max_reconnects = max_reconnects
        self._pseudonymize = pseudonymizer or Pseudonymizer()
        self.stats = RecordStats()

    def _handshake(self, conn: Connection) -> None:
        nick = f"justinfan{secrets.randbelow(80000) + 10000}"
        for command in ("CAP REQ :twitch.tv/tags twitch.tv/commands", "PASS SCHMOOPIIE",
                        f"NICK {nick}", f"JOIN #{self.channel}"):
            conn.sendall((command + "\r\n").encode("utf-8"))

    def run(self) -> RecordStats:
        started = self._clock()
        backoff = 1.0
        try:
            while True:
                if self._time_up(started):
                    self.stats.stopped_by = "Zeitlimit erreicht"
                    break
                try:
                    conn = self._connect()
                except OSError as exc:
                    if not self._may_retry(f"Verbindung fehlgeschlagen ({type(exc).__name__})"):
                        break
                    self._sleep(backoff)
                    backoff = min(backoff * 2, 60)
                    continue
                try:
                    self._handshake(conn)
                    reason = self._read_loop(conn, started)
                except OSError:
                    reason = "lost"
                finally:
                    try:
                        conn.close()
                    except OSError:
                        pass
                if reason in {"Zeitlimit erreicht", "Kanal nicht verfügbar"}:
                    self.stats.stopped_by = reason
                    break
                if reason == "connected-then-lost":
                    backoff = 1.0  # war verbunden: sofort und ohne lange Pause neu verbinden
                if not self._may_retry("Verbindung getrennt"):
                    break
                self._sleep(backoff)
                backoff = min(backoff * 2, 60)
        except KeyboardInterrupt:
            self.stats.stopped_by = "Strg+C"
        return self.stats

    def _time_up(self, started: float) -> bool:
        return self.max_seconds is not None and self._clock() - started >= self.max_seconds

    def _may_retry(self, reason: str) -> bool:
        self.stats.reconnects += 1
        if self.stats.reconnects > self.max_reconnects:
            self.stats.stopped_by = f"zu viele Verbindungsfehler ({reason})"
            return False
        self._log(f"{reason} – neuer Versuch …")
        return True

    def _read_loop(self, conn: Connection, started: float) -> str:
        conn.settimeout(5)
        buffer = b""
        last_data = self._clock()
        received_any = False
        while True:
            if self._time_up(started):
                return "Zeitlimit erreicht"
            try:
                chunk = conn.recv(65536)
            except TimeoutError:
                if self._clock() - last_data > self.KEEPALIVE_SECONDS:
                    return "connected-then-lost" if received_any else "lost"
                continue
            except OSError:
                return "connected-then-lost" if received_any else "lost"
            if not chunk:
                return "connected-then-lost" if received_any else "lost"
            last_data = self._clock()
            received_any = True
            buffer += chunk
            *lines, buffer = buffer.split(b"\r\n")
            for raw in lines:
                outcome = self._handle(conn, raw.decode("utf-8", errors="replace"))
                if outcome:
                    return outcome

    def _handle(self, conn: Connection, raw: str) -> str | None:
        line = parse_irc_line(raw)
        if line is None:
            return None
        if line.command == "PING":
            conn.sendall(f"PONG :{line.trailing or 'tmi.twitch.tv'}\r\n".encode())
            return None
        if line.command == "RECONNECT":
            return "connected-then-lost"
        if line.command == "NOTICE":
            text = line.trailing or ""
            self.stats.notices.append(text[:200])
            self._log(f"Twitch-Hinweis: {text}")
            if line.tags.get("msg-id") in {"msg_channel_suspended", "msg_channel_blocked"}:
                return "Kanal nicht verfügbar"
            return None
        message = to_chat_message(line, self._pseudonymize, bot_names=self.bot_names,
                                  now=self._clock)
        if message is not None:
            self.writer.write(message)
            if message.kind == "message":
                self.stats.messages += 1
            else:
                self.stats.events += 1
        return None
