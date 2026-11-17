# Clip Hunter v4 – Chat + Audio

Der Clip Hunter findet in einem Stream die Stellen, die sich als Clip für TikTok,
YouTube Shorts oder Reels lohnen könnten. Er arbeitet **komplett lokal und kostenlos**.
Optional prüft eine [KI-Stufe](#ki-stufe-optional) die besten Kandidaten, legt den Schnitt
fest und schreibt Titel und Hook – standardmäßig ebenfalls lokal und kostenlos.

## Wie er entscheidet

| Signal | Was gemessen wird | Wofür es gut ist |
| --- | --- | --- |
| **Chat** | Wie viele *verschiedene* Chatter in wenigen Sekunden schreiben, verglichen mit dem normalen Tempo der letzten 2 Minuten. Dazu kommt die Art der Reaktion: lustig (KEKW, LUL, „hahaha“), Hype (Pog, W, „LETS GO“), Schock (WHAT, „??“), Fail (L, Sadge, F) oder Spannung (monkaS) | *Dass* etwas passiert ist und *was* |
| **Audio** | Plötzlicher Anstieg der Lautstärke gegenüber den Sekunden davor, also nicht einfach die lautesten Stellen | Den *genauen Zeitpunkt* |

Aussortiert oder abgewertet werden:

- Nachrichten von Bots und Befehle mit `!`, etwa Gewinnspiele
- Nachrichten des Streamers selbst
- ein einzelner Nutzer, der spammt (er zählt nur einmal)
- Chat-Wellen, die nur auf Subs, Geschenk-Subs, Bits oder Raids reagieren
- Wiederholungen beim Raid („KANAL RAID 💜“)

So werden Chat und Audio zusammengeführt:

| Fall | Bewertung |
| --- | --- |
| Chat-Ausschlag **und** Audio-Spitze kurz davor | hoch. Der Zeitpunkt kommt vom Audio, die Art der Reaktion vom Chat |
| Nur Chat-Ausschlag | mittel bis hoch, je nach Stärke. Die Chat-Verzögerung (gemessen etwa 8 s) wird herausgerechnet |
| Nur Audio-Spitze bei aktivem Chat | niedrig: vermutlich Alert-Ton, Musik oder Lärm |
| Nur Audio-Spitze ohne oder mit wenig Chat | Hauptsignal, aber mit mehr Fehlalarmen |

Jeder Kandidat ist standardmäßig ein Fenster von 20 s vor bis 10 s nach dem Höhepunkt,
damit der Aufbau eines Witzes oder Spielzugs mit drin ist.

## Einrichtung (einmalig)

1. **Python 3.11 oder neuer** und die Agenten installieren (siehe [README](../README.md)).
2. **FFmpeg** installieren. Unter Windows in PowerShell: `winget install Gyan.FFmpeg`.
   Danach ein neues Konsolenfenster öffnen und mit `ffmpeg -version` prüfen.
3. Optional die **Twitch-Entwickler-App** anlegen. Damit holt der Clip Hunter die
   VOD-Startzeit und die Zuschauer-Clips automatisch:
   - Auf <https://dev.twitch.tv/console> anmelden und unter *Applications* eine App registrieren.
     Twitch verlangt dafür eine aktivierte Zwei-Faktor-Anmeldung.
     Als OAuth-Redirect `http://localhost` eintragen, als Kategorie z. B. *Analytics Tool*.
   - Die **Client-ID** kopieren und ein **Client-Secret** erzeugen.
   - Beides vor jeder Nutzung in der Konsole setzen, niemals in Dateien im Repo:
     ```powershell
     $env:TWITCH_CLIENT_ID = "deine-client-id"
     $env:TWITCH_CLIENT_SECRET = "dein-secret"
     ```

## Erster echter Test: Schritt für Schritt

Am besten mit einem eigenen Stream, zu dem ihr das VOD habt.

**1. Vor dem Stream** ein zweites PowerShell-Fenster öffnen, in den Ordner `agents` wechseln
und den Mitschnitt starten:

```powershell
python -m streaming_agents.clip_hunter record-chat deinkanal --out streams\2026-11-14_chat.jsonl
```

Der Mitschnitt liest den öffentlichen Chat anonym mit und schreibt nichts in den Chat.
Er speichert laufend und verbindet sich bei Abbrüchen selbst neu. Nach dem Stream beendet
ihr ihn mit **Strg+C**.

**2. Das VOD besorgen.** Entweder ladet ihr es im Twitch-Creator-Dashboard im
*Video-Produzenten* über das Menü (⋮) des Videos herunter, oder ihr nehmt eine lokale
OBS-Aufnahme.

**3. Die Startzeit festlegen.** Chat und Video müssen auf dieselbe Uhr gebracht werden:

- Mit Twitch-App: `--twitch-video <VOD-ID oder Link>`. Die Startzeit kommt dann direkt von Twitch.
- Ohne App: `--vod-start 2026-11-14T18:00:05+01:00`, also die Uhrzeit, zu der das Video beginnt.
  Bei OBS-Aufnahmen steht sie meist im Dateinamen.
- Ohne Angabe nimmt der Clip Hunter den Beginn des Chat-Mitschnitts und weist im
  Ergebnis darauf hin.

**4. Auswerten:**

```powershell
python -m streaming_agents.clip_hunter analyze `
  --video streams\2026-11-14.mp4 --chat streams\2026-11-14_chat.jsonl `
  --twitch-video 2345678901 --report streams\bericht.html `
  --export-dir streams\clips --vertical --out streams\ergebnis.json
```

Danach `bericht.html` im Browser öffnen. Ihr seht eine Zeitleiste, alle Kandidaten mit
Begründung und Chat-Auszug, Links an die richtige Stelle im VOD und die exportierten
Hochformat-Clips. Ein vierstündiges VOD braucht je nach Rechner einige Minuten.

**5. Mit den Zuschauer-Clips vergleichen** (Twitch-App nötig): An Schritt 4 hängt ihr
`--compare` an. Der Clip Hunter lädt dann alle Clips, die Zuschauer aus diesem VOD
erstellt haben, und zeigt:

- **Abdeckung:** wie viele der Momente, die die Community geclippt hat, gefunden wurden.
  Sie wird auch nach Aufrufen gewichtet.
- **Trefferquote:** wie viele der Top-10-Kandidaten einen solchen Moment treffen.

Ein guter Moment, den niemand geclippt hat, zählt dabei als Fehlalarm. Die Trefferquote
ist also eher zu streng.

Ohne Video geht es auch: `--chat` allein findet die Momente nur aus dem Chat.
`--video` allein nutzt nur das Audio.

## Messung an echten Streams

Die Chat-Erkennung ist an **111 echten Twitch-Streams** gemessen und eingestellt. Grundlage
ist der öffentliche Forschungsdatensatz **LIGHTOR** der Simon Fraser University: Chats von
Dota-2- und League-of-Legends-Streams, in denen Menschen die Highlights als Zeitintervalle
markiert haben.

**Vorgehen:**
- 61 Streams dienten zum Einstellen der Schwellen.
- 50 weitere wurden vorher beiseitegelegt und nur zum Prüfen verwendet.
- Die folgenden Zahlen gelten für alle 100 Test-Streams und nur für den Chat, ohne Audio.

| Test-Streams | Clip enthält ein Highlight (Top 10) | Treffer ±5 s (Top 10) | Abdeckung (Top 15) | Zufall | Nachrichten zählen |
| --- | --- | --- | --- | --- | --- |
| Dota 2 (50, ca. 42 Nachr./min) | **63 %** | 52 % | 56 % | 13 % | 47 % |
| LoL-E-Sport (50, ca. 126 Nachr./min) | **72 %** | 64 % | 48 % | 19 % | 67 % |
| zusammen | **67 %** | 58 % | 52 % | 17 % | 57 % |

So sind die Zahlen zu lesen:

- **Etwa zwei von drei vorgeschlagenen Clips enthalten ein markiertes Highlight.** Der Zufall
  schafft 13–19 %.
- Die Markierungen sind unvollständig. Echte, aber nicht markierte Momente zählen hier als
  Fehltreffer, die tatsächliche Quote liegt also eher höher.
- **Gegenüber den früheren Startwerten** gab es Verbesserungen bei mittelgroßen Chats wie
  bei Dota 2: Treffer von 46 % auf 52 %, Abdeckung von 45 % auf 56 %. In sehr großen
  E-Sport-Chats kostet die Einstellung ein paar Prozentpunkte. Weil die Zielgruppe wachsende
  Streamer mit kleineren Chats sind, gilt die Einstellung für mittelgroße Chats.
- Die echte Chat-Verzögerung liegt bei etwa **8 Sekunden**. Sie ist jetzt der Standardwert.
- Die Zahlen gelten **nur für den Chat**. Für die Audio-Spitzen gibt es noch keine echten
  Messdaten, weil der Datensatz keine Videos enthält.

**Selbst nachmessen** (Datensatz liegt nicht im Repository):

```bash
git clone https://github.com/sfu-db/Lightor_Exp
python -m streaming_agents.clip_hunter benchmark --lightor Lightor_Exp --game all --split test
```

Jede Änderung an Schwellen oder Emote-Listen sollte so geprüft werden, bevor sie übernommen wird.

## Kalibrieren für den eigenen Kanal

Die Standardwerte sind an echten Streams eingestellt (siehe oben). Für einen bestimmten Kanal
lassen sie sich mit 2–3 eigenen Streams weiter verfeinern:

| Beobachtung | Stellschraube |
| --- | --- |
| Clips beginnen durchweg zu früh oder zu spät | `--chat-offset` (Sekunden, positiv = Chat später) |
| Der Aufbau fehlt oder es ist zu viel Vorlauf | `--pre-roll` (Standard 20) |
| Die Reaktion wird abgeschnitten | `--post-roll` (Standard 10) |
| Zu viele oder zu wenige Kandidaten | `--max` (Standard 15) |

Weitere Schwellen stehen in `HuntSettings`
([`clip_hunter/models.py`](../streaming_agents/clip_hunter/models.py)), zum Beispiel
`chat_min_z` (Stärke eines Chat-Ausschlags), `audio_min_rise_db` (Mindestanstieg in dB) und
`chat_reaction_lag_seconds`. Am meisten hilft es, mir `ergebnis.json` mit dem Abgleich zu
schicken. Daran lässt sich sehen, welche Schwelle verschoben werden muss.

Die Emote-Listen in [`reactions.py`](../streaming_agents/clip_hunter/reactions.py) sind ein
Startpunkt. Kanal-eigene Emotes, etwa `kanalLOL`, kann man dort ergänzen.

## Datenschutz

- Der Mitschnitt speichert **keine Nutzernamen**. Jede Person bekommt ein Pseudonym,
  dessen Schlüssel zufällig erzeugt und nie gespeichert wird, ist also nicht umkehrbar.
- Gespeichert werden Zeit, Nachrichtentext (öffentlicher Chat) sowie Flags
  (Bot, Mod, Sub, Streamer) und Ereignisarten (Sub, Raid, Bits).
- Nur den eigenen Kanal mitschneiden oder einen, dessen Streamer einverstanden ist.
  Mitschnitte nach der Auswertung löschen, wenn sie nicht mehr gebraucht werden.
- Zugangsdaten für die Twitch-API nur als Umgebungsvariablen setzen. Sie werden nie
  ausgegeben oder gespeichert.

## Dateiformat des Chat-Mitschnitts

JSON Lines. Die erste Zeile ist der Kopf, danach folgt eine Nachricht pro Zeile:

```json
{"format":"sge-chat-log","version":1,"channel":"deinkanal","started_at":1794679205.0,"source":"twitch-irc"}
{"ts":1794679261.512,"user":"3f9a1c0b7d2e","text":"KEKW","subscriber":true}
{"ts":1794679302.004,"user":"a81d44e09c13","kind":"raid"}
```

Ein abgebrochener Mitschnitt bleibt lesbar, denn eine halbe letzte Zeile wird übersprungen.

## Grenzen

- Ohne KI-Stufe versteht er keine Inhalte. Leise Komik ohne Chat-Reaktion und rein
  visuelle Momente können fehlen – auch die KI-Stufe findet keine *neuen* Momente, sie
  prüft nur die gefundenen.
- Bei kleinem oder fehlendem Chat beruht die Auswahl fast nur auf Lautstärke. Dann gibt
  es mehr Fehlalarme, etwa durch Alert-Töne oder Musik.
- Das Hochformat ist ein einfacher Mittenausschnitt. Facecam-Layouts und Untertitel fehlen noch.
- Den Chat vergangener VODs gibt Twitch nicht offiziell heraus. Deshalb muss er **live**
  mitgeschnitten werden.

## KI-Stufe (optional)

Mit `--ai` sieht sich ein Sprachmodell **nur die besten Kandidaten** an (Standard 8,
höchstens 10). Pro Kandidat bekommt es das Fenster ±15 s um den Clip:

- den **Chat-Auszug** (ohne Pseudonyme, ohne Bots und Befehle, höchstens 40 Zeilen),
- mit `--transcribe` zusätzlich das **Transkript** des Streamers, lokal mit Whisper erstellt.

Es antwortet mit: clipwürdig ja/nein, Sicherheit, genauer Schnitt, **Titel**, **Hook**
(erste Texteinblendung), **Caption** und bis zu 5 Hashtags. Clipwürdige Kandidaten
rücken nach vorn, der Export schneidet nach dem KI-Vorschlag, der Bericht zeigt alle Texte.

Die Antwort wird streng geprüft: Der Schnitt bleibt im Fenster und zwischen 12 und 60 s,
Texte werden gekürzt und bereinigt. Chat und Transkript gelten als fremde Daten – das
Modell soll Anweisungen darin ignorieren, und seine Antwort wird nur als Daten verwendet.
Scheitert ein Kandidat (keine gültige Antwort), bleibt er unverändert; ist der Server nicht
erreichbar, läuft die Analyse ohne KI weiter.

### Kostenlos auf dem eigenen Rechner (Standard)

1. **Ollama** installieren: <https://ollama.com> → Download, danach läuft es im Hintergrund.
2. Ein Modell laden (einmalig, etwa 4,7 GB):
   ```powershell
   ollama pull qwen2.5:7b
   ```
   Für schwächere Rechner: `qwen2.5:3b` und `--ai-model qwen2.5:3b`.
3. Optional für Transkripte: `python -m pip install -e ".[whisper]"`. Das Whisper-Modell
   (Standard `small`) wird beim ersten Mal automatisch geladen.
4. Auswerten:
   ```powershell
   python -m streaming_agents.clip_hunter analyze --video vod.mp4 --chat chat.jsonl `
       --twitch-video 2345678901 --ai --transcribe --report bericht.html `
       --export-dir clips --vertical
   ```

Ohne Grafikkarte braucht ein 7B-Modell je Kandidat grob eine halbe bis zwei Minuten.

### Anderer Anbieter (kostet Geld)

Jede OpenAI-kompatible Schnittstelle funktioniert (LM Studio, OpenRouter, OpenAI …).
Einstellung nur über Umgebungsvariablen, nie in Dateien im Repo:

| Variable | Bedeutung | Standard |
| --- | --- | --- |
| `SGE_CLIP_AI_BASE_URL` | Adresse der Schnittstelle (entfernt nur mit `https://`) | `http://localhost:11434/v1` |
| `SGE_CLIP_AI_MODEL` | Modellname (oder `--ai-model`) | `qwen2.5:7b` |
| `SGE_CLIP_AI_API_KEY` | Schlüssel, falls der Anbieter einen verlangt | – |
| `SGE_CLIP_AI_TIMEOUT` | Wartezeit je Anfrage in Sekunden | 180 |

Pro VOD gehen höchstens 10 Anfragen mit je grob 1.500 Eingabe- und bis zu 700
Ausgabe-Token raus. Bei kleinen Modellen ist das meist ein Bruchteil eines Cents bis
wenige Cent pro VOD – die aktuellen Preise des Anbieters vorher prüfen.
**Datenschutz:** Bei einem entfernten Anbieter verlassen Chat-Auszüge (und Transkripte)
den Rechner. Der Clip Hunter weist vor dem Start darauf hin.

### Was die KI-Stufe (noch) nicht kann

- Sie sieht **kein Bild**. Rein visuelle Momente beurteilt sie nur über Chat und Sprache.
- Ihr Nutzen ist noch nicht an echten Streams gemessen, weil dafür VODs mit Ton nötig sind
  (der LIGHTOR-Datensatz enthält nur Chat). Erst echte Tests zeigen, ob sie die Auswahl
  wirklich verbessert. Bis dahin: Titel und Schnitt als Vorschlag sehen.
