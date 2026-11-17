# Browser-Tests der Website

Playwright-Tests (Python, pytest, Chromium headless) für die statische Website in der
Repo-Wurzel. Sie laufen ohne Internet und ohne echtes Firebase. In der CI startet sie
`.github/workflows/web-tests.yml` bei Änderungen an `*.html`, `js/**`, `css/**`,
`database.rules.json` oder `tests/web/**`. Man kann sie dort auch per Hand starten
(„Run workflow“).

## Lokal ausführen

```bash
python -m pip install pytest playwright
python -m playwright install chromium
python -m pytest tests/web -q
```

Den Befehl aus der Repo-Wurzel starten. Einen eigenen Server braucht man nicht, die Tests
starten selbst einen auf einem zufälligen Port.

Passt die installierte Playwright-Version nicht zum vorhandenen Chromium, kann man den
Browser direkt angeben: `SGE_CHROMIUM=/pfad/zu/chrome python -m pytest tests/web -q`.

## Was nachgebaut ist

`conftest.py` leitet im Browser alle Anfragen um:

- **Lokaler Server:** Anfragen an die Repo-Wurzel gehen an `http.server`.
- **Alles andere im Internet** (Google Fonts, CDNs, Bilder) bekommt Status 204, also eine
  leere Antwort. Die Tests hängen damit nicht vom Netz ab.
- **Firebase** (`https://www.gstatic.com/firebasejs/...`) wird durch die Module in `stubs/`
  ersetzt:
  - `firebase-app.js`: `initializeApp`
  - `firebase-auth.js`: `getAuth`, `onAuthStateChanged`, `signOut`, `GoogleAuthProvider`.
    Im Test meldet `window.__setUser({ uid, displayName })` an, `window.__setUser(null)`
    meldet ab. Login per E-Mail oder Google-Popup ist nicht nachgebaut.
  - `firebase-database.js`: `getDatabase`, `ref`, `get`, `set`, `remove`, `update`,
    `serverTimestamp`, `query`, `orderByChild`, `startAt`, `endAt`, `limitToFirst`,
    `limitToLast`. Die Daten liegen als JSON im `localStorage` unter `__sgeDb`.
    Mit `window.__deny = true` scheitert jede Anfrage mit `PERMISSION_DENIED`, so als
    wären die Firebase-Regeln noch nicht veröffentlicht.

Die Datenbank-Regeln (`database.rules.json`) prüft der Nachbau **nicht**.

## Hilfsfunktionen (`conftest.py`)

| Funktion | Zweck |
| --- | --- |
| `context` / `make_context(**optionen)` | Browser-Kontext mit Umleitungen (z. B. `viewport` für Handy) |
| `set_language(context, "de")` | Sprache vor dem ersten Laden festlegen |
| `seed_db(context, daten)` | Startdaten der Datenbank (nur beim ersten Laden) |
| `read_db(page)` / `write_db(page, daten)` | Datenbank lesen oder ersetzen |
| `collect_errors(page)` | sammelt JS-Fehler und `console.error` |
| `wait_for_auth(page)` | wartet, bis die Seite den Anmeldestand kennt |
| `login(page, uid, name)` | meldet einen Testnutzer an |
| `profile(uid, username, platform)` | ein öffentliches Profil wie aus `social.js` |

## Einen Test ergänzen

1. Neue Datei `tests/web/test_<thema>.py` anlegen, Hilfen per `from conftest import ...` holen.
2. Grundgerüst:

   ```python
   from conftest import collect_errors, set_language, wait_for_auth


   def test_beispiel(context, base_url):
       set_language(context, "de")
       page = context.new_page()
       errors = collect_errors(page)
       page.goto(f"{base_url}/guides.html", wait_until="load")
       wait_for_auth(page)
       assert page.locator("h1").first.text_content().strip() != ""
       assert errors == []
   ```

3. Braucht eine neue Seite eine weitere Firebase-Funktion, diese im passenden Modul in
   `stubs/` ergänzen.

## Stolperfallen

- GSAP blendet Elemente erst beim Scrollen ein. Bis dahin liefert `inner_text()` leeren
  Text und Playwright hält Elemente teils für unsichtbar. Für Textvergleiche
  `text_content()` nehmen und für Zustände das `hidden`-Attribut prüfen.
- `text-transform: uppercase` verändert, was `inner_text()` liefert, `text_content()` nicht.
- Headless-Chromium meldet Englisch als Browsersprache. Deutsche Tests brauchen deshalb
  `set_language(context, "de")`.
- Bekannte Website-Fehler stehen als `xfail(strict=True)` im Test. Ist der Fehler behoben,
  schlägt der Test als „XPASS“ fehl. Dann die Markierung entfernen.
