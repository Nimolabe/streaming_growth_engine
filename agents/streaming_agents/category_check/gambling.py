"""Glücksspiel wird von der Streaming Growth Engine NICHT unterstützt.

Entscheidung des Nutzers vom 26.11.2026: nie vorschlagen, nie messen, nie planen; es gibt
keine Option zum Einschalten. Diese Datei ist die EINE Liste dafür – der Kategorie-Check und
der Content Strategist nutzen sie gemeinsam. Ein späterer Export für die Website muss
dieselbe Liste übernehmen.

Liste per Search Categories und Get Streams gegen die echte Twitch-API ermittelt
(26.11.2026, Stand: November 2026). Auf Twitch gibt es mehrere Kategorien gleichen Namens;
die IDs mit Live-Kanälen stehen hier, alle anderen gleichnamigen erfasst ``GAMBLING_NAMES``.

Bewusst NICHT in der Liste:
- „Crypto“ (499634): Handel/Finanzen, kein Glücksspiel im engeren Sinn.
- „Bingo“ (31080) und Lotterie-Spiele: meist Gelegenheitsspiele ohne Einsatz.
- „Sports Betting Simulator“ (233837772): eine Simulation. Eine Kategorie für echte
  Sportwetten gibt es auf Twitch nicht (Suche nach „betting“, „sportwetten“, „sportsbook“);
  der Name „Sports Betting“ ist trotzdem gesperrt, falls sie entsteht.
"""
from .aliases import alias_target, normalize

GAMBLING_CATEGORIES: dict[str, str] = {
    "498566": "Slots",               # mit Abstand die größte (93+ Kanäle weltweit am 26.11.)
    "1429674651": "Slots",
    "29452": "Virtual Casino",       # 32+ Kanäle
    "488190": "Poker",               # 48+ Kanäle
    "493887283": "Casino",
    "582382910": "Casino",
    "610885098": "Casino Games",
    "490344": "Roulette",
    "202076418": "Blackjack",
    "129708622": "Black Jack",
    "760679498": "Baccarat",
    "1954967210": "Gates of Olympus",  # Spielautomat eines Online-Casinos
}

# Gleichnamige Kategorien mit anderer ID (z. B. sieben verschiedene „Blackjack“).
GAMBLING_NAMES: frozenset[str] = frozenset(normalize(name) for name in (
    *GAMBLING_CATEGORIES.values(), "Texas Hold'em", "Texas Hold 'Em Poker", "Sports Betting",
))


class GamblingNotSupported(ValueError):
    """Eine Glücksspiel-Kategorie wurde angefragt; die Meldung ist freundlich und zweisprachig."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(rejection(name, "de"))


def is_gambling_name(name: str) -> bool:
    """Name (oder seine Kurzform) ist eine Glücksspiel-Kategorie – für Eingaben ohne ID."""
    target = alias_target(name)
    return normalize(name) in GAMBLING_NAMES or (target is not None
                                                  and normalize(target) in GAMBLING_NAMES)


def is_gambling(category_id: str, name: str) -> bool:
    return str(category_id) in GAMBLING_CATEGORIES or is_gambling_name(name)


def rejection(name: str, language: str) -> str:
    if language == "de":
        return (f"„{name}“ ist eine Glücksspiel-Kategorie. Glücksspiel-Kategorien werden von der "
                "Streaming Growth Engine nicht unterstützt – sie werden weder gemessen noch "
                "vorgeschlagen oder geplant.")
    return (f"“{name}” is a gambling category. Gambling categories are not supported by the "
            "Streaming Growth Engine – they are never measured, suggested or planned.")


def skipped_note(count: int, language: str) -> str:
    """Neutrale Zahl ohne Namen (z. B. bei ``suggest``)."""
    if language == "de":
        word = "Glücksspiel-Kategorie" if count == 1 else "Glücksspiel-Kategorien"
        return f"Ohne {count} {word} (werden nicht unterstützt)."
    word = "gambling category" if count == 1 else "gambling categories"
    return f"Without {count} {word} (not supported)."


def ignored_note(count: int, language: str) -> str:
    """Hinweis, wenn alte Messdateien Glücksspiel-Einträge enthalten (``report``, API)."""
    if language == "de":
        word = "Messung" if count == 1 else "Messungen"
        return (f"{count} {word} zu Glücksspiel-Kategorien ignoriert (werden nicht "
                "unterstützt).")
    word = "measurement" if count == 1 else "measurements"
    return f"{count} {word} of gambling categories ignored (not supported)."
