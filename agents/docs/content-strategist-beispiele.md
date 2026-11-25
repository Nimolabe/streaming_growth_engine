# Content Strategist – 30 Beispielpläne

Automatisch erzeugt mit `build_plan` (Variante A, ohne Messungen, Sprache Deutsch).
Gekürzt: pro Stream Zeit, Format, Haupttitel mit 2 Alternativen, Tags, Vorbereitung und
Clip. Vollständige Pläne (Ablauf, Hook, Messgröße, Begründungen, Hinweise) liefert
`python -m streaming_agents.content_strategist plan … --html plan.html`.

Zeitfenster in allen Beispielen: Mo 18-22, Mi 18-22, Fr 19-23, Sa 14-20, So 15-19.

Je Genre ein Spiel (9 Genres) plus **World of Warcraft** als vertrautes Spiel ohne erkanntes
Genre, jeweils in drei Kanalgrößen: 10 × 3 = 30 Pläne.

| Profil | Zuschauer | aktive Chatter | Stunden/Woche | Streams | Erfahrung | Ziel | Mitspieler |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| 0–3 Zuschauer | 1 | 0 | 6 | 2 | Einsteiger | neue Zuschauer | nein |
| 5–10 Zuschauer | 7 | 4 | 10 | 3 | Fortgeschritten | Community | nein |
| 15–20 Zuschauer | 18 | 9 | 14 | 4 | Erfahren | Regelmäßigkeit | ja |

## Titel: fünf Versionen im Vergleich

Je ein Format pro Genre, Deutsch, erstes Vorkommen, Stream um 19 Uhr, Stimmung passend zum
Genre.

- **1** (23.11.): Spielname vorn, Format beschrieben.
- **2** (24.11. mittags): ein einzelner Moment.
- **3** (24.11. nachmittags): ganzer Stream, aber aus Bausteinen zusammengesetzt.
- **4** (24.11. abends): ganzer Stream, von Hand formulierte Sätze, Emoji am Ende.
- **5** (jetzt): Bausteine mit „ | “ nach echten Twitch-Vorbildern, Emoji am Anfang.

| Genre | 1 | 2 | 3 | 4 | 5 (jetzt) |
| --- | --- | --- | --- | --- | --- |
| Shooter | Valorant: Welche Entscheidung kostet mich die Runde? Analyse am Ende | Hätte ich diese Runde retten können? | Lernen aus jeder Niederlage – wie viele Siege holen wir heute? 🔥 | Jede Niederlage wird zur Lektion – wie viel lerne ich heute? 🔥 | 🔴 Ranked mit Köpfchen \| Tag 1 \| Heute wird nicht getiltet |
| Battle Royale | Fortnite: Rotation oder Risiko? Ich erkläre jede Entscheidung | Rotieren oder bleiben? Jede Entscheidung erklärt | Jede Zone mit Plan – holen wir heute einen Sieg? 🏆 | Jede Zone mit Plan – reicht das heute für einen Sieg? 🏆 | 🏆 Erst ein Sieg, dann Feierabend \| Wie lange dauert's heute? |
| MOBA | League of Legends: Wo habe ich das Match verloren? Analyse nach jeder Runde | Wo habe ich dieses Match verloren? | Jedes Match mit Nachbesprechung – wie viele Siege holen wir heute? ⚔️ | Weniger Fehler, mehr Siege – schaffen wir das heute? ⚔️ | 🔴 Ranked-Abend \| Tag 1 \| Heute wird geklettert |
| Story/Singleplayer | Hollow Knight: Mein erster Durchgang – bitte keine Spoiler | Erster Durchgang, Etappe 1: Was erwartet mich? | Mein erster Durchgang, Etappe 1 – was erwartet mich heute? 🗡️ | Mein erster Durchgang, Etappe 1 – was erwartet mich heute? 📖 | 📖 Erster Durchgang \| Teil 1 \| Keine Spoiler! |
| Horror | Phasmophobia: Erster Durchgang mit Facecam – ehrliche Reaktionen | Wie lange halte ich ohne Schrei durch? | Horror mit Facecam – wie oft schreie ich heute? 😱 | Horror mit Facecam – wie oft schreie ich heute? 😱 | 👻 Licht aus, Ton laut \| Wie oft schreie ich heute? |
| Cozy/Simulation | Stardew Valley: Gemütlich spielen mit drei kleinen Zielen | Drei kleine Ziele, Woche 1 – schaffe ich alle? | Drei kleine Ziele, Woche 1 – schaffen wir alle? ☕ | Drei kleine Ziele, Woche 1 – schaffen wir alle? ☕ | 🌱 Drei kleine Ziele \| Woche 1 \| Schaffen wir alle? |
| Sandbox/Survival | Minecraft: Großprojekt Etappe für Etappe | Großprojekt, Etappe 1: Heute wächst es | Großprojekt Tag 1 – wie weit kommen wir heute? 🏰 | Großprojekt Tag 1 – wie weit kommen wir heute? ⛏️ | 🏰 Großprojekt \| Tag 1 \| Wie weit kommen wir heute? |
| Sport/Rennspiele | Rocket League: Jagd auf meine eigene Bestmarke | Knacke ich heute meine Bestmarke? | Jagd auf die eigene Bestmarke – knacken wir heute die Marke? 🚗 | Jagd auf meine Bestmarke – klappt's heute? 🏁 | 🏁 Jagd auf meine Bestmarke \| Heute fällt sie. Oder? |
| Just Chatting | Fragerunde – ihr fragt, ich antworte ehrlich | Frag mich, was du willst – ich antworte ehrlich | Kaffee, Quatschen und eure Fragen – was willst du wissen? ☕ | Kaffee, Quatschen und eure Fragen – was willst du wissen? ☕ | ❓ Frag mich ALLES \| Ich antworte ehrlich |

## Titel nach Stimmung, Rang-Ziel und erstem Mal

Je Genre der Titel „Stimmung + Einladung oder Frage“ in den drei Stimmungen (19 Uhr),
dazu „Ziel + Frage“ mit Rang-Ziel `Platin` (Ranked-Genres) bzw. `first_time` (Story,
Horror). Format wie in der Tabelle oben, bei Rang-Zielen ein Ranked-Format.

| Genre | chillig | ehrgeizig | lustig | mit Rang-Ziel / erstes Mal |
| --- | --- | --- | --- | --- |
| Shooter | 🎯 Chilliges Valorant & Quatschen \| Komm rein und sag Hallo! | 🔴 Ranked-Abend \| Heute wird geklettert – komm mit! | 😂 Chaos-Abend in Valorant \| Skill optional | 🔴 Ranked Grind \| Tag 5 \| Road to Platin |
| Battle Royale | 🪂 Entspannte Runden & Quatschen \| Sag Hallo! | 🔴 Ranked-Abend \| Heute wird geklettert – komm mit! | 😂 Chaos-Drops in Fortnite \| Wo landen wir diesmal? | 🔴 Ranked Grind \| Tag 5 \| Road to Platin |
| MOBA | ☕ Entspanntes League of Legends & Quatschen \| Sag Hallo! | 🔴 Ranked Grind \| Heute wird geklettert | 😂 Chaos-Abend in League of Legends \| Wer feedet zuerst? | 🔴 Ranked Grind \| Tag 5 \| Road to Platin |
| Story/Singleplayer | 📖 Gemütlicher Story-Abend \| Komm mit auf die Reise | 🗡️ Heute geht's WEIT voran \| Komm mit! | 😅 Lachen und Leiden in Hollow Knight \| Leidest du mit? | 🗡️ Zum ersten Mal Hollow Knight \| Blind \| Keine Spoiler! |
| Horror | 🕯️ Gemütlicher Grusel-Abend \| Trau dich rein | 👻 Horror-Abend mit Licht aus \| Hältst du durch? | 😱 Horror-Abend in Phasmophobia \| Lachen oder schreien? | 👻 Zum ersten Mal Phasmophobia \| Blind \| Wie oft schreie ich? |
| Cozy/Simulation | ☕ Gemütlicher Abend in Stardew Valley \| Kaffee & Quatschen | 🌱 Fleißiger Abend in Stardew Valley \| Was schaffen wir alles? | 😄 Gemütliches Chaos in Stardew Valley \| Was geht heute schief? | – |
| Sandbox/Survival | ⛏️ Entspannt bauen in Minecraft \| Komm rein und chill mit! | 🏰 Bau-Abend \| Heute wird RICHTIG was geschafft | 😂 Bau-Chaos in Minecraft \| Hält das am Ende? | – |
| Sport/Rennspiele | ⚽ Lockeres Rocket League & Quatschen \| Sag Hallo! | 🔴 Heute wird GESCHWITZT \| Fiebere mit! | 😂 Spaß-Abend in Rocket League \| Wer lacht zuletzt? | 🔴 Ranked Grind \| Tag 5 \| Road to Platin |
| Just Chatting | ☕ Kaffee & Quatschen \| Komm rein und sag Hallo! | 💬 Großes Thema heute \| Red mit! | 😂 Quatsch-Abend \| Worüber lachen wir heute? | – |

## Beispiele mit eigenen Befehlen und Rang-Reise

Stream um 19 Uhr; die Befehle bei Just Chatting (Fragerunde), die Ränge bei Valorant:

- `commands=["!discord", "!insta"]`: „❓ Frag mich ALLES | Ich antworte ehrlich | !discord !insta“
- `rank_goal="Platin"`, `current_rank="Silber"`: „🔴 Von Silber nach Platin | Tag 5 | Komm rein!“
- `rank_goal="Platin"` (ohne aktuellen Rang): „🔴 Ranked Grind | Tag 5 | Road to Platin“
- alles zusammen, Englisch: „🔴 From Silver to Platinum | Day 5 | Come in! | !discord“

## Vertraute Spiele ohne Genre und knappe Zeit

Seit der Simulation mit 100 Test-Streamern (25.11.2026):

- **Ohne `first_time`** bekommt ein Spiel ohne erkanntes Genre (World of Warcraft, GTA V,
  Teamfight Tactics …) die Formate für vertraute Spiele: „Abend mit Ziel“, „Entspanntes Spielen
  & Quatschen“, „Mit Zuschauern spielen“ (ab 3 aktiven Chattern) und „Fortschritt mit
  Tageszähler“ – nie mehr „🎮 Erste Stunde in World of Warcraft | Lohnt sich das?“.
- **Mit `first_time`** (2 Streams, 6 Stunden): 1. „Erste Eindrücke“ – „🎮 Zum ersten Mal World
  of Warcraft | Blind | Lohnt sich das?“, 2. „Abend mit Ziel“ – „✨ Mit Ziel in World of
  Warcraft | Schaffe ich es heute?“.
- Tageszeit im Titel als ein Wort, durchgekoppelt: „🎮 World-of-Warcraft-Abend | Chill mit!“.

Knappe Stunden (World of Warcraft, Profil 0–3 Zuschauer, sonst gleiche Eingaben):

| Stunden | Streams | Stream | Vorbereitung | Clip-Zeit | Rückblick | nicht verplant | Hinweis im Plan |
| ---: | ---: | --- | --- | --- | --- | ---: | --- |
| 6 | 2 | 2 × 105 min | 2 × 20 min | 2 × 30 min | 30 min | 20 | – |
| 4 | 2 | 2 × 60 min | 2 × 20 min | 2 × 30 min | 15 min | 5 | Wochenrückblick auf 15 min gekürzt |
| 3 | 2 | 2 × 60 min | 2 × 20 min | – | – | 20 | Wochenrückblick weggelassen, keine feste Clip-Zeit |
| 5 | 4 | 4 × 60 min | 4 × 15 min | – | – | 0 | … und Vorbereitung auf 15 min gekürzt |
| 3 | 3 | – | – | – | – | – | Fehler: 3 × (60 + 15) min brauchen mindestens 4 Stunden |

## Shooter: Valorant

### 0–3 Zuschauer

1. **Mo 18:00–19:45** (105 min) · Die Entscheidung, die die Runde gekostet hat · _ohne Chat_
   - Titel: „🔴 Ranked mit Köpfchen | Tag 1 | Heute wird nicht getiltet“
   - Alternativen: „🔴 Ranked-Abend | Heute wird geklettert – komm mit!“ · „🧠 Erst denken, dann peeken | Ranked | Klappt das heute?“
   - Titel fürs Kurzvideo: „Hätte ich diese Runde retten können?“ · „Welcher Fehler kostet mich die meisten Runden?“
   - Tags: Valorant, Deutsch, Shooter, Analyse, Taktik
   - Vorbereitung (Mo 17:30): Marker-Taste (Twitch „Stream-Marker“) oder Notizzettel bereitlegen
   - Clip (Di): Szene bis kurz vor dem Ausgang, Standbild mit zwei Optionen, dann die Auflösung
2. **Fr 19:00–20:45** (105 min) · Ein Skill pro Stream · _ohne Chat_
   - Titel: „🔴 Ranked-Abend | Heute wird geklettert – komm mit!“
   - Alternativen: „🎯 Fadenkreuz-Training | Tag 1 | Mein Aim braucht Hilfe“ · „🎯 Aim-Woche, Tag 1 | Heute trifft ALLES. Hoffentlich.“
   - Titel fürs Kurzvideo: „Warum verliere ich an dieser Ecke immer?“ · „Vorher, nachher: sitzt das Fadenkreuz?“
   - Tags: Valorant, Deutsch, Shooter, Lernen, Training
   - Vorbereitung (Fr 18:30): Eine Fähigkeit auswählen und aufschreiben, woran man sie erkennt
   - Clip (Sa): Zwei Szenen nebeneinander: vorher und nachher, mit einer Zeile, was sich geändert hat

Mini-Serie: Ein Skill pro Stream – Folge 1: Ausgangslage aufnehmen · Folge 2: gezielt üben · Folge 3: vorher und nachher vergleichen

### 5–10 Zuschauer

1. **Mo 18:00–20:15** (135 min) · Der Chat bestimmt die Regel · _kleiner Chat_
   - Titel: „😂 Jedes Match mit nur einer Waffe | Ihr habt das so gewollt“
   - Alternativen: „😂 Chaos-Abend in Valorant | Skill optional“ · „🎲 Der Chat macht die Regeln | Ich muss trotzdem gewinnen“
   - Titel fürs Kurzvideo: „Wie lange halte ich mit nur einer Waffe durch?“ · „Der Chat hat die Regel gewählt …“
   - Tags: Valorant, Deutsch, Shooter, Challenge, Community
   - Vorbereitung (Mo 17:30): Drei spielbare Regeln aufschreiben
   - Clip (Di): Bester Moment mit der Regel, Regel als Einblendung
2. **Mi 18:00–20:15** (135 min) · Die Entscheidung, die die Runde gekostet hat · _ohne Chat_
   - Titel: „🔴 Ranked-Abend | Heute wird geklettert – komm mit!“
   - Alternativen: „🧠 Erst denken, dann peeken | Ranked | Klappt das heute?“ · „🔴 Ranked mit Köpfchen | Tag 1 | Heute wird nicht getiltet“
   - Titel fürs Kurzvideo: „Hätte ich diese Runde retten können?“ · „Welcher Fehler kostet mich die meisten Runden?“
   - Tags: Valorant, Deutsch, Shooter, Analyse, Taktik
   - Vorbereitung (Mi 17:30): Marker-Taste (Twitch „Stream-Marker“) oder Notizzettel bereitlegen
   - Clip (Do): Szene bis kurz vor dem Ausgang, Standbild mit zwei Optionen, dann die Auflösung
3. **Sa 14:00–16:15** (135 min) · Ein Skill pro Stream · _ohne Chat_
   - Titel: „🎯 Fadenkreuz-Training | Tag 1 | Mein Aim braucht Hilfe“
   - Alternativen: „🎯 Aim-Woche, Tag 1 | Heute trifft ALLES. Hoffentlich.“ · „🔴 Ranked-Nachmittag | Heute wird geklettert – komm mit!“
   - Titel fürs Kurzvideo: „Warum verliere ich an dieser Ecke immer?“ · „Vorher, nachher: sitzt das Fadenkreuz?“
   - Tags: Valorant, Deutsch, Shooter, Lernen, Training
   - Vorbereitung (Sa 13:30): Eine Fähigkeit auswählen und aufschreiben, woran man sie erkennt
   - Clip (So): Zwei Szenen nebeneinander: vorher und nachher, mit einer Zeile, was sich geändert hat

Mini-Serie: Ein Skill pro Stream – Folge 1: Ausgangslage aufnehmen · Folge 2: gezielt üben · Folge 3: vorher und nachher vergleichen

### 15–20 Zuschauer

1. **Mo 18:00–20:30** (150 min) · Ein Skill pro Stream · _ohne Chat_
   - Titel: „🎯 Aim-Woche, Tag 1 | Heute trifft ALLES. Hoffentlich.“
   - Alternativen: „🔴 Ranked-Abend | Heute wird geklettert – komm mit!“ · „🎯 Fadenkreuz-Training | Tag 1 | Mein Aim braucht Hilfe“
   - Titel fürs Kurzvideo: „Warum verliere ich an dieser Ecke immer?“ · „Vorher, nachher: sitzt das Fadenkreuz?“
   - Tags: Valorant, Deutsch, Shooter, Lernen, Training
   - Vorbereitung (Mo 17:30): Eine Fähigkeit auswählen und aufschreiben, woran man sie erkennt
   - Clip (Di): Zwei Szenen nebeneinander: vorher und nachher, mit einer Zeile, was sich geändert hat
2. **Mi 18:00–20:30** (150 min) · Der Chat bestimmt die Regel · _kleiner Chat_
   - Titel: „😂 Chaos-Abend in Valorant | Skill optional“
   - Alternativen: „🎲 Der Chat macht die Regeln | Ich muss trotzdem gewinnen“ · „😂 Jedes Match mit nur einer Waffe | Ihr habt das so gewollt“
   - Titel fürs Kurzvideo: „Wie lange halte ich mit nur einer Waffe durch?“ · „Der Chat hat die Regel gewählt …“
   - Tags: Valorant, Deutsch, Shooter, Challenge, Community
   - Vorbereitung (Mi 17:30): Drei spielbare Regeln aufschreiben
   - Clip (Do): Bester Moment mit der Regel, Regel als Einblendung
3. **Fr 19:00–21:30** (150 min) · Ein Coach schaut zu · _ohne Chat, mit Mitspieler_
   - Titel: „🎧 Live-Coaching | Hör mit, was ich alles falsch mache“
   - Alternativen: „🎧 Coach im Ohr | Ranked | Werde ich heute endlich besser?“ · „🔴 Ranked Grind | Heute wird GESCHWITZT“
   - Titel fürs Kurzvideo: „Ein Coach sieht meine schlechteste Runde“ · „Ein Tipp, der sofort hilft“
   - Tags: Valorant, Deutsch, Shooter, Coaching
   - Vorbereitung (Fr 18:30): Einverständnis der Mitspieler klären, dass ihre Stimme im Stream zu hören ist
   - Clip (Sa): Der Tipp des Coaches und die Szene, in der er klappt
4. **Sa 14:00–16:30** (150 min) · Rollenwechsel: Was ändert sich? · _ohne Chat_
   - Titel: „😬 Heute spiele ich die Rolle, die ich hasse | Das wird was“
   - Alternativen: „🔴 Ranked Grind | Heute wird GESCHWITZT“ · „🔁 Rollentausch | Raus aus der Komfortzone | Komm rein und leide mit!“
   - Titel fürs Kurzvideo: „Wie schlecht bin ich abseits meiner Main-Rolle?“ · „Neue Rolle, null Ausreden“
   - Tags: Valorant, Deutsch, Shooter, Rollenwechsel
   - Vorbereitung (Sa 13:30): Die neue Rolle kurz im Übungsmodus ausprobieren
   - Clip (So): Der Moment, in dem die neue Rolle klappt oder schiefgeht, mit einer Zeile Erklärung

Mini-Serie: Ein Skill pro Stream – Folge 1: Ausgangslage aufnehmen · Folge 2: gezielt üben · Folge 3: vorher und nachher vergleichen

## Battle Royale: Fortnite

### 0–3 Zuschauer

1. **Mo 18:00–19:45** (105 min) · Landeplatz-Vergleich · _ohne Chat_
   - Titel: „🪂 Neuer Lieblings-Drop gesucht | Tag 1 | Hot Drop oder Ecke?“
   - Alternativen: „🔴 Ranked-Abend | Heute wird geklettert – komm mit!“ · „🪂 Landeplatz-Test | Zwei Orte, ein Sieger | Rate mit!“
   - Titel fürs Kurzvideo: „Heißer Landeplatz oder ruhige Ecke?“ · „Zwei Landeplätze, nur einer bleibt“
   - Tags: Fortnite, Deutsch, BattleRoyale, Strategie, Vergleich
   - Vorbereitung (Mo 17:30): Zwei Orte auswählen und eine kleine Notiztabelle anlegen
   - Clip (Di): Gegenüberstellung beider Orte mit dem Ergebnis als Einblendung
2. **Fr 19:00–20:45** (105 min) · Rotation oder Risiko? · _ohne Chat_
   - Titel: „🔴 Ranked-Abend | Heute wird geklettert – komm mit!“
   - Alternativen: „🏆 Siegjagd mit Plan | Jede Zone zählt | Komm rein!“ · „🏆 Erst ein Sieg, dann Feierabend | Wie lange dauert's heute?“
   - Titel fürs Kurzvideo: „Rotieren oder bleiben?“ · „Warum sterbe ich immer in der Zone?“
   - Tags: Fortnite, Deutsch, BattleRoyale, Analyse, Strategie
   - Vorbereitung (Fr 18:30): Marker-Taste (Twitch „Stream-Marker“) oder Notizzettel bereitlegen
   - Clip (Sa): Sicht bis zur Entscheidung, Standbild, dann die Auflösung

### 5–10 Zuschauer

1. **Mo 18:00–20:15** (135 min) · Der Chat wählt den Landeplatz · _kleiner Chat_
   - Titel: „😂 Ihr wählt jeden Landeplatz | Das kann ja heiter werden“
   - Alternativen: „😂 Chaos-Drops in Fortnite | Wo landen wir diesmal?“ · „🎯 Chat wählt den Drop | Überlebe ich das? Eher nicht.“
   - Titel fürs Kurzvideo: „Mein Chat hat mich hierhin geschickt“ · „Überlebe ich da?“
   - Tags: Fortnite, Deutsch, BattleRoyale, Community, Challenge
   - Vorbereitung (Mo 17:30): Liste mit Orten bereitlegen
   - Clip (Di): Landung und bester Moment am gewählten Ort
2. **Mi 18:00–20:15** (135 min) · Landeplatz-Vergleich · _ohne Chat_
   - Titel: „🔴 Ranked-Abend | Heute wird geklettert – komm mit!“
   - Alternativen: „🪂 Landeplatz-Test | Zwei Orte, ein Sieger | Rate mit!“ · „🪂 Neuer Lieblings-Drop gesucht | Tag 1 | Hot Drop oder Ecke?“
   - Titel fürs Kurzvideo: „Heißer Landeplatz oder ruhige Ecke?“ · „Zwei Landeplätze, nur einer bleibt“
   - Tags: Fortnite, Deutsch, BattleRoyale, Strategie, Vergleich
   - Vorbereitung (Mi 17:30): Zwei Orte auswählen und eine kleine Notiztabelle anlegen
   - Clip (Do): Gegenüberstellung beider Orte mit dem Ergebnis als Einblendung
3. **Sa 14:00–16:15** (135 min) · Rotation oder Risiko? · _ohne Chat_
   - Titel: „🏆 Siegjagd mit Plan | Jede Zone zählt | Komm rein!“
   - Alternativen: „🏆 Erst ein Sieg, dann Feierabend | Wie lange dauert's heute?“ · „🔴 Ranked-Nachmittag | Heute wird geklettert – komm mit!“
   - Titel fürs Kurzvideo: „Rotieren oder bleiben?“ · „Warum sterbe ich immer in der Zone?“
   - Tags: Fortnite, Deutsch, BattleRoyale, Analyse, Strategie
   - Vorbereitung (Sa 13:30): Marker-Taste (Twitch „Stream-Marker“) oder Notizzettel bereitlegen
   - Clip (So): Sicht bis zur Entscheidung, Standbild, dann die Auflösung

### 15–20 Zuschauer

1. **Mo 18:00–20:30** (150 min) · Ausrüstungs-Labor · _ohne Chat_
   - Titel: „🔬 Loadout-Labor | Test 1 | Welche Kombi holt den SIEG?“
   - Alternativen: „🔴 Ranked-Abend | Heute wird geklettert – komm mit!“ · „🔬 Zwei Loadouts, ein Gewinner | Tüftel mit!“
   - Titel fürs Kurzvideo: „Welche Ausrüstung bringt mich weiter?“ · „Bauchgefühl oder Zahlen?“
   - Tags: Fortnite, Deutsch, BattleRoyale, Experiment
   - Vorbereitung (Mo 17:30): Kriterien festlegen (z. B. gewonnene Kämpfe, Überlebenszeit)
   - Clip (Di): Bestes Gefecht mit jeder Ausrüstung, Ergebnis am Ende
2. **Mi 18:00–20:30** (150 min) · Teamkommunikation vorher und nachher · _ohne Chat, mit Mitspieler_
   - Titel: „🏆 Erst ein Sieg, dann Feierabend | Komm rein!“
   - Alternativen: „📢 Squad mit Ansagen | Endlich sagt mal jemand was Sinnvolles“ · „📢 Squad-Abend | Heute holen wir den Sieg zusammen“
   - Titel fürs Kurzvideo: „Chaos-Ansage gegen klare Ansage“ · „Spielen wir mit klaren Ansagen besser?“
   - Tags: Fortnite, Deutsch, BattleRoyale, Squad, Teamplay
   - Vorbereitung (Mi 17:30): Einverständnis der Mitspieler klären, dass ihre Stimme im Stream zu hören ist
   - Clip (Do): Chaotische Ansage vorher gegen klare Ansage nachher
3. **Fr 19:00–21:30** (150 min) · Der Chat wählt den Landeplatz · _kleiner Chat_
   - Titel: „🎯 Chat wählt den Drop | Überlebe ich das? Eher nicht.“
   - Alternativen: „😂 Ihr wählt jeden Landeplatz | Das kann ja heiter werden“ · „😂 Chaos-Drops in Fortnite | Wo landen wir diesmal?“
   - Titel fürs Kurzvideo: „Mein Chat hat mich hierhin geschickt“ · „Überlebe ich da?“
   - Tags: Fortnite, Deutsch, BattleRoyale, Community, Challenge
   - Vorbereitung (Fr 18:30): Liste mit Orten bereitlegen
   - Clip (Sa): Landung und bester Moment am gewählten Ort
4. **Sa 14:00–16:30** (150 min) · Landeplatz-Vergleich · _ohne Chat_
   - Titel: „🪂 Neuer Lieblings-Drop gesucht | Tag 1 | Hot Drop oder Ecke?“
   - Alternativen: „🔴 Ranked-Nachmittag | Heute wird geklettert – komm mit!“ · „🪂 Landeplatz-Test | Zwei Orte, ein Sieger | Rate mit!“
   - Titel fürs Kurzvideo: „Heißer Landeplatz oder ruhige Ecke?“ · „Zwei Landeplätze, nur einer bleibt“
   - Tags: Fortnite, Deutsch, BattleRoyale, Strategie, Vergleich
   - Vorbereitung (Sa 13:30): Zwei Orte auswählen und eine kleine Notiztabelle anlegen
   - Clip (So): Gegenüberstellung beider Orte mit dem Ergebnis als Einblendung

Mini-Serie: Ausrüstungs-Labor – Folge 1: Variante A · Folge 2: Variante B · Folge 3: fairer Vergleich

## MOBA: League of Legends

### 0–3 Zuschauer

1. **Mo 18:00–19:45** (105 min) · Wo habe ich das Match verloren? · _ohne Chat_
   - Titel: „🔴 Ranked-Abend | Tag 1 | Heute wird geklettert“
   - Alternativen: „🔴 Ranked Grind | Heute wird geklettert“ · „⚔️ Weniger feeden, mehr gewinnen | Ranked | Der Plan steht“
   - Titel fürs Kurzvideo: „Wo habe ich dieses Match verloren?“ · „Der eine Fehler, der mich das Match kostet“
   - Tags: LeagueOfLegends, Deutsch, MOBA, Analyse
   - Vorbereitung (Mo 17:30): Wiederholungsfunktion oder lokale Aufnahme testen
   - Clip (Di): Szene bis zum Fehler, Standbild, Erklärung in einem Satz
2. **Fr 19:00–20:45** (105 min) · Neuer Charakter von null · _ohne Chat_
   - Titel: „🔴 Ranked Grind | Heute wird geklettert“
   - Alternativen: „🆕 Ich lerne einen neuen Main | Komm rein und lach mit!“ · „⚔️ Neuer Main, Tag 1 | 90 % Hoffnung, 10 % Skill“
   - Titel fürs Kurzvideo: „Der erste richtige Erfolg mit dem neuen Charakter“ · „Wie lange, bis der neue Charakter sitzt?“
   - Tags: LeagueOfLegends, Deutsch, MOBA, Lernen
   - Vorbereitung (Fr 18:30): Grundlagen des Charakters im Übungsmodus ansehen
   - Clip (Sa): Der erste richtige Erfolg mit dem neuen Charakter

Mini-Serie: Neuer Charakter von null – Tag 1: erste Matches · Tag 2: gezielte Lernziele · Tag 3: Vergleich mit Tag 1

### 5–10 Zuschauer

1. **Mo 18:00–20:15** (135 min) · Der Chat wählt den Charakter · _kleiner Chat_
   - Titel: „😂 Ihr wählt meinen Charakter | Gewinne ich trotzdem?“
   - Alternativen: „😂 Chaos-Abend in League of Legends | Wer feedet zuerst?“ · „🎲 Chat-Picks only | Sucht mir was Schlimmes aus“
   - Titel fürs Kurzvideo: „Gewinne ich mit dem Charakter vom Chat?“ · „Chat-Pick, den ich nie spiele“
   - Tags: LeagueOfLegends, Deutsch, MOBA, Community
   - Vorbereitung (Mo 17:30): Charaktere auswählen, die du grundsätzlich spielen kannst
   - Clip (Di): Bester Moment mit dem gewählten Charakter
2. **Mi 18:00–20:15** (135 min) · Wo habe ich das Match verloren? · _ohne Chat_
   - Titel: „🔴 Ranked Grind | Heute wird geklettert“
   - Alternativen: „⚔️ Weniger feeden, mehr gewinnen | Ranked | Der Plan steht“ · „🔴 Ranked-Abend | Tag 1 | Heute wird geklettert“
   - Titel fürs Kurzvideo: „Wo habe ich dieses Match verloren?“ · „Der eine Fehler, der mich das Match kostet“
   - Tags: LeagueOfLegends, Deutsch, MOBA, Analyse
   - Vorbereitung (Mi 17:30): Wiederholungsfunktion oder lokale Aufnahme testen
   - Clip (Do): Szene bis zum Fehler, Standbild, Erklärung in einem Satz
3. **Sa 14:00–16:15** (135 min) · Neuer Charakter von null · _ohne Chat_
   - Titel: „🆕 Ich lerne einen neuen Main | Komm rein und lach mit!“
   - Alternativen: „⚔️ Neuer Main, Tag 1 | 90 % Hoffnung, 10 % Skill“ · „🔴 Ranked Grind | Heute wird geklettert“
   - Titel fürs Kurzvideo: „Der erste richtige Erfolg mit dem neuen Charakter“ · „Wie lange, bis der neue Charakter sitzt?“
   - Tags: LeagueOfLegends, Deutsch, MOBA, Lernen
   - Vorbereitung (Sa 13:30): Grundlagen des Charakters im Übungsmodus ansehen
   - Clip (So): Der erste richtige Erfolg mit dem neuen Charakter

Mini-Serie: Neuer Charakter von null – Tag 1: erste Matches · Tag 2: gezielte Lernziele · Tag 3: Vergleich mit Tag 1

### 15–20 Zuschauer

1. **Mo 18:00–20:30** (150 min) · Neuer Charakter von null · _ohne Chat_
   - Titel: „⚔️ Neuer Main, Tag 1 | 90 % Hoffnung, 10 % Skill“
   - Alternativen: „🔴 Ranked Grind | Heute wird geklettert“ · „🆕 Ich lerne einen neuen Main | Komm rein und lach mit!“
   - Titel fürs Kurzvideo: „Der erste richtige Erfolg mit dem neuen Charakter“ · „Wie lange, bis der neue Charakter sitzt?“
   - Tags: LeagueOfLegends, Deutsch, MOBA, Lernen
   - Vorbereitung (Mo 17:30): Grundlagen des Charakters im Übungsmodus ansehen
   - Clip (Di): Der erste richtige Erfolg mit dem neuen Charakter
2. **Mi 18:00–20:30** (150 min) · Heute zählt nur ein Wert · _ohne Chat_
   - Titel: „🔴 Ranked-Abend | Heute wird geklettert – komm mit!“
   - Alternativen: „🌾 Last-Hit-Grind ohne Gnade | Tag 1 | Zähl mit!“ · „🌾 Farm-Challenge | 70 Last Hits in 10 Minuten | Schaffe ich das HEUTE?“
   - Titel fürs Kurzvideo: „Neuer Bestwert beim Farmen?“ · „Nur eine Zahl zählt“
   - Tags: LeagueOfLegends, Deutsch, MOBA, Training
   - Vorbereitung (Mi 17:30): Zielwert und Notiztabelle festlegen
   - Clip (Do): Kurzer Zusammenschnitt: der Wert nach jedem Match
3. **Fr 19:00–21:30** (150 min) · Der Chat wählt den Charakter · _kleiner Chat_
   - Titel: „🎲 Chat-Picks only | Sucht mir was Schlimmes aus“
   - Alternativen: „😂 Ihr wählt meinen Charakter | Gewinne ich trotzdem?“ · „😂 Chaos-Abend in League of Legends | Wer feedet zuerst?“
   - Titel fürs Kurzvideo: „Gewinne ich mit dem Charakter vom Chat?“ · „Chat-Pick, den ich nie spiele“
   - Tags: LeagueOfLegends, Deutsch, MOBA, Community
   - Vorbereitung (Fr 18:30): Charaktere auswählen, die du grundsätzlich spielen kannst
   - Clip (Sa): Bester Moment mit dem gewählten Charakter
4. **Sa 14:00–16:30** (150 min) · Duo mit erfahrenem Mitspieler · _ohne Chat, mit Mitspieler_
   - Titel: „👥 Duo-Nachmittag mit Profi | Trägt er mich heute nach oben?“
   - Alternativen: „🔴 Ranked Grind | Heute wird geklettert“ · „👥 Duo-Queue mit Coach | Hör mit, wie ich lerne“
   - Titel fürs Kurzvideo: „Was sieht mein Duo, das ich übersehe?“ · „Ein Tipp vom Duo, sofort umgesetzt“
   - Tags: LeagueOfLegends, Deutsch, MOBA, Duo, Coaching
   - Vorbereitung (Sa 13:30): Einverständnis der Mitspieler klären, dass ihre Stimme im Stream zu hören ist
   - Clip (So): Tipp und Szene, in der er klappt

Mini-Serie: Neuer Charakter von null – Tag 1: erste Matches · Tag 2: gezielte Lernziele · Tag 3: Vergleich mit Tag 1

## Story/Singleplayer: Hollow Knight

### 0–3 Zuschauer

1. **Mo 18:00–19:45** (105 min) · Versuche zählen bis zum Durchbruch · _ohne Chat_
   - Titel: „💀 Heute fällt der Boss | Ich gebe nicht auf. Vielleicht.“
   - Alternativen: „🗡️ Heute geht's WEIT voran | Komm mit!“ · „💀 Todeszähler läuft | Wie oft sterbe ich HEUTE?“
   - Titel fürs Kurzvideo: „Versuch 1 gegen den Versuch, der geklappt hat“ · „Wie viele Versuche hat dieser Abschnitt gebraucht?“
   - Tags: HollowKnight, Deutsch, Singleplayer, Challenge
   - Vorbereitung (Mo 17:30): Zähler-Einblendung oder Notiz vorbereiten
   - Clip (Di): Erster Versuch neben dem erfolgreichen Versuch
2. **Fr 19:00–20:45** (105 min) · Erster Durchgang in Etappen · _ohne Chat_
   - Titel: „📖 Gemütlicher Story-Abend | Komm mit auf die Reise“
   - Alternativen: „🗡️ Blind weiter | Teil 1 | Was erwartet uns heute?“ · „📖 Erster Durchgang | Teil 1 | Keine Spoiler!“
   - Titel fürs Kurzvideo: „Meine ehrliche erste Reaktion“ · „Damit habe ich nicht gerechnet“
   - Tags: HollowKnight, Deutsch, Singleplayer, ErsterDurchgang, Story
   - Vorbereitung (Fr 18:30): Etappenziel festlegen (Kapitel oder Gebiet)
   - Clip (Sa): Ehrliche erste Reaktion auf eine Wendung – ohne das Ende zu verraten

Mini-Serie: Erster Durchgang in Etappen – Etappe 1: Anfang und erste Eindrücke · Etappe 2: Mitte und Vermutungen · Etappe 3: Ende und Fazit

### 5–10 Zuschauer

1. **Mo 18:00–20:15** (135 min) · Der Chat trifft die Entscheidungen · _kleiner Chat_
   - Titel: „😅 Ihr trefft jede Entscheidung | Wie schlimm endet das?“
   - Alternativen: „😅 Lachen und Leiden in Hollow Knight | Leidest du mit?“ · „🎲 Chat schreibt meine Geschichte | Stimm ab!“
   - Titel fürs Kurzvideo: „Der Chat hat entschieden …“ · „Diese Entscheidung hatte Folgen“
   - Tags: HollowKnight, Deutsch, Singleplayer, Community, Entscheidungen
   - Vorbereitung (Mo 17:30): Prüfen, dass das Spiel echte Entscheidungen hat
   - Clip (Di): Entscheidung und ihre Folge in einem Clip
2. **Mi 18:00–20:15** (135 min) · Erster Durchgang in Etappen · _ohne Chat_
   - Titel: „📖 Gemütlicher Story-Abend | Komm mit auf die Reise“
   - Alternativen: „🗡️ Blind weiter | Teil 1 | Was erwartet uns heute?“ · „📖 Erster Durchgang | Teil 1 | Keine Spoiler!“
   - Titel fürs Kurzvideo: „Meine ehrliche erste Reaktion“ · „Damit habe ich nicht gerechnet“
   - Tags: HollowKnight, Deutsch, Singleplayer, ErsterDurchgang, Story
   - Vorbereitung (Mi 17:30): Etappenziel festlegen (Kapitel oder Gebiet)
   - Clip (Do): Ehrliche erste Reaktion auf eine Wendung – ohne das Ende zu verraten
3. **Sa 14:00–16:15** (135 min) · Erkunden statt durchrennen · _ohne Chat_
   - Titel: „🧭 Langsam & gründlich | Entdeck mit mir!“
   - Alternativen: „🧭 Jede Ecke, jedes Geheimnis | Heute wird nichts übersprungen“ · „📖 Gemütlicher Story-Nachmittag | Komm mit auf die Reise“
   - Titel fürs Kurzvideo: „Drei Dinge, die du vielleicht übersehen hast“ · „Was man hier beim ersten Mal übersieht“
   - Tags: HollowKnight, Deutsch, Singleplayer, Erkunden, Entspannt
   - Vorbereitung (Sa 13:30): Ein Gebiet zum Erkunden auswählen
   - Clip (So): Drei Entdeckungen in 30 Sekunden

Mini-Serie: Erster Durchgang in Etappen – Etappe 1: Anfang und erste Eindrücke · Etappe 2: Mitte und Vermutungen · Etappe 3: Ende und Fazit

### 15–20 Zuschauer

1. **Mo 18:00–20:30** (150 min) · Erster Durchgang in Etappen · _ohne Chat_
   - Titel: „📖 Erster Durchgang | Teil 1 | Keine Spoiler!“
   - Alternativen: „📖 Gemütlicher Story-Abend | Komm mit auf die Reise“ · „🗡️ Blind weiter | Teil 1 | Was erwartet uns heute?“
   - Titel fürs Kurzvideo: „Meine ehrliche erste Reaktion“ · „Damit habe ich nicht gerechnet“
   - Tags: HollowKnight, Deutsch, Singleplayer, ErsterDurchgang, Story
   - Vorbereitung (Mo 17:30): Etappenziel festlegen (Kapitel oder Gebiet)
   - Clip (Di): Ehrliche erste Reaktion auf eine Wendung – ohne das Ende zu verraten
2. **Mi 18:00–20:30** (150 min) · Der Chat trifft die Entscheidungen · _kleiner Chat_
   - Titel: „😅 Lachen und Leiden in Hollow Knight | Leidest du mit?“
   - Alternativen: „🎲 Chat schreibt meine Geschichte | Stimm ab!“ · „😅 Ihr trefft jede Entscheidung | Wie schlimm endet das?“
   - Titel fürs Kurzvideo: „Der Chat hat entschieden …“ · „Diese Entscheidung hatte Folgen“
   - Tags: HollowKnight, Deutsch, Singleplayer, Community, Entscheidungen
   - Vorbereitung (Mi 17:30): Prüfen, dass das Spiel echte Entscheidungen hat
   - Clip (Do): Entscheidung und ihre Folge in einem Clip
3. **Fr 19:00–21:30** (150 min) · Die Geschichte bisher in 5 Minuten · _ohne Chat_
   - Titel: „📖 Story-Abend | Teil 1 | Wohin führt uns die Geschichte?“
   - Alternativen: „📖 Neu hier? 5-Minuten-Rückblick | Dann geht's weiter!“ · „📖 Gemütlicher Story-Abend | Komm mit auf die Reise“
   - Titel fürs Kurzvideo: „Die Geschichte bisher in 60 Sekunden“ · „Meine Theorie zur Geschichte“
   - Tags: HollowKnight, Deutsch, Singleplayer, Story, Lore
   - Vorbereitung (Fr 18:30): Stichpunkte für die Zusammenfassung schreiben
   - Clip (Sa): Die Zusammenfassung als 60-Sekunden-Kurzvideo
4. **Sa 14:00–16:30** (150 min) · Versuche zählen bis zum Durchbruch · _ohne Chat_
   - Titel: „💀 Heute fällt der Boss | Ich gebe nicht auf. Vielleicht.“
   - Alternativen: „🗡️ Heute geht's WEIT voran | Komm mit!“ · „💀 Todeszähler läuft | Wie oft sterbe ich HEUTE?“
   - Titel fürs Kurzvideo: „Versuch 1 gegen den Versuch, der geklappt hat“ · „Wie viele Versuche hat dieser Abschnitt gebraucht?“
   - Tags: HollowKnight, Deutsch, Singleplayer, Challenge
   - Vorbereitung (Sa 13:30): Zähler-Einblendung oder Notiz vorbereiten
   - Clip (So): Erster Versuch neben dem erfolgreichen Versuch

Mini-Serie: Erster Durchgang in Etappen – Etappe 1: Anfang und erste Eindrücke · Etappe 2: Mitte und Vermutungen · Etappe 3: Ende und Fazit

## Horror: Phasmophobia

### 0–3 Zuschauer

1. **Mo 18:00–19:45** (105 min) · Ehrliche Reaktionen mit Facecam · _ohne Chat_
   - Titel: „👻 Licht aus, Ton laut | Wie oft schreie ich heute?“
   - Alternativen: „😱 Horror-Abend in Phasmophobia | Lachen oder schreien?“ · „😱 Horror mit Facecam | Komm rein, wenn du dich traust!“
   - Titel fürs Kurzvideo: „Meine ehrliche Reaktion auf diesen Moment“ · „Bin ich zu schreckhaft für dieses Spiel?“
   - Tags: Phasmophobia, Deutsch, Horror, Facecam
   - Vorbereitung (Mo 17:30): Facecam und Licht prüfen, damit Reaktionen gut zu sehen sind
   - Clip (Di): Kurz vor dem Schreckmoment beginnen, Facecam groß, höchstens 30 Sekunden
2. **Fr 19:00–20:45** (105 min) · Mutprobe in drei Stufen · _ohne Chat_
   - Titel: „😱 Horror-Abend in Phasmophobia | Lachen oder schreien?“
   - Alternativen: „😱 Ich bin ein ANGSTHASE | Mutprobe-Abend | Halt mir die Hand“ · „🕯️ Mutprobe | Stufe für Stufe dunkler | Wie weit komme ich?“
   - Titel fürs Kurzvideo: „Stufe 3: Licht aus, Ton lauter“ · „Bis zu welcher Stufe halte ich durch?“
   - Tags: Phasmophobia, Deutsch, Horror, Challenge
   - Vorbereitung (Fr 18:30): Stufen als Einblendung vorbereiten
   - Clip (Sa): Reaktion auf der höchsten Stufe

### 5–10 Zuschauer

1. **Mo 18:00–20:15** (135 min) · Der Chat tippt den nächsten Schreckmoment · _kleiner Chat_
   - Titel: „😱 Schreck-Wetten | Wer ahnt den nächsten Jumpscare?“
   - Alternativen: „😱 Horror-Abend in Phasmophobia | Lachen oder schreien?“ · „🎲 Tipp mit, wann's knallt | Komm rein, wenn du dich traust!“
   - Titel fürs Kurzvideo: „Der Chat wusste es vor mir“ · „Wer ahnt den Schreck zuerst?“
   - Tags: Phasmophobia, Deutsch, Horror, Community
   - Vorbereitung (Mo 17:30): Abschnitte grob einteilen
   - Clip (Di): Tipp im Chat und der Schreckmoment direkt danach
2. **Mi 18:00–20:15** (135 min) · Mutprobe in drei Stufen · _ohne Chat_
   - Titel: „😱 Horror-Abend in Phasmophobia | Lachen oder schreien?“
   - Alternativen: „😱 Ich bin ein ANGSTHASE | Mutprobe-Abend | Halt mir die Hand“ · „🕯️ Mutprobe | Stufe für Stufe dunkler | Wie weit komme ich?“
   - Titel fürs Kurzvideo: „Stufe 3: Licht aus, Ton lauter“ · „Bis zu welcher Stufe halte ich durch?“
   - Tags: Phasmophobia, Deutsch, Horror, Challenge
   - Vorbereitung (Mi 17:30): Stufen als Einblendung vorbereiten
   - Clip (Do): Reaktion auf der höchsten Stufe
3. **Sa 14:00–16:15** (135 min) · Was ist hier passiert? Hinweise ordnen · _ohne Chat_
   - Titel: „🔎 Gruseliges Rätsel | Ermittle mit!“
   - Alternativen: „🕯️ Spurensuche | Teil 1 | Lösen wir heute das Rätsel?“ · „🕯️ Gemütlicher Grusel-Nachmittag | Trau dich rein“
   - Titel fürs Kurzvideo: „Was ist hier wirklich passiert?“ · „Dieser Hinweis ändert alles“
   - Tags: Phasmophobia, Deutsch, Horror, Lore
   - Vorbereitung (Sa 13:30): Notizzettel für gefundene Hinweise anlegen
   - Clip (So): Kurze Erklärung mit Bildern der Hinweise

Mini-Serie: Was ist hier passiert? Hinweise ordnen – Teil 1: erste Hinweise · Teil 2: neue Spuren · Teil 3: die Auflösung

### 15–20 Zuschauer

1. **Mo 18:00–20:30** (150 min) · Koop-Nacht mit Freunden · _ohne Chat, mit Mitspieler_
   - Titel: „👻 Koop-Horror mit Freunden | Wer schreit zuerst?“
   - Alternativen: „😱 Horror-Abend in Phasmophobia | Lachen oder schreien?“ · „😂 Horror-Squad am Start | Wir sterben alle. Gemeinsam.“
   - Titel fürs Kurzvideo: „Wir haben gesagt, wir bleiben zusammen …“ · „Wer von uns bleibt ruhig?“
   - Tags: Phasmophobia, Deutsch, Horror, Koop
   - Vorbereitung (Mo 17:30): Einverständnis der Mitspieler klären, dass ihre Stimme im Stream zu hören ist
   - Clip (Di): Gruppenreaktion auf einen Schreckmoment
2. **Mi 18:00–20:30** (150 min) · Der Chat tippt den nächsten Schreckmoment · _kleiner Chat_
   - Titel: „😱 Horror-Abend in Phasmophobia | Lachen oder schreien?“
   - Alternativen: „🎲 Tipp mit, wann's knallt | Komm rein, wenn du dich traust!“ · „😱 Schreck-Wetten | Wer ahnt den nächsten Jumpscare?“
   - Titel fürs Kurzvideo: „Der Chat wusste es vor mir“ · „Wer ahnt den Schreck zuerst?“
   - Tags: Phasmophobia, Deutsch, Horror, Community
   - Vorbereitung (Mi 17:30): Abschnitte grob einteilen
   - Clip (Do): Tipp im Chat und der Schreckmoment direkt danach
3. **Fr 19:00–21:30** (150 min) · Was ist hier passiert? Hinweise ordnen · _ohne Chat_
   - Titel: „🔎 Gruseliges Rätsel | Ermittle mit!“
   - Alternativen: „🕯️ Spurensuche | Teil 1 | Lösen wir heute das Rätsel?“ · „🕯️ Gemütlicher Grusel-Abend | Trau dich rein“
   - Titel fürs Kurzvideo: „Was ist hier wirklich passiert?“ · „Dieser Hinweis ändert alles“
   - Tags: Phasmophobia, Deutsch, Horror, Lore
   - Vorbereitung (Fr 18:30): Notizzettel für gefundene Hinweise anlegen
   - Clip (Sa): Kurze Erklärung mit Bildern der Hinweise
4. **Sa 14:00–16:30** (150 min) · Ehrliche Reaktionen mit Facecam · _ohne Chat_
   - Titel: „👻 Licht aus, Ton laut | Wie oft schreie ich heute?“
   - Alternativen: „😱 Horror-Nachmittag in Phasmophobia | Lachen oder schreien?“ · „😱 Horror mit Facecam | Komm rein, wenn du dich traust!“
   - Titel fürs Kurzvideo: „Meine ehrliche Reaktion auf diesen Moment“ · „Bin ich zu schreckhaft für dieses Spiel?“
   - Tags: Phasmophobia, Deutsch, Horror, Facecam
   - Vorbereitung (Sa 13:30): Facecam und Licht prüfen, damit Reaktionen gut zu sehen sind
   - Clip (So): Kurz vor dem Schreckmoment beginnen, Facecam groß, höchstens 30 Sekunden

Mini-Serie: Was ist hier passiert? Hinweise ordnen – Teil 1: erste Hinweise · Teil 2: neue Spuren · Teil 3: die Auflösung

## Cozy/Simulation: Stardew Valley

### 0–3 Zuschauer

1. **Mo 18:00–19:45** (105 min) · Vorher/Nachher: ein Ort wird neu gestaltet · _ohne Chat_
   - Titel: „🏡 Großer Umbau | Wie schön wird's bis Stream-Ende?“
   - Alternativen: „☕ Gemütlicher Abend in Stardew Valley | Kaffee & Quatschen“ · „🏡 Vorher: trostlos. Nachher: ? | Gib mir Tipps!“
   - Titel fürs Kurzvideo: „Vorher trostlos – und nachher?“ · „Von leer zu gemütlich“
   - Tags: StardewValley, Deutsch, Simulation, Gestalten, Gemütlich
   - Vorbereitung (Mo 17:30): Vorher-Screenshot machen
   - Clip (Di): Vorher/Nachher-Übergang in 15 Sekunden
2. **Fr 19:00–20:45** (105 min) · Gemütlich, aber mit einer Regel · _ohne Chat_
   - Titel: „😄 Gemütliches Chaos in Stardew Valley | Was geht heute schief?“
   - Alternativen: „🎨 Gemütlich, aber mit Regel | Was kann da schon schiefgehen?“ · „😄 Alles mit nur einer Farbe | Bleibt's trotzdem gemütlich?“
   - Titel fürs Kurzvideo: „Nur eine Farbe – geht das?“ · „Das Ergebnis mit nur einer Regel“
   - Tags: StardewValley, Deutsch, Simulation, Challenge, Gemütlich
   - Vorbereitung (Fr 18:30): Regel als Einblendung vorbereiten
   - Clip (Sa): Rundgang durch das Ergebnis der Regel

### 5–10 Zuschauer

1. **Mo 18:00–20:15** (135 min) · Der Chat gibt Namen und Wünsche · _kleiner Chat_
   - Titel: „🏷️ Ihr gebt die Namen | Wie heißt unser neues Zuhause?“
   - Alternativen: „☕ Gemütlicher Abend in Stardew Valley | Kaffee & Quatschen“ · „🏷️ Namens-Abend | Tauf mit!“
   - Titel fürs Kurzvideo: „Mein Chat hat diesen Ort mitgestaltet“ · „Die Namen kommen vom Chat“
   - Tags: StardewValley, Deutsch, Simulation, Community, Gemütlich
   - Vorbereitung (Mo 17:30): Regeln für Namen festlegen (freundlich, keine echten Namen)
   - Clip (Di): Rundgang mit den Namen aus dem Chat
2. **Mi 18:00–20:15** (135 min) · Drei kleine Ziele für einen gemütlichen Stream · _ohne Chat_
   - Titel: „☕ Gemütlicher Abend in Stardew Valley | Kaffee & Quatschen“
   - Alternativen: „☕ Gemütlich Ziele abhaken | Kaffee & Quatschen“ · „🌱 Drei kleine Ziele | Woche 1 | Schaffen wir alle?“
   - Titel fürs Kurzvideo: „Drei Ziele, ein gemütlicher Stream“ · „Abgehakt: so sieht es jetzt aus“
   - Tags: StardewValley, Deutsch, Simulation, Gemütlich, Entspannt
   - Vorbereitung (Mi 17:30): Drei Ziele als Checkliste-Einblendung vorbereiten
   - Clip (Do): Zeitraffer des Fortschritts mit abgehakter Liste
3. **Sa 14:00–16:15** (135 min) · Vorher/Nachher: ein Ort wird neu gestaltet · _ohne Chat_
   - Titel: „🏡 Vorher: trostlos. Nachher: ? | Gib mir Tipps!“
   - Alternativen: „🏡 Großer Umbau | Wie schön wird's bis Stream-Ende?“ · „☕ Gemütlicher Nachmittag in Stardew Valley | Kaffee & Quatschen“
   - Titel fürs Kurzvideo: „Vorher trostlos – und nachher?“ · „Von leer zu gemütlich“
   - Tags: StardewValley, Deutsch, Simulation, Gestalten, Gemütlich
   - Vorbereitung (Sa 13:30): Vorher-Screenshot machen
   - Clip (So): Vorher/Nachher-Übergang in 15 Sekunden

Mini-Serie: Drei kleine Ziele für einen gemütlichen Stream – Woche 1: Start · Woche 2: Ausbau · Woche 3: Rückblick mit Vorher/Nachher

### 15–20 Zuschauer

1. **Mo 18:00–20:30** (150 min) · Drei kleine Ziele für einen gemütlichen Stream · _ohne Chat_
   - Titel: „🌱 Drei kleine Ziele | Woche 1 | Schaffen wir alle?“
   - Alternativen: „☕ Gemütlicher Abend in Stardew Valley | Kaffee & Quatschen“ · „☕ Gemütlich Ziele abhaken | Kaffee & Quatschen“
   - Titel fürs Kurzvideo: „Drei Ziele, ein gemütlicher Stream“ · „Abgehakt: so sieht es jetzt aus“
   - Tags: StardewValley, Deutsch, Simulation, Gemütlich, Entspannt
   - Vorbereitung (Mo 17:30): Drei Ziele als Checkliste-Einblendung vorbereiten
   - Clip (Di): Zeitraffer des Fortschritts mit abgehakter Liste
2. **Mi 18:00–20:30** (150 min) · Der Chat gibt Namen und Wünsche · _kleiner Chat_
   - Titel: „☕ Gemütlicher Abend in Stardew Valley | Kaffee & Quatschen“
   - Alternativen: „🏷️ Namens-Abend | Tauf mit!“ · „🏷️ Ihr gebt die Namen | Wie heißt unser neues Zuhause?“
   - Titel fürs Kurzvideo: „Mein Chat hat diesen Ort mitgestaltet“ · „Die Namen kommen vom Chat“
   - Tags: StardewValley, Deutsch, Simulation, Community, Gemütlich
   - Vorbereitung (Mi 17:30): Regeln für Namen festlegen (freundlich, keine echten Namen)
   - Clip (Do): Rundgang mit den Namen aus dem Chat
3. **Fr 19:00–21:30** (150 min) · Drei Dinge, die ich am Anfang gern gewusst hätte · _ohne Chat_
   - Titel: „☕ Frisch angefangen? | Wir starten zusammen!“
   - Alternativen: „🌱 Neu in Stardew Valley? | Gemütlich starten mit Tipps“ · „☕ Gemütlicher Abend in Stardew Valley | Kaffee & Quatschen“
   - Titel fürs Kurzvideo: „Was ich am Anfang gern gewusst hätte“ · „Ein Anfänger-Fehler, den du dir sparen kannst“
   - Tags: StardewValley, Deutsch, Simulation, Tipps, Gemütlich
   - Vorbereitung (Fr 18:30): Drei Tipps wählen und prüfen, dass sie in deiner Spielversion stimmen
   - Clip (Sa): Ein Tipp in 20 Sekunden
4. **Sa 14:00–16:30** (150 min) · Vorher/Nachher: ein Ort wird neu gestaltet · _ohne Chat_
   - Titel: „🏡 Großer Umbau | Wie schön wird's bis Stream-Ende?“
   - Alternativen: „☕ Gemütlicher Nachmittag in Stardew Valley | Kaffee & Quatschen“ · „🏡 Vorher: trostlos. Nachher: ? | Gib mir Tipps!“
   - Titel fürs Kurzvideo: „Vorher trostlos – und nachher?“ · „Von leer zu gemütlich“
   - Tags: StardewValley, Deutsch, Simulation, Gestalten, Gemütlich
   - Vorbereitung (Sa 13:30): Vorher-Screenshot machen
   - Clip (So): Vorher/Nachher-Übergang in 15 Sekunden

Mini-Serie: Drei kleine Ziele für einen gemütlichen Stream – Woche 1: Start · Woche 2: Ausbau · Woche 3: Rückblick mit Vorher/Nachher

## Sandbox/Survival: Minecraft

### 0–3 Zuschauer

1. **Mo 18:00–19:45** (105 min) · Warum funktioniert mein Bau nicht? · _ohne Chat_
   - Titel: „🔧 Warum läuft mein Bau nicht?! | Heute wird's gelöst“
   - Alternativen: „⛏️ Entspannt bauen in Minecraft | Komm rein und chill mit!“ · „🔧 Fehlersuche live | Hilf mir, bevor ich alles abreiße“
   - Titel fürs Kurzvideo: „Warum funktioniert mein Bau nicht?“ · „Die kleinste Korrektur, die funktioniert“
   - Tags: Minecraft, Deutsch, Sandbox, Bauen
   - Vorbereitung (Mo 17:30): Problemstelle im Spielstand markieren
   - Clip (Di): Fehler zuerst, dann die kleinste funktionierende Korrektur
2. **Fr 19:00–20:45** (105 min) · Neue Welt mit Tagesziel · _ohne Chat_
   - Titel: „⛏️ Entspannt bauen in Minecraft | Komm rein und chill mit!“
   - Alternativen: „🔥 Survival von null | Tag 1 | Überleb mit!“ · „⛏️ Neue Welt | Tag 1 | Überleben wir die Nacht?“
   - Titel fürs Kurzvideo: „Das war knapp“ · „Überlebe ich den ersten Tag?“
   - Tags: Minecraft, Deutsch, Sandbox, Survival
   - Vorbereitung (Fr 18:30): Weltregeln festlegen (Schwierigkeit, eigene Regeln)
   - Clip (Sa): Der knappste Moment des Tages

Mini-Serie: Neue Welt mit Tagesziel – Tag 1: Ankommen · Tag 2: Ausbau · Tag 3: erstes großes Ziel

### 5–10 Zuschauer

1. **Mo 18:00–20:15** (135 min) · Drei Lösungen für dieselbe Aufgabe · _ohne Chat_
   - Titel: „⛏️ Drei Wege, ein Problem | Welcher Bau gewinnt?“
   - Alternativen: „⛏️ Entspannt bauen in Minecraft | Komm rein und chill mit!“ · „🔧 Bau-Labor geöffnet | Tüftel mit!“
   - Titel fürs Kurzvideo: „Drei Wege zur selben Lösung“ · „Geht das auch einfacher?“
   - Tags: Minecraft, Deutsch, Sandbox, Bauen, Technik
   - Vorbereitung (Mo 17:30): Testwelt oder Kreativmodus vorbereiten
   - Clip (Di): Alle drei Lösungen schnell hintereinander, die beste ausführlicher
2. **Mi 18:00–20:15** (135 min) · Warum funktioniert mein Bau nicht? · _ohne Chat_
   - Titel: „⛏️ Entspannt bauen in Minecraft | Komm rein und chill mit!“
   - Alternativen: „🔧 Fehlersuche live | Hilf mir, bevor ich alles abreiße“ · „🔧 Warum läuft mein Bau nicht?! | Heute wird's gelöst“
   - Titel fürs Kurzvideo: „Warum funktioniert mein Bau nicht?“ · „Die kleinste Korrektur, die funktioniert“
   - Tags: Minecraft, Deutsch, Sandbox, Bauen
   - Vorbereitung (Mi 17:30): Problemstelle im Spielstand markieren
   - Clip (Do): Fehler zuerst, dann die kleinste funktionierende Korrektur
3. **Sa 14:00–16:15** (135 min) · Großprojekt in Etappen · _ohne Chat_
   - Titel: „🏰 Wir bauen was GROSSES | Tag 1 | Schau zu!“
   - Alternativen: „🏰 Großprojekt | Tag 1 | Wie weit kommen wir heute?“ · „⛏️ Entspannt bauen in Minecraft | Komm rein und chill mit!“
   - Titel fürs Kurzvideo: „Aus leerem Gelände wird ein Dorf“ · „Eine Etappe im Zeitraffer“
   - Tags: Minecraft, Deutsch, Sandbox, Bauen, Projekt
   - Vorbereitung (Sa 13:30): Etappenplan skizzieren
   - Clip (So): Zeitraffer einer Etappe

Mini-Serie: Großprojekt in Etappen – Etappe 1: Fundament · Etappe 2: Ausbau · Etappe 3: Details und Rundgang

### 15–20 Zuschauer

1. **Mo 18:00–20:30** (150 min) · Großprojekt in Etappen · _ohne Chat_
   - Titel: „🏰 Großprojekt | Tag 1 | Wie weit kommen wir heute?“
   - Alternativen: „⛏️ Entspannt bauen in Minecraft | Komm rein und chill mit!“ · „🏰 Wir bauen was GROSSES | Tag 1 | Schau zu!“
   - Titel fürs Kurzvideo: „Aus leerem Gelände wird ein Dorf“ · „Eine Etappe im Zeitraffer“
   - Tags: Minecraft, Deutsch, Sandbox, Bauen, Projekt
   - Vorbereitung (Mo 17:30): Etappenplan skizzieren
   - Clip (Di): Zeitraffer einer Etappe
2. **Mi 18:00–20:30** (150 min) · Neue Welt mit Tagesziel · _ohne Chat_
   - Titel: „⛏️ Entspannt bauen in Minecraft | Komm rein und chill mit!“
   - Alternativen: „🔥 Survival von null | Tag 1 | Überleb mit!“ · „⛏️ Neue Welt | Tag 1 | Überleben wir die Nacht?“
   - Titel fürs Kurzvideo: „Das war knapp“ · „Überlebe ich den ersten Tag?“
   - Tags: Minecraft, Deutsch, Sandbox, Survival
   - Vorbereitung (Mi 17:30): Weltregeln festlegen (Schwierigkeit, eigene Regeln)
   - Clip (Do): Der knappste Moment des Tages
3. **Fr 19:00–21:30** (150 min) · Bauprojekt aus Chat-Ideen · _aktiver Chat_
   - Titel: „🏗️ Ihr plant, ich baue | Was kommt dabei raus?“
   - Alternativen: „😂 Minecraft, aber der Chat baut | Das kann nur schiefgehen“ · „😂 Bau-Chaos in Minecraft | Hält das am Ende?“
   - Titel fürs Kurzvideo: „Mein Chat hat entschieden, was ich baue“ · „Vom Vorschlag zum fertigen Bau“
   - Tags: Minecraft, Deutsch, Sandbox, Community, Bauen
   - Vorbereitung (Fr 18:30): Rahmen festlegen: Größe, Ort, Zeit
   - Clip (Sa): Zeitraffer vom Vorschlag bis zum fertigen Bau
4. **Sa 14:00–16:30** (150 min) · Drei Lösungen für dieselbe Aufgabe · _ohne Chat_
   - Titel: „⛏️ Drei Wege, ein Problem | Welcher Bau gewinnt?“
   - Alternativen: „⛏️ Entspannt bauen in Minecraft | Komm rein und chill mit!“ · „🔧 Bau-Labor geöffnet | Tüftel mit!“
   - Titel fürs Kurzvideo: „Drei Wege zur selben Lösung“ · „Geht das auch einfacher?“
   - Tags: Minecraft, Deutsch, Sandbox, Bauen, Technik
   - Vorbereitung (Sa 13:30): Testwelt oder Kreativmodus vorbereiten
   - Clip (So): Alle drei Lösungen schnell hintereinander, die beste ausführlicher

Mini-Serie: Großprojekt in Etappen – Etappe 1: Fundament · Etappe 2: Ausbau · Etappe 3: Details und Rundgang

## Sport/Rennspiele: Rocket League

### 0–3 Zuschauer

1. **Mo 18:00–19:45** (105 min) · Jagd auf die eigene Bestmarke · _ohne Chat_
   - Titel: „🏁 Jagd auf meine Bestmarke | Heute fällt sie. Oder?“
   - Alternativen: „🔴 Heute wird GESCHWITZT | Fiebere mit!“ · „🏁 Neue Bestmarke gesucht | Drück mir die Daumen!“
   - Titel fürs Kurzvideo: „Neue Bestmarke“ · „So nah an meiner Bestmarke“
   - Tags: RocketLeague, Deutsch, Sport, Rekord
   - Vorbereitung (Mo 17:30): Aktuelle Bestmarke notieren
   - Clip (Di): Der Versuch mit der neuen Bestmarke
2. **Fr 19:00–20:45** (105 min) · Eine Technik, bis sie sitzt · _ohne Chat_
   - Titel: „🔴 Heute wird GESCHWITZT | Fiebere mit!“
   - Alternativen: „💪 Training statt Ausreden | Tag 1 | Komm rein!“ · „⚽ Trick-Training | Tag 1 | Sitzt der Move HEUTE?“
   - Titel fürs Kurzvideo: „Erster gegen besten Versuch“ · „Warum klappt dieser Move nie?“
   - Tags: RocketLeague, Deutsch, Sport, Training
   - Vorbereitung (Fr 18:30): Trainingsmodus oder Zeitfahren vorbereiten
   - Clip (Sa): Erster Versuch gegen besten Versuch

Mini-Serie: Eine Technik, bis sie sitzt – Tag 1: erste Versuche · Tag 2: im Spiel einsetzen · Tag 3: Vergleich mit Tag 1

### 5–10 Zuschauer

1. **Mo 18:00–20:15** (135 min) · Der Chat wählt die Spielweise · _kleiner Chat_
   - Titel: „😂 Ihr bestimmt die Taktik | Geht das gut? Nein.“
   - Alternativen: „😂 Spaß-Abend in Rocket League | Wer lacht zuletzt?“ · „📋 Chat ist Trainer | Gib die Ansage!“
   - Titel fürs Kurzvideo: „Mein Chat stellt die Taktik“ · „Die verrückteste Wahl des Chats“
   - Tags: RocketLeague, Deutsch, Sport, Community
   - Vorbereitung (Mo 17:30): Optionen vorab auswählen
   - Clip (Di): Bester Moment mit der Wahl des Chats
2. **Mi 18:00–20:15** (135 min) · Meine Saison als Serie · _ohne Chat_
   - Titel: „🔴 Heute wird GESCHWITZT | Fiebere mit!“
   - Alternativen: „📺 Die Saison läuft | Folge 1 | Fiebere mit!“ · „🏆 Karriere-Modus | Folge 1 | Was passiert heute?“
   - Titel fürs Kurzvideo: „Das entscheidende Tor des Tages“ · „Hält mein Plan?“
   - Tags: RocketLeague, Deutsch, Sport, Saison
   - Vorbereitung (Mi 17:30): Stand der Saison für neue Zuschauer notieren
   - Clip (Do): Das entscheidende Tor, Überholmanöver oder der wichtigste Spielzug des Tages
3. **Sa 14:00–16:15** (135 min) · Eine Technik, bis sie sitzt · _ohne Chat_
   - Titel: „💪 Training statt Ausreden | Tag 1 | Komm rein!“
   - Alternativen: „⚽ Trick-Training | Tag 1 | Sitzt der Move HEUTE?“ · „🔴 Heute wird GESCHWITZT | Fiebere mit!“
   - Titel fürs Kurzvideo: „Erster gegen besten Versuch“ · „Warum klappt dieser Move nie?“
   - Tags: RocketLeague, Deutsch, Sport, Training
   - Vorbereitung (Sa 13:30): Trainingsmodus oder Zeitfahren vorbereiten
   - Clip (So): Erster Versuch gegen besten Versuch

Mini-Serie: Meine Saison als Serie – Folge 1: Saisonstart · Folge 2: Saisonmitte · Folge 3: Saisonende und Fazit

### 15–20 Zuschauer

1. **Mo 18:00–20:30** (150 min) · Eine Technik, bis sie sitzt · _ohne Chat_
   - Titel: „⚽ Trick-Training | Tag 1 | Sitzt der Move HEUTE?“
   - Alternativen: „🔴 Heute wird GESCHWITZT | Fiebere mit!“ · „💪 Training statt Ausreden | Tag 1 | Komm rein!“
   - Titel fürs Kurzvideo: „Erster gegen besten Versuch“ · „Warum klappt dieser Move nie?“
   - Tags: RocketLeague, Deutsch, Sport, Training
   - Vorbereitung (Mo 17:30): Trainingsmodus oder Zeitfahren vorbereiten
   - Clip (Di): Erster Versuch gegen besten Versuch
2. **Mi 18:00–20:30** (150 min) · Meine Saison als Serie · _ohne Chat_
   - Titel: „🔴 Heute wird GESCHWITZT | Fiebere mit!“
   - Alternativen: „📺 Die Saison läuft | Folge 1 | Fiebere mit!“ · „🏆 Karriere-Modus | Folge 1 | Was passiert heute?“
   - Titel fürs Kurzvideo: „Das entscheidende Tor des Tages“ · „Hält mein Plan?“
   - Tags: RocketLeague, Deutsch, Sport, Saison
   - Vorbereitung (Mi 17:30): Stand der Saison für neue Zuschauer notieren
   - Clip (Do): Das entscheidende Tor, Überholmanöver oder der wichtigste Spielzug des Tages
3. **Fr 19:00–21:30** (150 min) · Der Chat wählt die Spielweise · _kleiner Chat_
   - Titel: „📋 Chat ist Trainer | Gib die Ansage!“
   - Alternativen: „😂 Ihr bestimmt die Taktik | Geht das gut? Nein.“ · „😂 Spaß-Abend in Rocket League | Wer lacht zuletzt?“
   - Titel fürs Kurzvideo: „Mein Chat stellt die Taktik“ · „Die verrückteste Wahl des Chats“
   - Tags: RocketLeague, Deutsch, Sport, Community
   - Vorbereitung (Fr 18:30): Optionen vorab auswählen
   - Clip (Sa): Bester Moment mit der Wahl des Chats
4. **Sa 14:00–16:30** (150 min) · Wo habe ich verloren? · _ohne Chat_
   - Titel: „🔴 Ranked-Nachmittag | Tag 1 | Wie viele Siege holen wir?“
   - Alternativen: „🔴 Heute wird GESCHWITZT | Fiebere mit!“ · „🏆 Heute ohne Controller-Wurf | Ranked | Versprochen.“
   - Titel fürs Kurzvideo: „Hier habe ich das Spiel verloren“ · „Der eine Fehler, der mich Spiele kostet“
   - Tags: RocketLeague, Deutsch, Sport, Analyse
   - Vorbereitung (Sa 13:30): Wiederholungsfunktion testen
   - Clip (So): Szene, Standbild, eine Zeile Erklärung

Mini-Serie: Eine Technik, bis sie sitzt – Tag 1: erste Versuche · Tag 2: im Spiel einsetzen · Tag 3: Vergleich mit Tag 1

## Just Chatting: Just Chatting

### 0–3 Zuschauer

1. **Mo 18:00–19:45** (105 min) · Ein Thema, drei Punkte · _ohne Chat_
   - Titel: „☕ Drei Dinge über mein Hobby | Rate mal, was kommt!“
   - Alternativen: „☕ Kaffee & Quatschen | Komm rein und sag Hallo!“ · „💬 Kaffee & mein Hobby | Komm rein und quatsch mit!“
   - Titel fürs Kurzvideo: „Drei Dinge, die mir mein Hobby beigebracht hat“ · „Lohnt sich mein Hobby?“
   - Tags: Deutsch, JustChatting, Gespräch, Hobby
   - Vorbereitung (Mo 17:30): Drei Stichpunkte und ein Bild oder Gegenstand vorbereiten
   - Clip (Di): Der stärkste der drei Punkte in 30–45 Sekunden
2. **Fr 19:00–20:45** (105 min) · Live etwas Neues lernen · _ohne Chat_
   - Titel: „☕ Kaffee & Quatschen | Komm rein und sag Hallo!“
   - Alternativen: „📚 Live lernen von null | Tag 1 | Lach mit!“ · „📚 Ich lerne etwas Neues | Tag 1 | Wie PEINLICH wird's heute?“
   - Titel fürs Kurzvideo: „Erster gegen letzten Versuch“ · „Das habe ich heute von null gelernt“
   - Tags: Deutsch, JustChatting, Lernen, Gespräch
   - Vorbereitung (Fr 18:30): Material oder Anleitung bereitlegen
   - Clip (Sa): Erster gegen letzten Versuch

Mini-Serie: Live etwas Neues lernen – Tag 1: Anfang · Tag 2: Übung · Tag 3: Vergleich mit Tag 1

### 5–10 Zuschauer

1. **Mo 18:00–20:15** (135 min) · Fragerunde · _kleiner Chat_
   - Titel: „❓ Frag mich ALLES | Ich antworte ehrlich“
   - Alternativen: „☕ Kaffee & Quatschen | Komm rein und sag Hallo!“ · „☕ Kaffee, Quatschen & eure Fragen | Komm rein!“
   - Titel fürs Kurzvideo: „Die beste Frage des Streams“ · „Ehrliche Antwort auf eine ehrliche Frage“
   - Tags: Deutsch, JustChatting, Fragerunde, Gespräch
   - Vorbereitung (Mo 17:30): Drei eigene Fragen bereithalten, falls keine kommen
   - Clip (Di): Die beste Antwort als Kurzvideo
2. **Mi 18:00–20:15** (135 min) · Ein Thema, drei Punkte · _ohne Chat_
   - Titel: „☕ Kaffee & Quatschen | Komm rein und sag Hallo!“
   - Alternativen: „💬 Kaffee & mein Hobby | Komm rein und quatsch mit!“ · „☕ Drei Dinge über mein Hobby | Rate mal, was kommt!“
   - Titel fürs Kurzvideo: „Drei Dinge, die mir mein Hobby beigebracht hat“ · „Lohnt sich mein Hobby?“
   - Tags: Deutsch, JustChatting, Gespräch, Hobby
   - Vorbereitung (Mi 17:30): Drei Stichpunkte und ein Bild oder Gegenstand vorbereiten
   - Clip (Do): Der stärkste der drei Punkte in 30–45 Sekunden
3. **Sa 14:00–16:15** (135 min) · Wochenrückblick und Plan · _ohne Chat_
   - Titel: „💬 Wochenrückblick | Erzähl mir von deiner Woche!“
   - Alternativen: „☕ Was für eine Woche | Und wie war deine?“ · „☕ Kaffee & Quatschen | Komm rein und sag Hallo!“
   - Titel fürs Kurzvideo: „Meine Woche in 60 Sekunden“ · „Das war meine Woche“
   - Tags: Deutsch, JustChatting, Wochenrückblick, Gespräch
   - Vorbereitung (Sa 13:30): Eigene Clips der Woche heraussuchen
   - Clip (So): Wochenrückblick in 60 Sekunden

### 15–20 Zuschauer

1. **Mo 18:00–20:30** (150 min) · Live-Projekt nebenbei · _ohne Chat_
   - Titel: „🛠️ Live-Projekt | Teil 1 | Werde ich heute fertig?“
   - Alternativen: „☕ Kaffee & Quatschen | Komm rein und sag Hallo!“ · „🛠️ Basteln & Quatschen | Teil 1 | Schau zu!“
   - Titel fürs Kurzvideo: „Von leer zu fertig“ · „Das Projekt im Zeitraffer“
   - Tags: Deutsch, JustChatting, Projekt, Kreativ
   - Vorbereitung (Mo 17:30): Material bereitlegen und eine Kamera auf die Hände richten
   - Clip (Di): Zeitraffer vom Anfang bis zum Ergebnis
2. **Mi 18:00–20:30** (150 min) · Der Chat wählt das Thema · _aktiver Chat_
   - Titel: „😂 Quatsch-Abend | Worüber lachen wir heute?“
   - Alternativen: „😂 Chat bestimmt das Thema | Ich bereue es jetzt schon“ · „🗳️ Ihr wählt das Thema | Worüber reden wir heute?“
   - Titel fürs Kurzvideo: „Mein Chat hat das Thema gewählt“ · „Der beste Moment der Diskussion“
   - Tags: Deutsch, JustChatting, Community, Gespräch
   - Vorbereitung (Mi 17:30): Drei Themen vorbereiten
   - Clip (Do): Die beste Diskussionsstelle in 45 Sekunden
3. **Fr 19:00–21:30** (150 min) · Fragerunde · _kleiner Chat_
   - Titel: „☕ Kaffee, Quatschen & eure Fragen | Komm rein!“
   - Alternativen: „❓ Frag mich ALLES | Ich antworte ehrlich“ · „☕ Kaffee & Quatschen | Komm rein und sag Hallo!“
   - Titel fürs Kurzvideo: „Die beste Frage des Streams“ · „Ehrliche Antwort auf eine ehrliche Frage“
   - Tags: Deutsch, JustChatting, Fragerunde, Gespräch
   - Vorbereitung (Fr 18:30): Drei eigene Fragen bereithalten, falls keine kommen
   - Clip (Sa): Die beste Antwort als Kurzvideo
4. **Sa 14:00–16:30** (150 min) · Wochenrückblick und Plan · _ohne Chat_
   - Titel: „☕ Was für eine Woche | Und wie war deine?“
   - Alternativen: „☕ Kaffee & Quatschen | Komm rein und sag Hallo!“ · „💬 Wochenrückblick | Erzähl mir von deiner Woche!“
   - Titel fürs Kurzvideo: „Meine Woche in 60 Sekunden“ · „Das war meine Woche“
   - Tags: Deutsch, JustChatting, Wochenrückblick, Gespräch
   - Vorbereitung (Sa 13:30): Eigene Clips der Woche heraussuchen
   - Clip (So): Wochenrückblick in 60 Sekunden

Mini-Serie: Live-Projekt nebenbei – Teil 1: Start · Teil 2: Hauptarbeit · Teil 3: fertig und Rückblick

## Kein Genre erkannt (vertrautes Spiel): World of Warcraft

### 0–3 Zuschauer

1. **Mo 18:00–19:45** (105 min) · Abend mit Ziel · _ohne Chat_
   - Titel: „🎯 Heute mit Ziel in World of Warcraft | Schaffen wir das?“
   - Alternativen: „✨ Mit Ziel in World of Warcraft | Schaffe ich es heute?“ · „🎮 World of Warcraft mit Plan | Komm rein und schau, ob's klappt!“
   - Titel fürs Kurzvideo: „Ziel geschafft – oder knapp daneben?“ · „So lange hat mein Ziel gedauert“
   - Tags: WorldOfWarcraft, Deutsch, Ziel
   - Vorbereitung (Mo 17:30): Ein Ziel wählen, das in einem Stream schaffbar ist
   - Clip (Di): Der Moment, in dem das Ziel klappt oder scheitert
2. **Fr 19:00–20:45** (105 min) · Zwei Wege zum selben Ziel · _ohne Chat_
   - Titel: „🎮 Entspannt World of Warcraft zocken | Sag Hallo!“
   - Alternativen: „🔀 Ich teste beide Wege | Tipp mit!“ · „🔀 Zwei Wege, ein Ziel | Welcher ist schneller?“
   - Titel fürs Kurzvideo: „Zwei Wege, ein Ziel – welcher passt besser?“ · „Schnell oder sicher?“
   - Tags: WorldOfWarcraft, Deutsch, Vergleich
   - Vorbereitung (Fr 18:30): Ziel und Kriterien festlegen
   - Clip (Sa): Beide Wege im Schnelldurchlauf, dann das Ergebnis

### 5–10 Zuschauer

1. **Mo 18:00–20:15** (135 min) · Mit Zuschauern spielen · _kleiner Chat_
   - Titel: „🤝 Zuschauerrunde in World of Warcraft | Spiel mit!“
   - Alternativen: „😂 Chaos in World of Warcraft | Was passiert als Nächstes?“ · „😂 Ihr spielt mit mir | Das kann ja heiter werden“
   - Titel fürs Kurzvideo: „Meine Zuschauer spielen mit mir“ · „Das passiert, wenn der Chat mitspielt“
   - Tags: WorldOfWarcraft, Deutsch, Zuschauerrunde, Community
   - Vorbereitung (Mo 17:30): Prüfen, ob und wie Zuschauer im Spiel beitreten können
   - Clip (Di): Der lustigste Moment mit den Mitspielern aus dem Chat
2. **Mi 18:00–20:15** (135 min) · Zuschauer entscheiden den nächsten Abschnitt · _kleiner Chat_
   - Titel: „😂 Chaos in World of Warcraft | Was passiert als Nächstes?“
   - Alternativen: „😂 Chat am Steuer | Was soll da schon passieren?“ · „🗳️ Ihr entscheidet, wie's weitergeht | Wohin heute?“
   - Titel fürs Kurzvideo: „Mein Chat hat entschieden“ · „So ging es weiter“
   - Tags: WorldOfWarcraft, Deutsch, Community
   - Vorbereitung (Mi 17:30): Optionen vorab festlegen
   - Clip (Do): Die Wahl und ihr Ergebnis in einem Clip
3. **Sa 14:00–16:15** (135 min) · Moment der Woche mit Kontext · _ohne Chat_
   - Titel: „⭐ Highlight-Nachmittag | Stimm für den besten Moment!“
   - Alternativen: „⭐ Die besten Momente der Woche | Welcher war deiner?“ · „🎮 Entspannt World of Warcraft zocken | Sag Hallo!“
   - Titel fürs Kurzvideo: „Dieser Moment hat meine Woche geprägt“ · „Wie kam es zu diesem Moment?“
   - Tags: WorldOfWarcraft, Deutsch, Highlights
   - Vorbereitung (Sa 13:30): Eigene Clips der Woche durchsehen
   - Clip (So): Der Moment mit einer Einblendung zum Kontext

### 15–20 Zuschauer

1. **Mo 18:00–20:30** (150 min) · Fortschritt mit Tageszähler · _ohne Chat_
   - Titel: „📈 World of Warcraft | Tag 1 | Wie weit kommen wir heute?“
   - Alternativen: „✨ Mit Ziel in World of Warcraft | Schaffe ich es heute?“ · „🔥 Weiter geht's in World of Warcraft | Tag 1 | Komm rein!“
   - Titel fürs Kurzvideo: „Tag 1 gegen heute“ · „Wie weit bin ich nach ein paar Tagen?“
   - Tags: WorldOfWarcraft, Deutsch, Fortschritt
   - Vorbereitung (Mo 17:30): Stand vom letzten Stream notieren
   - Clip (Di): Vorher und nachher: Stand zu Beginn und am Ende des Tages
2. **Mi 18:00–20:30** (150 min) · Lern-Tagebuch: ein sichtbarer Fortschritt · _ohne Chat_
   - Titel: „🎮 Entspannt World of Warcraft zocken | Sag Hallo!“
   - Alternativen: „📈 Jeden Tag ein bisschen besser | Tag 1“ · „📈 Trainingstag 1 | Schaffe ich heute mein Ziel?“
   - Titel fürs Kurzvideo: „Erster gegen letzten Versuch“ · „Habe ich mein Ziel geschafft?“
   - Tags: WorldOfWarcraft, Deutsch, Lernen
   - Vorbereitung (Mi 17:30): Ziel so wählen, dass es in einen Stream passt
   - Clip (Do): Erster gegen letzten Versuch
3. **Fr 19:00–21:30** (150 min) · Abend mit Ziel · _ohne Chat_
   - Titel: „🎮 World of Warcraft mit Plan | Komm rein und schau, ob's klappt!“
   - Alternativen: „🎯 Heute mit Ziel in World of Warcraft | Schaffen wir das?“ · „✨ Mit Ziel in World of Warcraft | Schaffe ich es heute?“
   - Titel fürs Kurzvideo: „Ziel geschafft – oder knapp daneben?“ · „So lange hat mein Ziel gedauert“
   - Tags: WorldOfWarcraft, Deutsch, Ziel
   - Vorbereitung (Fr 18:30): Ein Ziel wählen, das in einem Stream schaffbar ist
   - Clip (Sa): Der Moment, in dem das Ziel klappt oder scheitert
4. **Sa 14:00–16:30** (150 min) · Mit Zuschauern spielen · _kleiner Chat_
   - Titel: „🤝 Zuschauerrunde in World of Warcraft | Spiel mit!“
   - Alternativen: „😂 Chaos in World of Warcraft | Was passiert als Nächstes?“ · „😂 Ihr spielt mit mir | Das kann ja heiter werden“
   - Titel fürs Kurzvideo: „Meine Zuschauer spielen mit mir“ · „Das passiert, wenn der Chat mitspielt“
   - Tags: WorldOfWarcraft, Deutsch, Zuschauerrunde, Community
   - Vorbereitung (Sa 13:30): Prüfen, ob und wie Zuschauer im Spiel beitreten können
   - Clip (So): Der lustigste Moment mit den Mitspielern aus dem Chat

Mini-Serie: Fortschritt mit Tageszähler – Tag 1: Ausgangslage und Ziel · Tag 2: das erste Etappenziel · Tag 3: Rückblick auf die Tage 1 bis 3
