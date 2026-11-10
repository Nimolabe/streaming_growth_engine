# Setup Intelligence Agent – Verifizierungsregeln

Stand: 10.11.2026 · Umsetzung: `backend/setup_agent/verification.py`, `pricing.py`, `identity.py`

Alle Regeln sind transparent und deterministisch. Gleiche Eingaben und gleicher Zeitpunkt ergeben
immer dasselbe Ergebnis. Jede Bewertung liefert eine Liste von Begründungen.

## 1. Vertrauenswert (Confidence Evaluator)

**Gewicht nach Quellentyp**

| Quellentyp | Gewicht | Primär |
| --- | --- | --- |
| `official_statement` | 0,95 | ja |
| `own_setup_page` | 0,90 | ja |
| `video_statement` | 0,85 | ja |
| `manufacturer` | 0,80 | ja |
| `video_visual` | 0,60 | nein |
| `third_party` | 0,40 | nein |

**Aktualität** (Alter = heute − `observed_at`)

| Alter | Faktor | Einstufung |
| --- | --- | --- |
| bis 365 Tage | 1,0 | aktuell |
| 366–730 Tage | 0,7 | älter |
| über 730 Tage | 0,4 | veraltet |

**Berechnung**

1. Pro Beleg: Gewicht × Faktor. Der beste Beleg ist die Basis.
2. Bonus +0,05 für jede **weitere unabhängige Domain** mit aktuellem Beleg (gleiche Domain zählt nicht doppelt).
3. Obergrenze 0,99. Es gibt nie 1,0, weil sich Setups ändern können.

**Stufen:** ab 0,80 `high` · ab 0,50 `medium` · über 0 `low` · 0 `none`.

## 2. Status einer Setup-Angabe (Setup Verifier)

Die Regeln werden **in dieser Reihenfolge** geprüft, die erste zutreffende entscheidet:

| # | Bedingung | Status |
| --- | --- | --- |
| 1 | Kein Beleg vorhanden | `unknown` |
| 2 | Produkt nicht eindeutig zugeordnet (`product_id` fehlt) | `unknown` |
| 3 | Widerspruch im selben Slot (siehe 3) | `conflicting` |
| 4 | Durch neueren Primärbeleg im selben Slot abgelöst | `outdated` |
| 5 | Alle Belege älter als 730 Tage | `outdated` |
| 6 | Mindestens ein Primärbeleg bis 365 Tage | `confirmed` |
| 7 | Sonst (Primärbeleg 366–730 Tage oder nur Sekundärbelege) | `probable` |

Folgen:

- Sekundärquellen allein (sichtbar im Video, Drittseiten) führen **nie** zu `confirmed`, egal wie viele.
- Ein altes Setup wird nicht in die Gegenwart übertragen: ohne aktuellen Primärbeleg höchstens `probable`.
- Die Bewertung ist eine **Empfehlung**. Ändert sie den Status einer veröffentlichten Angabe,
  entsteht ein Änderungsvorschlag. Bestätigte Datensätze werden nie direkt überschrieben.

## 3. Widersprüche und Ablösung (pro Slot)

Ein Slot ist Kategorie + Rolle, z. B. `mikrofon:primary`. Mehrere Produkte derselben Kategorie
sind kein Widerspruch, wenn sie verschiedene Rollen haben (`primary`, `secondary`, `irl`).

Für alle nicht veralteten Angaben eines Slots mit **verschiedenen Produkten**:

- Entscheidend ist je Angabe das Datum des **neuesten Primärbelegs**.
- Liegen die neuesten Primärbelege zweier Produkte **höchstens 30 Tage** auseinander,
  ist die Lage unklar → beide `conflicting`, manuelle Prüfung.
- Liegt ein Produkt **mehr als 30 Tage** vorn, gelten die älteren Angaben als abgelöst → `outdated`
  (als Vorschlag, nicht automatisch).
- Angaben ohne Primärbeleg lösen nichts ab und werden auch nicht durch andere abgelöst; sie bleiben `probable`.

## 4. Produktzuordnung

- `match_key` = Hersteller und Modell klein geschrieben, Umlaute ersetzt, ohne Leerzeichen,
  Binde- und Unterstriche. `Shure SM-7B` und `Shure SM7B` → `shure:sm7b` (gleiches Produkt).
  `Shure SM7dB` → `shure:sm7db` (anderes Produkt).
- Zwei Katalogeinträge mit gleichem `match_key` sind ein Duplikat und werden abgelehnt.
- Der Product Resolver (Phase 3) ordnet nur bei **genau einem** Treffer zu. Mehrere oder kein Treffer
  → `product_id = null`, Status `unknown`, Rohname bleibt für die manuelle Prüfung erhalten.
- GTIN/EAN werden über die Prüfziffer validiert.

## 5. Preise

- Ein neuer Preis ändert **nur** die Preisdaten (Offer, PriceObservation), nie eine Setup-Angabe.
- Preiszustand: `current` (letzter Erfolg ≤ 14 Tage), `stale` (älter), `unknown` (nie erfolgreich).
- Fehlgeschlagener Abruf: Preis bleibt, `failed_checks` +1, Audit-Eintrag `check_failed`.
  Ab 3 Fehlversuchen in Folge erscheint das Angebot in der manuellen Prüfliste.
- Eine Preisänderung wird gemeldet, wenn sich Betrag, Währung oder Verfügbarkeit ändern.
  Gleicher Preis bei erneutem Abruf erzeugt keine neue Beobachtung im Verlauf.

## 6. Veröffentlichung

- Öffentlich sichtbar sind nur Angaben mit `published = true`, das ausschließlich durch eine
  Admin-Freigabe gesetzt wird.
- Veröffentlicht werden `confirmed` (als „bestätigt") und `probable` (deutlich als „nicht bestätigt"
  gekennzeichnet). `unknown`, `conflicting` und `outdated` erscheinen nicht als aktuelles Setup.
- Zu jeder Angabe werden Quelle(n), Quellentyp und Prüfdatum angezeigt.

## 7. Idempotenz

| Datensatz | ID aus |
| --- | --- |
| Produkt | Hersteller + Modell (Slug) |
| Quelle | normalisierte URL (klein, ohne `www.`, ohne Fragment, ohne Tracking-Parameter wie `utm_*`) |
| Setup-Angabe | Streamer + Slot + Produkt (oder normalisierter Rohname) |
| Angebot | Produkt + Händler + normalisierte URL |
| Vorschlag | `dedupe_key` aus Entität + Operation + Payload |

Wiederholte Läufe mit gleichen Daten schreiben dadurch auf dieselben IDs und erzeugen keine Duplikate.
