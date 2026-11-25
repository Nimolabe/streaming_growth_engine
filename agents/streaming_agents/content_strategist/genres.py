"""Die EINE zentrale Zuordnung Spiel → Genre für den Content Strategist.

Erkannt wird über Schreibweisen (Aliasse) als ganze Wörter, unabhängig von Groß-/Kleinschreibung
und Satzzeichen („Counter-Strike 2“, „CS2“, „counter strike“). Gibt es mehrere Treffer, gewinnt
der längste Alias, damit z. B. „Call of Duty: Warzone“ als Battle Royale erkannt wird und nicht
als Shooter. Unbekannte Spiele bekommen kein Genre (``None``); der Plan nutzt dann allgemeine
Formate und sagt das ehrlich.
"""
import re
from typing import Literal

Genre = Literal[
    "shooter", "battle_royale", "moba", "story", "horror", "cozy", "sandbox", "sports",
    "just_chatting",
]

GENRE_LABELS: dict[str, tuple[str, str]] = {
    "shooter": ("Shooter", "Shooter"),
    "battle_royale": ("Battle Royale", "Battle royale"),
    "moba": ("MOBA", "MOBA"),
    "story": ("Story/Singleplayer", "Story/single-player"),
    "horror": ("Horror", "Horror"),
    "cozy": ("Cozy/Simulation", "Cozy/simulation"),
    "sandbox": ("Sandbox/Survival", "Sandbox/survival"),
    "sports": ("Sport/Rennspiele", "Sports/racing"),
    "just_chatting": ("Just Chatting", "Just Chatting"),
}
UNKNOWN_LABEL = ("kein Genre erkannt", "no genre recognised")

# Aliasse in normalisierter Form: Kleinbuchstaben, Satzzeichen → Leerzeichen.
# Bewusst OHNE Genre (→ „kein Genre erkannt“, allgemeine Formate):
# - GTA V / GTA RP: Rollenspiel-Server und Missionen passen weder zu den Bau-/Überlebens-Formaten
#   (Sandbox) noch zu einem anderen Genre.
# - World of Warcraft: ein MMO. Story/Singleplayer wäre falsch (Tag „Singleplayer“), ein
#   eigenes MMO-Genre gibt es noch nicht.
# - Teamfight Tactics: Auto-Battler, passt zu keinem Genre.
# Diese Spiele bekommen die allgemeinen Formate für VERTRAUTE Spiele (Abend mit Ziel,
# entspanntes Spielen, Zuschauerrunde, Fortschritt); „Erste Eindrücke“ nur mit first_time.
# Nur „R.E.P.O.“ (→ „r e p o“), nicht „repo“,
# damit z. B. „Repo Man“ nicht als Horror gilt.
GAME_ALIASES: dict[str, tuple[str, ...]] = {
    "shooter": (
        "valorant", "cs2", "cs 2", "csgo", "cs go", "counter strike", "counterstrike",
        "call of duty", "cod", "overwatch", "overwatch 2", "rainbow six", "rainbow six siege",
        "r6", "r6s", "battlefield", "the finals", "destiny 2", "escape from tarkov", "tarkov",
        "halo", "team fortress 2", "tf2", "marvel rivals", "deadlock", "arc raiders",
    ),
    "battle_royale": (
        "fortnite", "apex", "apex legends", "warzone", "call of duty warzone", "cod warzone",
        "pubg", "pubg battlegrounds", "playerunknown s battlegrounds", "fall guys",
    ),
    "moba": (
        "league of legends", "lol", "dota", "dota 2", "smite", "smite 2",
        "heroes of the storm", "pokemon unite", "pokémon unite",
    ),
    "story": (
        "the last of us", "elden ring", "hollow knight", "hollow knight silksong", "silksong",
        "god of war", "zelda", "the legend of zelda", "baldur s gate", "baldur s gate 3",
        "cyberpunk 2077", "red dead redemption", "red dead redemption 2", "the witcher",
        "the witcher 3", "hades", "hades ii", "hades 2", "celeste", "undertale", "cuphead",
        "dead cells", "dark souls", "sekiro", "bloodborne", "final fantasy", "persona",
        "it takes two", "split fiction", "ori", "spider man", "horizon", "indie", "indie games",
        "metroidvania", "kingdom come deliverance", "clair obscur",
        "hogwarts legacy",
        # Pokémon-Hauptspiele (Legenden, Karmesin/Purpur, Schwert/Schild …) sind Story-Abenteuer;
        # „Pokémon Unite“ bleibt MOBA, weil der längere Alias gewinnt.
        "pokemon", "pokémon",
    ),
    "horror": (
        "phasmophobia", "resident evil", "lethal company", "outlast", "dead by daylight",
        "silent hill", "five nights at freddy s", "fnaf", "content warning", "amnesia",
        "the outlast trials", "alien isolation", "dead space", "r e p o", "horror",
    ),
    "cozy": (
        "stardew valley", "stardew", "die sims", "the sims", "sims", "sims 4", "die sims 4",
        "animal crossing", "planet zoo", "planet coaster", "cities skylines", "two point",
        "euro truck simulator", "american truck simulator", "ets2", "ets 2",
        "landwirtschafts simulator",
        "farming simulator", "powerwash simulator", "house flipper", "unpacking",
        "coral island", "disney dreamlight valley", "slime rancher", "spiritfarer", "cozy",
    ),
    "sandbox": (
        "minecraft", "rust", "valheim", "ark", "ark survival evolved", "ark survival ascended",
        "terraria", "7 days to die", "palworld", "subnautica", "the forest", "sons of the forest",
        "factorio", "satisfactory", "don t starve", "don t starve together", "enshrouded",
        "dayz", "raft", "grounded", "no man s sky", "space engineers", "conan exiles",
    ),
    "sports": (
        "ea sports fc", "ea fc", "fc 24", "fc 25", "fc 26", "fifa", "rocket league", "forza",
        "forza horizon", "forza motorsport", "gran turismo", "f1", "f1 24", "f1 25",
        "nba 2k", "madden", "efootball", "mario kart", "trackmania", "assetto corsa",
        "iracing", "nhl", "wwe 2k", "tony hawk",
    ),
    "just_chatting": (
        "just chatting", "chatting", "irl", "talk", "talk shows", "talk shows podcasts",
        "talk shows & podcasts", "podcast", "podcasts", "travel outdoors", "travel & outdoors",
    ),
}


def normalize(name: str) -> str:
    text = re.sub(r"[^\w]+", " ", name.casefold().replace("&", " "), flags=re.UNICODE)
    return " ".join(text.replace("_", " ").split())


_ALIAS_TABLE: list[tuple[str, str]] = sorted(
    ((normalize(alias), genre) for genre, aliases in GAME_ALIASES.items() for alias in aliases),
    key=lambda pair: (-len(pair[0]), pair[0]),
)


def detect_genre(game: str) -> Genre | None:
    """Genre eines Spiels oder ``None``, wenn keine Schreibweise passt."""
    words = f" {normalize(game)} "
    for alias, genre in _ALIAS_TABLE:
        if alias and f" {alias} " in words:
            return genre  # type: ignore[return-value]
    return None


def genre_label(genre: str | None, language: str) -> str:
    pair = GENRE_LABELS.get(genre or "", UNKNOWN_LABEL)
    return pair[0] if language == "de" else pair[1]
