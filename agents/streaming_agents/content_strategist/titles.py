"""Stream-Titel: beschreiben den GANZEN Stream und laden zum Reinkommen ein.

Regeln (auch in agents/docs/content-strategist.md; Tests prüfen 1, 2, 3, 5 und 6):
1. Bezug auf den ganzen Stream, nie auf eine einzelne Runde, Szene oder ein Match
   („diese Runde“, „dieses Match“, „diese Ecke“, „dieser Abschnitt“ … sind verboten).
2. Aufbau aus Bausteinen: [Ziel ODER Stimmung des Streams] + [Einladung ODER Neugier-Frage]
   + genau EIN passendes Emoji.
   - Ziel: Rang-Ziel („Road to Platin“), Tagesziel, Projekt („Großprojekt Tag 3“), erstes Mal.
   - Stimmung: chillig, ehrgeizig, lustig – mit Tageszeit („Ranked-Abend“, „Horror-Nacht“).
   - Einladung: „komm rein“, „sag Hallo“, „komm mit“, „chill mit“, „quatsch mit“ (du-Form).
   - Fortschritt: „Tag 5“, „Folge 3“ zählt über ``week_number`` weiter.
3. Genau ein Emoji pro Titel, aus einer kleinen festen Liste pro Genre (``EMOJIS``).
4. Spielname nur, wenn er Teil des Hooks ist („Zum ersten Mal <Spiel>“, „Chilliges <Spiel> &
   Quatschen“) – Twitch zeigt die Kategorie ohnehin an.
5. Ehrlich: nur versprechen, was der Stream liefert. Rang-Ziele nur, wenn eins angegeben ist
   (sonst allgemein „Ranked-Abend“); keine Rekord- oder „Unmöglich“-Versprechen; keine
   Großbuchstaben-Wörter außer Abkürzungen; höchstens ein Ausrufezeichen.
6. Ziel ≤ 70 Zeichen (das Wichtigste vorn), hart ≤ 140 (Twitch).
7. Deutsch und Englisch eigenständig und natürlich formuliert, nicht wörtlich übersetzt.

Jeder Titel entsteht aus Bausteinen (``TitleOption``) – so lässt sich der Aufbau prüfen, ohne im
Text nach Wörtern zu suchen. Pro Stream gibt es drei Ansätze:
- ``goal``:   Ziel + Neugier-Frage   („Großprojekt Tag 3 – wie weit kommen wir heute? 🏰“)
- ``mood``:   Stimmung + Einladung   („Chilliges Valorant & Quatschen – sag Hallo 👋“)
- ``invite``: Ziel + Einladung       („Großprojekt Tag 3 – komm mit! ⛏️“)

Die frühere, auf einen Moment bezogene Titel-Version lebt als Ideen für den Clip-Titel weiter
(``CLIP_TITLES``), denn ein Kurzvideo zeigt genau einen Moment.
"""
from dataclasses import dataclass
from typing import Literal

from .genres import normalize

Mood = Literal["chill", "ambitious", "funny"]
Approach = Literal["goal", "mood", "invite"]
Text = tuple[str, str]

TITLE_TARGET_CHARS = 70

EMOJIS: dict[str, tuple[str, ...]] = {
    "shooter": ("🔥", "🎯"), "battle_royale": ("🏆", "🔥"), "moba": ("⚔️", "🏆"),
    "story": ("🗡️", "📖"), "horror": ("😱", "👻"), "cozy": ("☕", "🌱"),
    "sandbox": ("🏰", "⛏️"), "sports": ("⚽", "🏆"), "racing": ("🚗", "🏁"),
    "just_chatting": ("☕", "👋"), "general": ("🎮", "✨"),
}
ALL_EMOJIS = frozenset(emoji for group in EMOJIS.values() for emoji in group)
_RACING = ("forza", "gran turismo", "f1", "mario kart", "trackmania", "assetto corsa",
           "iracing", "rocket league")

GENRE_MOOD: dict[str | None, Mood] = {
    "shooter": "ambitious", "battle_royale": "ambitious", "moba": "ambitious",
    "story": "chill", "horror": "funny", "cozy": "chill", "sandbox": "chill",
    "sports": "ambitious", "just_chatting": "chill", None: "chill",
}
RANKED_GENRES = frozenset({"shooter", "battle_royale", "moba", "sports"})

# Stimmungs-Bausteine pro Genre. Platzhalter: {game}, {zeit} (Abend, Nacht …), {zeit_m}
# (nur männliche Formen, für „Gemütlicher …“), {time} (englisch).
MOOD_LEADS: dict[str | None, dict[str, Text]] = {
    "shooter": {"chill": ("Chilliges {game} & Quatschen", "Chill {game} & chatting"),
                "ambitious": ("Heute wird gegrindet", "Grind session"),
                "funny": ("Chaos-{zeit} in {game}", "Chaos {time} in {game}")},
    "battle_royale": {"chill": ("Entspanntes {game} & Quatschen", "Laid-back {game} & chatting"),
                      "ambitious": ("Heute jagen wir den Sieg", "Hunting a win today"),
                      "funny": ("Chaos-Drops in {game}", "Chaotic drops in {game}")},
    "moba": {"chill": ("Entspanntes {game} & Quatschen", "Laid-back {game} & chatting"),
             "ambitious": ("Heute wird gegrindet", "Grind session"),
             "funny": ("Chaos-{zeit} in {game}", "Chaos {time} in {game}")},
    "story": {"chill": ("Gemütlicher Story-{zeit_m}", "Cosy story {time}"),
              "ambitious": ("Heute geht's weit voran", "Big progress day"),
              "funny": ("Lachen und Leiden in {game}", "Laughing and suffering through {game}")},
    "horror": {"chill": ("Grusel in Ruhe", "Slow-burn scares"),
               "ambitious": ("Horror-{zeit}: kein Weglaufen", "Horror {time}, no running away"),
               "funny": ("Horror-{zeit} in {game}", "Horror {time} in {game}")},
    "cozy": {"chill": ("Gemütlicher {zeit_m} in {game}", "Cosy {time} in {game}"),
             "ambitious": ("Fleißiger {zeit_m} in {game}", "Busy {time} in {game}"),
             "funny": ("Gemütliches Chaos in {game}", "Cosy chaos in {game}")},
    "sandbox": {"chill": ("Entspannt bauen in {game}", "Chill building in {game}"),
                "ambitious": ("Bau-{zeit}: heute geht's voran", "Build {time}: big progress today"),
                "funny": ("Bau-Chaos in {game}", "Building chaos in {game}")},
    "sports": {"chill": ("Entspanntes {game} & Quatschen", "Laid-back {game} & chatting"),
               "ambitious": ("Heute wird trainiert", "Practice session"),
               "funny": ("Spaß-{zeit} in {game}", "Fun {time} in {game}")},
    "just_chatting": {"chill": ("Kaffee & Quatschen", "Coffee & chatting"),
                      "ambitious": ("Ein Thema, volle Konzentration", "One topic, full focus"),
                      "funny": ("Lockerer Quatsch-{zeit}", "Silly chat {time}")},
    None: {"chill": ("Entspannt {game} zocken", "Chilling with {game}"),
           "ambitious": ("Mit Ziel in {game}", "Playing {game} with a goal"),
           "funny": ("Chaos in {game}", "Chaos in {game}")},
}
RANKED_LEAD: Text = ("Ranked-{zeit}: heute wird geklettert", "Ranked {time}: time to climb")
RANKED_GOAL_LEAD: Text = ("Ranked-{zeit}: wir klettern Richtung {rank}",
                          "Ranked {time}: climbing towards {rank}")
RANK_GOAL: Text = ("Road to {rank}, Tag {k}", "Road to {rank}, day {k}")
RANK_QUESTION: Text = ("kommen wir heute ein Stück näher?", "do we get closer today?")
FIRST_TIME: Text = ("Zum ersten Mal {game}, blind", "First time in {game}, blind")

INVITES: dict[str, tuple[Text, Text]] = {
    "chill": (("sag Hallo", "say hi"), ("chill mit", "come hang out")),
    "ambitious": (("komm mit", "come along"), ("komm rein", "jump in")),
    "funny": (("komm rein und lach mit", "come laugh along"), ("sag Hallo", "say hi")),
    "chat": (("quatsch mit", "come chat"), ("sag Hallo", "say hi")),
}

DAYPARTS = (  # (bis Stunde, Deutsch, Deutsch männlich, Englisch)
    (5, "Nacht", "Abend", "night"), (12, "Vormittag", "Vormittag", "morning"),
    (17, "Nachmittag", "Nachmittag", "afternoon"), (22, "Abend", "Abend", "evening"),
    (24, "Nacht", "Abend", "night"),
)

FILLS: dict[str, dict[str, Text]] = {
    "shooter-chat-rule": {"regel": ("nur einer Waffe", "one weapon only")},
    "moba-one-number": {"ziel": ("70 Farm nach 10 Minuten", "70 CS at 10 minutes")},
    "cozy-one-rule": {"regel": ("nur einer Farbe", "one colour only")},
    "jc-three-points": {"thema": ("mein Hobby", "my hobby")},
    "jc-learn-live": {"skill": ("etwas Neues", "something new")},
}


@dataclass(frozen=True)
class StreamTitle:
    goal: Text            # Ziel des ganzen Streams
    question: Text        # Neugier-Frage zum ganzen Stream
    ranked: bool = False  # passt zu einem Ranked-Stream (Rang-Ziel möglich)
    mood: Mood | None = None   # Standard-Stimmung des Formats (sonst die des Genres)
    first_time: bool = False   # „Zum ersten Mal <Spiel>“ möglich


STREAM_TITLES: dict[str, StreamTitle] = {
    # Shooter
    "shooter-decision-review": StreamTitle(
        ("Lernen aus jeder Niederlage", "Learning from every loss"),
        ("wie viele Siege holen wir heute?", "how many wins can we grab?"), ranked=True),
    "shooter-micro-skill": StreamTitle(
        ("Aim-Training Tag {n}", "Aim training, day {n}"),
        ("sitzt das Fadenkreuz heute?", "will my crosshair behave today?"), ranked=True),
    "shooter-role-swap": StreamTitle(
        ("Neue Rolle, null Ausreden", "New role, zero excuses"),
        ("wie schlage ich mich?", "how do I hold up?")),
    "shooter-chat-rule": StreamTitle(
        ("Jedes Match mit {regel}", "Every match with {regel}"),
        ("wie lange halte ich durch?", "how long can I last?"),
        mood="funny"),
    "shooter-coach": StreamTitle(
        ("Mit Coach im Ohr", "Coach on comms"),
        ("werde ich heute besser?", "do I get better today?")),
    # Battle Royale
    "br-drop-study": StreamTitle(
        ("Landeplatz-Test: zwei Orte, ein Sieger", "Drop spot test: two spots, one winner"),
        ("wo lande ich ab jetzt?", "where should I drop?"), ranked=True),
    "br-rotation": StreamTitle(
        ("Jede Zone mit Plan", "Every zone with a plan"),
        ("holen wir heute einen Sieg?", "can we grab a win today?"), ranked=True),
    "br-loadout-lab": StreamTitle(
        ("Ausrüstungs-Labor, Test {n}", "Loadout lab, test {n}"),
        ("welche Ausrüstung gewinnt heute?", "which loadout wins today?"), ranked=True),
    "br-squad-comms": StreamTitle(
        ("Squad-{zeit}, klare Ansagen", "Squad {time}, clean callouts"),
        ("spielen wir besser zusammen?", "do we play better together?")),
    "br-chat-drop": StreamTitle(
        ("Der Chat wählt jeden Landeplatz", "Chat picks every drop"),
        ("überlebe ich das?", "can I survive this?"), mood="funny"),
    # MOBA
    "moba-scene-review": StreamTitle(
        ("Jedes Match mit Nachbesprechung", "Every game gets a debrief"),
        ("wie viele Siege holen wir heute?", "how many wins can we get?"), ranked=True),
    "moba-new-character": StreamTitle(
        ("Neuer Main von null, Tag {n}", "New main from zero, day {n}"),
        ("wann sitzt der Charakter?", "when will it click?")),
    "moba-one-number": StreamTitle(
        ("Farm-Training: {ziel}", "Farm practice: {ziel}"),
        ("schaffen wir das heute?", "can we hit it today?"), ranked=True),
    "moba-chat-pick": StreamTitle(
        ("Der Chat wählt jeden Charakter", "Chat picks every character"),
        ("gewinne ich mit allem?", "can I win with anything?"), mood="funny"),
    "moba-duo": StreamTitle(
        ("Duo-{zeit} mit Coach", "Duo {time} with a coach"),
        ("zieht mich mein Duo nach oben?", "can my duo pull me up?")),
    # Story/Singleplayer
    "story-first-playthrough": StreamTitle(
        ("Mein erster Durchgang, Etappe {n}", "My first playthrough, part {n}"),
        ("was erwartet mich heute?", "what's waiting today?"), first_time=True),
    "story-attempt-counter": StreamTitle(
        ("Versuch um Versuch", "Attempt after attempt"),
        ("wie viele werden es heute?", "how many will it take today?"),
        mood="ambitious"),
    "story-recap": StreamTitle(
        ("Story-{zeit} mit Rückblick", "Story {time} with a recap"),
        ("wohin geht die Geschichte?", "where does the story go?")),
    "story-explore": StreamTitle(
        ("Langsam spielen, alles entdecken", "Slow play, see everything"),
        ("was finden wir heute?", "what will we find today?")),
    "story-chat-choices": StreamTitle(
        ("Der Chat lenkt die Geschichte", "Chat steers the story"),
        ("wohin führt uns das?", "where will this take us?"), mood="funny"),
    # Horror
    "horror-honest-reactions": StreamTitle(
        ("Horror mit Facecam", "Horror on facecam"),
        ("wie oft schreie ich heute?", "how often will I scream?"), first_time=True),
    "horror-courage-levels": StreamTitle(
        ("Mutprobe in drei Stufen", "Three-step courage test"),
        ("wie weit komme ich heute?", "how far will I make it?")),
    "horror-clue-board": StreamTitle(
        ("Rätsel-{zeit}, Teil {n}", "Mystery {time}, part {n}"),
        ("was ist hier passiert?", "what happened here?"), mood="chill", first_time=True),
    "horror-coop-night": StreamTitle(
        ("Koop-Horror mit Freunden", "Co-op horror with friends"),
        ("wer bleibt am längsten ruhig?", "who keeps it together longest?")),
    "horror-chat-guess": StreamTitle(
        ("Schreck-Wetten mit dem Chat", "Scare bets with chat"),
        ("wer ahnt den Schreck zuerst?", "who calls the scare first?")),
    # Cozy/Simulation
    "cozy-three-goals": StreamTitle(
        ("Drei kleine Ziele, Woche {n}", "Three small goals, week {n}"),
        ("schaffen wir alle?", "can we tick them all?")),
    "cozy-before-after": StreamTitle(
        ("Vorher/Nachher: ein Ort wird schön", "Before/after: making one place lovely"),
        ("wie schön wird es heute?", "how lovely can it get?")),
    "cozy-starter-tips": StreamTitle(
        ("Einsteiger-Tipps nebenbei", "Starter tips on the side"),
        ("bist du neu im Spiel?", "just started playing?")),
    "cozy-one-rule": StreamTitle(
        ("Den ganzen Stream mit {regel}", "A whole stream with {regel}"),
        ("bleibt's gemütlich?", "can it stay cosy?"), mood="funny"),
    "cozy-chat-names": StreamTitle(
        ("Der Chat gibt die Namen", "Chat names everything"),
        ("wie soll es heißen?", "what should we call it?")),
    # Sandbox/Survival
    "sandbox-three-solutions": StreamTitle(
        ("Bau-Labor: drei Lösungen", "Build lab: three solutions"),
        ("welche gewinnt?", "which one wins?")),
    "sandbox-fix-it": StreamTitle(
        ("Fehlersuche am eigenen Bau", "Fixing my own build"),
        ("läuft es heute endlich?", "will it finally work today?")),
    "sandbox-big-project": StreamTitle(
        ("Großprojekt Tag {n}", "Big build, day {n}"),
        ("wie weit kommen wir heute?", "how far do we get today?")),
    "sandbox-survival-start": StreamTitle(
        ("Neue Welt, Tag {n}", "Fresh world, day {n}"),
        ("schaffen wir das Tagesziel?", "do we hit today's goal?")),
    "sandbox-chat-build": StreamTitle(
        ("Der Chat plant, ich baue", "Chat plans, I build"),
        ("was entsteht heute?", "what gets built today?"), mood="funny"),
    # Sport/Rennspiele
    "sports-one-technique": StreamTitle(
        ("Technik-Training, Tag {n}", "Skill practice, day {n}"),
        ("sitzt sie heute?", "does it click today?")),
    "sports-personal-best": StreamTitle(
        ("Jagd auf die eigene Bestmarke", "Chasing my personal best"),
        ("knacken wir heute die Marke?", "do we beat it today?")),
    "sports-match-review": StreamTitle(
        ("Jedes Spiel mit Nachbesprechung", "Every game gets a debrief"),
        ("wie viele Siege werden es?", "how many wins today?"), ranked=True),
    "sports-career": StreamTitle(
        ("Meine Saison, Folge {n}", "My season, episode {n}"),
        ("wie weit kommen wir?", "how far can we go?")),
    "sports-chat-tactic": StreamTitle(
        ("Der Chat stellt die Taktik", "Chat calls the tactics"),
        ("geht das gut?", "will it work?"), mood="funny"),
    # Just Chatting
    "jc-three-points": StreamTitle(
        ("Heute geht's um {thema}", "Today's topic: {thema}"),
        ("was meinst du dazu?", "what's your take?")),
    "jc-live-project": StreamTitle(
        ("Live-Projekt, Teil {n}", "Live project, part {n}"),
        ("werde ich heute fertig?", "will I finish today?")),
    "jc-week-recap": StreamTitle(
        ("Wochenrückblick & Plan", "Week recap & next week's plan"),
        ("wie war deine Woche?", "how was your week?")),
    "jc-learn-live": StreamTitle(
        ("Ich lerne {skill}, Tag {n}", "Learning {skill}, day {n}"),
        ("wie weit komme ich heute?", "how far do I get today?")),
    "jc-qna": StreamTitle(
        ("Kaffee, Quatschen und eure Fragen", "Coffee, chat and your questions"),
        ("was willst du wissen?", "what do you want to know?")),
    "jc-topic-vote": StreamTitle(
        ("Der Chat wählt das Thema", "Chat picks the topic"),
        ("worüber reden wir heute?", "what are we talking about today?"), mood="funny"),
    # Allgemein
    "general-first-impressions": StreamTitle(
        ("Erste Stunde in {game}", "First hour in {game}"),
        ("lohnt es sich?", "is it worth it?"), first_time=True),
    "general-skill-diary": StreamTitle(
        ("Lern-Tagebuch, Tag {n}", "Learning diary, day {n}"),
        ("schaffe ich mein Ziel?", "do I hit my goal?")),
    "general-two-ways": StreamTitle(
        ("Zwei Wege, ein Ziel", "Two routes, one goal"),
        ("welcher ist besser?", "which one's better?")),
    "general-moment-of-week": StreamTitle(
        ("Die Woche in Momenten", "The week in moments"),
        ("welcher war dein Favorit?", "which one's your favourite?")),
    "general-audience-choice": StreamTitle(
        ("Der Chat entscheidet alles", "Chat decides everything"),
        ("wohin geht's heute?", "where are we headed today?"), mood="funny"),
}

# Ideen für den Titel des Kurzvideos: ein Moment, darum dürfen sie „diese Runde“ sagen.
# (Das war die Titel-Version vom 24.11.2026 mittags.)
CLIP_TITLES: dict[str, tuple[Text, Text]] = {
    "shooter-decision-review": (("Hätte ich diese Runde retten können?", "Could I have saved that round?"),
                                ("Welcher Fehler kostet mich die meisten Runden?",
                                 "Which mistake costs me the most rounds?")),
    "shooter-micro-skill": (("Warum verliere ich an dieser Ecke immer?", "Why do I always lose this corner?"),
                            ("Vorher, nachher: sitzt das Fadenkreuz?", "Before and after: did the crosshair fix stick?")),
    "shooter-role-swap": (("Wie schlecht bin ich abseits meiner Main-Rolle?", "How bad am I off my main role?"),
                          ("Neue Rolle, null Ausreden", "New role, zero excuses")),
    "shooter-chat-rule": (("Wie lange halte ich mit nur einer Waffe durch?", "How long can I last with one weapon only?"),
                          ("Der Chat hat die Regel gewählt …", "Chat picked the rule …")),
    "shooter-coach": (("Ein Coach sieht meine schlechteste Runde", "A coach watches my worst round"),
                      ("Ein Tipp, der sofort hilft", "One tip that helped right away")),
    "br-drop-study": (("Heißer Landeplatz oder ruhige Ecke?", "Hot drop or quiet corner?"),
                      ("Zwei Landeplätze, nur einer bleibt", "Two drop spots, only one stays")),
    "br-rotation": (("Rotieren oder bleiben?", "Rotate or hold?"),
                    ("Warum sterbe ich immer in der Zone?", "Why do I keep dying to the zone?")),
    "br-loadout-lab": (("Welche Ausrüstung bringt mich weiter?", "Which loadout actually helps me?"),
                       ("Bauchgefühl oder Zahlen?", "Gut feeling or numbers?")),
    "br-squad-comms": (("Chaos-Ansage gegen klare Ansage", "Messy callout vs clean callout"),
                       ("Spielen wir mit klaren Ansagen besser?", "Do clean callouts make us better?")),
    "br-chat-drop": (("Mein Chat hat mich hierhin geschickt", "Chat sent me here"),
                     ("Überlebe ich da?", "Can I survive this?")),
    "moba-scene-review": (("Wo habe ich dieses Match verloren?", "Where did I lose that game?"),
                          ("Der eine Fehler, der mich das Match kostet", "The one mistake that cost me the game")),
    "moba-new-character": (("Der erste richtige Erfolg mit dem neuen Charakter", "First real win on my new pick"),
                           ("Wie lange, bis der neue Charakter sitzt?", "How long until my new pick clicks?")),
    "moba-one-number": (("Neuer Bestwert beim Farmen?", "New farming best?"),
                        ("Nur eine Zahl zählt", "Only one number counts")),
    "moba-chat-pick": (("Gewinne ich mit dem Charakter vom Chat?", "Can I win with chat's pick?"),
                       ("Chat-Pick, den ich nie spiele", "A chat pick I never play")),
    "moba-duo": (("Was sieht mein Duo, das ich übersehe?", "What does my duo see that I miss?"),
                 ("Ein Tipp vom Duo, sofort umgesetzt", "My duo's tip, applied right away")),
    "story-first-playthrough": (("Meine ehrliche erste Reaktion", "My honest first reaction"),
                                ("Damit habe ich nicht gerechnet", "Did not see that coming")),
    "story-attempt-counter": (("Versuch 1 gegen den Versuch, der geklappt hat", "Attempt 1 vs the one that worked"),
                              ("Wie viele Versuche hat dieser Abschnitt gebraucht?", "How many tries did this section take?")),
    "story-recap": (("Die Geschichte bisher in 60 Sekunden", "The story so far in 60 seconds"),
                    ("Meine Theorie zur Geschichte", "My theory about the story")),
    "story-explore": (("Drei Dinge, die du vielleicht übersehen hast", "Three things you probably walked past"),
                      ("Was man hier beim ersten Mal übersieht", "What everyone misses here the first time")),
    "story-chat-choices": (("Der Chat hat entschieden …", "Chat decided …"),
                           ("Diese Entscheidung hatte Folgen", "That choice had consequences")),
    "horror-honest-reactions": (("Meine ehrliche Reaktion auf diesen Moment", "My honest reaction to this moment"),
                                ("Bin ich zu schreckhaft für dieses Spiel?", "Am I too jumpy for this one?")),
    "horror-courage-levels": (("Stufe 3: Licht aus, Ton lauter", "Level 3: lights off, volume up"),
                              ("Bis zu welcher Stufe halte ich durch?", "How far up the ladder can I go?")),
    "horror-clue-board": (("Was ist hier wirklich passiert?", "What really happened here?"),
                          ("Dieser Hinweis ändert alles", "This clue changes everything")),
    "horror-coop-night": (("Wir haben gesagt, wir bleiben zusammen …", "We said we'd stick together …"),
                          ("Wer von uns bleibt ruhig?", "Which of us stays calm?")),
    "horror-chat-guess": (("Der Chat wusste es vor mir", "Chat saw it coming before I did"),
                          ("Wer ahnt den Schreck zuerst?", "Who calls the scare first?")),
    "cozy-three-goals": (("Drei Ziele, ein gemütlicher Stream", "Three goals, one cosy stream"),
                         ("Abgehakt: so sieht es jetzt aus", "Ticked off: here's how it looks now")),
    "cozy-before-after": (("Vorher trostlos – und nachher?", "Bleak before – and after?"),
                          ("Von leer zu gemütlich", "From empty to cosy")),
    "cozy-starter-tips": (("Was ich am Anfang gern gewusst hätte", "What I wish I'd known on day one"),
                          ("Ein Anfänger-Fehler, den du dir sparen kannst", "A beginner mistake you can skip")),
    "cozy-one-rule": (("Nur eine Farbe – geht das?", "Only one colour – can it work?"),
                      ("Das Ergebnis mit nur einer Regel", "The result with just one rule")),
    "cozy-chat-names": (("Mein Chat hat diesen Ort mitgestaltet", "My chat helped design this place"),
                        ("Die Namen kommen vom Chat", "Chat picked every name")),
    "sandbox-three-solutions": (("Drei Wege zur selben Lösung", "Three ways to the same result"),
                                ("Geht das auch einfacher?", "Is there a simpler way?")),
    "sandbox-fix-it": (("Warum funktioniert mein Bau nicht?", "Why won't my build work?"),
                       ("Die kleinste Korrektur, die funktioniert", "The smallest fix that works")),
    "sandbox-big-project": (("Aus leerem Gelände wird ein Dorf", "Empty land to village"),
                            ("Eine Etappe im Zeitraffer", "One stage in time-lapse")),
    "sandbox-survival-start": (("Das war knapp", "That was close"),
                               ("Überlebe ich den ersten Tag?", "Do I survive day one?")),
    "sandbox-chat-build": (("Mein Chat hat entschieden, was ich baue", "My chat decided what I build"),
                           ("Vom Vorschlag zum fertigen Bau", "From idea to finished build")),
    "sports-one-technique": (("Erster gegen besten Versuch", "First attempt vs best attempt"),
                             ("Warum klappt dieser Move nie?", "Why can't I land this move?")),
    "sports-personal-best": (("Neue Bestmarke", "New personal best"),
                             ("So nah an meiner Bestmarke", "This close to my best")),
    "sports-match-review": (("Hier habe ich das Spiel verloren", "This is where I lost the game"),
                            ("Der eine Fehler, der mich Spiele kostet", "The one mistake that keeps costing me")),
    "sports-career": (("Das entscheidende Tor des Tages", "The deciding moment of the day"),
                      ("Hält mein Plan?", "Does my plan hold up?")),
    "sports-chat-tactic": (("Mein Chat stellt die Taktik", "My chat sets the tactics"),
                           ("Die verrückteste Wahl des Chats", "Chat's wildest call")),
    "jc-three-points": (("Drei Dinge, die mir mein Hobby beigebracht hat", "Three things my hobby taught me"),
                        ("Lohnt sich mein Hobby?", "Is my hobby worth it?")),
    "jc-live-project": (("Von leer zu fertig", "From blank to done"),
                        ("Das Projekt im Zeitraffer", "The project in time-lapse")),
    "jc-week-recap": (("Meine Woche in 60 Sekunden", "My week in 60 seconds"),
                      ("Das war meine Woche", "That was my week")),
    "jc-learn-live": (("Erster gegen letzten Versuch", "First vs last attempt"),
                      ("Das habe ich heute von null gelernt", "Learned this from zero today")),
    "jc-qna": (("Die beste Frage des Streams", "The best question of the stream"),
               ("Ehrliche Antwort auf eine ehrliche Frage", "Honest answer to an honest question")),
    "jc-topic-vote": (("Mein Chat hat das Thema gewählt", "My chat picked the topic"),
                      ("Der beste Moment der Diskussion", "The best moment of the discussion")),
    "general-first-impressions": (("Meine erste Stunde in diesem Spiel", "My first hour in this game"),
                                  ("Weiterspielen oder aufhören?", "Keep playing or drop it?")),
    "general-skill-diary": (("Erster gegen letzten Versuch", "First vs last attempt"),
                            ("Habe ich mein Ziel geschafft?", "Did I hit my goal?")),
    "general-two-ways": (("Zwei Wege, ein Ziel – welcher passt besser?", "Two ways, one goal – which fits better?"),
                         ("Schnell oder sicher?", "Fast or safe?")),
    "general-moment-of-week": (("Dieser Moment hat meine Woche geprägt", "This moment defined my week"),
                               ("Wie kam es zu diesem Moment?", "How did this moment even happen?")),
    "general-audience-choice": (("Mein Chat hat entschieden", "My chat decided"),
                                ("So ging es weiter", "Here's what happened next")),
}


@dataclass(frozen=True)
class TitleOption:
    """Ein Titel und die Bausteine, aus denen er besteht (für Tests und Begründungen)."""

    text: str
    approach: Approach
    lead_kind: Literal["goal", "mood"]
    tail_kind: Literal["question", "invite"]
    emoji: str


def daypart(minute_of_day: int) -> tuple[str, str, str]:
    hour = minute_of_day // 60 % 24
    for limit, noun, noun_m, english in DAYPARTS:
        if hour < limit:
            return noun, noun_m, english
    return DAYPARTS[-1][1:]  # pragma: no cover


def emojis_for(genre: str | None, game: str) -> tuple[str, ...]:
    if genre == "sports" and any(f" {alias} " in f" {normalize(game)} " for alias in _RACING):
        return EMOJIS["racing"]
    return EMOJIS.get(genre or "general", EMOJIS["general"])


def stream_mood(format_id: str, genre: str | None, requested: Mood | None) -> Mood:
    if requested:
        return requested
    return STREAM_TITLES[format_id].mood or GENRE_MOOD.get(genre, "chill")


def build_titles(format_id: str, genre: str | None, game: str, language: str, *,
                 counter: int = 1, start_minute: int = 18 * 60, mood: Mood | None = None,
                 rank_goal: str | None = None, rank_counter: int = 1,
                 first_time: bool = False, rotation: int | None = None) -> list[TitleOption]:
    """Drei Titel für den ganzen Stream (Ziel, Stimmung, Einladung); der erste ist der Haupttitel.

    ``counter`` zählt Folgen dieses Formats über die Wochen („Tag {n}“); ``rank_counter`` die
    Ranked-Streams mit Rang-Ziel. ``rotation`` wählt, welcher Ansatz Haupttitel ist (Standard:
    nach ``counter``), damit sich die Titel über die Woche abwechseln.
    """
    de = language == "de"
    pick = (lambda pair: pair[0]) if de else (lambda pair: pair[1])
    data = STREAM_TITLES[format_id]
    current = stream_mood(format_id, genre, mood)
    zeit, zeit_m, time = daypart(start_minute % 1440)
    fills = {key: pick(value) for key, value in FILLS.get(format_id, {}).items()}
    values = {"game": game, "zeit": zeit, "zeit_m": zeit_m, "time": time, "n": counter,
              "k": rank_counter, "rank": rank_goal or "", **fills}

    def fmt(pair: Text) -> str:
        return pick(pair).format(**values)

    ranked = data.ranked and genre in RANKED_GENRES
    if ranked and rank_goal:
        goal, question = fmt(RANK_GOAL), fmt(RANK_QUESTION)
    elif first_time and data.first_time:
        goal, question = fmt(FIRST_TIME), fmt(data.question)
    else:
        goal, question = fmt(data.goal), fmt(data.question)
    if ranked and current == "ambitious":
        mood_lead = fmt(RANKED_GOAL_LEAD if rank_goal else RANKED_LEAD)
    else:
        mood_lead = fmt(MOOD_LEADS.get(genre, MOOD_LEADS[None])[current])
    invites = INVITES["chat" if genre == "just_chatting" and current == "chill" else current]
    emoji = emojis_for(genre, game)

    options = [
        TitleOption(f"{goal} – {question} {emoji[0]}", "goal", "goal", "question", emoji[0]),
        TitleOption(f"{mood_lead} – {pick(invites[0])} {emoji[1]}", "mood", "mood", "invite",
                    emoji[1]),
        TitleOption(f"{goal} – {pick(invites[1])}! {emoji[0]}", "invite", "goal", "invite",
                    emoji[0]),
    ]
    start = (counter - 1 if rotation is None else rotation) % len(options)
    return options[start:] + options[:start]


def clip_titles(format_id: str, language: str) -> list[str]:
    index = 0 if language == "de" else 1
    return [pair[index] for pair in CLIP_TITLES[format_id]]
