# Kategorie-Check – Content Strategist auf echten Twitch-Daten

Der Kategorie-Check beantwortet zwei Fragen mit echten Live-Daten von Twitch:

1. **In welcher Kategorie wirst du mit deinen Zuschauern überhaupt gesehen?**
2. **Wann lohnt es sich dort zu streamen?**

Dafür misst er, wie viele Kanäle in einer Kategorie und Sprache gerade live sind und
wie viele Zuschauer sie haben. Ein eigener Kanal ist nicht nötig – man kann also schon
vor dem ersten Stream planen.

## Was gemessen und berechnet wird

| Wert | Bedeutung |
| --- | --- |
| Live-Kanäle | Wie viele Kanäle in der Kategorie und Sprache gerade senden |
| Zuschauer gesamt | Summe aller Zuschauer dieser Kanäle, also das Publikum der Kategorie |
| Zuschauer pro Kanal (Median) | Was ein typischer Kanal dort hat |
| Anteil Top 3 | Wie viel Publikum die drei größten Kanäle binden |
| **Dein Platz** | Wie viele Kanäle mindestens so viele Zuschauer haben wie du, plus eins. So weit unten stehst du in der nach Zuschauern sortierten Liste |

Bei mehreren Messungen gilt jeweils der Median. Beim Platz wird bei einer geraden
Anzahl der schlechtere der beiden mittleren Werte genommen, die Schätzung ist also vorsichtig.

**Einschätzung** (Faustregeln, keine Twitch-Vorgaben):

| Einschätzung | Bedingung |
| --- | --- |
| gute Chance | Platz bis 15 |
| machbar | Platz bis 40 |
| schwer | Platz dahinter |
| wenig Publikum | weniger als 25 Zuschauer insgesamt. Man wäre sichtbar, aber es schaut kaum jemand |

**Beste Zeiten:** Zwei-Stunden-Blöcke in deiner Ortszeit, sortiert nach dem Publikum
pro Platz vor dir (Zuschauer gesamt ÷ dein Platz). So landen Abende mit viel Publikum
und trotzdem gutem Platz vorne, nicht die leerste Uhrzeit um 4 Uhr nachts. Mit
`--window 16-24` werden nur Zeiten gezeigt, zu denen du wirklich streamen kannst.

## Einrichtung (einmalig)

Es wird dieselbe kostenlose Twitch-Entwickler-App wie beim Clip Hunter verwendet
(siehe [clip-hunter.md → Einrichtung](clip-hunter.md#einrichtung-einmalig)):

```powershell
$env:TWITCH_CLIENT_ID = "deine-client-id"
$env:TWITCH_CLIENT_SECRET = "dein-secret"
```

Zugangsdaten nur als Umgebungsvariablen setzen und niemals in Dateien im Repo speichern.

## Benutzung

```powershell
cd agents

# 1. Einmal messen (Kategorienamen wie auf Twitch, Groß-/Kleinschreibung egal; gängige
#    Kurzformen wie „CS2“ oder „gta 5“ gehen auch; bei Tippfehlern kommen Vorschläge)
python -m streaming_agents.category_check measure "Minecraft" "Stardew Valley" "Factorio" `
    --out messungen.jsonl

# Oder: die gerade meistgesehenen Kategorien vergleichen
python -m streaming_agents.category_check suggest --top 30 --out messungen.jsonl

# 2. Für die besten Zeiten: eine Woche lang stündlich messen (Rechner muss laufen)
python -m streaming_agents.category_check watch "Minecraft" "Stardew Valley" "Factorio" `
    --every 60 --hours 168 --out messungen.jsonl

# 3. Auswerten (mit deinen durchschnittlichen Zuschauern und deinen Streamzeiten)
python -m streaming_agents.category_check report messungen.jsonl --viewers 2 --window 16-24 `
    --html bericht.html
```

Wichtige Optionen:

- `--lang de`: nur deutschsprachige Streams (Standard). `en` für Englisch, `any` für alle Sprachen.
- `--viewers 2`: deine durchschnittlichen Zuschauer. Vor dem ersten Stream 1–3 annehmen.
- `--pages 10`: höchstens 10 × 100 Kanäle pro Kategorie. Bei `suggest` sind es standardmäßig 3,
  damit es schnell geht. Bei riesigen Kategorien steht dann „hinter Platz …“. Das reicht, denn
  dort wäre man ohnehin kaum zu sehen.
- `--ui en`: Ausgabe auf Englisch.

### Kurzformen (Aliasse)

Twitch findet Kategorien über den exakten Namen; die Groß-/Kleinschreibung ist egal
(echt getestet am 26.11.2026). Abkürzungen findet Twitch aber nicht oder falsch: „CS2“ ist
auf Twitch das Spiel „Carrot Slime 2“, und Counter-Strike 2 läuft unter „Counter-Strike“.
Deshalb übersetzt der Kategorie-Check gängige Kurzformen vorher in den offiziellen Namen
(Liste in `streaming_agents/category_check/aliases.py`, jeder Zielname per API geprüft):

| Eingabe (Beispiele) | Gemessen wird |
| --- | --- |
| CS2, CS 2, Counter Strike 2, Counter-Strike 2, CS:GO | Counter-Strike |
| LoL | League of Legends |
| GTA, GTA 5, GTA V, GTA RP, GTA Online | Grand Theft Auto V |
| GTA 6, GTA VI | Grand Theft Auto VI |
| WoW | World of Warcraft |
| Apex | Apex Legends |
| R6, R6S, Rainbow Six, Rainbow Six Siege X | Rainbow Six Siege |
| EA FC, FC 27 / FC 26 / FC 25 | EA Sports FC 27 / 26 / 25 („EA FC“ = aktuelle Ausgabe, Stand November 2026) |
| TFT, DbD | Teamfight Tactics, Dead by Daylight |
| PUBG, Warzone, Tarkov/EFT, Dota, OW/OW2, Valo, PoE/PoE 2 | jeweils der offizielle Name |

Greift ein Alias, steht das in der Ausgabe, im Bericht und in der Messdatei:
`CS2 → Counter-Strike (Alias)`. So ist immer sichtbar, was gemessen wurde.

### Glücksspiel wird nicht unterstützt

Entscheidung des Nutzers vom 26.11.2026: Die Streaming Growth Engine unterstützt Glücksspiel
**gar nicht** – nie vorschlagen, nie messen, nie planen. Es gibt keine Option zum Einschalten.

Die eine Liste steht in `streaming_agents/category_check/gambling.py` (Slots, Virtual Casino,
Poker, Casino, Casino Games, Roulette, Blackjack, Baccarat, Gates of Olympus, Texas Hold'em;
IDs und Namen, per API ermittelt, Stand November 2026). Gleichnamige Kategorien mit anderer ID
und Kurzformen, die auf eine dieser Kategorien zeigen, zählen genauso.

- `suggest` misst Glücksspiel-Kategorien gar nicht erst, füllt mit den nächsten Kategorien auf
  und nennt nur die Zahl: „Ohne 2 Glücksspiel-Kategorien (werden nicht unterstützt).“
- `measure` und `watch` lehnen eine Glücksspiel-Kategorie freundlich ab (DE/EN) und messen die
  übrigen Kategorien normal. Kommt nur Glücksspiel vor, endet der Befehl mit Exit-Code 2.
- `report` und die API ignorieren Glücksspiel-Einträge aus älteren Messdateien und nennen
  nur die Zahl. Ein Feld `include_gambling` in der API-Anfrage wird wie jedes unbekannte Feld
  ignoriert und ändert nichts.
- Der [Content Strategist](content-strategist.md) nutzt dieselbe Liste.
- Ein späterer Export für die Website (z. B. Kategorie-Listen oder Vorschläge im Browser) muss
  diese Liste mit übernehmen.

Eine Twitch-Kategorie für echte Sportwetten gibt es nicht (nur „Sports Betting Simulator“).
„Crypto“ steht bewusst nicht in der Liste (Handel, kein Glücksspiel im engeren Sinn).

## Lesehilfe

- **Gute Chance und genug Publikum** sind die interessanten Kategorien. Wer dort ein Spiel
  mag, kann ernsthaft testen.
- **Riesige Kategorien** (Just Chatting, die großen Shooter) sind für kleine Kanäle fast
  immer „schwer“. Dort entsteht Reichweite eher über Kurzvideos als über die Liste.
- **Ein hoher Anteil Top 3** heißt: Das Publikum schaut vor allem die großen Kanäle.
- **Eine Messung ist ein Moment.** Für Entscheidungen an mehreren Tagen zur geplanten
  Streamzeit messen, am besten mit `watch`.

## Datenschutz und Fairness

- Gespeichert werden **nur Zuschauerzahlen**, keine Kanalnamen, Titel oder Nutzer. Dazu kommt
  der Name der Kategorie und, falls ein Alias gegriffen hat, die eigene Eingabe (z. B. „CS2“).
- Es werden ausschließlich öffentliche Live-Daten über die offizielle Twitch-API abgefragt,
  mit kurzen Pausen zwischen den Anfragen. `watch` misst höchstens alle 10 Minuten.

## Grenzen

- Der Platz ist eine Näherung. Twitch kann Listen auch personalisiert sortieren, und
  Empfehlungen, Raids und Kurzvideos bringen Zuschauer an der Liste vorbei.
- Die Schwellen (15/40/25) sind Faustregeln und lassen sich mit echten Erfahrungen nachschärfen.
- Ohne Twitch-Zugangsdaten kann nicht gemessen werden. Vorhandene Messdateien lassen sich
  aber jederzeit auswerten.
