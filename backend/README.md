# Setup Intelligence Agent (Backend)

Regelbasierter Agent, der Streamer-Setups mit Quellen verwaltet. **Keine kostenpflichtigen KI-APIs.**
Architektur, Datenmodell und Regeln: [`docs/setup-agent/`](../docs/setup-agent/ARCHITEKTUR.md)

## Stand (Phase 1)

| Modul | Inhalt | Status |
| --- | --- | --- |
| `setup_agent/models.py` | Datenmodelle A–F mit Validierung, Freigabe-Übergänge | umgesetzt, getestet |
| `setup_agent/identity.py` | Deterministische IDs, URL- und Namensnormalisierung, GTIN-Prüfung | umgesetzt, getestet |
| `setup_agent/verification.py` | Confidence Evaluator, Statusregeln, Widerspruchs- und Ablöseerkennung pro Slot | umgesetzt, getestet |
| `setup_agent/pricing.py` | Preiszustand, Preisänderung, Fehlversuche | umgesetzt, getestet |
| `setup_agent/repository.py` | Speicher-Schnittstelle + In-Memory-Umsetzung | umgesetzt, getestet |
| Firestore-Adapter, FastAPI, Export | | geplant (Phase 2) |

## Lokal testen

```bash
cd backend
python3 -m pip install -e ".[dev]"   # oder: pip install pydantic pytest
python3 -m pytest
```

Die Tests nutzen nur synthetische Daten (erfundene Streamer, Domains unter `.example`) und rufen
keine externen Dienste auf.
