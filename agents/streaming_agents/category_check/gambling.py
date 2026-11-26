"""Glücksspiel-Kategorien: werden standardmäßig NICHT vorgeschlagen (Entscheidung des Nutzers).

Liste per Search Categories und Get Streams gegen die echte Twitch-API ermittelt
(26.11.2026, Stand: November 2026). Auf Twitch gibt es mehrere Kategorien gleichen Namens;
die IDs mit Live-Kanälen stehen hier, alle anderen gleichnamigen erfasst ``GAMBLING_NAMES``.

Bewusst NICHT in der Liste:
- „Crypto“ (499634): Handel/Finanzen, kein Glücksspiel im engeren Sinn.
- „Bingo“ (31080) und Lotterie-Spiele: meist Gelegenheitsspiele ohne Einsatz.
- „Sports Betting Simulator“ (233837772): eine Simulation. Eine Kategorie für echte
  Sportwetten gibt es auf Twitch nicht (Suche nach „betting“, „sportwetten“, „sportsbook“).
"""
from .aliases import normalize

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


def is_gambling(category_id: str, name: str) -> bool:
    return str(category_id) in GAMBLING_CATEGORIES or normalize(name) in GAMBLING_NAMES


def gambling_warning(name: str, language: str) -> str:
    if language == "de":
        return (f"Achtung: „{name}“ ist eine Glücksspiel-Kategorie. Der Kategorie-Check schlägt "
                "Glücksspiel standardmäßig nicht vor (Suchtgefahr, strenge Twitch-Regeln) und "
                "empfiehlt sie nicht.")
    return (f"Warning: “{name}” is a gambling category. The category check does not suggest "
            "gambling by default (risk of addiction, strict Twitch rules) and does not "
            "recommend it.")


def filtered_note(names: list[str], language: str) -> str:
    listed = ", ".join(names)
    if language == "de":
        word = "Glücksspiel-Kategorie" if len(names) == 1 else "Glücksspiel-Kategorien"
        return (f"{len(names)} {word} ausgeblendet ({listed}). Anzeigen mit --include-gambling "
                "(API: include_gambling).")
    word = "gambling category" if len(names) == 1 else "gambling categories"
    return (f"{len(names)} {word} hidden ({listed}). Show them with --include-gambling "
            "(API: include_gambling).")
