"""Curated evergreen game situations, separated from the ranking algorithm.

These are editorial examples, not claims of current balance, meta or ranked success.
No scraped or live information is used.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Situation:
    title_de: str
    title_en: str
    setup_de: str
    setup_en: str
    hook_de: str
    hook_en: str


# Specific concepts tied to existing format IDs and common game mechanics.
SITUATIONS: dict[str, dict[str, Situation]] = {
    "valorant": {
        "decision-review": Situation(
            "Retake oder Save? Eine Valorant-Runde auseinandernehmen",
            "Retake or save? Break down a Valorant round",
            "Wähle einen eigenen Clip mit einer echten Retake-oder-Save-Entscheidung. Zeige Ressourcen, verbleibende Zeit und Teampositionen, bevor du das Ergebnis auflöst.",
            "Choose your own clip showing a genuine retake-or-save decision. Show resources, remaining time and team positions before the reveal.",
            "Retake oder Save: Was wäre in dieser Runde die bessere Entscheidung?",
            "Retake or save: which decision fits this round?",
        ),
        "coach-my-round": Situation(
            "Ein freiwilliger Coach überprüft meine Utility-Nutzung",
            "A volunteer coach reviews my utility decisions",
            "Fokussiere die Tipps auf ein klares Ziel: Wann nutze ich meine Fähigkeiten für den Site-Einstieg? Bitte nur mit einem freiwilligen, respektvollen Coach.",
            "Focus on one issue: when to use abilities to help enter a site. Use only a willing, respectful coach.",
            "Ich lasse meine Utility-Entscheidungen in einer Runde coachen.",
            "I let a coach guide my utility choices for one round.",
        ),
        "role-swap": Situation(
            "Von Duelist zu Sentinel: Was ändert sich in meinen Entscheidungen?",
            "Duelist to Sentinel: what changes in my decisions?",
            "Vergleiche den Spielstil eines Duelists mit der defensiven Rolle eines Sentinels. Konzentriere dich auf Positionierung statt auf Kills.",
            "Compare a Duelist's role with the defensive duties of a Sentinel. Focus on positioning rather than eliminations.",
            "Ich tausche meine gewohnte Valorant-Rolle: Was vergesse ich zuerst?",
            "I switch my usual Valorant role: what do I forget first?",
        ),
        "micro-skill": Situation(
            "Ein Valorant-Fehler: Crosshair-Placement an einer Ecke",
            "One Valorant mistake: crosshair placement at a corner",
            "Zeige dieselbe Ecke in zwei eigenen Szenen: einmal mit unpassender Fadenkreuzposition und einmal mit bewusster Vorbereitung.",
            "Show the same corner in two of your own clips: one poor crosshair position and one deliberately prepared angle.",
            "Zwei Szenen, dieselbe Ecke – warum war mein Crosshair falsch?",
            "Two clips, the same corner — what was wrong with my crosshair?",
        ),
        "round-prediction": Situation(
            "Valorant: Was passiert nach dieser Economy-Entscheidung?",
            "Valorant: what follows this economy choice?",
            "Stelle eine klare Vorhersage zu einer Spar- oder Kaufentscheidung und prüfe sie an einer selbst gespielten Runde.",
            "Predict the effect of a save-or-buy decision, then review your own round.",
            "Unser Team kauft oder spart – wie endet die Runde?",
            "Our team buys or saves — how does the round go?",
        ),
        "team-communication": Situation(
            "Team-Calls: eine Info statt fünf hektischer Ansagen",
            "Team calls: one useful update instead of five",
            "Vergleiche selbst aufgezeichnete Szenen mit langen und kurzen Callouts. Bitte Mitspieler vor der Veröffentlichung um Erlaubnis.",
            "Compare your own recorded clips with lengthy and concise callouts. Get teammate permission before publishing their voices.",
            "Wie verändert ein kurzer Callout diese Runde?",
            "What changes when we use one short callout?",
        ),
    },
    "minecraft": {
        "build-mistake-fix": Situation(
            "Minecraft: Warum funktioniert mein Redstone-Aufbau nicht?",
            "Minecraft: why isn't my redstone build working?",
            "Nimm einen eigenen fehlerhaften Redstone-Aufbau. Zeige zuerst das Problem, dann die Ursache und eine nachvollziehbare Korrektur.",
            "Record your own broken redstone build. Show the issue, cause, and a reproducible fix.",
            "Mein Redstone-Aufbau macht nicht, was er soll – hier ist der Fehler.",
            "My redstone build is broken — here's the reason.",
        ),
        "before-after-world": Situation(
            "Minecraft: vom leeren Gelände zu einem funktionalen Dorfplatz",
            "Minecraft: from empty terrain to a village square",
            "Definiere drei kleine Bauetappen und filme sie aus demselben Blickwinkel, um den Fortschritt sichtbar zu machen.",
            "Plan three compact building stages and record each from the same camera angle to show progress.",
            "Wie verwandelt sich dieses leere Minecraft-Gelände?",
            "How will this empty Minecraft space transform?",
        ),
        "one-mechanic-build": Situation(
            "Minecraft: drei Lösungen für dieselbe Redstone-Aufgabe",
            "Minecraft: three designs for one redstone goal",
            "Verwende eine selbst gewählte einfache Redstone-Funktion und vergleiche drei Umsetzungen nach Aufwand und Verständlichkeit.",
            "Choose a simple redstone function and compare three designs for simplicity and practical effort.",
            "Drei Wege zur selben Redstone-Funktion – welcher ist am einfachsten?",
            "Three ways to achieve one redstone goal — which is easiest?",
        ),
        "skill-diary": Situation(
            "Minecraft: Bautechnik über drei Sessions verbessern",
            "Minecraft: improve one building skill over three sessions",
            "Wähle eine Bautechnik, etwa Dachgestaltung, und dokumentiere deinen Fortschritt bei vergleichbaren Ausgangspunkten.",
            "Choose a building skill, such as roofs, and document progress on comparable examples.",
            "Mein erstes und drittes Minecraft-Dach: Was hat sich geändert?",
            "My first and third Minecraft roof: what changed?",
        ),
    },
    "fortnite": {
        "decision-under-pressure": Situation(
            "Fortnite: bessere Rotation oder unnötiges Risiko?",
            "Fortnite: sensible rotation or unnecessary risk?",
            "Vergleiche zwei eigene Rotationsentscheidungen hinsichtlich Position, verfügbarer Ressourcen und möglicher Deckung.",
            "Compare two of your own rotation choices based on positioning, available resources and cover.",
            "An dieser Stelle muss ich rotieren: welcher Weg ist sinnvoll?",
            "I need to rotate here — which path makes sense?",
        ),
        "drop-location-study": Situation(
            "Fortnite: drei Landeorte nach Risiko vergleichen",
            "Fortnite: compare three drop spots by risk",
            "Vergleiche drei selbst gewählte Landeorte nach Ressourcen, Konkurrenz und Weg in die nächste Zone; keine Meta-Behauptungen.",
            "Compare three drop spots by resources, competition and your route to the next zone; do not claim a universal best spot.",
            "Welcher dieser Landeorte passt zu meinem Spielstil?",
            "Which drop spot fits my playstyle?",
        ),
        "loadout-lab": Situation(
            "Fortnite: zwei verfügbare Ausrüstungen fair vergleichen",
            "Fortnite: compare two available loadouts fairly",
            "Wähle zwei in deiner aktuellen Spielversion verfügbare Ausrüstungsvarianten und teste sie unter möglichst gleichen Bedingungen.",
            "Choose two loadouts available in your game version and test them under comparable conditions.",
            "Welche Ausrüstung hat mir in ähnlichen Situationen mehr geholfen?",
            "Which loadout helped me more in similar situations?",
        ),
    },
}


def game_key(name: str) -> str | None:
    lower = name.casefold()
    if "valorant" in lower:
        return "valorant"
    if "minecraft" in lower:
        return "minecraft"
    if "fortnite" in lower:
        return "fortnite"
    return None
