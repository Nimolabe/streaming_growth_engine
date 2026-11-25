# Content Strategist – Wochenplan für kleine Streamer

Der Content Strategist beantwortet für Kanäle mit etwa 0–20 Zuschauern eine Frage:
**Was streame ich diese Woche, wann, in welcher Kategorie, mit welchem Titel und welchen Tags,
was bereite ich vor und welcher Clip kommt danach?**

Alles läuft **lokal und regelbasiert**, ohne Sprachmodell und ohne Kosten. Gleiche Eingabe
ergibt immer denselben Plan. 30 gekürzte Beispielpläne (9 Genres und ein vertrautes Spiel ohne
Genre, je 3 Kanalgrößen) stehen in
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
| `windows` | `--window "Mo 18-22"` | Zeitfenster pro Wochentag in Ortszeit. Tage deutsch oder englisch („Mo“, „Montag“, „Mon“). `"Fr 22-2"` geht über Mitternacht, `"So 0-24"` ist der ganze Tag. In der API: `{"day": "Mo", "start": "18:30", "end": 22}` – `start`/`end` sind **Uhrzeiten** („HH“ oder „HH:MM“ oder eine Zahl 0–24 für volle Stunden), keine Minuten seit Mitternacht; 1080 wird mit einer Fehlermeldung abgelehnt, die das Format nennt |
| `hours_per_week` | `--hours` | **Gesamte Zeit** pro Woche: Streams **plus** Vorbereitung, Clips und Wochenrückblick. Ist sie knapp, kürzt der Plan die Zusatzaufgaben (siehe Zeitbudget) |
| `streams_per_week` | `--streams` | 1–7 |
| `average_viewers` | `--viewers` | Ø Zuschauer (für den Platz im Kategorie-Check) |
| `active_chatters` | `--chatters` | Wie viele Leute pro Stream wirklich schreiben |
| `goal` | `--goal` | `discovery` (neue Zuschauer), `community` oder `consistency` (Regelmäßigkeit) |
| `experience` | `--experience` | `beginner`, `intermediate`, `advanced` |
| `language` | `--lang` | `de` oder `en` – Plan, Titel und Tags |
| `platform` | `--platform` | `twitch` (Standard), `youtube`, `kick`, `tiktok`, `other` |
| `rank_goal` | `--rank-goal` | Optional: Rang-Ziel für die Titel, z. B. „Platin“ („Road to Platin, Tag 3“) |
| `current_rank` | `--current-rank` | Optional: aktueller Rang; mit `rank_goal` entsteht „Von Silber nach Platin“ |
| `commands` | `--commands` | Optional: bis zu 3 eigene Chat-Befehle (z. B. `!discord`), ans Ende jedes Titels gehängt |
| `mood` | `--mood` | Optional: Stimmung der Titel – `chill`, `ambitious` (ehrgeizig), `funny` (lustig); auch „chillig“, „ehrgeizig“, „lustig“ |
| `first_time` | `--first-time` | Optional: zum ersten Mal / blind. Nur dann gibt es Titel wie „Zum ersten Mal …“ und bei Spielen ohne Genre das Format „Erste Eindrücke“ |
| `week_number` | `--week` | Wievielte Woche du planst (Standard 1); Zähler in Titeln laufen weiter |
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
     Bewusst ohne Genre:
     - GTA V und GTA RP: Rollenspiel und Missionen passen nicht zu Bau- oder Überlebensformaten.
     - World of Warcraft: ein MMO. Story/Singleplayer hätte den falschen Tag „Singleplayer“
       ergeben.
     - Teamfight Tactics: ein Auto-Battler.
   - Seit der Simulation mit 100 Test-Streamern erkannt: Hogwarts Legacy und Pokémon-Spiele
     („Pokémon Legenden: Z-A“, „Pokémon Karmesin/Purpur“ …) als Story; „Pokémon Unite“ bleibt
     MOBA. Euro Truck Simulator (auch „ETS2“) ist Cozy/Simulation.
2. **Zeitbudget.**
   - Pro Stream: 20 min Vorbereitung (endet 10 min vor dem Start) und 30 min für einen Clip danach.
   - Pro Woche: 30 min Rückblick.
   - Der Rest wird gleichmäßig auf die Streams verteilt, in 15-Minuten-Schritten abgerundet.
   - Ein Stream dauert mindestens 60 und höchstens 240 Minuten und ist nie länger als sein
     Zeitfenster.
   - Der Plan verbraucht nie mehr Zeit als angegeben. Was übrig bleibt, steht als „nicht verplant“.
   - **Wenn die Zeit knapp ist** (z. B. 2 Streams à 2 h bei 4 Stunden pro Woche), kürzt der Plan
     die Zusatzaufgaben, bis Streams mit 60 Minuten passen, in dieser Reihenfolge:
     Wochenrückblick (30 → 15 → 0 min), Clip-Zeit (30 → 15 → 0 min pro Stream), Vorbereitung
     (20 → 15 min). Was gekürzt wurde, steht ehrlich als erster Hinweis im Plan; ein weggelassener
     Rückblick heißt im Bericht „optional, nur wenn Zeit übrig ist“.
   - Eine Fehlermeldung gibt es nur, wenn nicht einmal Streams mit 60 Minuten plus 15 Minuten
     Vorbereitung in die Woche passen (z. B. 3 Streams in 3 Stunden).
3. **Zeitfenster wählen.**
   - Überlappende Fenster werden zusammengelegt, Fenster unter 60 Minuten zählen nicht.
   - Ein Stream pro Fenster.
   - Ohne Messungen werden die Streams über die Woche verteilt, bevorzugt ein Stream pro Tag.
   - Mit Messungen wählt der Plan je Stream das Fenster und die Startzeit, in der der
     Zwei-Stunden-Block mit dem besten **Publikum pro Platz** liegt. Das ist dieselbe Logik wie
     „beste Zeiten“ im Kategorie-Check (`category_check.analysis.slot_stats`). Die Begründung
     steht dabei, z. B. „Mit 3 Zuschauern etwa Platz 16 in League of Legends (Di 20–22 Uhr …)“.
   - Mehr Streams als nutzbare Fenster ergeben eine klare Fehlermeldung.
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
   - **Wochen-Formate** kommen nur auf den letzten Stream der Woche und nur, wenn es mindestens
     zwei Streams gibt: der Just-Chatting-„Wochenrückblick“ (Ziel Community oder
     Regelmäßigkeit) und „Moment der Woche“ bei Spielen ohne Genre („⭐ Die besten Momente der
     Woche“, Ziel Community).
   - „Die Geschichte bisher in 5 Minuten“ (Story, „📖 Neu hier? 5-Minuten-Rückblick“) braucht
     eine Vorgeschichte: In Woche 1 ist es nie der erste Stream eines Spiels; es rückt dann einen
     Stream nach hinten (Merkmal `needs_history`).
   - **Spiele ohne erkanntes Genre:**
     - „Erste Eindrücke“ („🎮 Erste Stunde in …“) nur mit `first_time` (Merkmal
       `first_time_only`).
     - Sonst – für vertraute Spiele wie World of Warcraft – vier eigene Formate:
       „Abend mit Ziel“ (`general-evening-goal`), „Entspanntes Spielen & Quatschen“
       (`general-chill`), „Mit Zuschauern spielen“ (`general-viewer-games`, braucht ab
       3 aktive Chatter) und „Fortschritt mit Tageszähler“ (`general-progress`, Mini-Serie).
       Dazu die bisherigen: Lern-Tagebuch, Zwei Wege, Zuschauer entscheiden.
5. **Titel und Tags.**
   - Titel beschreiben den **ganzen Stream** im Stil echter Twitch-Titel (Recherche bei
     deutschen Streamern in Valorant, Fortnite, LoL, Minecraft, Just Chatting, Stardew, Elden
     Ring und Phasmophobia; vom Nutzer bestätigt, `content_strategist/titles.py`). Beispiele:
     „🏰 Großprojekt | Tag 3 | Wie weit kommen wir heute?“,
     „⚔️ Neuer Main, Tag 1 | 90 % Hoffnung, 10 % Skill“,
     „🔴 Von Silber nach Platin | Tag 5 | Komm rein!“.
   - Pro Stream gibt es drei Titel, die sich im **ersten Baustein** unterscheiden: Ziel bzw.
     Fortschritt, Stimmung des Genres, Einladung.
   - Der Plan zeigt pro Stream einen Haupttitel und zwei Alternativen. Die Ansätze wechseln
     sich über die Woche ab, und dasselbe Format bekommt in einer Woche nie zweimal denselben
     Haupttitel.
   - Zähler wie „Tag 2“, „Folge 3“ und „Road to Platin, Tag 5“ laufen mit; mit `--week 2`
     (API: `week_number`) beginnen sie dort, wo die Vorwoche aufgehört hat.
   - Die Tageszeit des Streams fließt ein: „Ranked-Abend“ um 19 Uhr, „Ranked-Nachmittag“
     um 14 Uhr, „Horror-Nacht“ ab 22 Uhr. Spielname und Tageszeit werden wie im Duden
     durchgekoppelt: „World-of-Warcraft-Abend“, „GTA-V-Nacht“. Enthält der Name andere
     Satzzeichen (z. B. „Warhammer 40,000: Darktide“), steht stattdessen „Abend in …“.
   - Die früheren Titel, die sich auf einen einzelnen Moment bezogen („Hätte ich diese Runde
     retten können?“), stehen jetzt als **Titel fürs Kurzvideo** im Plan, denn ein Clip zeigt
     genau einen Moment.
   - Die Grenzen von Twitch werden streng eingehalten:
     - Titel höchstens 140 Zeichen;
     - höchstens 10 Tags mit je höchstens 25 Zeichen, ohne Leer- und Sonderzeichen. Erlaubt sind
       nur Buchstaben und Ziffern.
   - Quelle: [Twitch API Reference, Modify Channel Information](https://dev.twitch.tv/docs/api/reference/channels#modify-channel-information),
     Stand: November 2026.
   - **Regeln für Titel** (ein Test prüft 1, 2, 4, 5 und 6 für alle Formate, alle Stimmungen
     und beide Sprachen):
     1. Bausteine mit „ | “ statt ganzer Sätze: [Emoji + Hook] | [Fortschritt/Info] |
        [Twist/Einladung]. 2–4 Bausteine.
     2. Genau ein Emoji, am **Anfang** des Titels. Es steht im Titeltext selbst.
     3. Persönlichkeit und Selbstironie sind erwünscht („90 % Hoffnung, 10 % Skill“).
     4. Höchstens 2 Wörter pro Titel in GROSSBUCHSTABEN (Abkürzungen wie LoL, CS2, MMR zählen
        nicht).
     5. Höchstens ein „!“ („?!“ zählt als eins). Bezug auf den ganzen Stream, nie auf eine
        einzelne Runde, Szene oder ein Match.
     6. Ziel höchstens 70 Zeichen ohne Befehle (bei normalen Spielnamen bis etwa 17 Zeichen wie
        „League of Legends“), hart höchstens 140.
     7. Chat-Formate sprechen den Chat mit „Ihr“ an, Einladungen mit „du“.
   - **Eigene Chat-Befehle** (`commands` / `--commands '!discord' '!insta'`, höchstens 3, jeder
     wie `!name` aus Kleinbuchstaben, Ziffern und `_`) werden mit „ | “ ans Ende jedes Titels
     gehängt: „❓ Frag mich ALLES | Ich antworte ehrlich | !discord !insta“. Würde der Titel
     dadurch länger als 140 Zeichen, fallen die Befehle weg, nie der Titel selbst.
   - **Rang-Reise:** Mit `rank_goal` und `current_rank` entsteht „🔴 Von Silber nach Platin |
     Tag 5 | Komm rein!“, mit `rank_goal` allein „🔴 Ranked Grind | Tag 5 | Road to Platin“.
     `current_rank` ohne `rank_goal` wird ignoriert.
   - Beginnen Ziel- und Ranked-Stimmungstitel mit demselben Baustein (z. B. „🔴 Ranked-Abend“
     bei MOBA und Sport), nimmt der Plan für die Stimmung den ehrgeizigen Titel des Genres, damit
     sich die drei Titel im Anfang unterscheiden.
   - Platzhalter wie `{regel}` oder `{ziel}` haben feste Standardwerte aus dem Format
     (z. B. „nur einer Waffe“). Gleiche Eingabe ergibt also weiter denselben Titel.
   - **Ohne Angaben** wählt der Plan die Stimmung passend zum Genre bzw. Format:
     - Cozy, Story, Sandbox, Just Chatting: chillig
     - Shooter, Battle Royale, MOBA, Sport: ehrgeizig
     - Horror und die meisten Mitmach-Formate: lustig
     - Ausnahmen pro Format: z. B. die Horror-Hinweissuche chillig, „Versuche zählen“ (Story)
       ehrgeizig
6. **Mini-Serie** nur, wenn das gewählte Format von Natur aus in Folgen funktioniert,
   z. B. erster Durchgang in Etappen oder Großprojekt in Etappen.

## Ausgabe

Pro Stream gibt es:

- Wochentag und Uhrzeit, Spiel, Format, Haupttitel mit zwei Alternativen, Tags;
- Titel-Ideen fürs Kurzvideo;
- Vorbereitung mit Uhrzeit und Schritten;
- Ablauf und, bei langen Streams, Pausenhinweis;
- Clip-Idee mit Tag, Hook, Messgröße;
- Begründung für Format und Uhrzeit.

Dazu kommen der Wochenrückblick mit drei Fragen, das Zeitbudget, Hinweise und Grenzen.
`--json` speichert alles maschinenlesbar (Schema-Version `content-strategist-a1`), `--html`
erzeugt einen Bericht, der auch auf dem Handy lesbar ist.

## Regressionstest aus der Simulation

`tests/test_content_strategist.py::test_simulation_regression` plant 30 fest definierte Profile
(bekannte und unbekannte Spiele, 1–3 Spiele, 2–6 Streams, knappe Stunden, 0–100 Zuschauer,
DE/EN, Woche 1–5, mit und ohne Befehle) und prüft: kein Fehler; Zeitbudget geht auf; keine
„Erste Stunde“/„Neues Spiel“/„Zum ersten Mal“ ohne `first_time`; Wochen-Formate nur am Ende
des Plans; kein Rückblick-Format als erster Stream eines Spiels in Woche 1; Chat- und
Mitspieler-Bedarf passt; alle Titelregeln und Twitch-Grenzen. Echte Unmöglichkeiten (zu wenig
Stunden für 60-Minuten-Streams, zu wenige Zeitfenster) müssen dagegen einen Fehler ergeben.

## Grenzen

- Redaktionelle Regeln, keine Wachstumsvorhersage. Die Ideen sind Hypothesen zum Ausprobieren.
- Die Genre-Liste kennt nicht jedes Spiel. Unbekannte Spiele bekommen allgemeine Formate.
- Ohne Messungen kommen Uhrzeiten nur aus den eigenen Zeitfenstern.
- Mit Messungen ist der Platz eine Näherung, weil Twitch Listen personalisiert sortieren kann.
- Spielinhalte ändern sich mit Updates; Ideen vor dem Stream in der eigenen Spielversion prüfen.
- Gegen die echte Twitch-API ist nur der Kategorie-Check gebaut, und auch der ist noch nicht
  echt getestet. Der Content Strategist selbst fragt nichts im Netz an.
