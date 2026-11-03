# Zusammenarbeit mit zwei Entwicklern und KI-Assistenten

## Branches
- `main` bleibt die gemeinsame, lauffähige Version. Nicht direkt darauf entwickeln.
- Pro Aufgabe einen **neuen** Branch von aktuellem `main` erstellen (z. B. `feature/dashboard-navigation` oder `feature/hardware-filter`).
- Branches `feature/dashboard` und `feature/hardware-finder` sind getrennte Start-Arbeitsbereiche; künftig pro Teilaufgabe einen frischen Branch verwenden.
- Vor Beginn: Änderungen auf `main` prüfen und mit dem anderen Entwickler kurz abstimmen.

## Zuständigkeiten
- Dashboard: primär Dashboard-Komponenten und Navigation.
- Hardware-Finder: primär Hardware-Daten und Finder-Komponenten.
- Änderungen an gemeinsam genutzten Dateien (`index.html`, globale CSS-/JS-Dateien, Authentifizierung, Konfiguration) vorher gemeinsam abstimmen. Dort ist das Konfliktrisiko besonders hoch.

## Ablauf für jede KI-Aufgabe
1. GitHub Issue oder eindeutige Aufgabenbeschreibung mit Akzeptanzkriterien anlegen.
2. Den **genauen Branch und die erlaubten Dateipfade** angeben.
3. Der KI ausdrücklich verbieten, auf `main` zu schreiben oder fremde Änderungen zurückzusetzen.
4. Nach Änderungen lokal prüfen und, soweit verfügbar, Tests ausführen.
5. Pull Request nach `main` erstellen; geänderte Dateien, Teststatus und Risiken dokumentieren.
6. Der jeweils andere Entwickler prüft den PR. Erst danach zusammenführen.
7. Vor dem Merge den Branch mit aktuellem `main` synchronisieren; Konflikte bewusst lösen.

## Regeln für Sicherheit
- Keine API-Schlüssel, Passwörter, Tokens, Firebase-Geheimnisse oder `.env`-Dateien committen.
- Keine Änderungen an Authentifizierung, Deployment oder Datenbankmigrationen ohne Abstimmung.
- Keine automatischen PR-Merges durch KI, solange keine verpflichtenden Reviews/Checks eingerichtet sind.
- `main` niemals per Force-Push überschreiben.
- Vor Veröffentlichung sicherstellen, dass Firebase-Sicherheitsregeln und Zugriffskontrollen geprüft wurden.

## Vorlage für KI-Aufträge
> Repository: Nimolabe/streaming_growth_engine. Arbeite ausschließlich auf Branch: [BRANCH]. Aufgabe: [AUFGABE]. Erlaubte Dateien: [PFADE]. Verändere `main` nicht, ändere keine anderen Dateien, überschreibe keine fremden Änderungen. Liste vorab betroffene Dateien und liefere zum Abschluss eine Zusammenfassung samt Tests. Erstelle einen Pull Request zur gemeinsamen Prüfung; merge nicht selbst.

## GitHub-Einstellungen
Wenn der GitHub-Tarif Branch-Schutz im privaten Repository unterstützt: Pull Requests verpflichtend, mindestens ein Review, CI-Checks vor Merge und Force-Push-Verbot. Falls nicht verfügbar, gelten die Regeln oben als Teamvereinbarung.
