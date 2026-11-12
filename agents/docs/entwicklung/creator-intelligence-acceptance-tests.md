# Creator Intelligence V1 — redaktionelle Abnahmeszenarien

Diese **synthetischen** Szenarien sind Testfälle, keine echten Kanalstatistiken
und kein Nachweis einer Wachstumswirkung.

Der Testcode liegt unter `tests/test_creator_intelligence_scenarios.py`.
Er läuft automatisch mit dem vorhandenen `pytest`-Schritt in GitHub Actions.

| Szenario | Ausgangslage | Erwartete Diagnose | Was **nicht** behauptet werden darf |
| --- | --- | --- | --- |
| Anfänger ohne Clips | ~2 Zuschauer, konstante Streams, 0 veröffentlichte Clips | `no_clips`; überschaubares Clip-Experiment vorschlagen | Stagnation eindeutig durch fehlende Clips verursacht |
| Wachsender Kanal mit stabilen Kennzahlen | ~11 Zuschauer, regelmäßige Clips und ähnlich hohe Reichweite | `baseline_review`; Vergleichsbasis beibehalten | Künstlich einen Rückgang oder neuen Erfolgshebel erfinden |
| Größerer Kanal mit weniger Rückkehrern | Durchschnittszuschauer stabil, wöchentliche Einzelzuschauer steigen, Rückkehrerzahlen sinken | `returning_viewers_decline`; regelmäßige Formate prüfen | Sichere Ursache oder einen Rückkehr-Effekt vorhersagen |
| Zeitbudget überlastet | ~9 Streamingstunden bei nur 3 verfügbaren Stunden, keine Clips | `time_budget_overrun` **vor** `no_clips` | Zuerst zusätzliche Clip-Arbeit verordnen |
| Keine Clipzahlen | Veröffentlichungen sind unbekannt, nicht null | Keine `no_clips`-Diagnose | Unbekannte Daten zu null umdeuten |
| Fehlende Rückkehrerzahlen | Eine Woche hat keine Rückkehrerzahl | Kein Rückkehrer-Rückgang | Lückenhaftes Zahlenmaterial extrapolieren |

## Redaktionelle Abnahmebedingungen

1. **Beobachtung und Ursache trennen:** Der Agent darf Änderungen nennen, aber
   keine Ursachen ohne Kontrollvergleich beweisen.
2. **Keine falschen Wachstumswahrscheinlichkeiten:** Prioritäten sind
   Entscheidungsregeln, keine Erfolgschancen.
3. **Wichtige Abhängigkeiten zuerst:** Eine hohe Arbeitslast wird vor zusätzlichen
   Content-Aufgaben sichtbar.
4. **Keine Fantasieanalysen:** Fehlende Daten sperren nicht gestützte Diagnosen.
5. **Klare Handlung und Kontrolle:** Jede Empfehlung nennt eine umsetzbare
   Maßnahme, eine Überprüfung und die betroffenen Kennzahlen.
6. **Nicht zu viel aus vier Wochen schließen:** Kleine Stichproben und
   Aggregationen bleiben ausdrücklich begrenzt.

## Grenzen

Ein grüner automatischer Test zeigt, dass der Code diese künstlichen Szenarien
korrekt verarbeitet. **Er bestätigt nicht**, dass die Regeln bei allen echten
Kanälen zu nützlichen Wachstumsentscheidungen führen.

Vor einer Freigabe mit echten Nutzerdaten werden anonymisierte Testfälle,
unterschiedliche Spielkategorien, echte Plattformexporte und eine Bewertung
der Empfehlungsgüte durch menschliche Reviewer benötigt. Das System darf
weiterhin ohne kostenpflichtiges Sprachmodell betrieben werden.

## Tests ohne lokale Installation

1. `https://github.com/langemojo-byte/streaming_ai_agents/actions/workflows/tests.yml`
2. `Run workflow` öffnen und `feature/creator-intelligence-v1-offline` auswählen.
3. Mit `Run workflow` ausführen.
4. Den Schritt `Run tests` und die anschließende `Lint`-Prüfung ansehen.

Bestehende Workflows wurden für diese Tests nicht verändert.
