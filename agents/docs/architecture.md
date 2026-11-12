# Architektur der KI-Agenten

## Aufbau

```
agents/
├── streaming_agents/
│   ├── api.py            → FastAPI-App, alle Endpunkte unter /api/v1
│   ├── contracts.py      → gemeinsame Datenmodelle (Agent-Liste, Wochenplan)
│   ├── registry.py       → ehrlicher Status jedes Agenten (geplant / Prototyp / fertig)
│   ├── clip_cli.py       → Kommandozeile für den Clip Hunter
│   ├── agents/           → die Logik der einzelnen Agenten
│   └── llm/              → austauschbare Sprachmodell-Schnittstelle (standardmäßig aus)
├── tests/                → pytest, läuft ohne Netzwerk
├── examples/             → Beispiel-Anfragen für die API
└── docs/                 → diese Datei und Entwicklungsnotizen
```

## Agenten und Module

| Agent | Module in `streaming_agents/agents/` | Endpunkte |
| --- | --- | --- |
| Content Strategist | `v3_recommender`, `v3_contracts`, `v3_game_knowledge`, `v2_catalog`, `v2_recommender`, `v2_contracts`, `weekly_planner` | `/content/strategy`, `/content/weekly-plan` |
| Growth Analyst | `creator_intelligence`, `creator_strategy`, `creator_strategy_review` (+ `_contracts`) | `/growth/analysis`, `/growth/strategy`, `/growth/review` |
| Clip Hunter | `clip_intelligence`, `clip_intelligence_v2`, `clip_export`, `clip_evaluation`, `clip_review_queue_v3` (+ `_contracts`) | `/clips/scan`, `/clips/evaluate`, `/clips/review-queue` |
| Trend Scout | – (geplant, soll die Scouts aus dem Trend Radar wiederverwenden) | – |
| Setup Advisor | – (wird vom Setup Intelligence Agent in `backend/setup_agent` abgedeckt) | – |

`v2_*` sind keine eigenen Endpunkte mehr, sondern die Grundlage (Format-Katalog,
Spiel-Einordnung), auf der `v3_recommender` aufbaut.

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
