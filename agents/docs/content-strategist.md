# Content Strategist – Wochenplan für kleine Streamer

Der Content Strategist beantwortet für Kanäle mit etwa 0–20 Zuschauern eine Frage:
**Was streame ich diese Woche, wann, in welcher Kategorie, mit welchem Titel und welchen Tags,
was bereite ich vor und welcher Clip kommt danach?**

Alles läuft **lokal und regelbasiert**, ohne Sprachmodell und ohne Kosten. Gleiche Eingabe
ergibt immer denselben Plan. 27 gekürzte Beispielpläne (9 Genres × 3 Kanalgrößen) stehen in
[content-strategist-beispiele.md](content-strategist-beispiele.md).

## Schnellstart

```bash
cd agents
python -m streaming_agents.content_strategist plan --game "Stardew Valley" \
    --window "Mo 18-22" --window "Mi 18-22" --window "Sa 14-20" \
    --hours 8 --streams 3 --viewers 3 --chatters 1 --html plan.html
```

Mit Messungen aus dem [Kategorie-Check](category-check.md) wählt der Plan die Uhrzeiten nach
Publikum:

```bash
python -m streaming_agents.category_check watch "Minecraft" --every 60 --hours 168 --out messungen.jsonl
python -m streaming_agents.content_strategist plan --game "Minecraft" --window "Fr 18-23" \
    --window "Sa 12-22" --hours 6 --streams 2 --viewers 3 --measurements messungen.jsonl
```

API: `POST /api/v1/content/strategy`, Beispiel: [`examples/content_strategy_request.json`](../examples/content_strategy_request.json).

## Eingaben

| Feld (API) | Kommandozeile | Bedeutung |
| --- | --- | --- |
| `games` | `--game` (1–5×) | Spiele bzw. Twitch-Kategorien |
| `windows` | `--window "Mo 18-22"` | Zeitfenster pro Wochentag in Ortszeit. Tage deutsch oder englisch („Mo“, „Montag“, „Mon“). `"Fr 22-2"` geht über Mitternacht, `"So 0-24"` ist der ganze Tag |
| `hours_per_week` | `--hours` | **Gesamtzeit** pro Woche, inklusive Vorbereitung, Clips und Rückblick |
| `streams_per_week` | `--streams` | 1–7 |
| `average_viewers` | `--viewers` | Ø Zuschauer (für den Platz im Kategorie-Check) |
| `active_chatters` | `--chatters` | Wie viele Leute pro Stream wirklich schreiben |
| `goal` | `--goal` | `discovery` (neue Zuschauer), `community` oder `consistency` (Regelmäßigkeit) |
| `experience` | `--experience` | `beginner`, `intermediate`, `advanced` |
| `language` | `--lang` | `de` oder `en` – Plan, Titel und Tags |
| `platform` | `--platform` | `twitch` (Standard), `youtube`, `kick`, `tiktok`, `other` |
| `collab_partner` | `--collab` | Mitspieler oder Gast verfügbar (Koop- und Coach-Formate) |
| `measurements` | `--measurements` | Optional: Messungen aus dem Kategorie-Check |
| `utc_offset_minutes` | `--utc-offset` | Zeitzone der Messungen (Standard: Ortszeit des Rechners) |

## So entsteht der Plan

1. **Genre erkennen.** Eine zentrale Liste in `content_strategist/genres.py` ordnet Spiele
   neun Genres zu: Shooter, Battle Royale, MOBA, Story/Singleplayer, Horror, Cozy/Simulation,
   Sandbox/Survival, Sport/Rennspiele und Just Chatting.
   - Groß-/Kleinschreibung und Satzzeichen sind egal („CS2“, „Counter-Strike 2“, „LoL“).
   - Es zählen ganze Wörter. Bei mehreren Treffern gewinnt der längste: „Call of Duty: Warzone“
     ist Battle Royale, „Call of Duty“ ist Shooter.
   - Ein unbekanntes Spiel wird als „kein Genre erkannt“ markiert und bekommt allgemeine Formate.
2. **Zeitbudget.**
   - Pro Stream: 20 min Vorbereitung (endet 10 min vor dem Start) und 30 min für einen Clip danach.
   - Pro Woche: 30 min Rückblick.
   - Der Rest wird gleichmäßig auf die Streams verteilt, in 15-Minuten-Schritten abgerundet.
   - Ein Stream dauert mindestens 60 und höchstens 240 Minuten und ist nie länger als sein
     Zeitfenster.
   - Der Plan verbraucht nie mehr Zeit als angegeben. Was übrig bleibt, steht als „nicht verplant“.
3. **Zeitfenster wählen.**
   - Überlappende Fenster werden zusammengelegt, Fenster unter 60 Minuten zählen nicht.
   - Ein Stream pro Fenster.
   - Ohne Messungen werden die Streams über die Woche verteilt, bevorzugt ein Stream pro Tag.
   - Mit Messungen wählt der Plan je Stream das Fenster und die Startzeit, in der der
     Zwei-Stunden-Block mit dem besten **Publikum pro Platz** liegt. Das ist dieselbe Logik wie
     „beste Zeiten“ im Kategorie-Check (`category_check.analysis.slot_stats`). Die Begründung
     steht dabei, z. B. „Mit 3 Zuschauern etwa Platz 16 in League of Legends (Di 20–22 Uhr …)“.
   - Mehr Streams als nutzbare Fenster oder zu wenig Stunden ergeben eine klare Fehlermeldung.
4. **Format wählen.**
   - Pro Genre gibt es 5–6 Formate (`content_strategist/formats.py`), alle mit Ablauf in drei
     Schritten, zwei Vorbereitungsschritten, Hook, Clip-Idee, Messgröße, Titel und Tags.
   - Jedes Format hat das Merkmal `needs_chat`:
     - `none` braucht keinen Chat; auch seine Messgröße kommt ohne Chat-Reaktionen aus.
     - `low` braucht mindestens 3 aktive Chatter.
     - `active` braucht mindestens 8.
   - `needs_collab` braucht einen Mitspieler.
   - Bei 0–2 Chattern kommen nur Formate mit `needs_chat: none` in den Plan.
   - Innerhalb eines Genres werden die Formate der Reihe nach vergeben. Sie wiederholen sich
     erst, wenn alle passenden einmal dran waren.
5. **Titel und Tags.**
   - Vorlagen pro Format, auf Deutsch und Englisch, ohne Clickbait-Versprechen und ohne Marken
     außer dem Spielnamen.
   - Die Grenzen von Twitch werden streng eingehalten:
     - Titel höchstens 140 Zeichen;
     - höchstens 10 Tags mit je höchstens 25 Zeichen, ohne Leer- und Sonderzeichen. Erlaubt sind
       nur Buchstaben und Ziffern.
   - Quelle: [Twitch API Reference, Modify Channel Information](https://dev.twitch.tv/docs/api/reference/channels#modify-channel-information),
     Stand: November 2026.
6. **Mini-Serie** nur, wenn das gewählte Format von Natur aus in Folgen funktioniert,
   z. B. erster Durchgang in Etappen oder Großprojekt in Etappen.

## Ausgabe

Pro Stream gibt es:

- Wochentag und Uhrzeit, Spiel, Format, Titel, Tags;
- Vorbereitung mit Uhrzeit und Schritten;
- Ablauf und, bei langen Streams, Pausenhinweis;
- Clip-Idee mit Tag, Hook, Messgröße;
- Begründung für Format und Uhrzeit.

Dazu kommen der Wochenrückblick mit drei Fragen, das Zeitbudget, Hinweise und Grenzen.
`--json` speichert alles maschinenlesbar (Schema-Version `content-strategist-a1`), `--html`
erzeugt einen Bericht, der auch auf dem Handy lesbar ist.

## Grenzen

- Redaktionelle Regeln, keine Wachstumsvorhersage. Die Ideen sind Hypothesen zum Ausprobieren.
- Die Genre-Liste kennt nicht jedes Spiel. Unbekannte Spiele bekommen allgemeine Formate.
- Ohne Messungen kommen Uhrzeiten nur aus den eigenen Zeitfenstern.
- Mit Messungen ist der Platz eine Näherung, weil Twitch Listen personalisiert sortieren kann.
- Spielinhalte ändern sich mit Updates; Ideen vor dem Stream in der eigenen Spielversion prüfen.
- Gegen die echte Twitch-API ist nur der Kategorie-Check gebaut, und auch der ist noch nicht
  echt getestet. Der Content Strategist selbst fragt nichts im Netz an.
