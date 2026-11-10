# Setup Intelligence Agent – Schnittstellen (Entwurf v1)

Stand: 10.11.2026 · Umsetzung: `backend/setup_agent/api_core.py` (Logik) und `api.py` (FastAPI, Doku unter `/api/v1/docs`)

Alle Endpunkte liegen unter `/api/v1`. Antworten sind JSON, Zeitstempel ISO 8601 in UTC,
Geldbeträge als `{"amount_minor": 39900, "currency": "EUR"}`. Unbekannte Werte sind `null`.
Die öffentlichen Endpunkte gibt es zusätzlich als statische Dateien im Branch `data` unter `v1/…`
mit gleicher Struktur (siehe ARCHITEKTUR.md, 3.3): `/api/v1/streamers/{id}/setup` → `v1/streamers/{id}/setup.json`.
Dort sind Listen ungeteilt (ohne Seiten) und ohne `generated_at`/`last_runs`, damit sich Dateien nur bei echten Datenänderungen ändern.

Breaking Changes erhöhen die Hauptversion (`/api/v2`); `v1` bleibt dann mindestens 6 Monate erhalten.

## Öffentlich (nur lesen, nur freigegebene Daten)

| Methode | Pfad | Zweck | Filter |
| --- | --- | --- | --- |
| GET | `/streamers` | Streamer auflisten | `category`, `platform`, `language`, `q`, `page`, `page_size` (max. 100) |
| GET | `/streamers/{id}` | Streamer-Details | |
| GET | `/streamers/{id}/setup` | Setup eines Streamers: veröffentlichte Angaben mit Status, Quellen, Prüfdatum | `category` |
| GET | `/products` | Hardware nach Kategorie und Preisbereich | `category`, `min_price`, `max_price` (Cent), `currency`, `q` |
| GET | `/products/{id}` | Produktdetails inkl. Specs | |
| GET | `/products/{id}/offers` | Händler und Preise mit Preiszustand (`current`, `stale`, `unknown`) | |
| GET | `/products/{id}/alternatives` | Preisalternativen derselben Kategorie | `max_price`, `limit` |
| GET | `/meta` | Datenstand: Zeitpunkt des Exports, letzter Agent-Lauf | |

Beispiel `GET /api/v1/streamers/twitch-beispielkanal/setup`:

```json
{
  "streamer_id": "twitch-beispielkanal",
  "generated_at": "2026-11-10T12:00:00Z",
  "items": [
    {
      "claim_id": "c_5f2a…",
      "category": "mikrofon",
      "role": "primary",
      "product": { "id": "shure-sm7b", "manufacturer": "Shure", "model": "SM7B" },
      "status": "confirmed",
      "confidence_level": "high",
      "last_verified_at": "2026-11-02T09:00:00Z",
      "sources": [
        { "url": "https://…", "source_type": "own_setup_page", "observed_at": "2026-10-28T00:00:00Z" }
      ]
    }
  ]
}
```

## Admin (Firebase-ID-Token mit Custom Claim `admin: true`)

Header: `Authorization: Bearer <Firebase ID Token>`. Ohne gültiges Token `401`, ohne Admin-Recht `403`.
Jede Admin-Änderung wird als Vorschlag gespeichert, sofort vom Admin freigegeben, vom Agenten geprüft
und ins Änderungsprotokoll geschrieben. Antwort: `{"proposal_id": "…", "applied_at": "…"}`.

`{kind}` ∈ `streamers`, `products`, `claims`, `offers`, `sources`, `source-registry`.

| Methode | Pfad | Zweck | Body |
| --- | --- | --- | --- |
| POST | `/admin/{kind}` | anlegen | Felder laut DATENMODELL.md, optional `reason` |
| PATCH | `/admin/{kind}/{id}` | korrigieren | `{"changes": {…}, "expected_version": 3, "reason": "…"}` |
| POST | `/admin/{kind}/{id}/retire` | zurückziehen (Angabe nicht mehr öffentlich, Produkt eingestellt …) | `{"expected_version": 3, "reason": "…"}` |
| PUT | `/admin/offers/{id}/price` | Preis manuell setzen | `{"price": {"amount_minor": 39900, "currency": "EUR"}` oder `null`, `"availability": "in_stock", "reason": "…"}` |
| GET | `/admin/proposals` | Vorschläge, Filter `status` (Standard `pending`), `entity_type` | |
| POST | `/admin/proposals/{id}/approve` | freigeben | optional `{"note": "…"}` |
| POST | `/admin/proposals/{id}/reject` | ablehnen | `{"note": "…"}` (Pflicht) |
| GET | `/admin/sources` | Quellen und Source Registry | |
| GET | `/admin/audit` | Änderungsprotokoll, Filter `entity_type`, `entity_id`, `since` | |

Die Admin-Seite (`admin.html`) braucht diese API nicht: Sie arbeitet direkt mit Firestore und den
Sicherheitsregeln (`firestore.rules`), mit demselben Ablauf.

## Fehlerformat

```json
{ "error": { "code": "version_conflict", "message": "Datensatz wurde zwischenzeitlich geändert.", "details": {} } }
```

| HTTP | `code` | Wann |
| --- | --- | --- |
| 400 | `invalid_input` | Validierung fehlgeschlagen (z. B. fehlende Quelle, Zeitpunkt in der Zukunft, Verweis auf unbekanntes Produkt) |
| 401 | `unauthenticated` | kein oder ungültiges Token |
| 403 | `forbidden` | kein Admin |
| 404 | `not_found` | ID unbekannt |
| 409 | `version_conflict` / `duplicate` / `apply_failed` | `expected_version` passt nicht / existiert schon / Agent hat die Übernahme abgelehnt (Grund in `message`) |
| 422 | `invalid_transition` | z. B. bereits entschiedenen Vorschlag erneut entscheiden |
| 503 | `storage_unavailable` | Datenbank nicht erreichbar; nichts wurde geändert |
