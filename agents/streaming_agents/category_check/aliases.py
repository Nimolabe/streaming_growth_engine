"""Gängige Schreibweisen → offizieller Twitch-Kategoriename.

Wird VOR Get Games angewendet. Get Games ignoriert zwar die Groß-/Kleinschreibung (echt getestet
am 26.11.2026), findet aber keine Abkürzungen: „CS2“ passt exakt auf „Carrot Slime 2“,
„Counter Strike 2“ auf gar nichts (die Kategorie heißt „Counter-Strike“).

Jeder Zielname wurde am 26.11.2026 per Get Games gegen die echte Twitch-API geprüft
(Name → ID in Klammern). Stand: November 2026.

Abgrenzung zu ``content_strategist/genres.py``: Dort stehen Schreibweisen, um ein Genre zu
erkennen (Treffer als Wort irgendwo im Namen, ~200 Spiele). Hier geht es nur um den exakten
Twitch-Namen für die Messung; ein Alias muss den GANZEN Namen treffen.
"""
import re

# Schlüssel in normalisierter Form (siehe ``normalize``), Ziel exakt wie auf Twitch.
CATEGORY_ALIASES: dict[str, str] = {
    # Counter-Strike (32399): CS2 läuft auf Twitch unter dem alten Namen.
    "cs2": "Counter-Strike", "cs 2": "Counter-Strike", "counter strike 2": "Counter-Strike",
    "counterstrike 2": "Counter-Strike", "counterstrike2": "Counter-Strike",
    "counter strike2": "Counter-Strike", "csgo": "Counter-Strike", "cs go": "Counter-Strike",
    "counter strike global offensive": "Counter-Strike",
    # League of Legends (21779)
    "lol": "League of Legends",
    # Grand Theft Auto V (32982), GTA RP läuft in derselben Kategorie
    "gta": "Grand Theft Auto V", "gta 5": "Grand Theft Auto V", "gta5": "Grand Theft Auto V",
    "gta v": "Grand Theft Auto V", "gtav": "Grand Theft Auto V",
    "gta online": "Grand Theft Auto V", "gta rp": "Grand Theft Auto V",
    "grand theft auto 5": "Grand Theft Auto V",
    # Grand Theft Auto VI (1867279146)
    "gta 6": "Grand Theft Auto VI", "gta6": "Grand Theft Auto VI",
    "gta vi": "Grand Theft Auto VI", "grand theft auto 6": "Grand Theft Auto VI",
    # World of Warcraft (18122)
    "wow": "World of Warcraft",
    # Apex Legends (511224)
    "apex": "Apex Legends",
    # Rainbow Six Siege (460630); „Tom Clancy's Rainbow Six Siege“ findet Get Games selbst,
    # „Rainbow Six Siege X“ dagegen nicht.
    "r6": "Rainbow Six Siege", "r6s": "Rainbow Six Siege", "r6 siege": "Rainbow Six Siege",
    "rainbow six": "Rainbow Six Siege", "rainbow 6": "Rainbow Six Siege",
    "rainbow six siege x": "Rainbow Six Siege", "r6 siege x": "Rainbow Six Siege",
    # EA Sports FC: „EA FC“ ohne Zahl = aktuelle Ausgabe (FC 27 seit September 2026).
    "ea fc": "EA Sports FC 27", "eafc": "EA Sports FC 27",
    "fc 27": "EA Sports FC 27", "fc27": "EA Sports FC 27", "ea fc 27": "EA Sports FC 27",
    "fc 26": "EA Sports FC 26", "fc26": "EA Sports FC 26", "ea fc 26": "EA Sports FC 26",
    "fc 25": "EA Sports FC 25", "fc25": "EA Sports FC 25", "ea fc 25": "EA Sports FC 25",
    # Teamfight Tactics (513143), Dead by Daylight (491487)
    "tft": "Teamfight Tactics",
    "dbd": "Dead by Daylight",
    # Weitere häufige Kurzformen
    "pubg": "PUBG: BATTLEGROUNDS",                  # 493057
    "warzone": "Call of Duty: Warzone",             # 512710
    "tarkov": "Escape from Tarkov", "eft": "Escape from Tarkov",  # 491931
    "dota": "Dota 2",                               # 29595
    "ow": "Overwatch", "ow2": "Overwatch", "ow 2": "Overwatch",   # 515025
    "valo": "VALORANT",                             # 516575
    "poe": "Path of Exile",                         # 29307
    "poe2": "Path of Exile 2", "poe 2": "Path of Exile 2",       # 1702520304
}


def normalize(name: str) -> str:
    """Kleinbuchstaben, Satzzeichen → Leerzeichen, Leerzeichen zusammengefasst."""
    text = re.sub(r"[^\w]+", " ", name.casefold(), flags=re.UNICODE)
    return " ".join(text.replace("_", " ").split())


def alias_target(name: str) -> str | None:
    """Offizieller Twitch-Name, falls ``name`` eine bekannte Schreibweise ist, sonst ``None``."""
    target = CATEGORY_ALIASES.get(normalize(name))
    if target is None or normalize(target) == normalize(name):
        return None
    return target


def alias_label(alias: str, category: str) -> str:
    """„CS2 → Counter-Strike (Alias)“ – sprachneutral, damit sichtbar ist, was gemessen wurde."""
    return f"{alias} → {category} (Alias)"
