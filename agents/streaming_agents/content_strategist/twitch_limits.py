"""Twitch-Grenzen für Stream-Titel und Tags – streng eingehalten.

Quelle (Stand: November 2026): Twitch API Reference, „Modify Channel Information“,
https://dev.twitch.tv/docs/api/reference/channels#modify-channel-information

- Titel: darf nicht leer sein; „Title exceeds the 140 character limit“ → höchstens 140 Zeichen.
- Tags: „A channel may specify a maximum of 10 tags. Each tag is limited to a maximum of 25
  characters and may not be an empty string or contain spaces or special characters.“

Was genau als Sonderzeichen gilt, nennt Twitch nicht. Wir erlauben deshalb nur Buchstaben
(auch Umlaute) und Ziffern – das ist die sichere Seite.
"""
import re

TITLE_MAX_CHARS = 140
TAGS_MAX_COUNT = 10
TAG_MAX_CHARS = 25
SOURCE_URL = "https://dev.twitch.tv/docs/api/reference/channels#modify-channel-information"
SOURCE_DATE = "November 2026"

_TAG_RE = re.compile(r"^[^\W_]+$", re.UNICODE)


def is_valid_title(title: str) -> bool:
    return bool(title.strip()) and len(title) <= TITLE_MAX_CHARS


def is_valid_tag(tag: str) -> bool:
    return 0 < len(tag) <= TAG_MAX_CHARS and bool(_TAG_RE.match(tag))


def fit_title(title: str) -> str:
    """Kürzt einen Titel wortweise auf höchstens 140 Zeichen (mit „…“)."""
    title = " ".join(title.split())
    if len(title) <= TITLE_MAX_CHARS:
        return title
    cut = title[: TITLE_MAX_CHARS - 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" -|:,") + "…"


def tag_from_text(text: str) -> str | None:
    """Macht aus beliebigem Text einen gültigen Tag: Wörter zusammenziehen, Rest entfernen.

    „Counter-Strike 2“ → „CounterStrike2“, „Baldur's Gate 3“ → „BaldursGate3“.
    """
    words = re.findall(r"[^\W_]+", text.replace("'", "").replace("’", ""), flags=re.UNICODE)
    tag = "".join(word[:1].upper() + word[1:] for word in words)[:TAG_MAX_CHARS]
    return tag if is_valid_tag(tag) else None


def clean_tags(candidates: list[str]) -> list[str]:
    """Gültige Tags in Reihenfolge, ohne Dubletten (Groß-/Kleinschreibung egal), höchstens 10."""
    result: list[str] = []
    seen: set[str] = set()
    for raw in candidates:
        tag = raw if is_valid_tag(raw) else tag_from_text(raw)
        if tag is None or tag.casefold() in seen:
            continue
        seen.add(tag.casefold())
        result.append(tag)
        if len(result) == TAGS_MAX_COUNT:
            break
    return result
