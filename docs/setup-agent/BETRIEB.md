# Setup Intelligence Agent – Inbetriebnahme und Betrieb

Stand: 10.11.2026. Alles läuft im kostenlosen Firebase-Spark-Tarif und mit kostenlosen
GitHub-Actions-Läufen (öffentliches Repository). Keine Kreditkarte, keine KI-API.

## Einmalig einrichten

1. **Firestore anlegen**: Firebase-Konsole → Projekt `streaminggrowthengine` → Firestore Database →
   Datenbank erstellen (Produktionsmodus, Standort z. B. `eur3` oder `europe-west3`).
2. **Sicherheitsregeln**: Inhalt von [`firestore.rules`](../../firestore.rules) unter
   Firestore → Regeln einfügen und veröffentlichen.
3. **Service-Konto**: Projekteinstellungen → Dienstkonten → „Neuen privaten Schlüssel generieren".
   Die JSON-Datei **nie committen**. Inhalt als Repository-Secret `FIREBASE_SERVICE_ACCOUNT` speichern
   (GitHub → Settings → Secrets and variables → Actions).
4. **Admin-Recht vergeben** (auf dem eigenen Rechner, einmal pro Admin):
   ```bash
   cd backend
   pip install -e ".[firestore]"
   export FIREBASE_SERVICE_ACCOUNT="$(cat /pfad/zum/schluessel.json)"
   python -m setup_agent set-admin --email admin@beispiel.de
   ```
   Das Konto muss sich vorher einmal auf der Website registriert haben. Danach ab- und wieder anmelden.
5. **Admin-Seite** öffnen: `admin.html` (nicht im Menü verlinkt, für Suchmaschinen gesperrt).
6. **Workflows** laufen nach dem Merge automatisch. Ersten Lauf manuell starten:
   GitHub → Actions → „Setup-Agent Jobs" → Run workflow → `apply`.

## Täglicher Ablauf

| Wer | Was | Wo |
| --- | --- | --- |
| Admin | Streamer, Produkte, Setup-Angaben mit Quellen, Angebote, Preise anlegen | Admin-Seite → Neu anlegen |
| Agent (stündlich) | Freigegebene Vorschläge prüfen und übernehmen, JSON-Export aktualisieren | GitHub Actions |
| Agent (montags) | Freigegebene Quellen abrufen, Änderungen als Vorschläge einreichen; Regeln neu bewerten (z. B. Beleg wird älter als 12 Monate) | GitHub Actions |
| Agent (täglich) | Preise aus zulässigen Preis-Feeds aktualisieren (falls konfiguriert) | GitHub Actions |
| Admin | Vorschläge des Agenten prüfen: freigeben oder mit Begründung ablehnen | Admin-Seite → Vorschläge |

Die Admin-Seite zeigt eine Warnung, wenn Läufe ausbleiben (stündlich > 3 h, wöchentlich > 14 Tage).

## Quellen automatisch prüfen lassen

Standard ist „nur manuell". Für den automatischen Abruf einer Domain:

1. Nutzungsbedingungen und `robots.txt` der Seite lesen. Nur wenn der Abruf erlaubt ist, weiter.
2. Admin-Seite → Neu anlegen → **Zugelassene Domain**: Zugriffsart „Seitenabruf erlaubt",
   Haken bei „Automatischer Abruf erlaubt", Link zu den Bedingungen, Mindestabstand (Standard 168 h).
3. Admin-Seite → **Quelle**: URL der Setup-Seite, Typ, zugehöriger Streamer.

Der Agent speichert vom Inhalt nur einen Hash (zur Änderungserkennung), keine Texte.
Er schlägt Produkte nur vor, wenn Hersteller und Modell wörtlich auf der Seite stehen.

## Preise

- Standard: manuell über die Admin-Seite („Preis ändern"). Ab 14 Tagen ohne Prüfung gilt ein Preis als veraltet.
- Automatisch nur über einen **zulässigen JSON-Feed** (z. B. Produkt-Feed eines Partnerprogramms, dessen
  Bedingungen das erlauben). Konfiguration als Repository-Variable `PRICE_FEEDS`:
  `[{"name": "partner-a", "url": "https://…/feed.json"}]`. Angebote mit `price_source = "partner-a"` werden
  dann täglich aktualisiert. Format siehe `JsonFeedPriceSource` in `backend/setup_agent/monitors.py`.

## Daten für Website und App

Der Export liegt im Branch **`data`** (nicht `main`), z. B.:

- `https://raw.githubusercontent.com/Nimolabe/streaming_growth_engine/data/v1/streamers.json`
- `…/data/v1/streamers/<id>/setup.json`, `…/data/v1/products.json`, `…/data/v1/meta.json`

Struktur wie die REST-API ([API.md](API.md)). Die Anbindung der Setups-Seite an diese Daten folgt,
sobald PR #4 (neue Bauteil-Kategorien) zusammengeführt ist, um Konflikte in `setups.js` zu vermeiden.

## Lokal ausprobieren (ohne Datenbank)

```bash
cd backend
pip install -e ".[dev]"
python -m pytest                                   # alle Tests
python -m setup_agent demo --out ../vorschau      # Beispieldaten (erfunden) als JSON exportieren
SETUP_AGENT_DEMO=1 uvicorn --factory setup_agent.api:app_from_env   # REST-API, Doku unter /api/v1/docs
```

## Wenn etwas schiefgeht

| Symptom | Ursache / Lösung |
| --- | --- |
| Freigabe wird nicht übernommen, „Nicht übernommen: …" | Der Agent hat die Daten geprüft und abgelehnt (z. B. Duplikat, Datensatz zwischenzeitlich geändert). Hinweis lesen, neuen Vorschlag anlegen. |
| Lauf meldet `storage_unavailable` | Firestore nicht erreichbar oder Tageskontingent erschöpft. Nichts wurde geändert; der nächste Lauf versucht es erneut. |
| Lauf übersprungen („FIREBASE_SERVICE_ACCOUNT fehlt") | Secret fehlt oder heißt anders. |
| Geplante Läufe stehen still | GitHub deaktiviert sie nach 60 Tagen ohne Repository-Aktivität. Unter Actions wieder aktivieren. |
| Schlüssel ist öffentlich geworden | Sofort in der Firebase-Konsole löschen, neuen erzeugen, Secret ersetzen. |
