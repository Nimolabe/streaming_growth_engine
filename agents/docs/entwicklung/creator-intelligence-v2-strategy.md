# Creator Intelligence V2: Strategische Entscheidungen und Lernschleife

**Status:** separat entwickelter, noch nicht CI-freigegebener Offline-Prototyp.
**Keine** Änderung an Website oder `main`; der ältere V1-Endpunkt und der
Content Strategist bleiben erhalten.

## Warum V2?

V1 erkennt Kennzahlen-Muster. V2 muss daraus **eine** priorisierte Maßnahme
unter realistischen Rahmenbedingungen ableiten. Es darf niemals behaupten,
dass eine bestimmte Wachstumsstrategie garantiert funktioniert.

**POST `/api/v1/growth/strategy`**

V1-Wochenkennzahlen (4–26 aufeinanderfolgende Wochen) und zusätzliche Felder:

- `has_own_recordings`: Bereits eigene, verwendbare Stream-Aufnahmen vorhanden?
- `can_edit_short_clips`: Ist ein geeigneter Schnitt-/Clip-Workflow vorhanden?
- `can_access_stream_summaries`: Kann die Person eigene Auswertungen nachsehen?
- `minimum_stream_hours`: Bereits fest eingeplante Livestream-Zeit pro Woche;
  muss kleiner/gleich `weekly_hours_available` sein.
- `weekly_hours_available` umfasst **alle** Aufgaben, nicht nur das Streaming.

Siehe [Beispiel-Anfrage](../../examples/creator_intelligence_v2_strategy.json).

## Auswahl und Priorisierung

1. Die V1-Diagnose bleibt Grundlage: Zeitüberlastung, Zuschauer-Rückgang,
   fehlende Clips, Clip-Reichweite, Rückkehrer, Follows oder ruhige Baseline.
2. Schweregrad aus V1 wird beibehalten. Bei gleichrangigen Hinweisen wird
   das gewählte Ziel (Reichweite, Rückkehrer oder Kontinuität) berücksichtigt.
   Ein bereits überlasteter Creator soll **keine zusätzlichen Content-Pflichten** erhalten.
3. Clips werden nur als sofortiger Test vorgeschlagen, wenn eigene Aufnahmen
   **und** eine Schnittmöglichkeit angegeben sind. Andernfalls wird nur
   die notwendige Vorbereitung empfohlen.
4. Zeitbudget wird in Streaming, Experiment, Messung und freie Restzeit
   aufgeteilt. Alle Minuten summieren sich auf das angegebene Wochenbudget.
5. Wenn kein Experiment mit der verbindlichen Mindest-Streamingzeit
   vereinbar ist, wird zur Baseline-Erfassung zurückgefallen und die
   ursprünglich erkannte Chance ausdrücklich als `deferred_signals` ausgewiesen.
6. Nur **ein** Primärexperiment gleichzeitig; weitere Hinweise werden
   zurückgestellt. Ein Regelwert ist keine Erfolgswahrscheinlichkeit.

**POST `/api/v1/growth/review`**

Der Auswertungs-Endpunkt akzeptiert eine zu prüfende Kennzahl, 2–8
Baseline-Wochenwerte und 2–8 Wochenwerte nach der Maßnahme.
Die Eingabe bestätigt selbst, ob Beobachtungsfenster vergleichbar waren
und ob nur eine größere Veränderung vorgenommen wurde.

Bei fehlenden Daten, mehreren wesentlichen Veränderungen oder ungleichen
Beobachtungszeiträumen ist das Ergebnis **inconclusive**. Sonst gibt
der Agent rein beschreibend eine Veränderung aus, **niemals** einen
wissenschaftlichen Wirkungsnachweis. Bei Vorher-Wert null wird keine
unendliche prozentuale Wachstumsrate erfunden.

Siehe [Beispiel-Nachprüfung](../../examples/creator_intelligence_v2_review.json).

## Tests

Die getrennten Dateien `tests/test_creator_strategy_v2.py` und
`tests/test_creator_strategy_review_v2.py` prüfen u. a.:

- korrekte Priorisierung bei Zeitüberlastung;
- fehlende Aufnahmen / fehlenden Clip-Editor;
- minutengenaue Budgetgrenzen und geschützte Streamingzeit;
- ungültige Anfragen und Rückwärtskompatibilität zu V1;
- vorsichtige Nachprüfung mit fehlenden, ungleichen oder falschen Daten.

Im GitHub-Actions-Workflow `Agent backend tests` muss dafür
`feature/creator-intelligence-v2-strategy` ausgewählt werden.
Erst nach erfolgreicher Ausführung von `pytest` **und** `ruff`
kann V2 als technisch getesteter Prototyp gelten.

## Wichtige Grenzen

- Keine realen Datenverbindungen, kein LLM, keine Abrechnung über APIs.
- Die Diagnose ist regelbasiert und arbeitet nur mit Wochenaggregaten.
- Zwei Wochen Vergleich sind eine **Orientierung**, keine signifikante Stichprobe.
- Die Prüfung ist keine kausale A/B-Messung und hat keine Kontrolle für
  Saisonalität, Algorithmusänderungen oder Zufall.
- Keine tatsächliche Veröffentlichung, Videobearbeitung oder Speicherung.
- Für ein öffentliches Produkt brauchen wir Authentifizierung, echte
  Datenexport-Adapter, Privacy-Review und Qualitätsstudien mit realen Daten.
