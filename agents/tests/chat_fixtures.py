"""Nachgebaute Chat-Verläufe für Tests (keine echten Nutzerdaten)."""
import random
from dataclasses import dataclass, field

from streaming_agents.clip_hunter.models import ChatLog, ChatLogHeader, ChatMessage

START = 1_760_000_000.0

NORMAL = [
    "hi", "hallo zusammen", "what game is this", "wie lange streamst du heute?", "nice",
    "gg", "welcher rang bist du", "moin", "o7", "Kappa", "true", "lets see", "hmm",
    "wo kommst du her", "ich muss gleich los", "spielst du später noch ranked",
    "LUL", "xD", "ok", "ja", "nein", "BatChest", "Clueless", "WAYTOODANK",
]
REACTIONS = {
    "funny": ["KEKW", "KEKW KEKW", "OMEGALUL", "LUL LUL", "hahahaha", "ICANT", "xDDD", "😂😂"],
    "hype": ["Pog", "POGGERS", "W", "LETS GOOO", "PogChamp", "insane", "W W W", "🔥🔥"],
    "shock": ["WHAT", "??", "NO WAY", "wtf", "WAYTOO", "omg", "HUH"],
    "fail": ["L", "Sadge", "F", "NotLikeThis", "rip", "L L L"],
    "tension": ["monkaS", "monkaW", "PauseChamp", "monkaS monkaS", "😬"],
}


@dataclass
class Burst:
    event: float
    category: str
    users: int
    lag: float = 5.0


@dataclass
class ChatScenario:
    duration: int = 3600
    rate: float = 1.2          # normale Nachrichten pro Sekunde
    audience: int = 150        # Anzahl aktiver Chatter
    seed: int = 7
    bursts: list[Burst] = field(default_factory=list)
    subs: list[float] = field(default_factory=list)
    raids: list[float] = field(default_factory=list)
    command_floods: list[float] = field(default_factory=list)
    bot_spam_every: float = 300


def build_chat(s: ChatScenario) -> ChatLog:
    rng = random.Random(s.seed)
    users = [f"u{index:04}" for index in range(s.audience)]
    messages: list[ChatMessage] = []

    def add(t: float, user: str, text: str, **kw) -> None:
        if 0 <= t:
            messages.append(ChatMessage(ts=START + t, user=user, text=text, **kw))

    t = 0.0
    while t < s.duration:
        t += rng.expovariate(s.rate)
        add(t, rng.choice(users), rng.choice(NORMAL))
    for burst in s.bursts:
        for user in rng.sample(users, min(burst.users, len(users))):
            first = burst.event + burst.lag + rng.uniform(-1.5, 2.5)
            add(first, user, rng.choice(REACTIONS[burst.category]))
            if rng.random() < 0.4:
                add(first + rng.uniform(0.5, 3), user, rng.choice(REACTIONS[burst.category]))
    for sub in s.subs:
        add(sub, "sub0", "", kind="sub")
        for user in rng.sample(users, 20):
            add(sub + rng.uniform(1, 9), user,
                rng.choice(["Danke für den Sub <3", "welcome", "HeyGuys", "hype", "ty for sub",
                            "<3 <3"]))
    for raid in s.raids:
        add(raid, "raider", "", kind="raid")
        for index in range(60):
            add(raid + rng.uniform(1, 12), f"r{index:03}", "FREUNDESKANAL RAID 💜 💜 💜")
    for flood in s.command_floods:
        for user in rng.sample(users, 50):
            add(flood + rng.uniform(0, 8), user, "!enter")
    spam = s.bot_spam_every
    while s.bot_spam_every and spam < s.duration:
        add(spam, "bot1", "Folgt auf Instagram! Discord: !discord", bot=True)
        spam += s.bot_spam_every
    messages.sort(key=lambda item: item.ts)
    return ChatLog(header=ChatLogHeader(channel="testkanal", started_at=START),
                   messages=messages)
