# KI-Agenten der Streaming Growth Engine

Python-Backend für die Agenten, die später als Leistungen in der Plattform landen sollen.
Ehrlicher Stand: **Prototypen, offline und regelbasiert.** Es ist noch kein Sprachmodell aktiv,
es gibt keine Verbindung zur Website und keine öffentliche Bereitstellung.

| Agent | Status | Was er heute kann |
| --- | --- | --- |
| Content Strategist | Prototyp | Format-Empfehlungen und Mini-Serien nach Streamer-Profil, Wochenplan nach Zeitbudget. Spielspezifische Beispiele bisher nur für Valorant, Minecraft und Fortnite |
| Growth Analyst | Prototyp | Vergleicht selbst eingegebene Wochenwerte, wählt ein passendes Experiment und wertet es aus, ohne Wachstum zu versprechen |
| Clip Hunter | Prototyp | Findet Audio-Spitzen und Bildwechsel in eigenen Aufnahmen als Prüfkandidaten, kann sie als MP4 ausschneiden und gegen menschliche Markierungen messen. Versteht keine Inhalte |
| Trend Scout | geplant | soll die Scouts aus dem Trend Radar auf Streaming-Kategorien umstellen |
| Setup Advisor | geplant | wird über den Setup Intelligence Agent (`backend/setup_agent`) abgedeckt |

Herkunft: zusammengeführt aus `langemojo-byte/streaming_ai_agents`
(Stand `806476a`, alle Feature-Branches; siehe [Bereinigung](#bereinigung)).

## Lokal starten

Voraussetzung: Python 3.11 oder neuer. Für Videos zusätzlich FFmpeg im `PATH`.

```bash
cd agents
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux:        source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check streaming_agents tests
python -m uvicorn streaming_agents.api:app --reload --host 127.0.0.1 --port 8000
```

Danach im Browser: <http://127.0.0.1:8000/api/v1/docs> (zum Ausprobieren aller Endpunkte).

**Nur lokal betreiben.** Die API hat noch keine Anmeldung und keine Limits.

## Endpunkte

| Methode | Pfad | Agent | Beispiel |
| --- | --- | --- | --- |
| GET | `/health` | – | |
| GET | `/api/v1/agents` | Übersicht mit Status | |
| POST | `/api/v1/content/strategy` | Content Strategist | [`v3_minecraft.json`](examples/v3_minecraft.json) |
| POST | `/api/v1/content/weekly-plan` | Content Strategist | siehe unten |
| POST | `/api/v1/growth/analysis` | Growth Analyst | [`creator_intelligence_v1_request.json`](examples/creator_intelligence_v1_request.json) |
| POST | `/api/v1/growth/strategy` | Growth Analyst | [`creator_intelligence_v2_strategy.json`](examples/creator_intelligence_v2_strategy.json) |
| POST | `/api/v1/growth/review` | Growth Analyst | [`creator_intelligence_v2_review.json`](examples/creator_intelligence_v2_review.json) |
| POST | `/api/v1/clips/scan` | Clip Hunter (Datei-Upload, max. 100 MB / 15 Min.) | |
| POST | `/api/v1/clips/evaluate` | Clip Hunter: Treffer gegen menschliche Markierungen | |
| POST | `/api/v1/clips/review-queue` | Clip Hunter: verblindete Prüfliste | |

Wochenplan-Beispiel:

```json
{
  "platform": "Twitch", "category": "Minecraft", "audience": "Anfänger", "language": "de",
  "weekly_hours": 8, "stream_days": 3, "primary_goal": "community"
}
```

### Clip Hunter auf der Kommandozeile

```bash
python -m streaming_agents.clip_cli --input mein_stream.mp4 --json kandidaten.json --extract-dir clip_exports
```

Nur für eigene Aufnahmen. Die Kandidaten sind Stellen zum Ansehen, keine Bewertung,
ob ein Clip gut ankommt.

### Optional: Sprachmodell (aus, kostet Geld)

`streaming_agents/llm/` enthält eine austauschbare Modell-Schnittstelle mit einem
OpenAI-Adapter. Er wird nur über die Kommandozeile und nur mit `--live` aufgerufen:

```bash
python -m pip install -e ".[llm,dev]"
# OPENAI_API_KEY, SGE_LLM_MODEL und Preisangaben lokal setzen (siehe .env.example)
python -m streaming_agents.llm.cli --live --platform Twitch --category Minecraft --audience Anfänger
```

Ohne `--live` wird keine Anfrage gesendet. Schlüssel niemals committen.
Die automatischen Tests rufen kein echtes Modell auf.

## Bereinigung

Im alten Repository lagen 13 Feature-Branches, die alle aufeinander aufbauten, und
`main` enthielt davon nichts. Übernommen wurde der vollständige Stand, danach:

- **Entfernt (überholt):** V1-Content-Plan mit drei festen Vorlagen, eigener V2-Endpunkt
  des Content Strategist, V1-Upload-Endpunkt des Clip Hunter.
  Die V2-Logik bleibt intern, weil V3 darauf aufbaut. V1-Scan und CLI bleiben.
- **Entfernt (kein Produktnutzen):** Referenz-Benchmark mit Streamer-Liste, Quellen-Audit,
  Open-Media-Rechteprüfung, lokales Video-Pilot-Gate samt Daten und Tests.
  Bei Bedarf sind sie im alten Repository nachlesbar.
- **Vereinheitlicht:** alle Endpunkte unter `/api/v1/<bereich>/...` statt
  `/v1/demo`, `/v2/demo`, `/v3/demo`.
- **Dokumentation:** [Architektur](docs/architecture.md) und
  [Entwicklungsnotizen](docs/entwicklung/README.md) der einzelnen Versionen.
