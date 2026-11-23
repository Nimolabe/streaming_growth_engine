# Bestandsaufnahme der KI-Agenten (Stand 23.11.2026)

Ehrliche Bestandsaufnahme von allem unter `agents/`: Was tut jedes Modul wirklich, woher stammt es,
was bringt es einem kleinen Streamer, was ist doppelt und was fehlt?
Dieses Dokument **ändert keinen Code**. Alle Entscheidungen am Ende trifft der Nutzer.

## So wurde geprüft

- Den Code jedes Moduls gelesen und die Git-Historie jeder Datei angesehen.
- Jedes Modul am 23.11.2026 lokal **wirklich aufgerufen**, über die API (`TestClient`) oder die
  Kommandozeile. Die Beispielausgaben unten stammen aus diesen Aufrufen und sind nur gekürzt.
- Eingabedaten waren **nachgebaut**: ein selbst erzeugtes 3-Minuten-Testvideo (Rauschen mit
  zwei lauten Stellen und einem weißen Bild), nachgebaute Chat-Verläufe aus
  `tests/chat_fixtures.py`, nachgebaute Twitch-Messungen und die Beispiel-Dateien unter
  `agents/examples/`.
- **Nicht** geprüft: echte Twitch-API, echte Sprachmodelle, echte VODs (siehe Schluss).
- Alle 407 Python-Tests laufen grün. Das sagt etwas über die Stabilität, nicht über den Nutzen.

Als Maßstab dient ein **kleiner Streamer mit 0–20 Zuschauern**, oft 0–3 aktiven Chattern.

## Kurzfassung

- **Wirklich nützlich für kleine Streamer:** der **Kategorie-Check** (konkrete Zahlen wie
  „mit 3 Zuschauern Platz 23 statt Platz 219“). Er braucht aber eine Twitch-App und die
  Kommandozeile und ist gegen die echte Twitch-API noch nicht getestet.
- **Technisch stark, aber für die Zielgruppe nur halb passend:** der **Clip Hunter v4**. Seine
  Stärke (Chat-Reaktionen) braucht mindestens 4 verschiedene Chatter in einem Moment. Bei
  kleinen Kanälen fällt er auf reine Lautstärke zurück.
- **Content Strategist v3:** sauber gebaut und ehrlich formuliert, aber die Ideen sind meist
  **Vorlagen mit eingesetztem Spielnamen**. Konkrete Ideen gibt es nur für Valorant, Minecraft
  und Fortnite. Er nutzt den Kategorie-Check nicht.
- **Wochenplaner:** sehr einfach, verteilt nur Minuten (70/30) auf „Tag 1–7“, ohne Wochentage,
  Uhrzeiten oder Inhalte.
- **Growth Analyst** (Creator Intelligence): vorsichtig und korrekt gerechnet, aber **nur auf
  Englisch**. Er braucht vier Wochen Zahlen per Hand, und bei 3–5 Zuschauern meldet er schon
  einen Unterschied von einem Zuschauer als „hohe Priorität“.
- **Altlasten:** Clip Intelligence v1/v2, die Prüfliste v3, `clip_evaluation`, der
  Content-Strategist-v2-Empfehler und `llm/` stammen aus der ChatGPT-Zeit. Sie werden nur noch
  von Tests und der lokalen API benutzt und überschneiden sich mit dem Clip Hunter bzw. v3.
- **Die Website nutzt keinen einzigen Agenten.** Es gibt nur die Clip-Hunter-Kachel mit
  Warteliste (Text) auf der Startseite.

## Übersicht

Zeilen = Python-Zeilen ohne Tests. „#9“ = mit PR #9 aus `streaming_ai_agents` übernommen
(ChatGPT-Zeit). „neu“ = in diesem Repo neu gebaut.

| Modul | Agent | Herkunft | Zeilen | Aufruf | Tests | Datenquelle |
| --- | --- | --- | ---: | --- | ---: | --- |
| `agents/v3_recommender.py`, `v3_contracts.py`, `v3_game_knowledge.py` | Content Strategist v3 | #9 | 631 | API `/content/strategy` | 35 | fest kodiert + Nutzereingabe |
| `agents/v2_catalog.py` | Formatkatalog (26 Formate) | #9 | 506 | von v3 genutzt | – | fest kodiert |
| `agents/v2_recommender.py`, `v2_contracts.py` | Content Strategist v2 | #9 | 226 | nur `classify_game` von v3; `generate_strategy` nur Tests | 14 | fest kodiert + Nutzereingabe |
| `agents/weekly_planner.py` (+ `contracts.py`) | Wochenplaner | #9 | 157 | API `/content/weekly-plan` | 6 | Nutzereingabe |
| `category_check/` | Kategorie-Check | neu (#20) | 864 | CLI `measure/suggest/watch/report`, API `/content/category-check` | 41 | **echte Twitch-API** |
| `agents/creator_intelligence*.py` | Growth Analyst v1 | #9 | 279 | API `/growth/analysis` | 30 | Nutzereingabe (Wochenwerte) |
| `agents/creator_strategy*.py` | Growth Analyst v2 (Experiment) | #9 | 371 | API `/growth/strategy` | 25 | Nutzereingabe |
| `agents/creator_strategy_review.py` | Growth Analyst v2 (Auswertung) | #9 | 105 | API `/growth/review` | 15 | Nutzereingabe |
| `agents/clip_intelligence.py`, `_contracts.py`, `clip_export.py`, `clip_cli.py` | Clip Intelligence v1 | #9 | 326 | CLI `clip_cli` | 20 | eigene Aufnahme |
| `agents/clip_intelligence_v2.py`, `_v2_contracts.py` | Clip Intelligence v2 | #9 | 283 | API `/clips/scan` (Upload) | 17 | eigene Aufnahme |
| `agents/clip_review_queue_v3.py` | Prüfliste v3 | #9 | 137 | API `/clips/review-queue` | 8 | Ergebnis von v2 |
| `agents/clip_evaluation.py` | Treffer gegen Markierungen | #9 | 108 | API `/clips/evaluate` | 14 | Nutzereingabe |
| `clip_hunter/` | Clip Hunter v4 | neu (#10, #15, #16) | 3163 | CLI (5 Befehle), API `/clips/chat-moments` | 168 | eigene Aufnahme, Twitch-Chat (IRC), Twitch-API, optional KI |
| `llm/` | KI-Ideen (OpenAI) | #9 | 277 | CLI `llm.cli --live` | 10 | **kostenpflichtige OpenAI-API** |
| `api.py`, `registry.py`, `contracts.py` | Rahmen | #9, angepasst | 282 | – | 4 | – |

**Zur Herkunft:** Alle mit „#9“ markierten Dateien kamen in einem einzigen Commit
(`6d7751a`) und wurden **seitdem nicht mehr geändert**. Ausnahmen sind `api.py` und
`registry.py`, die für den Clip Hunter und den Kategorie-Check erweitert wurden.
„Bereinigt“ hieß bei #9 laut Commit-Text: ganze Endpunkte und Module entfernt (V1-Content-Plan,
V2-Content-Endpunkt, V1-Clip-Upload, Benchmark-, Audit- und Pilot-Module) und alle Pfade auf
`/api/v1/...` vereinheitlicht. Die Logik der übernommenen Module blieb, soweit erkennbar,
unverändert. Ein Vergleich Datei für Datei mit dem alten Repo war hier nicht möglich, weil es
nicht im Zugriff dieser Sitzung liegt.

---

## 1. Content Strategist v3 (mit Katalog aus v2)

**Was es tut:** Aus einem Profil (Spiel, Zielgruppe als Freitext, Erfahrung, Stil, Ziel,
Ø Zuschauer, aktive Chatter, Stunden und Streams pro Woche) wählt es 1–5 von **26 fest
kodierten Formaten** aus. Das Spiel wird einer Gruppe zugeordnet: `tactical`, `sandbox`,
`battle_royale` oder `general`. Die Formate werden mit einem Punktesystem bewertet (z. B.
+28 für passendes Genre, +15 für passenden Stil). Bei wenig Chat werden Formate ausgefiltert,
die einen aktiven Chat brauchen. Ausgabe: Formate mit Ablauf in 3 Schritten, Hook für ein
Kurzvideo, Messgröße und Quellen, dazu eine Mini-Serie mit 3 Folgen und eine Zeitaufteilung
(immer 65 % live, 15 % Vorbereitung, 15 % Schnitt, 5 % Auswertung). Es gibt **keinen**
Netzwerkzugriff und kein Sprachmodell.

**Beispiel** (API, gekürzt):

```json
POST /api/v1/content/strategy
{"game": "Stardew Valley", "audience": "Zuschauer", "language": "de",
 "average_viewers": 4, "active_chatters": 1, "hours_per_week": 8, "streams_per_week": 3}
```
```text
Gruppe: sandbox · Phase: early · Chat: low
[79] Nur eine Mechanik, viele Möglichkeiten · Stardew Valley
     Hook: Wie viel kann man aus nur einer Mechanik machen?
[63] Ein häufiger Baufehler und die Lösung · Stardew Valley
     Hook: Warum funktioniert dieses Bauprojekt nicht?
[59] Welt-Transformation in drei Etappen · Stardew Valley
Serie, Folge 1: „Baseline: Nur eine Mechanik, viele Möglichkeiten · Stardew Valley“
Zeit: 312 min live, 72 Vorbereitung, 72 Schnitt, 24 Auswertung
```

Zum Vergleich Minecraft (eines der 3 Spiele mit eigenen Ideen):

```text
[79] Minecraft: drei Lösungen für dieselbe Redstone-Aufgabe
[63] Minecraft: Warum funktioniert mein Redstone-Aufbau nicht?
[59] Minecraft: vom leeren Gelände zu einem funktionalen Dorfplatz
```

**Herkunft:** ChatGPT-Zeit, mit #9 übernommen, seitdem unverändert.

**Qualität für 0–20 Zuschauer:**

- ✅ Ehrlich: Jede Ausgabe sagt, dass der Wert „keine Wachstumswahrscheinlichkeit“ ist.
  Formate, die einen Chat brauchen, fallen bei wenig Chat heraus. Für Anfänger gibt es
  „Lernfortschritt statt Expertenrolle“.
- ✅ Für **Valorant, Minecraft und Fortnite** sind die Ideen konkret, z. B. „Retake oder Save?
  Eine Valorant-Runde auseinandernehmen“ oder „Von Duelist zu Sentinel“.
- ❌ Für **alle anderen Spiele** steht der Spielname nur hinter einer allgemeinen Vorlage.
  Stardew Valley landet in der Gruppe „sandbox“ und bekommt dadurch Minecraft-Denken
  („Baufehler“, „Bauprojekt“). Hollow Knight, League of Legends und Just Chatting landen in
  „general“ und bekommen z. B. „Mythos aus der Community überprüfen · Just Chatting“ oder
  „Hinter den Kulissen: Ein Stream entsteht · Hollow Knight“.
- ❌ Der Chat-Filter ist lückenhaft. Bei einem einzigen Chatter wird „Mythos aus der Community
  überprüfen“ empfohlen, mit der Messgröße „Qualität der Rückfragen zum Versuchsaufbau“.
  Das Wort „Rückfragen“ fängt der Filter nicht ab, nur Wörter wie „chat“ oder „zuschauer“.
- ❌ Die Mini-Serie ist immer gleich gebaut („Baseline / Verbesserung / Vergleich“ + Formatname).
  Das passt bei manchen Formaten nicht, z. B. „Baseline: Hinter den Kulissen: Ein Stream entsteht“.
- ❌ Kleinere Textfehler durch zusammengesetzte Sätze: „Für Zuschauer auf twitch: …“
  (Plattform klein geschrieben).
- ❌ Die Hebel, die für kleine Kanäle am meisten zählen, kommen nicht vor: Kategorie,
  Uhrzeit, Stream-Titel und Tags. Genau das misst der Kategorie-Check, aber die beiden sind
  nicht verbunden.
- Unerreichbare Daten: Für Valorant gibt es eine Idee zu `team-communication`. Dieses Format
  gehört aber zur Gruppe `battle_royale` und wird für Valorant (`tactical`) nie ausgewählt.

**Content Strategist v2 (`v2_recommender.py`):** der Vorgänger mit fast gleicher Logik.
Davon wird nur noch `classify_game()` von v3 genutzt. `generate_strategy()` und
`ContentStrategyV2` werden nur noch von `tests/test_content_strategy_v2.py` aufgerufen.

## 2. Wochenplaner (`weekly_planner.py`)

**Was es tut:** Aus Plattform, Kategorie, Zielgruppe, Wochenstunden, Stream-Tagen und Ziel
verteilt es die Zeit: 70 % gleichmäßig auf die Stream-Tage, 30 % auf Vorbereitung (45 %),
einen Highlight-Clip (35 %) und den Wochenrückblick (20 %). Es gibt keine Datenquelle außer der
Eingabe.

**Beispiel:**

```json
POST /api/v1/content/weekly-plan
{"platform": "Twitch", "category": "Stardew Valley", "audience": "gemütliche Zuschauer",
 "language": "de", "weekly_hours": 8, "stream_days": 3, "primary_goal": "discovery"}
```
```text
Tag 1 stream       112 min  Stardew Valley live auf Twitch – Schwerpunkt: Neue Zuschauer
                            durch kurze Highlights erreichen. Plane einen interaktiven Teil …
Tag 2 stream       112 min  (gleicher Text)
Tag 3 stream       112 min  (gleicher Text)
Tag 4 preparation   64 min  Themen und Stream-Titel vorbereiten
Tag 5 clip          50 min  Einen kurzen Highlight-Clip erstellen
Tag 6 review        30 min  Die Woche auswerten
```

**Herkunft:** ChatGPT-Zeit, mit #9 übernommen, unverändert.

**Qualität für 0–20 Zuschauer:** gering.

- Jeder Stream-Tag hat denselben Text. Es gibt keine Wochentage und keine Uhrzeiten.
- Die Vorbereitung liegt **nach** den Streams (Tag 4).
- Mit 7 Stream-Tagen landen Vorbereitung, Clip und Rückblick alle zusätzlich auf Tag 7
  (Beispiel: 6 h, 7 Tage → 7 × 36 min Stream, dazu am Tag 7 noch 48 + 37 + 23 min).
- „Plane einen interaktiven Teil“ wird auch dann geraten, wenn niemand chattet. Das Modell
  kennt keine Zuschauerzahl.
- Es nutzt weder die Formate aus v3 noch den Kategorie-Check.

## 3. Kategorie-Check (`category_check/`)

**Was es tut:** Es misst über die Twitch-API, wie viele Kanäle in einer Kategorie und Sprache
live sind und wie viele Zuschauer sie haben. Gespeichert werden nur Zuschauerzahlen (JSONL).
Daraus berechnet es: Live-Kanäle, Publikum, Median pro Kanal, Anteil der Top 3, den **eigenen
Platz** mit den eigenen Zuschauern, eine Einschätzung (bis Platz 15 gut, bis 40 machbar,
sonst schwer, unter 25 Zuschauern gesamt „wenig Publikum“) und die **besten 2-Stunden-Blöcke**
in Ortszeit (sortiert nach Publikum pro Platz). Die API wertet nur aus; gemessen wird mit
der Kommandozeile.

**Beispiel** (API mit nachgebauten Messungen, 2 Tage, je 14 und 19 Uhr):

```json
POST /api/v1/content/category-check
{"snapshots": [... 8 Messungen ...], "own_viewers": 3, "utc_offset_minutes": 60}
```
```text
Stardew Valley  Kanäle 38   Publikum 561   Platz 23  → Machbar: Mit 3 Zuschauern etwa Platz 23
                – ein Titel, der neugierig macht, hilft.
                beste Zeiten: Di 14–16 Uhr (Platz 11), Mo 14–16 Uhr (Platz 12), Di 18–20 Uhr (Platz 25)
Minecraft       Kanäle 424  Publikum 8932  Platz 219 → Schwer sichtbar: Mit 3 Zuschauern Platz 219.
                Eher eine kleinere Kategorie oder eine andere Uhrzeit wählen.
```

Kommandozeile (braucht `TWITCH_CLIENT_ID`/`TWITCH_CLIENT_SECRET`, hier **nicht** ausgeführt):
`python -m streaming_agents.category_check measure "Minecraft" "Stardew Valley" --out messungen.jsonl`,
danach `report messungen.jsonl --viewers 3 --window 16-24 --html bericht.html`.

**Herkunft:** neu gebaut (PR #20).

**Qualität für 0–20 Zuschauer:** am höchsten von allen Modulen. Die Ausgabe ist konkret,
beruht auf echten Zahlen und beantwortet eine Frage, die kleine Streamer wirklich haben
(„Werde ich in dieser Kategorie überhaupt gesehen?“).

Grenzen:

- Für die besten Zeiten muss `watch` eine Woche lang laufen, der Rechner also an sein.
- Gegen die echte Twitch-API noch nicht getestet. Die Twitch-App fehlt noch (CLAUDE.md, Abschnitt 7).
- Der Platz ist eine Näherung, weil Twitch Listen auch personalisiert sortiert. Das steht
  in der Ausgabe.
- Nur Kommandozeile, keine Website.

## 4. Growth Analyst (Creator Intelligence v1, Strategie v2, Auswertung)

**Was es tut:**

- **v1 `/growth/analysis`:** nimmt 4–26 aufeinanderfolgende Wochen mit von Hand eingetragenen
  Werten (Stream-Minuten, Ø Zuschauer, eindeutige Zuschauer, Follows, Rückkehrer, Clips,
  Clip-Aufrufe). Es vergleicht die erste mit der zweiten Hälfte und leitet Hinweise ab
  (z. B. ab −15 % Ø Zuschauer: `viewer_decline`).
- **v2 `/growth/strategy`:** dieselben Eingaben plus „habe Aufnahmen / kann schneiden /
  sehe Stream-Zusammenfassungen“. Es wählt **eines von 9 fest kodierten Experimenten**, das ins
  Zeitbudget passt.
- **Auswertung `/growth/review`:** vergleicht 2–8 Wochenwerte vor und nach dem Experiment
  und beschreibt die Veränderung, ausdrücklich ohne Ursachenbehauptung.

**Beispiel** (`examples/creator_intelligence_v1_request.json`: Valorant, Ø 4, 5, 4, 3 Zuschauer):

```text
average_viewers  4,46 → 3,57  (−20 %)  down
follows          3,5  → 2,0   (−43 %)  down
Hinweise:
 [high] viewer_decline: "Stream-minute-weighted average viewers decreased by 20% between the halves."
        Aktion: "Compare similar days, categories and stream lengths; test one change at a time."
 [high] no_clips: "No clips were recorded as published in the recent reporting period."
        Aktion: "Try one or two original short clips per week from already recorded streams."
```

Strategie (`examples/creator_intelligence_v2_strategy.json`) → `start_clip_experiment`:
„Try a small, original short-form discovery experiment“ mit 3 Schritten und 45 min pro Woche.
Auswertung (`examples/creator_intelligence_v2_review.json`, Clip-Aufrufe 50/55 → 62/61) →
`observed_increase`, +17,1 %, „This is descriptive, not a causal claim“.

**Herkunft:** ChatGPT-Zeit, mit #9 übernommen, unverändert.

**Qualität für 0–20 Zuschauer:**

- ✅ Die Rechnung ist sauber: nach Stream-Minuten gewichtet, mit Prüfungen (Rückkehrer
  höchstens so viele wie eindeutige Zuschauer, Wochen genau 7 Tage auseinander). Die
  Aussagen sind sehr vorsichtig formuliert.
- ❌ **Nur Englisch.** Es gibt kein Sprachfeld; alle Texte sind fest auf Englisch.
- ❌ Die Eingabe ist aufwendig: 4 Wochen × 7 Werte von Hand aus dem Twitch-Dashboard.
- ❌ Bei kleinen Zahlen ist es Rauschen: Ein Zuschauer weniger (4,5 → 3,6) wird als
  „hohe Priorität“ gemeldet. Der Hinweis „weniger als 8 Wochen“ steht nur in den Datennotizen.
- ❌ Die Aktionen sind allgemein („Compare similar days …“). Einen Bezug zu Spiel, Kategorie
  oder Uhrzeit gibt es nicht.
- Brauchbar ist der Gedanke „ein Experiment, ins Zeitbudget passend, danach messen“.

## 5. Clip Intelligence v1 und v2, Prüfliste v3, Treffer-Auswertung

**Was es tut:**

- **v1** (`clip_intelligence.py`, CLI `clip_cli`): findet in einer eigenen Aufnahme
  (WAV oder Video über FFmpeg, **höchstens 1 Stunde**) Stellen mit anhaltend höherer
  Lautstärke. Optional schneidet `clip_export.py` sie als MP4.
- **v2** (`clip_intelligence_v2.py`, API `/clips/scan` als Upload, **höchstens 15 min / 100 MB**):
  Lautstärke plus große Bildwechsel.
- **Prüfliste v3** (`/clips/review-queue`): mischt die Kandidaten aus v2 mit zufällig gewählten
  Kontroll-Stellen zu einer „verblindeten“ Liste für menschliche Prüfer.
- **Treffer-Auswertung** (`/clips/evaluate`): vergleicht vorgeschlagene Zeitpunkte mit
  menschlichen Markierungen (Precision, Recall, F1).

**Beispiel** (Testvideo, 3 min, laut bei 60 s und 130 s, weißes Bild bei 100–104 s):

```text
python -m streaming_agents.clip_cli --input test.mp4 --json v1.json --max-candidates 3
  52,5–73,5 s  Spitze 61,5 s  audio_activity_score 61  "Sustained audio-level increase; …"
  122,2–143,2 s Spitze 131,2 s audio_activity_score 61

POST /api/v1/clips/scan  (gleiches Video)
  91,0–112,0 s  visual_change  activity_score 96   ← weißes Bild liegt vorn
  52,5–73,5 s   audio_peak     activity_score 61
  122,2–143,2 s audio_peak     activity_score 61

POST /api/v1/clips/review-queue → 5 Aufgaben (3 Kandidaten + 2 Kontrollen, gemischt):
  "Is this segment independently worth clipping? What context is needed?"

POST /api/v1/clips/evaluate (Markierungen bei 61 s und 131 s)
  precision 0,67 · recall 1,0 · f1 0,8
```

**Herkunft:** alle ChatGPT-Zeit, mit #9 übernommen, unverändert.

**Qualität für 0–20 Zuschauer:** gering, und durch den Clip Hunter überholt.

- **Nur Englisch.**
- Die Längengrenzen (1 h bzw. 15 min) passen nicht zu echten Streams von 2–4 Stunden.
  Der Clip Hunter verarbeitet mehrstündige VODs.
- Bei v2 bekommt ein großer Bildwechsel den höchsten Wert (96 gegen 61). Ein Szenenwechsel in
  OBS oder ein Overlay landet also vor echten Reaktionen.
- Prüfliste und Treffer-Auswertung sind Forschungswerkzeuge für die Entwicklung, kein
  Streamer-Nutzen.

## 6. Clip Hunter v4 (`clip_hunter/`)

**Was es tut:** Es schneidet den Twitch-Chat live mit (`record-chat`, anonym über IRC, nur
lesen). Nach dem Stream wertet es VOD und/oder Chat aus (`analyze`):

- Chat-Ausschläge mit Emote-Arten (lustig, Hype, Schock, Fail, Spannung), Filter für Subs,
  Raids, Bots und Befehle;
- plötzliche Lautstärke-Spitzen gegenüber den Sekunden davor;
- Zusammenführung, HTML-Bericht und Export als MP4, auf Wunsch im Hochformat 9:16;
- optional eine KI-Stufe (lokal über Ollama, Whisper-Transkript), die die besten 8 Kandidaten
  prüft und Schnitt, Titel und Hook schreibt.

Dazu kommen der Abgleich mit Zuschauer-Clips über die Twitch-API (`viewer-clips`, `evaluate`)
und `benchmark` gegen den LIGHTOR-Datensatz.

**Beispiele:**

```text
python -m streaming_agents.clip_hunter analyze --video test.mp4 --max 5 --out hunt.json
Modus: audio · Chat-Momente: 0 · Audio-Spitzen: 2
  1   0:00:40   0:01:10  laut   90  medium
  2   0:01:50   0:02:20  laut   90  medium
```

Nur Chat, nachgebaute Verläufe (`tests/chat_fixtures.py`, 1 Stunde):

| Kanal | Nachrichten | Chat-Momente |
| --- | ---: | ---: |
| 150 Chatter, 1,2 Nachr./s, zwei Ausbrüche (40 bzw. 30 Leute) | 4.415 | 2 (bei 578 s „funny“, 1.779 s „hype“) |
| 5 Chatter, 0,03 Nachr./s, Ausbrüche mit 3 bzw. 2 Leuten | 133 | **0** |
| 2 Chatter, 0,01 Nachr./s | 45 | **0** |

Beim kleinen Kanal meldet das Ergebnis `chat.level: "low"` und den Hinweis
„Ohne aktiven Chat beruht die Auswahl fast nur auf Lautstärke – mehr Fehlalarme.“

**Herkunft:** neu gebaut (#10, kalibriert in #15, KI-Stufe #16).

**Qualität für 0–20 Zuschauer:**

- ✅ Bestes Modul technisch: mehrstündige VODs, Hochformat-Export, verständlicher deutscher
  Bericht, ehrliche Grenzen. An 100 LIGHTOR-Streams enthalten 67 % der Top 10 ein Highlight
  (Zufall: 17 %).
- ❌ Die Messung lief an **großen** Dota- und LoL-Streams. Ein Chat-Moment braucht
  standardmäßig **mindestens 4 verschiedene Chatter** (`chat_min_chatters=4`). Bei 0–20
  Zuschauern kommt das selten vor. Dann bleibt nur die Lautstärke, und genau dieser Teil ist
  **an echten VODs noch nicht gemessen** (CLAUDE.md, Abschnitt 8).
- ❌ Die KI-Stufe, die bei leisem Chat am meisten helfen könnte (Whisper hört, was gesagt
  wurde), ist nur mit einem nachgebauten Server getestet.
- ❌ Nur Kommandozeile mit FFmpeg. Auf der Website gibt es nur die Kachel mit Warteliste.

## 7. `llm/` (KI-Ideen über OpenAI)

**Was es tut:** Aus Plattform, Kategorie und Zielgruppe lässt es ein OpenAI-Modell
(Responses API, strenges JSON-Schema) **genau 3 Ideen** (Titel + Erklärung) schreiben. Es
gibt eine Kostenbremse über geschätzte Preise (`SGE_ESTIMATED_MAX_USD`, Standard 0,02 $) und
eine Größengrenze der Eingabe. Aufruf nur über die Kommandozeile und nur mit `--live`.

**Beispiel:**

```text
python -m streaming_agents.llm.cli
No request sent. Add --live to explicitly permit a paid API call.
```

Mit `--live` wurde **nicht** aufgerufen (kostet Geld, kein Schlüssel vorhanden). Es ist
nicht belegt, dass jemals ein echter Aufruf gelaufen ist; die 10 Tests nutzen einen
nachgebauten Anbieter.

**Herkunft:** ChatGPT-Zeit, mit #9 übernommen, unverändert.

**Qualität für 0–20 Zuschauer:** nicht beurteilbar, weil nie echt ausgeführt. Mit nur drei
Eingaben (Plattform, Kategorie, Zielgruppe) sind allgemeine Ideen zu erwarten. Zuschauerzahl,
Zeitbudget, Kategorie-Check und Formatkatalog fließen nicht ein. Das Modul ist mit keinem
anderen Agenten verbunden, und die CLI-Meldungen sind auf Englisch.

## 8. Rahmen (`api.py`, `registry.py`, `contracts.py`)

- `api.py`: lokale FastAPI ohne Anmeldung, 11 Endpunkte unter `/api/v1` plus `/health`, nur für 127.0.0.1
  gedacht.
- `registry.py`: Die Liste der Agenten ist teilweise **veraltet**:
  - „Setup Advisor … covered by the Setup Intelligence Agent (`backend/setup_agent`)“:
    `backend/setup_agent` gibt es auf `main` nicht, nur im geparkten PR #5.
  - „Trend Scout … to reuse the Trend Radar scouts“: Einen „Trend Radar“ gibt es in diesem
    Repo nicht.
- `contracts.py`: `ContentPlanRequest` wird nur noch vom Wochenplaner und von `llm/` genutzt.

---

## Doppelungen und Altlasten

| Thema | Wo | Überschneidung |
| --- | --- | --- |
| **Zeitplanung dreifach** | `weekly_planner` (70/30), `v3_recommender._workload` (65/15/15/5), `creator_strategy._budget` | Drei Aufteilungen des Wochenbudgets mit verschiedenen Regeln, kein gemeinsamer Code. Keine davon kennt Wochentage oder Uhrzeiten. |
| **Content-Empfehler doppelt** | `v2_recommender.generate_strategy` und `v3_recommender` | v3 ersetzt v2. Von v2 wird nur `classify_game` gebraucht. |
| **Spiel-Zuordnung dreifach** | `v2_recommender._GROUPS`, `v3_recommender.GENRE_GAME_MAP`, `v3_game_knowledge.game_key` | Drei Listen für dieselbe Frage „welches Spiel ist das?“. |
| **Lautstärke-Erkennung doppelt** | `clip_intelligence` (v1/v2) und `clip_hunter/audio_signal.py` | Der Clip Hunter kann alles, was v1 kann, und mehr (lange VODs, Spitzen statt Dauerlautstärke). Er nutzt keinen Code aus v1/v2. |
| **Clip-Export doppelt** | `agents/clip_export.py` und `clip_hunter/export.py` | Der Clip Hunter exportiert auch im Hochformat. |
| **Treffer-Messung dreifach** | `agents/clip_evaluation.py`, `clip_hunter/evaluation.py`, `clip_hunter/benchmark.py` | Messung gegen menschliche Markierungen, gegen Zuschauer-Clips und gegen LIGHTOR. |
| **Sprachmodell-Anbindung doppelt** | `llm/` (OpenAI-SDK, kostenpflichtig, `SGE_LLM_*`) und `clip_hunter/ai_stage.py` (jede OpenAI-kompatible Schnittstelle, Standard Ollama lokal, `SGE_CLIP_AI_*`) | Zwei Clients, zwei Sätze Umgebungsvariablen. Der neuere aus `ai_stage` passt besser zur Leitidee „erst kostenlos und lokal“. |

### Wer nutzt was noch?

| Modul | API | CLI | Tests | Website |
| --- | --- | --- | --- | --- |
| Content Strategist v3 | ✅ | – | ✅ | – |
| v2 `generate_strategy` | – | – | ✅ (nur) | – |
| Wochenplaner | ✅ | – | ✅ | – |
| Kategorie-Check | ✅ | ✅ | ✅ | – |
| Growth Analyst (3 Module) | ✅ | – | ✅ | – |
| Clip Intelligence v1 + Export | – | ✅ `clip_cli` | ✅ | – |
| Clip Intelligence v2 | ✅ `/clips/scan` | – | ✅ | – |
| Prüfliste v3 | ✅ | – | ✅ | – |
| `clip_evaluation` | ✅ | – | ✅ | – |
| Clip Hunter v4 | ✅ `/clips/chat-moments` | ✅ | ✅ | nur Kachel + Warteliste |
| `llm/` | – | ✅ (`--live`) | ✅ | – |

Die lokale API hat keine Anmeldung und läuft nirgends; auf der Website ruft **nichts** sie auf.
„Genutzt über die API“ heißt hier also nur: Man kann sie lokal ausprobieren.

## Lücken (was für echten Nutzen fehlt)

1. **Keine Website-Oberfläche** für irgendeinen Agenten. Alles läuft über Kommandozeile oder
   lokale API und setzt Python und FFmpeg voraus. Für die Zielgruppe ist das die größte Hürde.
2. **Konkrete Ideen nur für 3 Spiele** (Valorant 6, Minecraft 4, Fortnite 3 Ideen). Die
   meistgestreamten Kategorien kleiner deutscher Kanäle (Just Chatting, Story-/Indie-Spiele,
   Horror, Cozy Games, LoL, CS2 …) bekommen allgemeine Vorlagen.
3. **Der Wochenplaner nutzt den Kategorie-Check nicht.** Die beste Zeit und die passende
   Kategorie fließen in keinen Plan ein. Es gibt auch keine Wochentage und Uhrzeiten.
4. **Kein Agent kennt Titel und Tags.** Für Kanäle mit 0–20 Zuschauern sind das zusammen mit
   Kategorie und Uhrzeit die wichtigsten Hebel für Sichtbarkeit.
5. **Clip Hunter für kleine Kanäle:** Die Chat-Schwelle (4 Chatter) passt nicht, und der
   Lautstärke-Weg ist an echten VODs nicht gemessen.
6. **Growth Analyst nur auf Englisch und nur mit Handeingabe.** Ein Import von
   Twitch-Analytics-Exporten steht auf der Ideenliste, braucht aber eine echte Beispieldatei.
7. **Echte Tests fehlen:** Twitch-API (Kategorie-Check, Zuschauer-Clips), Sprachmodell
   (KI-Stufe, `llm/`), Audio an echten VODs.
8. **Trend Scout** ist nur ein Eintrag in `registry.py`. Die Messungen des Kategorie-Checks
   wären die Grundlage.

---

## Empfehlung: behalten / zusammenlegen / entfernen

Nur ein Vorschlag. Umgesetzt wird erst nach Entscheidung des Nutzers, in eigenen PRs.

| Modul | Vorschlag | Begründung |
| --- | --- | --- |
| Clip Hunter v4 | **behalten** | Bestes und neuestes Modul; als Nächstes an kleinen echten Streams prüfen (Audio, Chat-Schwelle). |
| Kategorie-Check | **behalten** | Konkretester Nutzen für kleine Streamer; Grundlage für Content Strategist und Trend Scout. |
| Content Strategist v3 + `v2_catalog` + `v3_game_knowledge` | **behalten, umbauen** | Der Katalog und die Chat-Filter sind brauchbar; erweitern um Genres und verbinden mit Kategorie-Check und Wochenplan (siehe Varianten). |
| `v2_recommender` + `v2_contracts` | **entfernen** (nur `classify_game` nach v3 verschieben) | Nur noch von Tests genutzt; v3 ersetzt v2. |
| Wochenplaner | **zusammenlegen** mit dem Content Strategist | Eigenständig zu dünn; dritte Zeitaufteilung neben v3 und Growth Analyst. |
| Growth Analyst v1 + v2 + Auswertung | **behalten, aber parken** | Rechnung solide, aber nur Englisch und Handeingabe. Erst weiterbauen, wenn klar ist, woher die Daten kommen (Export-Datei oder Twitch-Login). Strategie und Auswertung könnten dann ein Modul werden. |
| Clip Intelligence v1 + `clip_export` + `clip_cli` | **entfernen** | Der Clip Hunter kann alles davon besser; nur Englisch, höchstens 1 h. |
| Clip Intelligence v2 (`/clips/scan`) | **entfernen** | Höchstens 15 min, Bildwechsel führen zu Fehlalarmen (Szenenwechsel). Die Idee „Bildwechsel als Signal“ auf die Ideenliste setzen. |
| Prüfliste v3 | **entfernen** | Forschungswerkzeug nur für v2-Ergebnisse. |
| `clip_evaluation` | **entfernen** oder in `clip_hunter/evaluation.py` aufgehen lassen | Der Clip Hunter misst bereits gegen Zuschauer-Clips und LIGHTOR. |
| `llm/` | **zusammenlegen** mit dem Client aus `clip_hunter/ai_stage.py` | Ein gemeinsamer, OpenAI-kompatibler Client (Standard: lokal/Ollama) für alle Agenten statt zwei. |
| `registry.py` | **aktualisieren** | Hinweise auf `backend/setup_agent` und „Trend Radar“ stimmen nicht. |

Folgen beim Entfernen: Mit Clip Intelligence v1/v2, Prüfliste, `clip_evaluation` und
v2-Empfehler fielen 3 API-Endpunkte (`/clips/scan`, `/clips/review-queue`, `/clips/evaluate`),
die CLI `clip_cli`, rund 1.100 Zeilen Code und **73 Tests** weg
(20 + 17 + 8 + 14 + 14). README, `architecture.md` und die Entwicklungsnotizen unter
`docs/entwicklung/` müssten angepasst werden.

---

## Vorschlag: ein besserer Content Strategist (nicht gebaut)

Ziel für 0–20 Zuschauer: **„Was streame ich diese Woche, wann, in welcher Kategorie, mit welchem
Titel, und welcher Clip kommt danach?“** Allen Varianten gemeinsam:

- **Eingaben:** Spiele oder Kategorien, die man streamen möchte (1–5); verfügbare Zeitfenster
  (z. B. „Mo, Mi 18–22 Uhr, Sa 14–20 Uhr“); Ø Zuschauer und aktive Chatter; Ziel; Sprache.
- **Ausgaben:** ein Wochenplan mit **echten Wochentagen und Uhrzeiten**; je Stream Kategorie,
  Format, Vorschlag für Titel und Tags; Vorbereitung vor dem Stream; ein Clip danach; eine
  Messgröße für die nächste Woche.

### Variante A: lokal und regelbasiert, aber verbunden (klein)

- Kategorie-Check-Messungen (falls vorhanden) wählen Kategorie und Zeitfenster.
- Der vorhandene Formatkatalog wählt das Format; neue Genre-Gruppen (z. B. Story/Indie, Cozy,
  Horror, Just Chatting, MOBA, Shooter) mit je 3–5 konkreten Ideen.
- Wochenplaner und `_workload` werden ein Modul; die Vorbereitung liegt vor dem Stream.
- Titel und Tags kommen aus Vorlagen pro Format.
- Datenquellen: Nutzereingabe, fest kodierter Katalog, optional die eigenen
  Kategorie-Check-Messungen.
- Kein Sprachmodell, keine Kosten.
- **Aufwand:** etwa 3–5 Arbeitstage, davon der größte Teil für gut geschriebene Inhalte
  für die neuen Genres (DE und EN).

### Variante B: A plus KI-Texte, lokal zuerst (mittel)

- Wie A. Zusätzlich schreibt ein Sprachmodell zu jedem Stream einen konkreten Titel, 2–3 Tags
  und einen Hook für das passende Spiel. Es bekommt nur die bereits gewählten Daten (Format,
  Spiel, Zeit, Zuschauerzahl), keine freie Aufgabe.
- Ein gemeinsamer Client mit der KI-Stufe des Clip Hunters (Standard Ollama lokal, gehostet
  nur per Konfiguration). Die Antwort wird streng geprüft; ohne Modell gibt es die Vorlagen
  aus A.
- Optional: Ergebnisse des Clip Hunters vom letzten Stream fließen als „Clip der Woche“ ein.
- **Aufwand:** etwa 1,5–2 Wochen (A plus etwa 4–6 Tage). Risiko: Die Qualität eines
  7B-Modells auf Deutsch ist ungeprüft und muss mit echten Beispielen bewertet werden.

### Variante C: B auf der Website, mit Backend (groß)

- Eine Seite „Content-Plan“ auf der Website: Formular, Plan als Ansicht, Speichern im Profil
  (Firebase, neuer Datenbank-Bereich → Regeln neu veröffentlichen).
- Ein Backend misst die Kategorien regelmäßig auf dem Server (Twitch-Secret bleibt dort) und
  ruft das Sprachmodell auf. Dazu gehören Firebase-Anmeldung und Limits pro Nutzer.
- Optional: Twitch-Login für eigene Kanalzahlen. Welche Werte die Twitch-API dafür liefert,
  ist **nicht geprüft**.
- **Aufwand:** mehrere Wochen. Hängt an der **Hosting-Entscheidung** (Roadmap Schritt 4),
  an Impressum und Datenschutzerklärung und an laufenden Kosten (Server, ggf. Modell).

Sinnvolle Reihenfolge, falls gewünscht: A → (echte Tests mit Twitch-App) → B → C.

---

## Fragen, die der Nutzer entscheiden muss

1. **Aufräumen:** Sollen Clip Intelligence v1/v2, Prüfliste v3, `clip_evaluation` und der
   v2-Empfehler entfernt werden (73 Tests, 3 Endpunkte, `clip_cli`)? Oder erst einmal nur als
   „veraltet“ markieren?
2. **Content Strategist:** Variante A, B oder C? Oder zuerst etwas anderes?
3. **Genres:** Für welche Spiele oder Genres soll es zuerst konkrete Ideen geben? Gibt es
   Kanäle (eigene oder von Freunden), deren Kategorien als Maßstab dienen sollen?
4. **Sprachmodell:** Bleibt es bei „lokal zuerst“ (Ollama), oder ist ein gehosteter Anbieter
   mit Budget in Ordnung? (Offen seit Roadmap Schritt 3.)
5. **Growth Analyst:** Parken, ins Deutsche übersetzen oder entfernen? Gibt es eine echte
   Export-Datei aus Twitch Analytics als Beispiel?
6. **Website-Oberfläche:** Ab wann soll ein Agent auf der Website erscheinen, und welcher
   zuerst (Kategorie-Check wäre der naheliegende)? Das hängt an der Hosting-Entscheidung.
7. **Twitch-App:** Wann wird sie angelegt? Ohne sie lassen sich Kategorie-Check und
   Zuschauer-Clip-Abgleich nicht echt testen.
8. **Clip Hunter für kleine Kanäle:** Soll er an einem eigenen kleinen Stream (VOD + Chat)
   gemessen werden, bevor die Chat-Schwelle oder der Audio-Teil angepasst wird?

## Nicht getestet (in dieser Bestandsaufnahme)

- Echte Twitch-API: Kategorie-Messungen und Zuschauer-Clips nur mit nachgebauten Daten.
- Echte Sprachmodelle: weder `llm/ --live` noch die KI-Stufe des Clip Hunters mit Ollama.
- Echte VODs: Clip Hunter, Clip Intelligence v1/v2 nur mit einem 3-minütigen Testvideo.
- Die Aufwandsschätzungen sind grob und beruhen auf der Größe vergleichbarer bisheriger PRs.
