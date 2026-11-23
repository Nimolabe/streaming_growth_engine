# Architektur der KI-Agenten

## Aufbau

```
agents/
├── streaming_agents/
│   ├── api.py            → FastAPI-App, alle Endpunkte unter /api/v1
│   ├── contracts.py      → gemeinsame Datenmodelle (Agent-Liste, Wochenplan)
│   ├── registry.py       → ehrlicher Status jedes Agenten (geplant / Prototyp / fertig)
│   ├── clip_hunter/      → Clip Hunter v4: Chat-Mitschnitt, Chat- und Audio-Signale,
│   │                       Zusammenführung, Export, Bericht, Twitch-API, Kommandozeile
│   ├── category_check/   → Kategorie-Check: Twitch-Messungen, Auswertung, Kommandozeile
│   ├── agents/           → die Logik der einzelnen Agenten
│   └── llm/              → austauschbare Sprachmodell-Schnittstelle (standardmäßig aus)
├── tests/                → pytest, läuft ohne Netzwerk
├── examples/             → Beispiel-Anfragen für die API
└── docs/                 → diese Datei und Entwicklungsnotizen
```

## Agenten und Module

| Agent | Module in `streaming_agents/agents/` | Endpunkte |
| --- | --- | --- |
| Content Strategist | `v3_recommender`, `v3_contracts`, `v3_game_knowledge`, `catalog`, `weekly_planner`; Kategorie-Check in `category_check/` | `/content/strategy`, `/content/weekly-plan`, `/content/category-check` |
| Growth Analyst | `creator_intelligence`, `creator_strategy`, `creator_strategy_review` (+ `_contracts`) | `/growth/analysis`, `/growth/strategy`, `/growth/review` |
| Clip Hunter | `clip_hunter/` (v4, Chat + Audio, optionale KI-Stufe) | `/clips/chat-moments` (alles andere über die Kommandozeile) |
| Trend Scout | – (geplant, soll auf den Messungen des Kategorie-Checks aufbauen) | – |
| Setup Advisor | – (heute der Setup-Finder der Website; eigener Agent im PR #5 geparkt) | – |

`catalog` enthält die 26 kuratierten Formate, `v3_recommender` die Spiel-Einordnung
(`classify_game`) und die Auswahl. Die älteren Clip-Werkzeuge und der Empfehler v2 wurden
im November 2026 entfernt (siehe [Bestandsaufnahme](bestandsaufnahme-2026-11.md));
sie sind in der Git-Historie nachlesbar.

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
