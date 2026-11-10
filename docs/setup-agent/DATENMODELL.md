# Setup Intelligence Agent – Datenmodell

Stand: 10.11.2026 · Umsetzung: `backend/setup_agent/models.py` (Pydantic v2)

Die sechs Bereiche aus dem Auftrag sind getrennte Datensätze. Verbunden werden sie nur über IDs.

```
Streamer ──< SetupClaim >── Product ──< Offer ──< PriceObservation
                │                │
                └── Evidence ──> Source ──> SourceRegistryEntry
ChangeProposal (F) ──> beliebige Entität          AuditEntry (E) ──> beliebige Entität
```

## Allgemeine Regeln

- **Unbekannt** ist immer explizit: optionale Felder sind `null` (Anzeige „unbekannt"),
  Aufzählungen haben den Wert `unknown`. Nichts wird mit Schätzwerten aufgefüllt.
- **Zeitstempel** sind immer mit Zeitzone (UTC gespeichert). Zeitpunkte in der Zukunft werden abgelehnt.
- **IDs sind deterministisch** (aus fachlichen Schlüsseln abgeleitet), damit wiederholte Läufe
  keine Duplikate erzeugen.
- **Geld** wird als ganze Zahl in Cent (`amount_minor`) plus ISO-4217-Währung (`EUR`) gespeichert,
  nie als Kommazahl.
- **Versionierung:** Jede veränderbare Entität hat `version`. Schreibvorgänge geben die erwartete
  Version mit (optimistisches Sperren), damit nichts unbemerkt überschrieben wird.

---

## A. Streamer und Setup

### Streamer (`streamers/{id}`)

| Feld | Typ | Pflicht | Hinweis |
| --- | --- | --- | --- |
| `id` | string | ja | `<plattform>-<handle>` des Hauptkanals, z. B. `twitch-beispielkanal` |
| `display_name` | string | ja | 1–60 Zeichen |
| `platforms` | Liste `PlatformAccount` | ja, ≥ 1 | `platform` (twitch, tiktok, youtube, kick, other), `handle`, `url` |
| `primary_language` | string \| null | nein | ISO 639-1, z. B. `de` |
| `categories` | Liste | ja, ≥ 1 | gaming, chatting, irl, music, creative (wie auf der Website) |
| `profile_links` | Liste URL | nein | weitere offizielle Profile |
| `version`, `created_at`, `updated_at` | | ja | |

### SetupClaim (`setup_claims/{id}`) – „Streamer X nutzt Produkt Y"

| Feld | Typ | Pflicht | Hinweis |
| --- | --- | --- | --- |
| `id` | string | ja | Hash aus `streamer_id`, `slot`, Produkt (oder normalisiertem Rohnamen) |
| `streamer_id` | string | ja | |
| `category` | ProductCategory | ja | siehe Produktkategorien |
| `role` | string | ja | `primary` (Standard), `secondary`, `irl`, … – mehrere Mikros = verschiedene Rollen |
| `slot` | string | abgeleitet | `<category>:<role>`; Widersprüche werden pro Slot erkannt |
| `product_id` | string \| null | nein | `null` = Produkt nicht eindeutig erkannt → Status `unknown` |
| `raw_name` | string | ja | Bezeichnung wie in der Quelle (für die manuelle Prüfung) |
| `evidence` | Liste `Evidence` | **ja, ≥ 1** | ohne Beleg wird die Angabe abgelehnt |
| `status` | VerificationStatus | ja | confirmed, probable, outdated, conflicting, unknown |
| `confidence` | 0.0–1.0 | ja | vom Confidence Evaluator berechnet |
| `confidence_level` | high, medium, low, none | ja | |
| `reason` | string | ja | nachvollziehbare Begründung des Status |
| `last_verified_at` | Zeitstempel | ja | letzte Prüfung (auch wenn nichts geändert wurde) |
| `published` | bool | ja | nur durch Freigabe auf `true` |
| `version`, `created_at`, `updated_at` | | ja | |

## B. Produktkatalog

### Product (`products/{id}`)

| Feld | Typ | Pflicht | Hinweis |
| --- | --- | --- | --- |
| `id` | string | ja | Slug aus Hersteller und Modell, z. B. `shure-sm7b` |
| `manufacturer` | string | ja | |
| `model` | string | ja | exakte Modellbezeichnung |
| `category` | ProductCategory | ja | |
| `variant` | string \| null | nein | z. B. Farbe, Version |
| `aliases` | Liste string | nein | andere Schreibweisen für den Product Resolver |
| `match_key` | string | abgeleitet | normalisiert (klein, ohne Leer- und Bindestriche): `shure:sm7b`; zwei Produkte mit gleichem Schlüssel sind Duplikate |
| `gtin` | string \| null | nein | EAN/GTIN mit Prüfziffer-Validierung |
| `specs` | Map | nein | technische Eigenschaften, z. B. `{"anschluss": "XLR"}` |
| `discontinued` | bool \| null | nein | `null` = unbekannt |

**ProductCategory:** `mikrofon`, `mikrofonarm`, `audio_interface` (Interface/Mixer), `kamera`,
`objektiv`, `licht`, `headset`, `maus`, `tastatur`, `bildschirm`, `cpu`, `gpu`, `ram`,
`mainboard`, `pc` (Komplett-PC oder Konsole), `capture`, `streamdeck`, `greenscreen`, `stuhl`,
`schreibtisch`, `zubehoer`, `software_streaming`, `software_audio`, `software_plugin`, `sonstiges`.
Sie umfasst die Bauteil-Typen der Website (PR #4) plus die Einzelkomponenten aus dem Auftrag.

## C. Preis- und Händlerdaten

### Offer (`offers/{id}`) – „Produkt Y gibt es bei Händler Z"

| Feld | Typ | Pflicht | Hinweis |
| --- | --- | --- | --- |
| `id` | string | ja | Hash aus `product_id`, Händler, normalisierter URL |
| `product_id` | string | ja | |
| `retailer` | string | ja | |
| `url` | URL | ja | nur `https` |
| `price` | Money \| null | nein | `null` = Preis unbekannt |
| `availability` | in_stock, out_of_stock, discontinued, unknown | ja | |
| `checked_at` | Zeitstempel \| null | nein | letzter Prüfversuch |
| `last_success_at` | Zeitstempel \| null | nein | letzter erfolgreicher Abruf; Preis stammt von hier |
| `failed_checks` | int | ja | aufeinanderfolgende Fehlversuche |
| `price_source` | manual \| Adaptername | ja | |

### PriceObservation (`offers/{id}/observations/{id}`) – Preisverlauf, nur anfügen

`offer_id`, `price`, `availability`, `observed_at`, `price_source`.

Ein Preis gilt nach **14 Tagen ohne erfolgreiche Prüfung** als veraltet. Schlägt ein Abruf fehl,
bleiben Preis und `last_success_at` erhalten; nur `checked_at` und `failed_checks` ändern sich.

## D. Quellen und Verifizierung

### Evidence (eingebettet in `SetupClaim.evidence`)

| Feld | Typ | Pflicht | Hinweis |
| --- | --- | --- | --- |
| `source_id` | string | ja | Hash der normalisierten URL |
| `source_url` | URL | ja | nur `http`/`https` |
| `source_type` | SourceType | ja | siehe unten |
| `observed_at` | Zeitstempel | ja | Datum der Aussage/des Inhalts (nicht des Abrufs) |
| `retrieved_at` | Zeitstempel | ja | wann wir die Quelle geprüft haben; nicht vor `observed_at` |
| `media_timestamp` | string \| null | nein | z. B. `00:12:34` in einem Video |
| `note` | string \| null | nein | eigene Kurzzusammenfassung, max. 280 Zeichen, **kein kopierter Text** |

**SourceType:**

| Wert | Bedeutung | Primärquelle |
| --- | --- | --- |
| `official_statement` | eigene schriftliche Aussage des Streamers (Post, Panel-Text) | ja |
| `own_setup_page` | eigene Setup-Seite oder Geräteliste des Streamers | ja |
| `video_statement` | Streamer nennt das Produkt selbst in Video oder Stream | ja |
| `manufacturer` | offizielle Herstellerangabe (z. B. Partner-Seite) | ja |
| `video_visual` | Produkt nur sichtbar, nicht genannt | nein |
| `third_party` | andere öffentliche Quelle (Artikel, Datenbank) | nein |

### Source (`sources/{id}`)

`url`, `domain`, `source_type`, `registry_id`, `title`, `first_seen_at`, `last_checked_at`,
`last_check_ok`, `content_hash` (zur Änderungserkennung, kein Inhalt).

### SourceRegistryEntry (`source_registry/{id}`) – zugelassene Quellen

`domain`, `source_types`, `access_method` (`manual`, `official_api`, `rss`, `http_allowed`),
`auto_fetch_allowed` (Standard `false`), `terms_reviewed_at`, `terms_url`,
`min_interval_hours`, `notes`, `enabled`.

## E. Änderungshistorie

### AuditEntry (`audit_log/{id}`) – nur anfügen, nie ändern oder löschen

`at`, `actor` (`type`: admin, agent, system · `id`), `action` (create, update, retire,
approve, reject, check_failed), `entity_type`, `entity_id`, `from_version`, `to_version`,
`changes` (`{feld: [alt, neu]}`), `reason` (Pflicht), `proposal_id`.

## F. Freigabe-Workflow

### ChangeProposal (`change_proposals/{id}`)

| Feld | Typ | Hinweis |
| --- | --- | --- |
| `entity_type`, `entity_id` | | worauf sich der Vorschlag bezieht |
| `operation` | create, update, retire | |
| `payload` | Map | vorgeschlagene Feldwerte |
| `base_version` | int \| null | Version, auf der der Vorschlag beruht; passt sie nicht mehr, wird er `superseded` |
| `reason` | string | Pflicht |
| `evidence_source_ids` | Liste | Belege |
| `origin` | string | z. B. `change_detector`, `admin` |
| `created_by` | Actor | |
| `status` | pending, approved, rejected, superseded | |
| `dedupe_key` | string | Hash aus Entität, Operation und Payload – derselbe Vorschlag entsteht nur einmal |
| `decided_by`, `decided_at`, `decision_note` | | bei Entscheidung |

Erlaubte Übergänge: `pending → approved | rejected | superseded`. Entschiedene Vorschläge sind endgültig.
Ein Agent kann nie selbst freigeben.

---

## Firestore-Struktur und Zugriff

| Collection | Lesen | Schreiben |
| --- | --- | --- |
| `streamers`, `setup_claims`, `products`, `offers`, `sources`, `source_registry` | Admin | Admin, Service-Konto |
| `change_proposals` | Admin | Admin (Entscheidung), Service-Konto (nur neue, Status `pending`) |
| `audit_log` | Admin | nur anfügen, keine Änderung, kein Löschen |

Öffentliche Besucher lesen nicht aus Firestore, sondern aus dem freigegebenen JSON-Export.
Admin = Firebase-Nutzer mit Custom Claim `admin: true` (wird per Admin-SDK gesetzt, nicht im Client).
Das Service-Konto der Agent-Läufe umgeht die Regeln technisch; deshalb schreibt der Agent-Code
ausschließlich über den Approval Manager und das Audit-Log.
