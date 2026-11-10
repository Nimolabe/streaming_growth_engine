# Setup Intelligence Agent (Backend)

Regelbasierter Agent, der Streamer-Setups mit Quellen verwaltet. **Keine kostenpflichtigen KI-APIs.**
Architektur, Datenmodell, Regeln und Betrieb: [`docs/setup-agent/`](../docs/setup-agent/ARCHITEKTUR.md)

## Module

| Modul | Komponente | Inhalt |
| --- | --- | --- |
| `models.py` | – | Datenmodelle A–F mit Validierung |
| `identity.py` | – | deterministische IDs, Normalisierung, GTIN-Prüfung |
| `verification.py` | Setup Verifier, Confidence Evaluator | Statusregeln, Vertrauenswert, Widersprüche pro Slot |
| `approval.py` | Approval Manager, Audit Logger | Vorschlag → Admin-Entscheidung → Anwendung mit Prüfungen |
| `resolver.py` | Product Resolver | eindeutige Zuordnung, Erwähnungen in Texten |
| `registry.py` | Source Registry | zugelassene Quellen, automatischer Abruf, Intervalle |
| `detector.py` | Change Detector | Statusänderungen als Vorschläge, ohne Duplikate |
| `fetcher.py`, `monitors.py` | Source Monitor, Price Monitor | Abruf mit robots.txt, Preis-Feeds |
| `jobs.py`, `cli.py` | Update Scheduler | Jobs `apply`, `weekly`, `prices`, `export` |
| `pricing.py` | – | Preiszustand, Preisänderungen |
| `public_views.py`, `exporter.py` | – | öffentliche Sicht, statische JSON-API |
| `api_core.py`, `api.py` | – | REST-API v1 (Logik / FastAPI) |
| `repository.py`, `firestore_repo.py` | – | Speicher-Schnittstelle, In-Memory, Firestore |
| `demo.py` | – | erfundene Beispieldaten (nur lokal) |

## Testen

```bash
cd backend
python3 -m pip install -e ".[dev]"
python3 -m pytest
```

Alle Tests nutzen synthetische Daten (erfundene Streamer, Domains unter `.example`) und rufen keine externen
Dienste auf. Firestore wird mit einem nachgebauten Client getestet (`tests/fake_firestore.py`), über dieselben
Vertragstests wie der In-Memory-Speicher.

| Getestet | Wie |
| --- | --- |
| Falsche/ähnliche Produktnamen, Duplikate | `test_identity`, `test_services::TestResolver`, Vertragstests |
| Fehlende, doppelte, widersprüchliche, veraltete Quellen | `test_models`, `test_verification`, `test_services::TestChangeDetector` |
| Preisänderungen, nicht verfügbare Händlerdaten | `test_pricing_repository`, `test_monitors_jobs::TestPriceMonitor` |
| Ungültige Eingaben, fehlerhafte API-Antworten, Zugriffskontrolle, unberechtigte Änderungen | `test_api` |
| Fehlerhafte Datenbankoperationen, Ausfälle | Vertragstests, `test_services` |
| Wiederholte Läufe ohne Duplikate | `test_services`, `test_monitors_jobs` |
| FastAPI-Verdrahtung | `test_api_fastapi` (nur wenn FastAPI installiert ist, z. B. in der CI) |

Nicht automatisiert getestet: echte Firestore-Verbindung, `firestore.rules` (kein Emulator), GitHub-Actions-Jobs.
