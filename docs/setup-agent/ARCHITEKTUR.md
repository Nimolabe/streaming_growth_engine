# Setup Intelligence Agent – Architektur (Phase 1)

Stand: 10.11.2026 · Status: **Entwurf zur Prüfung** (Phase 1)

Der Setup Intelligence Agent sammelt, prüft und verwaltet Angaben dazu, welche Hardware und
Software bekannte Streamer nutzen. Er arbeitet **regelbasiert und ohne kostenpflichtige KI-APIs**.
Jede Angabe braucht eine Quelle; unbestätigte Angaben werden nie automatisch als Fakt veröffentlicht.

Begleitende Dokumente:

- [DATENMODELL.md](DATENMODELL.md) – Datenmodelle A–F und Firestore-Struktur
- [VERIFIZIERUNG.md](VERIFIZIERUNG.md) – Verifizierungs- und Vertrauensregeln
- [API.md](API.md) – versionierte Schnittstellen (v1)

---

## 1. Bestandsaufnahme des Repositorys

| Bereich | Heute | Bewertung für den Agenten |
| --- | --- | --- |
| Frontend | Statische Seiten (`index.html`, `setups.html`), Vanilla-JS-Module, kein Build-Schritt | Bleibt. Der Agent liefert Daten, das Frontend liest sie. |
| Setup-Daten | Fest im Code in `js/setups-data.js` (Produkte, Bauteil-Typen, fiktive Beispiel-Streamer) | Wird in Phase 2 durch exportierte, geprüfte Daten ersetzt. Bauteil-Typen werden übernommen. |
| Firebase | Projekt `streaminggrowthengine`: Authentication (E-Mail, Google), Realtime Database für `users/` (Favoriten) und `profiles/` | Bleibt unverändert. Der Agent bekommt einen eigenen Speicher (siehe 3.1). |
| Sicherheitsregeln | `database.rules.json`: Standard alles gesperrt, Nutzer nur eigene Daten | Gutes Muster, wird für Firestore übernommen. |
| Backend | keins | Neu: Python-Paket `backend/setup_agent`. |
| CI / Tests | keine | Neu: Python-Tests, später GitHub-Actions-Workflow. |
| Zusammenarbeit | `CONTRIBUTING.md`: Feature-Branches, PR mit Review, kein Merge durch KI | Wird eingehalten. |
| Offene PR | #4 (`feature/setup-kategorien-phase1`): neue Bauteil-Typen und Budget-Planer | Die Kategorien im Datenmodell sind darauf abgestimmt. Keine Dateiüberschneidung. |

Das Repository ist öffentlich. Daraus folgt: **keine Geheimnisse im Code**, und Logs von
GitHub Actions sind öffentlich einsehbar (keine personenbezogenen Daten loggen).

---

## 2. Grundsätze

1. **Kein Fakt ohne Beleg.** Jede Setup-Angabe verweist auf mindestens eine registrierte Quelle.
2. **Kein Raten.** Ein Produkt wird nur zugeordnet, wenn Hersteller und Modell eindeutig erkannt sind.
   Sonst bleibt die Angabe „unbekannt" mit dem Originaltext der Quelle.
3. **Vorschlagen statt Überschreiben.** Automatische Komponenten erzeugen nur Änderungsvorschläge.
   Veröffentlicht wird erst nach Freigabe durch einen Admin.
4. **Getrennte Wahrheiten.** Setup (wer nutzt was), Produkt (was ist es), Preis (was kostet es wo)
   und Quelle (wer sagt das) sind getrennte Datensätze. Ein neuer Preis ändert nie ein Setup.
5. **Letzter bestätigter Stand bleibt.** Ist eine Quelle nicht erreichbar, wird nichts ersetzt,
   sondern der Fehler protokolliert und der Datensatz als „Prüfung fehlgeschlagen" markiert.
6. **Idempotent.** Wiederholte Läufe mit denselben Eingaben erzeugen keine neuen Datensätze
   (deterministische IDs und Dedupe-Schlüssel).
7. **Nachvollziehbar.** Jede Änderung hat Zeitstempel, Akteur, Begründung und Verweis auf Vorschlag
   und Quelle (Audit-Log, nur anfügen).
8. **Austauschbare Speicherung.** Die Geschäftslogik spricht nur mit einer Repository-Schnittstelle.

---

## 3. Technische Entscheidungen

### 3.1 Datenbank: Firestore statt Realtime Database

Geprüft anhand der offiziellen Firebase-Preisseite (Stand 10.11.2026):

| Kriterium | Cloud Firestore (Spark) | Realtime Database (Spark) |
| --- | --- | --- |
| Kostenloses Kontingent | 1 GiB Speicher, 50.000 Lesen / 20.000 Schreiben / 20.000 Löschen pro Tag, 10 GiB Egress pro Monat | 1 GB Speicher, 10 GB Download pro Monat, 100 gleichzeitige Verbindungen |
| Datenmodell | Dokumente und Collections, gut für getrennte Modelle A–F | Ein großer JSON-Baum, Trennung nur über Pfade |
| Abfragen | Filter, Sortierung, Bereichsabfragen (z. B. Kategorie + Preisbereich) mit Indizes | Nur ein Sortier-/Filterkriterium pro Abfrage |
| Zugriffskontrolle | Regeln pro Collection und Dokument, Feldvalidierung, Custom Claims | Regeln pro Pfad, weniger ausdrucksstark |
| Änderungshistorie | Eigene Collection, nur anfügen, per Regel unveränderbar | Möglich, aber unhandlich |
| Wartbarkeit | Klare Schemas, offizielles Python-Admin-SDK | Gut für Echtzeit, schlecht für relationale Daten |
| Skalierung | Für Kataloge und viele Datensätze ausgelegt | Für Echtzeit-Sync kleiner Datenmengen ausgelegt |

**Entscheidung:** Firestore im selben Firebase-Projekt, Spark-Tarif, **keine Kreditkarte nötig**.
Die Realtime Database bleibt für Login-nahe Nutzerdaten. Beide laufen parallel im Spark-Tarif.

**Kostenschutz:** Öffentliche Besucher lesen **nicht** aus Firestore, sondern aus statischen
JSON-Dateien (siehe 3.3). So bleibt das Lese-Kontingent für Admin und Agent reserviert, und
Besucherzahlen können keine Kosten oder Sperren auslösen.

**Verworfene Alternative:** Daten als JSON-Dateien direkt im Git-Repository (Historie über Git,
Freigabe über Pull Requests). Sehr billig und transparent, aber ohne Admin-Oberfläche nur für
technisch versierte Pflegende nutzbar. Bleibt als Fallback möglich, weil die Logik über eine
Repository-Schnittstelle läuft.

### 3.2 Backend: Python, FastAPI erst ab Phase 2

- Geschäftslogik als Python-Paket `backend/setup_agent` (Python ≥ 3.11, Pydantic v2).
- REST-API mit **FastAPI** ab Phase 2. Grund für die Wahl: Pydantic-Modelle werden direkt zu
  dokumentierten OpenAPI-Schemas, Versionierung über `/api/v1`.
- **Hosting-Frage (offen):** Kostenloses, dauerhaftes Hosting für einen Python-Server ohne
  Kreditkarte ist in Phase 2 zu prüfen. Damit das System nicht davon abhängt:
  - Öffentliche Lese-API = statische JSON-Dateien (3.3), brauchen keinen Server.
  - Agent-Läufe = Batch-Jobs in GitHub Actions (3.4), brauchen keinen Server.
  - FastAPI dient der Admin-Bedienung und der späteren App-Integration und läuft notfalls lokal.

### 3.3 Veröffentlichung: statische JSON-API

Freigegebene Daten werden von einem Export-Job in versionierte JSON-Dateien geschrieben,
z. B. `data/v1/streamers.json`, `data/v1/streamers/<id>.json`, `data/v1/products.json`.
Sie werden mit der Website ausgeliefert (gleiche Hosting-Lösung wie heute).

Vorteile: keine Datenbankzugriffe durch Besucher, unabhängig vom Frontend-Framework,
cachebar, Versionsstand im Git nachvollziehbar. Die JSON-Struktur entspricht exakt den
Antworten der FastAPI-Endpunkte (siehe [API.md](API.md)).

### 3.4 Geplante Aktualisierung: GitHub Actions

Laut GitHub-Dokumentation sind Standard-Runner in öffentlichen Repositories kostenlos.
Geplante Läufe (z. B. wöchentlich) führen die Agent-Komponenten aus und schreiben
**nur Vorschläge** nach Firestore (Zugriff über ein Service-Konto, Schlüssel als GitHub-Secret).

Bekanntes Risiko: Laut GitHub werden geplante Workflows in öffentlichen Repositories nach
60 Tagen ohne Repository-Aktivität automatisch deaktiviert. Gegenmaßnahme: der Admin-Bereich
zeigt das Datum des letzten Laufs an; bei mehr als 14 Tagen ohne Lauf erscheint eine Warnung.

### 3.5 Kein Sprachmodell, aber vorbereitet

Alle Komponenten sind regelbasiert. Für eine spätere, optionale KI-Erweiterung gibt es eine
Schnittstelle `ClaimExtractor` (Text → Kandidaten-Angaben). Ein KI-Extraktor darf nur
**Vorschläge** mit Status „wahrscheinlich" erzeugen und muss dieselben Regeln durchlaufen.
Er kann nie eine Angabe bestätigen.

---

## 4. Komponenten

```
                ┌──────────────────┐
 Admin ────────▶│ Approval Manager │◀──────── Vorschläge ────────┐
 (Website/API)  └────────┬─────────┘                              │
                         │ freigegeben                            │
                         ▼                                        │
                ┌──────────────────┐   ┌──────────────┐   ┌──────┴────────┐
                │   Repository     │──▶│ Audit Logger │   │ Setup Verifier│◀─ Confidence Evaluator
                │ (Firestore/Mem.) │   └──────────────┘   │ Change Detect.│◀─ Product Resolver
                └────────┬─────────┘                      │ Price Monitor │◀─ Source Registry
                         │ Export                         └──────▲────────┘
                         ▼                                       │
                 data/v1/*.json ──▶ Website / App       Update Scheduler (GitHub Actions)
```

| Komponente | Aufgabe | Phase |
| --- | --- | --- |
| Source Registry | Liste zugelassener Quellen mit Typ, Zugriffsart, Nutzungsbedingungen, Rate-Limit, ob automatischer Abruf erlaubt ist | 1 (Modell), 3 |
| Product Resolver | Normalisiert Produktnamen („Shure SM-7B" → Shure SM7B), erkennt Aliase, lehnt mehrdeutige Treffer ab | 3 |
| Setup Verifier | Prüft Angaben gegen Regeln, setzt Status | 1 (Regeln), 3 |
| Confidence Evaluator | Berechnet Vertrauensstufe aus Quellentyp, Alter und unabhängigen Belegen | 1 |
| Change Detector | Vergleicht neuen mit bestätigtem Stand, erzeugt Vorschläge, erkennt Widersprüche | 3 |
| Price Monitor | Prüft Angebote, erkennt Preisänderungen und Nichtverfügbarkeit, ändert nur Preisdaten | 4 |
| Approval Manager | Freigabe-Workflow: offen → freigegeben / abgelehnt / ersetzt | 3 |
| Update Scheduler | Plant Läufe (GitHub Actions), respektiert Intervalle und Limits | 4 |
| Audit Logger | Schreibt jede Änderung unveränderbar ins Audit-Log | 2 |

Jede Komponente ist eine eigene Python-Klasse mit klaren Ein- und Ausgaben, ohne versteckten
Zustand, und wird einzeln getestet. Die Uhrzeit wird injiziert, damit Tests deterministisch sind.

---

## 5. Datenquellen und Recht

- Es werden nur Quellen abgerufen, die in der Source Registry stehen **und** für den
  automatischen Abruf freigegeben sind. Standard ist „nur manuell".
- Keine Umgehung von Zugriffsbeschränkungen, Logins, Captchas oder Rate-Limits. `robots.txt`
  wird beachtet. Kein Scraping von Händlerseiten, deren Bedingungen das untersagen.
- Gespeichert werden Fakten (welches Produkt, wann, wo belegt) und ein Link, **keine**
  kopierten Texte, Bilder oder Transkripte. Notizen sind eigene kurze Zusammenfassungen.
- Personenbezogene Daten beschränken sich auf öffentliche Streamer-Profile (Name, Kanal-Links).
- Welche externen Schnittstellen in Phase 4 nutzbar sind (z. B. offizielle Plattform-APIs,
  Händler-Partnerprogramme), wird dann jeweils anhand der offiziellen Bedingungen geprüft.
  Bis dahin werden Preise **manuell** gepflegt.

---

## 6. Risiken

| Risiko | Auswirkung | Gegenmaßnahme |
| --- | --- | --- |
| Keine legale automatische Preisquelle | Preise veralten | Manuelle Pflege, Preis-Alter sichtbar, ab 14 Tagen als „veraltet" markiert |
| Spark-Kontingent erreicht | Admin/Agent blockiert bis Tageswechsel | Öffentliche Leser nutzen statisches JSON, Agent-Läufe batchen Schreibzugriffe |
| Geplante Workflows deaktiviert (60 Tage) | Keine Updates | Warnung im Admin-Bereich |
| Service-Konto-Schlüssel gelangt nach außen | Vollzugriff auf Firestore | Nur als GitHub-Secret, minimale Rechte, Rotation dokumentiert |
| Falsche Zuordnung durch ähnliche Modellnamen | Falsche Fakten | Resolver lehnt mehrdeutige Treffer ab, Tests mit Namenspaaren (SM7B / SM7dB) |
| FastAPI-Hosting nicht kostenlos möglich | Keine Live-Admin-API | Admin über Firestore-Regeln und Website möglich; API lokal |

---

## 7. Phasenplan

| Phase | Inhalt | Status |
| --- | --- | --- |
| 1 | Architektur, Datenmodelle, Verifizierungsregeln, API-Entwurf; Modelle und Regeln als getesteter Code | **in diesem PR** |
| 2 | Repository-Adapter (In-Memory, Firestore), FastAPI v1, Audit Logger, JSON-Export, Beispiel-Setups | geplant |
| 3 | Source Registry, Product Resolver, Change Detector, Approval Manager | geplant |
| 4 | Datenadapter, Price Monitor, Scheduler (GitHub Actions), Fehlerbehandlung | geplant |
| 5 | Admin-Oberfläche, Sicherheitsregeln, Integrationstests, Frontend-Anbindung | geplant |
| 6 | Optional: KI-Extraktor, nur wenn messbarer Mehrwert | offen |
