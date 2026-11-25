# Architektur der KI-Agenten

## Aufbau

```
agents/
├── streaming_agents/
│   ├── api.py            → FastAPI-App, alle Endpunkte unter /api/v1
│   ├── contracts.py      → gemeinsame Datenmodelle (Agent-Liste, Anfrage für llm/)
│   ├── registry.py       → ehrlicher Status jedes Agenten (geplant / Prototyp / fertig)
│   ├── clip_hunter/      → Clip Hunter v4: Chat-Mitschnitt, Chat- und Audio-Signale,
│   │                       Zusammenführung, Export, Bericht, Twitch-API, Kommandozeile
│   ├── category_check/   → Kategorie-Check: Twitch-Messungen, Auswertung, Kommandozeile
│   ├── content_strategist/ → Wochenplan: Genres, Formate, Planer, Twitch-Grenzen, Bericht, CLI
│   ├── agents/           → die Logik der einzelnen Agenten
│   └── llm/              → austauschbare Sprachmodell-Schnittstelle (standardmäßig aus)
├── tests/                → pytest, läuft ohne Netzwerk
├── examples/             → Beispiel-Anfragen für die API
└── docs/                 → diese Datei und Entwicklungsnotizen
```

## Agenten und Module

| Agent | Module in `streaming_agents/agents/` | Endpunkte |
| --- | --- | --- |
| Content Strategist | `content_strategist/` (Wochenplan) und `category_check/` (Kategorie-Check) | `/content/strategy`, `/content/category-check` |
| Growth Analyst | `creator_intelligence`, `creator_strategy`, `creator_strategy_review` (+ `_contracts`) | `/growth/analysis`, `/growth/strategy`, `/growth/review` |
| Clip Hunter | `clip_hunter/` (v4, Chat + Audio, optionale KI-Stufe) | `/clips/chat-moments` (alles andere über die Kommandozeile) |
| Trend Scout | – (geplant, soll auf den Messungen des Kategorie-Checks aufbauen) | – |
| Setup Advisor | – (heute der Setup-Finder der Website; eigener Agent im PR #5 geparkt) | – |

Der Content Strategist hat eine zentrale Genre-Liste (`content_strategist/genres.py`), einen
Formatkatalog mit explizitem Chat-Bedarf pro Format (`formats.py`) und einen Planer, der die
„beste Zeiten“-Logik des Kategorie-Checks (`category_check.analysis.slot_stats`) wiederverwendet.
Die früheren Module `v3_recommender`, `v3_game_knowledge`, `catalog` und `weekly_planner` sind
darin aufgegangen; die älteren Clip-Werkzeuge und der Empfehler v2 wurden im November 2026
entfernt (siehe [Bestandsaufnahme](bestandsaufnahme-2026-11.md)). Alles ist in der Git-Historie
nachlesbar.

## Grundsätze

- Jeder Agent liefert nachvollziehbare Ergebnisse und behauptet nichts, was er nicht messen kann
  (keine „Viralitäts“-Werte, keine Wachstumsversprechen).
- Keine Daten von Streamern ohne deren Zustimmung; keine fremden Videos herunterladen.
- Die Sprachmodell-Anbindung (`llm/`) ist austauschbar und standardmäßig aus.
  Kostenpflichtige Aufrufe nur mit ausdrücklichem `--live` und eigenem Schlüssel.
- Keine API-Schlüssel im Frontend oder in GitHub Pages. Die Website spricht später
  nur über HTTPS mit einem angemeldeten Backend.

## Weg in die Plattform

1. **Jetzt:** lokale API und Tests, keine Verbindung zur Website.
2. **Beta:** Backend separat hosten, Firebase-ID-Token prüfen, Limits pro Nutzer,
   „Labs“-Bereich auf der Website für eingeladene Tester.
3. **Mit Kosten:** Sprachmodell-Anbieter per Konfiguration zuschalten,
   Clip-Analyse als Hintergrund-Job, Kosten pro Analyse protokollieren.
