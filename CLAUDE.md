# Streaming Growth Engine – Projektübergabe für Claude Code

## Pflege dieser Datei

- Nach jedem gemergten PR werden **Abschnitt 4** (gemergt) und **Abschnitt 5** (offen)
  aktualisiert.
- Neue Erkenntnisse und Stolperfallen kommen in **Abschnitt 10** (Bekannte Fallstricke).

Stand: 26.11.2026 (nach dem Merge von #33/#34) · Repo: `Nimolabe/streaming_growth_engine` (öffentlich, Standard-Branch `main`)
Website (GitHub Pages): https://nimolabe.github.io/streaming_growth_engine/

> **Für Claude Code:** Lies dieses Dokument vollständig, bevor du etwas änderst. Kommuniziere
> mit dem Nutzer auf **Deutsch**. Abschnitt 2 enthält verbindliche Regeln.

---

## 1. Worum es geht

Die **Streaming Growth Engine** ist eine Plattform für wachsende und etablierte Streamer.
Sie wird von zwei Personen entwickelt: dem Nutzer und seinem Kumpel (GitHub: `Nkllasbus`).
Beide arbeiten mit KI-Assistenten.

Das Produkt besteht aus zwei Teilen:

1. **Website** (statisch, GitHub Pages): Startseite, Setups/Hardware-Finder, Guides,
   Layout-Baukasten, Community mit Profilen. Firebase dient für Login und Datenbank.
   Beide Entwickler haben Zugang zur Firebase-Konsole.
2. **KI-Agenten** (`agents/`, Python): Clip Hunter, Content Strategist (inkl. Kategorie-Check),
   Creator Intelligence u. a. Lokal per Kommandozeile und als FastAPI-Prototyp.

Leitidee: **erst kostenlos und lokal**, später optional mit Kosten (gehostete KI, Backend).
Bewusst **einfach** halten, also kein StreamElements-Klon.

Hintergrund: Die Agenten entstanden ursprünglich mit ChatGPT im falschen Repo
(`langemojo-byte/AI-agents` bzw. `streaming_ai_agents`). Sie wurden bereinigt übernommen
(PR #9). Das alte Repo `streaming_ai_agents` soll archiviert werden; das macht der Nutzer manuell.

---

## 2. Verbindliche Arbeitsregeln

Diese Regeln kommen aus `CONTRIBUTING.md` und aus Absprachen mit dem Nutzer.

- **Nie auf `main` entwickeln.** Pro Aufgabe ein neuer Branch von aktuellem `main`
  (`feature/...`, `fix/...`), danach ein Pull Request.
- **Niemals selbst mergen**, außer der Nutzer verlangt es ausdrücklich für bestimmte PRs.
  Der jeweils andere Entwickler prüft den PR.
- **Kein Force-Push auf `main`**, keine fremden Änderungen zurücksetzen.
- **Keine Geheimnisse committen:** keine API-Schlüssel, Tokens oder `.env`-Dateien.
  Twitch-Zugang nur über Umgebungsvariablen (`TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`),
  KI-Anbieter über `SGE_CLIP_AI_*` bzw. `SGE_LLM_*`.
- **Änderungen an gemeinsam genutzten Dateien** (`index.html`, globale CSS/JS, Auth,
  `database.rules.json`, Konfiguration) im PR klar benennen. Dort ist das Konfliktrisiko hoch.
- **Firebase-Regeln:** Änderungen an `database.rules.json` werden erst wirksam, wenn sie in der
  Firebase-Konsole veröffentlicht sind. Das können der Nutzer und der Kumpel (beide haben
  Konsolenzugang). Jede Funktion muss ohne veröffentlichte Regeln verständlich reagieren
  (freundliche Meldung statt Absturz).
- **Jeder neue Datenbank-Bereich braucht eine erneute Veröffentlichung der Regeln.** Im PR
  muss darauf deutlich hingewiesen werden (z. B. als Hinweis ganz oben im PR-Text).
- **Neue Ideen nicht sofort bauen**, sondern auf eine Ideenliste setzen. Für jeden Schritt
  vorher festlegen, was „fertig genug“ heißt.
- **Qualität vor Tempo:** testen (Python-Tests, Browser), Desktop **und** Handy prüfen,
  Deutsch **und** Englisch prüfen, ehrlich sagen, was nicht getestet werden konnte.
- **Datensätze Dritter nicht committen**, z. B. LIGHTOR (Lizenz unklar).
- **Commit-Nachrichten und PR-Texte auf Deutsch**, mit Abschnitten „Was“, „Geprüft“ und
  „Nicht getestet“. PR-Texte als JSON-Datei mit Heredoc `<<'EOF'` bauen. Backticks in einem
  Bash-String in doppelten Anführungszeichen zerstören sonst den Text (das ist schon passiert).

---

## 3. Technik und Struktur

### Website (Repo-Wurzel)
```
index.html        Startseite (Features, Loadout-Karten, Quests, Clip-Hunter-Kachel)
setups.html       Setup-/Hardware-Finder (js/setups.js, js/setups-data.js)
community.html    Profilsuche / Community (js/community.js)
profil.html       Profilseite (js/profil.js)
css/style.css     globales Design (CSS-Variablen in :root), css/setups.css, css/social.css
css/fonts.css     @font-face der Website (Inter, Space Grotesk), Dateien unter fonts/
js/main.js        allgemeines Verhalten, js/motion.js Animationen (GSAP, ScrollTrigger, Lenis)
js/i18n.js        Deutsch/Englisch-Umschaltung
js/auth.js        Firebase Auth (Login-Modal, #login-btn mit data-open-auth)
js/social.js      Datenbank-Zugriff (getDb), Profile, Folgen
js/firebase-config.js  öffentliche Firebase-Konfiguration (Projekt "streaminggrowthengine")
database.rules.json    Realtime-Database-Regeln
```
Außerdem (seit #14–#20): `guides.html`, `layouts.html`, `overlay.html`,
`js/guides.js`, `js/layout-core.js`, `js/layouts.js`, `js/layouts-share.js`,
`js/layout-profile.js`, `js/waitlist.js`, `js/setups-i18n.js`, `css/guides.css`,
`css/layouts.css`, `css/overlay.css`. Seit dem PR „Quests und Community“: `js/quests.js`
(Erste Quests der Startseite, nur per Klick abhakbar, Stand im `localStorage` unter `sge-quests`).
Seit dem PR „Strategist Web-Kern“: `js/strategist-core.js` (Planer des Content Strategist als
ES-Modul ohne DOM/Netzwerk/Zufall, `buildPlan(request, data)`), `data/content-strategist.json`
(Inhalte als Export aus Python, committet), `tests/fixtures/strategist-parity.json`
(Paritäts-Fixtures), `tests/web/strategist_parity.mjs` und `tests/web/test_strategist_parity.py`.
Noch keine Seite dafür (kommt in Teil 2).

**Wichtige Mechanismen der Website:**
- **i18n (`js/i18n.js`):** Eine Map Deutsch→Englisch. Übersetzt werden **nur Textknoten mit
  exakt passendem, getrimmtem Text**. `<option>`-Elemente werden **nicht** übersetzt; das
  muss die jeweilige Seite selbst tun. Ein MutationObserver übersetzt neu eingefügte Knoten.
  API: `window.SGE_I18N` mit `t(text)`, `setLanguage(lang)`, `getLanguage()`; `add(entries)`
  gibt es seit PR #14. Beim Umschalten feuert das Event `sge:language`.
  → Dynamische Texte immer mit `SGE_I18N.t()` setzen und bei `sge:language` neu rendern.
  → **Neue Übersetzungen am Ende der Map anhängen**, nicht mittendrin. Sonst gibt es
  Merge-Konflikte zwischen parallelen PRs.
  → Keys gelten global: Ein Eintrag wie `"Pause"` übersetzt **jeden** Textknoten „Pause“.
- **Auth/Events:** `sge:auth` (detail `{user, app}`) und `window.sgeAuth` für den aktuellen
  Stand; `sge:profile` nach dem Laden des Profils. Login-Fenster programmatisch über
  `document.getElementById("login-btn").click()`.
- **Datenbank:** `getDb(app)` aus `js/social.js` liefert `{db, database}` (dynamischer Import
  des Firebase-SDK). Texte aus Daten **immer per `textContent`** einsetzen, nie per `innerHTML`.
- **Animationen:** GSAP blendet Elemente beim Scrollen ein. CSS-`transition` auf `transform`
  kollidiert mit GSAP (das war der Bug mit den versetzten Karten, PR #13). Bei
  Browser-Tests liefert `inner_text()` für noch unsichtbare Elemente einen leeren Text
  → `text_content()` nutzen. Mit `text-transform: uppercase` liefert `inner_text()`
  Großbuchstaben.

### KI-Agenten (`agents/`)
- Python ≥ 3.11, Paket `streaming_agents`, pydantic v2, FastAPI unter `/api/v1`, ruff
  (Zeilenlänge 100, py311), pytest.
- Installation: `cd agents && python -m pip install -e ".[dev]"` (optional `.[llm]`; auch
  `.[whisper]`).
- CI: `.github/workflows/agents-tests.yml` (bei Änderungen unter `agents/`); manuell mit
  Eingabe `enable_video_tests` auch die ffmpeg-Video-Tests.
- Module: `clip_hunter/` (Clip Hunter v4), `category_check/`, `content_strategist/`
  (Content Strategist Variante A seit #30, ersetzt v2/v3: `genres.py` mit 9 Genres,
  `formats.py` mit Formaten pro Genre, `planner.py` für den Wochenplan mit Zeitbudget und
  Kategorie-Check-Uhrzeiten, `titles.py` für Titel im Stil echter Twitch-Titel,
  `twitch_limits.py`, `report.py`, `cli.py`, `web_export.py`; CLI `python -m
  streaming_agents.content_strategist plan` und `export-web`, API `POST /api/v1/content/strategy`),
  `category_check/aliases.py` (Kurzformen → Twitch-Name) und `category_check/gambling.py`
  (Glücksspiel-Liste; Glücksspiel wird nicht unterstützt, auch im Content Strategist),
  `agents/` (Growth Analyst = Creator Intelligence + `creator_strategy*`, geparkt),
  `llm/` (OpenAI-Provider, opt-in mit `--live`, Kostenbremse; soll später mit
  `clip_hunter/ai_stage.py` zusammengelegt werden), `api.py`, `registry.py`. Entfernt:
  die älteren Clip-Intelligence-Module (v1/v2, Prüfliste, `clip_evaluation`, `clip_cli`),
  Content Strategist v2/v3 und der separate Wochenplaner (`/content/weekly-plan`).
- Doku: `agents/README.md`, `agents/docs/clip-hunter.md`, `agents/docs/category-check.md`,
  `agents/docs/content-strategist.md` (+ `content-strategist-beispiele.md`),
  `agents/docs/architecture.md`, `agents/docs/bestandsaufnahme-2026-11.md`.

---

## 4. Was auf `main` ist (alles gemergt)

| PR | Inhalt |
| --- | --- |
| #1 | Doku: sicherer Workflow für parallele KI-Entwicklung (CONTRIBUTING) |
| #2 | Setups-Seite: Budget-Planer, Streamer-Setups, Hardware |
| #3 | Länderwahl und Sprachumschaltung DE/EN |
| #4 | Setups: neue Kategorien, „Brauche ich / Habe ich / Nicht nötig“ |
| #6 | Redesign der Startseite mit Animationen |
| #7 | Social: Profile mit Nutzernamen, Profilsuche, Folgen |
| #8 | Datenbankregeln: von Firebase abgelehnte Muster ersetzt |
| #9 | KI-Agenten bereinigt aus `streaming_ai_agents` übernommen |
| #10 | Clip Hunter v4 (Chat-Reaktionen und Audio-Spitzen) |
| #11, #12 | Clip-Hunter-Kachel auf der Startseite |
| #13 | Fix: Loadout-Karten blieben versetzt (CSS-Transition vs. GSAP) |
| #14 | Setups-Seite vollständig auf Englisch |
| #15 | Clip Hunter an echten Streams kalibriert |
| #16 | Clip Hunter: KI-Stufe |
| #17 | Beta-Warteliste an der Clip-Hunter-Kachel |
| #18 | Guides-Seite |
| #19 | Layout-Baukasten |
| #20 | Content Strategist: Kategorie-Check auf echten Twitch-Daten |
| #21 | Doku: `CLAUDE.md` mit Projektstand und Arbeitsregeln |
| #22 | Browser-Tests (`tests/web/`, eigene CI) und Handy-Fixes für Guides und Layout-Baukasten |
| #23 | Aufräum-Paket: `CLAUDE.md` nach #21/#22, Setups-Reiter bei 320 px, Guides-Link zur Clip-Hunter-Kachel |
| #24 | Layouts v2: Facecam-Positionen und -Größen, schlichter Rahmen, Socials am Rahmen, eigener Logo-Upload, neue Overlay-Hintergründe und selbst gehostete Schriften |
| #25 | Doku: `CLAUDE.md` auf Stand 22.11.2026 |
| #26 | Schriften der Website selbst hosten statt Google Fonts (`css/fonts.css`, `fonts/`) |
| #27 | Bilder der Startseite selbst hosten (`images/`, WebP mit 600-px-Variante), Test gegen fremde Hosts |
| #28 | Doku: Bestandsaufnahme der KI-Agenten (`agents/docs/bestandsaufnahme-2026-11.md`) |
| #29 | KI-Agenten: Altlasten aus der ChatGPT-Zeit entfernt (Clip Intelligence v1/v2, Prüfliste, `clip_evaluation`, Content-Strategist-Empfehler v2) |
| #30 | Content Strategist Variante A: neues Paket `content_strategist/` (ersetzt v3 und `/content/weekly-plan`), 9 Genres, Wochenplan in den eigenen Zeitfenstern mit Zeitbudget, Anbindung an den Kategorie-Check (Uhrzeiten nach Publikum pro Platz), Titel im Stil echter Twitch-Titel (Bausteine mit „ \| “, Emoji vorn, drei Titel pro Stream) und Tags nach Twitch-Grenzen; optionale Eingaben `rank_goal`/`current_rank`/`mood`/`first_time`/`commands` |
| #31 | Content Strategist: Fehler aus einer Simulation mit 100 Test-Streamern behoben (Formate für vertraute Spiele ohne Genre, Kürzen bei knappen Stunden, TimeWindow als Uhrzeit, Wochen-Formate nur am Wochenende, Regressionstest) |
| #32 | Website: Quests nur per Klick abhakbar, ehrlicher Leer-Zustand der Community, Hinweis „im Aufbau“; `CLAUDE.md` nach #30 |
| #33 | Doku: Kategorie-Check am 26.11.2026 echt gegen die Twitch-API getestet (Fallstrick 8: Groß-/Kleinschreibung bei Get Games egal) |
| #34 | Kategorie-Check: Kurzformen (`category_check/aliases.py`, z. B. CS2 → Counter-Strike, jedes Ziel per API geprüft); Glücksspiel wird nirgends unterstützt (`category_check/gambling.py`, auch im Content Strategist, keine Option) |

#1–#20 gemergt bis 17.11.2026, #21–#27 bis 22.11.2026, #28–#29 am 23.11.2026, #30–#32 am
25.11.2026, #33–#34 am 26.11.2026. Stand nach #29: CI grün (Website 218 Browser-Tests, Agenten 341 Python-Tests),
alle Seiten DE/EN ohne JS-Fehler. Nach #30: Agenten 877 Python-Tests grün; nach #31/#32: 965;
nach #34: 1003.

## 5. Offene Pull Requests

- **#5** Setup Intelligence Agent: bewusst geparkt.
- **Strategist Web-Kern, Teil 1** (Branch `feature/strategist-web-kern`): Export
  `data/content-strategist.json`, `js/strategist-core.js`, Paritätstest Python ↔ JavaScript,
  Planer findet Messungen über Kurzformen. Noch keine Seite (Teil 2). Nach dem Merge in
  Abschnitt 4 eintragen.

### Details zu den zuletzt gemergten PRs (#14–#20)

**#14 Setups auf Englisch:** `js/setups-i18n.js` (`SETUPS_EN`, 161 Einträge, Platzhalter
wie „Dein {kategorie}-Setup“), `SGE_I18N.add()`, Helfer `t`/`tf`/`translateOptions` in
`js/setups.js`, Neu-Rendern bei `sge:language`.

**#15 Clip-Hunter-Kalibrierung:** Messung am LIGHTOR-Datensatz (100 Test-Streams, nur Chat).
Neue Standardwerte: `chat_window_seconds=12`, `chat_baseline_seconds=120`, `chat_min_z=2.0`,
`chat_reaction_lag_seconds=8` (`chat_min_gap_seconds` bleibt 25). Erweitertes Emote-Lexikon.
Neu: `benchmark.py` und der CLI-Befehl `benchmark`. Ergebnisse (Top 10):

| Daten | Clip enthält Highlight | Treffer ±5 s | Abdeckung (Top 15) | Zufall | nur Nachrichten zählen |
| --- | --- | --- | --- | --- | --- |
| Dota | 63 % | 52 % | 56 % | 13 % | 47 % |
| LoL | 72 % | 64 % | 48 % | 19 % | 67 % |
| Gesamt | 67 % | 58 % | 52 % | 17 % | 57 % |

Nur mit Chat ist bei etwa 62–72 % Schluss (die Labels sind unvollständig). Weitere Merkmale
(Nachrichtenlänge, Ähnlichkeit) brachten nichts Messbares. Eine Großbuchstaben-Heuristik
wurde getestet und wieder entfernt.

**#16 KI-Stufe:** `clip_hunter/ai_stage.py`, CLI `analyze --ai [--ai-max N] [--ai-model M]
[--transcribe] [--whisper-model small]`.
- Ein Sprachmodell prüft nur die besten 8 Kandidaten (höchstens 10). Es bekommt Chat-Auszug
  ±15 s (ohne Namen, Bots und Befehle) und optional ein lokales Whisper-Transkript.
- Antwort als JSON: clipwürdig, Sicherheit, Schnitt, Titel, Hook, Caption, Hashtags, Begründung.
  Die Antwort wird streng geprüft: Schnitt im Fenster, 12–60 s; Texte gekürzt.
- Clipwürdige Kandidaten rücken nach vorn. Der Export nutzt den KI-Schnitt, der Bericht zeigt
  die Texte.
- Standard: **Ollama lokal**, `http://localhost:11434/v1`, Modell `qwen2.5:7b`, kostenlos.
  Andere Anbieter über `SGE_CLIP_AI_BASE_URL`, `SGE_CLIP_AI_MODEL`, `SGE_CLIP_AI_API_KEY`,
  `SGE_CLIP_AI_TIMEOUT`. Entfernte Server nur per https, mit Datenschutzhinweis.
  **Nicht** `SGE_LLM_*` verwenden, die gehören zum Content-Strategist-Modul.
- Kennt ein Server den JSON-Modus nicht, wird automatisch ohne ihn wiederholt.
  Ist der Server weg, läuft die Analyse ohne KI weiter.
- Extra `whisper = ["faster-whisper>=1.0,<2"]`.

**#17 Warteliste:** `js/waitlist.js`. Daten: `waitlist/clipHunter/<uid>` =
`{createdAt (Serverzeit), platform?}`, keine zusätzliche E-Mail. Wer abgemeldet ist, sieht
das Login und wird danach automatisch vorgemerkt. Die Plattform wird beim Vormerken aus dem
öffentlichen Profil gelesen (Timing-Bug behoben).

**#18 Guides:** `guides.html` + `js/guides.js` (Inhalte als Daten DE/EN, nur `textContent`).
Sechs Guides: Plattform, OBS, erster Stream, Zeitplan, erste Zuschauer, Twitch Affiliate.
Fakten mit „Stand: November 2026“ und offizieller Quelle. Affiliate seit Juni 2026:
**25 Follower, 4 Stunden, 4 Tage, Ø 3 Zuschauer an 4 Tagen (in 30 Tagen)**.
„Guides“ steht in der Navigation aller Seiten.

**#19 Layout-Baukasten:** `layouts.html` (Editor), `overlay.html` (OBS-Browser-Quelle
1920×1080), `js/layout-core.js` (Prüfen/Kodieren; die Gestaltung steckt komplett in der URL).
- 4 Szenen (Startet gleich mit Countdown, Live mit Webcam-Rahmen bei x=60, y=640, 480×270,
  Pause, Ende). 3 Stile: Neon, Minimal, Kräftig.
- **OBS-Szenensammlung (.json):** Der Import prüft die Schlüssel `sources`, `name` und
  `current_scene`. Unter Windows sind Spielaufnahme, Webcam und Audio enthalten
  (wasapi_*), unter macOS/Linux Overlays und Mikrofon.
- Teilen per Link oder im Profil: `layouts/<uid>` = `{params ≤ 2000 Zeichen, updatedAt}`,
  wird beim Anzeigen immer neu geprüft. Die Profilseite zeigt Vorschau und
  „Design übernehmen“.

**#20 Kategorie-Check (Content Strategist auf echten Daten):** `agents/streaming_agents/category_check/`.
- Misst über die Twitch-API (Get Games → sonst Search Categories mit Vorschlägen,
  Get Streams nach Spiel-ID und Sprache, seitenweise je 100; Get Top Games für `suggest`).
  Gespeichert werden **nur Zuschauerzahlen** (JSONL).
- Berechnet: Live-Kanäle, Publikum, **Platz mit eigenen Zuschauern** (vorsichtig: hinter
  Gleichstand; bei Seitenlimit nur Untergrenze) und eine Einschätzung (Faustregeln:
  bis Platz 15 gut, bis 40 machbar, unter 25 Zuschauern gesamt wenig Publikum).
- **Beste Zeiten** sind 2-Stunden-Blöcke in Ortszeit, sortiert nach Publikum pro Platz.
  Nicht die leerste Uhrzeit, das war ein gefundener und behobener Denkfehler.
  `--window 16-24` funktioniert auch über Mitternacht.
- CLI: `measure`, `suggest`, `watch` (mindestens alle 10 Min.), `report` (+ `--html`/`--json`).
  API: `POST /api/v1/content/category-check` (nur Auswertung, kein Twitch-Zugriff).

**#23/#24 Layouts v2:** `js/layout-core.js` (Prüfen/Kodieren, Geometrie), `js/overlay.js`,
`js/layouts.js`, `js/layout-icons.js` (Logo-Upload), `css/overlay.css`, `css/layouts.css`.
- **URL-Parameter** (unbekannte Werte → Standard; Standardwerte stehen nicht in der URL, alte
  Links bleiben unverändert):
  - `cam`: Facecam-Ecke `tl`/`tr`/`bl`/`br` (Standard `bl`).
  - `cs`: Facecam-Größe `s`/`m`/`l` = 480×270 / 640×360 / 800×450 (Standard `s`).
  - `frame`: Rahmen `color` (farbig, Standard) oder `plain` (schlicht).
  - `fs`: Socials am Rahmen (`1` = an, nur bei `plain`).
  - `fi`: Logos anzeigen (`1` = an).
  - `u`: uid des angemeldeten Nutzers für die eigenen Logos. Steht **nur in den Overlay-Links**
    (Editor-Vorschau, Link-Liste, OBS-Export), **nie** im Teilen-Link und nie im Profil
    („Design übernehmen“ bekommt keine fremden Logos). Nur Buchstaben/Ziffern, 10–128 Zeichen.
- **Geometrie** an einer Stelle: `frameRect(config)`, `camRect(config)`, `plainBorders(config)`.
  Seitlich 60 px, oben ab y=112, unten bis y=968. Klein + farbig + unten links bleibt
  x=60, y=640, 480×270. `sceneCollection` setzt die Webcam-Quelle passend zu Position und Größe.
- **Logos:** Das Projekt liefert **keine** Plattform-Logos mit (Markenrecht). Angemeldete Nutzer
  laden eigene Bilder hoch (`js/layout-icons.js`, höchstens 300 KB, PNG/SVG/WebP). Im Browser
  werden sie über ein Canvas zu einer weißen 128×128-PNG-Maske umgerechnet (SVG nur als Bild
  geladen, nie ins DOM) und gespeichert unter `socialIcons/<uid>/<tw|yt|tt|ig|x>` (Data-URL,
  ≤ 40.000 Zeichen). Das Overlay lädt sie per REST-GET (`<databaseURL>/socialIcons/<uid>.json`,
  ohne Firebase-SDK) und zeigt sie per CSS `mask-image`, immer weiß. Fehlt ein Logo, steht Text.
- **Socials am Rahmen:** mit Logos höchstens 3, als Text höchstens 2 gleichzeitig; Handles bis
  15 Zeichen werden nie gekürzt; der Rest wechselt alle 8 s.
- **Schriften** selbst gehostet unter `fonts/` (SIL OFL, je `OFL.txt`): Oxanium (Neon),
  Sora (Minimal), Anton (Kräftig), Manrope (Fließtext). Kein Google Fonts im Overlay.

---

## 6. Roadmap und Status

**Hauptspur**
1. ✅ **Fundament:** PR #8 und #4 gemergt, PR #5 geparkt. Die Firebase-Regeln sind
   veröffentlicht, inklusive `layouts`, `waitlist` und `socialIcons` (zuletzt am 22.11.2026).
   Warteliste und „Layout im Profil“ wurden live getestet.
2. ✅ **Clip Hunter echt testen und kalibrieren** (PR #15). Zielkriterium war: mindestens die
   Hälfte der Top 10 clipwürdig. Erreicht mit 67 % „Clip enthält Highlight“, nur mit Chat.
   Offen: Audio an echten VODs mit Ton.
3. ✅ **KI-Stufe** (PR #16): Whisper lokal, Sprachmodell nur für die Top 5–10.
   Offen: Modell- und Budget-Entscheidung für einen gehosteten Anbieter, echter Test mit Ollama.
4. ⏸ **Backend und Beta-Bereich** (Firebase-Login, Limits pro Nutzer, Chat-Mitschnitt auf
   dem Server). Wartet auf die **Hosting-Entscheidung**.
5. ✅ **Content Strategist auf echten Daten** (PR #20, Kategorie-Check).
   ✅ Am 26.11.2026 echt gegen die Twitch-API getestet (`measure`, `suggest`, `report
   --html/--json`, Content Strategist mit `--measurements`): alles funktionierte, keine
   Fehler, kein Anfragelimit. Ergebnis zu Fallstrick 8 siehe Abschnitt 10.
   ✅ **Variante A** (PR #30): lokaler, regelbasierter Wochenplan für
   0–20 Zuschauer – echte Wochentage und Uhrzeiten in den eigenen Zeitfenstern, 9 Genres mit
   eigenen Formaten, Chat-Bedarf als Merkmal pro Format, Titel/Tags nach Twitch-Grenzen,
   Uhrzeiten nach Kategorie-Check-Messungen. CLI `python -m streaming_agents.content_strategist
   plan`, API `POST /api/v1/content/strategy`. Website „Weg A“: Planer als JavaScript
   (`js/strategist-core.js`), Inhalte als Export aus Python. Teil 1 (Kern + Paritätstest) im
   PR, die Seite selbst kommt in Teil 2.
6. ⏳ Später: **Growth Analyst** und **Trend Scout**. Der Trend Scout kann auf den Messungen
   des Kategorie-Checks aufbauen (Wachstum von Kategorien über Tage).

**Nebenspur**
- a) ✅ Einfacher Layout-Baukasten (PR #19). Am 23.11.2026 vom Nutzer erfolgreich getestet:
  Import der Szenensammlung in OBS und Logo-Upload mit echtem Konto.
- b) ✅ Guides-Seite (PR #18)
- c) ✅ Beta-Warteliste an der Clip-Hunter-Kachel (PR #17)

---

## 7. Offene Punkte, die nur Menschen erledigen können

- **Firebase-Regeln neu veröffentlichen**, sobald ein PR einen neuen Datenbank-Bereich
  hinzufügt (Nutzer oder Kumpel): Realtime Database → Regeln → Inhalt von
  `database.rules.json` einfügen → Veröffentlichen. Zuletzt am 22.11.2026.
- **Impressum und Datenschutzerklärung** ergänzen, bevor die Beta öffentlich wird.
- ✅ **Twitch-Entwickler-App** angelegt; Client-ID und Secret liegen als Umgebungsvariablen
  vor. Der Kategorie-Check wurde am 26.11.2026 echt getestet. Offen: den
  Clip-Hunter-Abgleich (VOD-Startzeit, Zuschauer-Clips) echt testen und `watch` über mehrere
  Tage laufen lassen, damit „beste Zeiten“ echte Daten bekommen.
- **KI-Stufe testen:** Ollama installieren, `ollama pull qwen2.5:7b`, dann
  `python -m streaming_agents.clip_hunter analyze --video vod.mp4 --chat chat.jsonl --ai --transcribe --report bericht.html`.
- **Entscheidungen:** Hosting für Schritt 4; Modell und Budget für einen gehosteten KI-Anbieter.
- **Aufräumen:** die alten Branches `feature/ki-agenten` und `feature/clip-hunter-chat`
  löschen, Repo `streaming_ai_agents` archivieren. Beides ist durch die Rechte der KI
  blockiert und muss manuell passieren.

## 8. Nicht getestet (ehrlich)

- KI-Stufe mit einem echten Modell und echtem Whisper (getestet nur mit nachgebautem Server).
- Kategorie-Check: `watch` über längere Zeit und damit „beste Zeiten“ aus echten Messungen
  (am 26.11.2026 nur einzelne Messungen um etwa 12 Uhr Ortszeit). `measure`, `suggest`,
  `report` und der Content Strategist mit echten Messungen sind seit dem 26.11.2026 echt
  getestet.
- Clip-Hunter-Abgleich mit der echten Twitch-API.
- Audio-Spitzen des Clip Hunters an echten VODs.

---

## 9. Prüfen und Testen

```bash
cd agents
python -m pip install -e ".[dev]"
ruff check .
python -m pytest -q
# Clip Hunter gegen LIGHTOR (Datensatz separat klonen, NICHT committen):
#   git clone https://github.com/sfu-db/Lightor_Exp
#   python -m streaming_agents.clip_hunter benchmark --lightor <Pfad>/Lightor_Exp --game all --split test
```

Content Strategist für die Website (nach jeder Änderung an Inhalten oder Planer, aus `agents/`):

```bash
python -m streaming_agents.content_strategist export-web --out ../data/content-strategist.json
python tests/strategist_parity.py      # Paritäts-Fixtures neu erzeugen
node ../tests/web/strategist_parity.mjs  # JavaScript gegen Python prüfen (ohne Browser)
```

Website lokal: `python -m http.server` in der Repo-Wurzel, dann im Browser öffnen.

Browser-Tests: `tests/web/` (Playwright, Chromium headless), Aufruf aus der Repo-Wurzel mit
`python -m pytest tests/web -q`. Die Tests starten selbst einen lokalen Server, beantworten
Anfragen nach außen mit 204 und bauen Firebase über Stub-Module nach
(`gstatic.com/firebasejs/...` → `tests/web/stubs/`). Anleitung: `tests/web/README.md`.
Die CI (`.github/workflows/web-tests.yml`) führt sie bei Änderungen an `*.html`, `js/**`,
`css/**`, `database.rules.json` und `tests/web/**` aus.

Prüfliste für Website-Änderungen:
- Deutsch und Englisch, auch beim Umschalten; keine deutschen Reste im Englischen.
- Desktop und Handy (390 und 360 px, Setups auch 320 px, kein seitliches Scrollen); keine
  JS-Fehler in der Konsole.
- Angemeldet und abgemeldet; Verhalten ohne veröffentlichte Firebase-Regeln.
- Eingaben aus URL oder Datenbank: XSS-Versuche (`<img onerror>`, `<script>`) bleiben Text.

---

## 10. Bekannte Fallstricke

1. i18n übersetzt nur exakte Textknoten. Sätze mit `<strong>` mittendrin zerfallen in
   Teile, die sich nicht übersetzen lassen. Solche Texte ohne Inline-Tags schreiben oder per
   JS rendern.
2. Neue i18n-Einträge ans Ende der Map, nicht neben bestehende Einträge. Sonst kollidieren
   parallele PRs.
3. GSAP und CSS-`transition: transform` vertragen sich nicht.
4. `SGE_LLM_*` gehört dem Content-Strategist-LLM-Modul, `SGE_CLIP_AI_*` der KI-Stufe des
   Clip Hunters.
5. Zeitzonen: Unter Windows fehlt oft die IANA-Datenbank (`zoneinfo`). Für Ortszeit
   `datetime.astimezone()` ohne Argument verwenden.
6. Firebase-Regeln: Manche Regex-/Validate-Muster lehnt Firebase ab (siehe PR #8).
   Funktionen müssen auch ohne veröffentlichte Regeln sauber reagieren
   (`PERMISSION_DENIED` → freundliche Meldung).
7. Seiten mit neuer Navigation: Wer eine Seite aus einer älteren kopiert, übernimmt deren
   Navigation. Prüfen, dass alle Nav-Links (inklusive „Guides“) vorhanden sind.
8. Twitch-API: Bei Get Games ist der Name ein exakter Treffer, die Groß-/Kleinschreibung ist
   aber **egal** (echt getestet am 26.11.2026: „valorant“, „Valorant“ → VALORANT,
   „MINECRAFT“ → Minecraft, „just chatting“ → Just Chatting). Der Rückfall über Search
   Categories greift damit nur bei echten Abweichungen und liefert dort brauchbare
   Vorschläge („Phasmo“ → Phasmophobia, „Fortnight“ → Fortnite). Achtung: Counter-Strike 2
   heißt auf Twitch „Counter-Strike“ (ID 32399); „Counter Strike 2“ und „Counter-Strike 2“
   werden nicht gefunden. Abkürzungen können exakt auf ein anderes Spiel passen („CS2“ →
   „Carrot Slime 2“). **Seit PR #34** übersetzt
   `category_check/aliases.py` gängige Kurzformen VOR Get Games in den offiziellen Namen
   (CS2 → Counter-Strike, LoL, GTA/GTA 5, WoW, Apex, R6 → Rainbow Six Siege, EA FC → EA Sports
   FC 27, TFT, DbD u. a.; jedes Ziel per API geprüft). Ausgabe, Bericht und Messdatei zeigen
   „CS2 → Counter-Strike (Alias)“. Neue Aliasse nur aufnehmen, wenn Get Games den Zielnamen
   exakt kennt; „EA FC“ bei der nächsten FC-Ausgabe anpassen. Die Genre-Aliasse in
   `content_strategist/genres.py` sind etwas anderes (Wort-Treffer → Genre) und bleiben getrennt.
9. Nichts mergen ohne ausdrücklichen Auftrag. Branches löschen oder Repos archivieren
   wird für die KI blockiert.
10. Neue Datenbank-Bereiche → Regeln in der Firebase-Konsole neu veröffentlichen, sonst
    antwortet die Datenbank mit `PERMISSION_DENIED`. Im PR deutlich darauf hinweisen.
11. Grids am Handy: `minmax(0, 1fr)` statt `1fr` verwenden, sonst wird die Spalte so breit wie
    ihr Inhalt und die Seite scrollt seitlich (PR #22, #23).
12. Keine Marken-Logos ins Repo. Plattform-Logos nur als eigene Uploads der Nutzer (#24).
13. Keine externen Schriften/CDNs mit Personenbezug (z. B. Google Fonts überträgt die IP-Adresse).
    Schriften liegen selbst gehostet unter `fonts/` (je Familie ein Ordner mit `OFL.txt`),
    eingebunden über `css/fonts.css` (Website) bzw. `css/overlay.css` (Overlay). Bilder liegen
    selbst gehostet unter `images/` (WebP mit `-600`-Variante per `srcset`, Herkunft und Lizenz
    in `images/README.md`). Der Test `test_no_requests_to_foreign_hosts` erlaubt fremde Hosts
    nur aus der Firebase-Liste `ALLOWED_FOREIGN` in `tests/web/test_pages.py`;
    `test_no_requests_to_google_fonts` prüft zusätzlich Google Fonts für jede Seite.
14. Dekorative Fortschrittsanzeigen nie automatisch füllen – nur echte Nutzeraktionen zählen.
    Die „Ersten Quests“ der Startseite haben sich früher beim Scrollen selbst abgehakt und die
    XP-Leiste gefüllt; das wirkte unehrlich. Seit dem PR „Quests und Community“ zählt nur ein
    Klick auf die Checkbox (`js/quests.js`). Dasselbe gilt für Zähler, Badges und
    Community-Angaben: nichts versprechen oder anzeigen, was nicht wirklich passiert ist.
15. Glücksspiel wird nicht unterstützt (Entscheidung des Nutzers vom 26.11.2026): nie
    vorschlagen, nie messen, nie planen; keine Option zum Einschalten. Die eine Liste steht in
    `category_check/gambling.py` (IDs und Namen, Stand November 2026); Kategorie-Check und
    Content Strategist nutzen sie gemeinsam, ein späterer Website-Export muss sie übernehmen.
    `suggest` nennt nur die Zahl, `measure`/`watch` lehnen freundlich ab (nur Glücksspiel →
    Exit-Code 2), `report`/API ignorieren alte Einträge, der Planer entfernt das Spiel (allein →
    Fehler). Die Website-Version bekommt die Liste über `data/content-strategist.json`.
16. Inhalte des Content Strategist nur in Python ändern (`content_strategist/formats.py`,
    `titles.py`, `genres.py` usw.), dann `export-web` ausführen und die Paritäts-Fixtures neu
    erzeugen (`python tests/strategist_parity.py` in `agents/`). Nie `data/content-strategist.json`
    von Hand bearbeiten. Die Planer-Logik (Hinweise, Fehlermeldungen, Reihenfolge) steht zweimal:
    in `planner.py` und in `js/strategist-core.js`. Eine Änderung dort muss in beiden
    Dateien passieren, sonst schlägt der Paritätstest fehl. Nicht den Test lockern, sondern die
    Ursache beheben. Typische Stolperfallen JS ↔ Python: Codepoints statt `.length`, `casefold`
    statt `toLowerCase`, Unicode-`\w`, Python-Whitespace, `//` und `%` bei negativen Zahlen.

---

## 11. Ideenliste (nicht ohne Auftrag bauen)

- Trend Scout auf Basis der Kategorie-Messungen (welche Kategorien wachsen?).
- Import von Twitch-Analytics-Exporten für den Growth Analyst. Braucht eine echte
  Beispieldatei, weil das Format nicht verifiziert ist.
- **TikTok-Untertitel für Clip-Exporte** (vom Nutzer beschlossen; umsetzen erst nach dem
  echten Test des Clip Hunters):
  - Wort-für-Wort-Untertitel per Whisper, lokal und mit Zeitstempel pro Wort.
  - Beim Hochformat-Export mit FFmpeg eingebrannt: große fette Schrift (z. B. Anton aus
    `fonts/`), 2–4 Wörter gleichzeitig, das aktive Wort farbig hervorgehoben.
  - Zusätzlich als Textdatei (z. B. `.srt`/`.ass`), um sie zu korrigieren und mit einem
    Befehl neu zu rendern.
  - Eigene Wortliste (Kanalname, Spielbegriffe) für bessere Erkennung.
