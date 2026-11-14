"""Einordnung von Chat-Nachrichten nach Reaktionsart.

Emotes von Twitch, 7TV, BTTV und FFZ kommen im Chat als Text an (z. B. ``KEKW``).
Emote-Namen werden mit Groß-/Kleinschreibung verglichen, Wörter ohne.
Einzelbuchstaben wie ``W``, ``L`` oder ``F`` zählen nur als eigenständiges,
großgeschriebenes Wort, damit normale Sätze nicht als Reaktion gelten.
Die Listen sind ein Startpunkt und sollen mit echten Mitschnitten erweitert werden.
"""
import re

REACTION_CATEGORIES = ("funny", "hype", "shock", "fail", "tension")

_EMOTES: dict[str, frozenset[str]] = {
    "funny": frozenset({
        "KEKW", "KEKL", "LUL", "LULW", "OMEGALUL", "ICANT", "pepeLaugh", "PepeLaugh",
        "LMAO", "4Head", "EleGiggle", "kekw", "Kekw", "KEK", "xdd", "XDD", "LOLW",
        "pepeLaughing", "OMEGADANCE",
    }),
    "hype": frozenset({
        "Pog", "POG", "PogU", "POGGERS", "Poggers", "PogChamp", "PagMan", "PagChomp", "POGCRAZY",
        "GIGACHAD", "Chad", "EZ", "Clap", "W", "WW", "WWW", "HYPERS", "PogBones", "catJAM",
        "LETSGO", "LETSGOOO", "FeelsStrongMan", "peepoClap",
    }),
    "shock": frozenset({
        "WHAT", "WAYTOO", "D:", "monkaOMEGA", "HUH", "Huh", "WutFace", "Stare", "OOOO", "OOOOO",
        "NOWAY", "WTF", "OMG", "pepeMeltdown", "Susge",
    }),
    "fail": frozenset({
        "L", "LL", "LLL", "F", "Sadge", "NotLikeThis", "BibleThump", "PepeHands", "FeelsBadMan",
        "Deadge", "Despairge", "BOOBA_RIP",
    }),
    "tension": frozenset({
        "monkaS", "monkaW", "monkaGIGA", "monkaH", "monkaSTEER", "PauseChamp", "PAUSE",
        "COPIUM", "Copium", "PRAYGE", "Prayge", "monkaEyes",
    }),
}

_WORDS: dict[str, frozenset[str]] = {
    "funny": frozenset({"lol", "lul", "lmao", "lmfao", "rofl", "xd", "xdd", "hahaha", "haha",
                        "ahahah", "hahahaha", "jaja", "jajaja", "dead", "💀", "😂", "🤣", "😆"}),
    "hype": frozenset({"pog", "poggers", "letsgo", "letsgoo", "letsgooo", "insane", "clutch",
                       "hype", "ehre", "goated", "🔥", "🐐", "👏"}),
    "shock": frozenset({"wtf", "omg", "wat", "noway", "krass", "huh", "bruh", "😱",
                        "😳", "🤯", "😨"}),
    "fail": frozenset({"rip", "unlucky", "sadge", "😭", "😢"}),
    "tension": frozenset({"😬", "😰"}),
}

_PHRASES: dict[str, tuple[re.Pattern[str], ...]] = {
    "hype": (re.compile(r"\blets+\s*go+\b"), re.compile(r"\blet'?s\s+go+\b")),
    "shock": (re.compile(r"\bno\s+way\b"), re.compile(r"\bwhat\s+the\b"),
              re.compile(r"\bach\s+du\s+sch")),
    "funny": (re.compile(r"\b(ha){3,}h?\b"), re.compile(r"\bx+d+\b")),
}

_QUESTION_ONLY = re.compile(r"^\?{2,}$")
# Ein- und Zweibuchstaben-Reaktionen zählen nur in kurzen Nachrichten („W“, „L L L“),
# nicht mitten in einem Satz („ich bin L. aus Köln“).
_SHORT_TOKENS = frozenset({"W", "WW", "WWW", "L", "LL", "LLL", "F"})
_SHORT_MESSAGE_TOKENS = 3
_TOKEN_SPLIT = re.compile(r"\s+")
_TRIM = ".,!;:\"'()[]{}"


def classify_message(text: str) -> frozenset[str]:
    """Liefert die Reaktionsarten einer Nachricht (leer, wenn keine erkannt)."""
    if not text:
        return frozenset()
    found: set[str] = set()
    stripped = text.strip()
    if _QUESTION_ONLY.match(stripped):
        found.add("shock")
    tokens = _TOKEN_SPLIT.split(stripped)
    short_message = len(tokens) <= _SHORT_MESSAGE_TOKENS or all(
        token in _SHORT_TOKENS for token in tokens)
    for raw_token in tokens:
        token = raw_token.strip(_TRIM) or raw_token
        if token in _SHORT_TOKENS and not short_message:
            continue
        lowered = token.casefold()
        for category, emotes in _EMOTES.items():
            if token in emotes:
                found.add(category)
        for category, words in _WORDS.items():
            if lowered in words:
                found.add(category)
        if lowered.startswith(("hahaha", "ahahaha")):
            found.add("funny")
    lowered_text = stripped.casefold()
    for category, patterns in _PHRASES.items():
        if category not in found and any(pattern.search(lowered_text) for pattern in patterns):
            found.add(category)
    return frozenset(found)


_ALERT_WORDS = re.compile(
    r"\b(raid|raiders?|welcome|willkommen|gifted|gift|subs?|subbed|resub|thanks?|ty|danke|"
    r"hype\s*train|bits|cheer\w*|follow\w*)\b",
    re.IGNORECASE,
)
_ALERT_EMOTES = frozenset({"<3", "HeyGuys", "VoHiYo", "TwitchUnity", "bleedPurple", "GivePLZ",
                           "TakeNRG", "SUBprise", "HSWP", "peepoHey", "Wave", "Hey"})


def is_alert_reaction(text: str) -> bool:
    """Typische Reaktion auf Subs, Raids oder Spenden (keine Reaktion auf Stream-Inhalt)."""
    if _ALERT_WORDS.search(text):
        return True
    return any(token in _ALERT_EMOTES for token in text.split())
