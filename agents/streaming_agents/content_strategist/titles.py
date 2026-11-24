"""Stream-Titel: beschreiben den GANZEN Stream und laden zum Reinkommen ein.

Regeln (auch in agents/docs/content-strategist.md; Tests prüfen 1, 2, 3, 5, 6 und 8):
1. Bezug auf den ganzen Stream, nie auf eine einzelne Runde, Szene oder ein Match
   („diese Runde“, „dieses Match“, „diese Ecke“, „dieser Abschnitt“ … sind verboten).
2. Jeder Titel ist ein von Hand formulierter, vollständiger Satz: [Ziel oder Stimmung] und
   [Einladung oder Neugier-Frage], die inhaltlich zusammenpassen. Keine automatisch
   angehängten Endungen. Platzhalter nur für Zähler ({n}, {k}), Rang-Ziel ({rank}), Spielname
   ({game}), Tageszeit ({zeit}/{time}) und feste Standardwerte des Formats ({regel} …).
3. Genau ein Emoji, passend zu Genre UND Stimmung (``EMOJIS``), z. B. Horror chillig 🕯️,
   Horror lustig 😱.
4. Spielname nur, wenn er Teil des Hooks ist („Zum ersten Mal <Spiel>, blind“).
5. Ehrlich: Rang-Ziel nur, wenn angegeben; keine Rekord- oder „Unmöglich“-Versprechen; keine
   Großbuchstaben-Wörter außer Abkürzungen; höchstens ein Ausrufezeichen.
6. Ziel ≤ 70 Zeichen (das Wichtigste vorn), hart ≤ 140 (Twitch).
7. Deutsch und Englisch eigenständig und natürlich formuliert, nicht wörtlich übersetzt.
8. Drei Titel pro Stream, die sich schon im ANFANG unterscheiden (Text vor dem „–“):
   - ``goal``:   Ziel des Streams + Frage   („Großprojekt Tag 3 – wie weit kommen wir heute?“)
   - ``mood``:   Stimmung + Einladung/Frage („Chilliges Valorant & Quatschen – sag Hallo“)
   - ``invite``: beginnt mit der Einladung  („Bau mit mir weiter – Großprojekt Tag 3“)
   Laut vorgelesen muss jeder Titel wie ein echter Twitch-Titel klingen.

Die früheren, auf einen Moment bezogenen Titel leben als Ideen für den Clip-Titel weiter
(``CLIP_TITLES``), denn ein Kurzvideo zeigt genau einen Moment.
"""
from dataclasses import dataclass
from typing import Literal

from .genres import normalize

Mood = Literal["chill", "ambitious", "funny"]
Approach = Literal["goal", "mood", "invite"]
Tail = Literal["question", "invite"]
Text = tuple[str, str]

TITLE_TARGET_CHARS = 70

# Ein Emoji pro Genre und Stimmung („racing“ = Rennspiele innerhalb von Sport).
EMOJIS: dict[str, dict[str, str]] = {
    "shooter": {"chill": "🎯", "ambitious": "🔥", "funny": "😂"},
    "battle_royale": {"chill": "🪂", "ambitious": "🏆", "funny": "😂"},
    "moba": {"chill": "☕", "ambitious": "⚔️", "funny": "😂"},
    "story": {"chill": "📖", "ambitious": "🗡️", "funny": "😅"},
    "horror": {"chill": "🕯️", "ambitious": "👻", "funny": "😱"},
    "cozy": {"chill": "☕", "ambitious": "🌱", "funny": "😄"},
    "sandbox": {"chill": "⛏️", "ambitious": "🏰", "funny": "😂"},
    "sports": {"chill": "⚽", "ambitious": "🏆", "funny": "😂"},
    "racing": {"chill": "🚗", "ambitious": "🏁", "funny": "😂"},
    "just_chatting": {"chill": "☕", "ambitious": "💬", "funny": "😂"},
    "general": {"chill": "🎮", "ambitious": "✨", "funny": "😂"},
}
ALL_EMOJIS = frozenset(emoji for group in EMOJIS.values() for emoji in group.values())
_RACING = ("forza", "gran turismo", "f1", "mario kart", "trackmania", "assetto corsa",
           "iracing", "rocket league")

GENRE_MOOD: dict[str | None, Mood] = {
    "shooter": "ambitious", "battle_royale": "ambitious", "moba": "ambitious",
    "story": "chill", "horror": "funny", "cozy": "chill", "sandbox": "chill",
    "sports": "ambitious", "just_chatting": "chill", None: "chill",
}
RANKED_GENRES = frozenset({"shooter", "battle_royale", "moba", "sports"})

# Stimmungs-Titel pro Genre: (Deutsch, Englisch, Art des zweiten Teils).
# Platzhalter: {game}, {zeit} (Abend, Nacht …), {zeit_m} (nur männliche Formen), {time}.
MOOD_TITLES: dict[str | None, dict[str, tuple[str, str, Tail]]] = {
    "shooter": {
        "chill": ("Chilliges {game} & Quatschen – sag Hallo",
                  "Chill {game} & chatting – come say hi", "invite"),
        "ambitious": ("Heute wird gegrindet – wie weit kommen wir?",
                      "Grind session – how far can we push?", "question"),
        "funny": ("Chaos-{zeit} in {game} – lach mit mir",
                  "Chaos {time} in {game} – come laugh with me", "invite")},
    "battle_royale": {
        "chill": ("Entspannte Drops & Quatschen – sag Hallo",
                  "Laid-back drops & chatting – come say hi", "invite"),
        "ambitious": ("Heute jagen wir den Sieg – jagst du mit?",
                      "Hunting a win today – want in?", "question"),
        "funny": ("Chaos-Drops in {game} – wo landen wir diesmal?",
                  "Chaotic drops in {game} – where do we land this time?", "question")},
    "moba": {
        "chill": ("Entspanntes {game} & Quatschen – sag Hallo",
                  "Laid-back {game} & chatting – come say hi", "invite"),
        "ambitious": ("Heute wird gegrindet – schaffen wir eine Siegesserie?",
                      "Grind day – can we string some wins together?", "question"),
        "funny": ("Chaos-{zeit} in {game} – wer feedet zuerst?",
                  "Chaos {time} in {game} – who feeds first?", "question")},
    "story": {
        "chill": ("Gemütlicher Story-{zeit_m} – komm mit auf die Reise",
                  "Cosy story {time} – come along for the ride", "invite"),
        "ambitious": ("Heute geht's weit voran – wie viel schaffen wir?",
                      "Big progress day – how far do we get?", "question"),
        "funny": ("Lachen und Leiden in {game} – leidest du mit?",
                  "Laughing and suffering through {game} – you with me?", "question")},
    "horror": {
        "chill": ("Gemütlicher Grusel-{zeit_m} – trau dich rein",
                  "A cosy horror {time} – come in if you dare", "invite"),
        "ambitious": ("Horror-{zeit} ohne Weglaufen – hältst du durch?",
                      "Horror {time}, no running away – can you handle it?", "question"),
        "funny": ("Horror-{zeit} in {game} – lachen oder schreien?",
                  "Horror {time} in {game} – laughing or screaming?", "question")},
    "cozy": {
        "chill": ("Gemütlicher {zeit_m} in {game} – setz dich dazu",
                  "Cosy {time} in {game} – come hang out", "invite"),
        "ambitious": ("Fleißiger {zeit_m} in {game} – was schaffen wir alles?",
                      "Busy {time} in {game} – how much can we get done?", "question"),
        "funny": ("Gemütliches Chaos in {game} – was geht heute schief?",
                  "Cosy chaos in {game} – what goes wrong today?", "question")},
    "sandbox": {
        "chill": ("Entspannt bauen in {game} – schau gern zu",
                  "Chill building in {game} – pull up a chair", "invite"),
        "ambitious": ("Bau-{zeit}: Wie viel steht am Ende?",
                      "Build {time}: how much stands by the end?", "question"),
        "funny": ("Bau-Chaos in {game} – hält das am Ende?",
                  "Building chaos in {game} – will it hold?", "question")},
    "sports": {
        "chill": ("Lockeres {game} & Quatschen – sag Hallo",
                  "Easygoing {game} & chatting – come say hi", "invite"),
        "ambitious": ("Trainingstag – wie viel besser werde ich heute?",
                      "Training day – how much better can I get?", "question"),
        "funny": ("Spaß-{zeit} in {game} – wer lacht zuletzt?",
                  "Fun {time} in {game} – who laughs last?", "question")},
    "just_chatting": {
        "chill": ("Kaffee & Quatschen – komm rein und sag Hallo",
                  "Coffee & chatting – come say hi", "invite"),
        "ambitious": ("Ein Thema, ehrlich besprochen – was denkst du?",
                      "One topic, honestly discussed – what do you think?", "question"),
        "funny": ("Quatsch-{zeit} – worüber lachen wir heute?",
                  "Silly chat {time} – what are we laughing about today?", "question")},
    None: {
        "chill": ("Entspannt {game} zocken – sag Hallo",
                  "Chilling with {game} – come say hi", "invite"),
        "ambitious": ("Mit Ziel in {game} – schaffe ich es heute?",
                      "Playing {game} with a goal – can I make it today?", "question"),
        "funny": ("Chaos in {game} – was passiert als Nächstes?",
                  "Chaos in {game} – what happens next?", "question")},
}
RANKED_MOOD: tuple[str, str, Tail] = ("Ranked-{zeit}: Wir klettern – kletterst du mit?",
                                      "Ranked {time}: time to climb – you in?", "question")
RANKED_GOAL_MOOD: tuple[str, str, Tail] = (
    "Ranked-{zeit}: Wir klettern Richtung {rank} – komm mit!",
    "Ranked {time}: climbing towards {rank} – come along!", "invite")
RANK_GOAL: Text = ("Road to {rank}, Tag {k} – kommen wir heute ein Stück näher?",
                   "Road to {rank}, day {k} – do we get closer today?")

DAYPARTS = (  # (bis Stunde, Deutsch, Deutsch männlich, Englisch)
    (5, "Nacht", "Abend", "night"), (12, "Vormittag", "Vormittag", "morning"),
    (17, "Nachmittag", "Nachmittag", "afternoon"), (22, "Abend", "Abend", "evening"),
    (24, "Nacht", "Abend", "night"),
)

FILLS: dict[str, dict[str, Text]] = {
    "shooter-chat-rule": {"regel": ("nur einer Waffe", "one weapon only")},
    "moba-one-number": {"ziel": ("70 Last Hits in 10 Minuten", "70 last hits by 10 minutes")},
    "cozy-one-rule": {"regel": ("nur einer Farbe", "one colour only")},
    "jc-three-points": {"thema": ("mein Hobby", "my hobby")},
    "jc-learn-live": {"skill": ("etwas Neues", "something new")},
}


@dataclass(frozen=True)
class StreamTitle:
    goal: Text                  # Ziel + Frage, als ganzer Satz
    invite: Text                # beginnt mit der Einladung, als ganzer Satz
    first: Text | None = None   # „Zum ersten Mal …“ (nur mit first_time)
    ranked: bool = False        # Ranked-Format: Rang-Ziel möglich
    mood: Mood | None = None    # Standard-Stimmung des Formats (sonst die des Genres)


STREAM_TITLES: dict[str, StreamTitle] = {
    # Shooter
    "shooter-decision-review": StreamTitle(
        ("Jede Niederlage wird zur Lektion – wie viel lerne ich heute?",
         "Every loss becomes a lesson – how much do I learn today?"),
        ("Komm mit – ich spiele und erkläre meine Entscheidungen",
         "Come along – I play and explain my calls"), ranked=True),
    "shooter-micro-skill": StreamTitle(
        ("Aim-Training Tag {n} – sitzt das Fadenkreuz heute?",
         "Aim training, day {n} – does my crosshair behave today?"),
        ("Schau mir beim Aim-Training zu, Tag {n}", "Watch me fix my aim, day {n}"),
        ranked=True),
    "shooter-role-swap": StreamTitle(
        ("Meine ungeliebte Rolle – wie schlimm wird's?",
         "My least favourite role – how bad will it get?"),
        ("Komm mit, ich spiele heute eine neue Rolle",
         "Come along – I'm trying a new role today")),
    "shooter-chat-rule": StreamTitle(
        ("Jedes Match mit {regel} – wie lange halte ich durch?",
         "Every match with {regel} – how long can I last?"),
        ("Du bestimmst die Regel, ich muss damit klarkommen",
         "You pick the rule, I have to live with it"), mood="funny"),
    "shooter-coach": StreamTitle(
        ("Mit Coach im Ohr – merkt man heute einen Unterschied?",
         "Coach on comms – will you see a difference today?"),
        ("Hör mit, was mein Coach mir rät", "Listen in on my coach's advice")),
    # Battle Royale
    "br-drop-study": StreamTitle(
        ("Landeplatz-Test: zwei Orte, ein Sieger – wo lande ich ab jetzt?",
         "Drop test: two spots, one winner – where do I land now?"),
        ("Rate mit: Welcher Landeplatz gewinnt heute?", "Guess along: which drop spot wins today?"),
        ranked=True),
    "br-rotation": StreamTitle(
        ("Jede Zone mit Plan – reicht das heute für einen Sieg?",
         "Every zone with a plan – enough for a win today?"),
        ("Komm mit auf Siegjagd – ich erkläre jeden Zug",
         "Join the hunt for a win – every move explained"), ranked=True),
    "br-loadout-lab": StreamTitle(
        ("Ausrüstungs-Labor, Test {n} – welche Kombi gewinnt?",
         "Loadout lab, test {n} – which setup wins?"),
        ("Tüftel mit: zwei Ausrüstungen im fairen Test", "Tinker along: two loadouts, one fair test"),
        ranked=True),
    "br-squad-comms": StreamTitle(
        ("Squad-{zeit} mit klaren Ansagen – werden wir besser?",
         "Squad {time} with clean callouts – do we get better?"),
        ("Hör unserem Squad zu – diesmal mit klaren Ansagen",
         "Listen in on our squad – clean callouts this time")),
    "br-chat-drop": StreamTitle(
        ("Der Chat wählt jeden Landeplatz – überlebe ich das?",
         "Chat picks every drop – can I survive this?"),
        ("Du wählst, wo ich lande – such dir was aus", "You pick where I drop – choose wisely"),
        mood="funny"),
    # MOBA
    "moba-scene-review": StreamTitle(
        ("Weniger Fehler, mehr Siege – schaffen wir das heute?",
         "Fewer mistakes, more wins – can we do it today?"),
        ("Komm mit in meine Matches – wir finden meine Fehler",
         "Come along – let's find my mistakes together"), ranked=True),
    "moba-new-character": StreamTitle(
        ("Tag {n} mit meinem neuen Main – klappt heute der erste Sieg?",
         "Day {n} on my new main – first win today?"),
        ("Lern mit mir einen neuen Charakter – Tag {n}", "Learn a new character with me – day {n}")),
    "moba-one-number": StreamTitle(
        ("Farm-Training – schaffe ich heute {ziel}?",
         "Farm practice – can I hit {ziel} today?"),
        ("Zähl mit: Komme ich heute auf {ziel}?", "Count along – do I get {ziel} today?"),
        ranked=True),
    "moba-chat-pick": StreamTitle(
        ("Der Chat wählt jeden Charakter – gewinne ich mit allem?",
         "Chat picks every character – can I win with anything?"),
        ("Du suchst den Charakter aus, ich muss ihn spielen",
         "You pick the character, I have to play it"), mood="funny"),
    "moba-duo": StreamTitle(
        ("Duo-{zeit} mit Coach – wie viel lerne ich heute?",
         "Duo {time} with a coach – how much do I learn today?"),
        ("Hör zu, was mein Duo mir beibringt", "Listen in as my duo teaches me")),
    # Story/Singleplayer
    "story-first-playthrough": StreamTitle(
        ("Mein erster Durchgang, Etappe {n} – was erwartet mich heute?",
         "My first playthrough, part {n} – what's waiting today?"),
        ("Erleb Etappe {n} mit mir – bitte keine Spoiler",
         "Experience part {n} with me – no spoilers please"),
        first=("Zum ersten Mal {game}, blind – was erwartet mich?",
               "First time playing {game}, blind – what awaits?")),
    "story-attempt-counter": StreamTitle(
        ("Ein harter Brocken – wie viele Versuche brauche ich?",
         "One tough fight – how many tries will it take?"),
        ("Zähl meine Versuche mit – heute wird's zäh", "Count my attempts with me – it'll be rough"),
        mood="ambitious"),
    "story-recap": StreamTitle(
        ("Story-{zeit} – wohin führt die Geschichte heute?",
         "Story {time} – where does the story go today?"),
        ("Neu dabei? Erst die Geschichte in 5 Minuten, dann weiter",
         "New here? Catch up in 5 minutes, then we play on")),
    "story-explore": StreamTitle(
        ("Langsam spielen, alles entdecken – was finden wir heute?",
         "Slow play, see everything – what will we find today?"),
        ("Erkunde mit mir jeden Winkel", "Explore every corner with me")),
    "story-chat-choices": StreamTitle(
        ("Der Chat lenkt die Geschichte – wohin führt uns das?",
         "Chat steers the story – where will it take us?"),
        ("Du triffst die Entscheidungen in meiner Geschichte", "You make the choices in my story"),
        mood="funny"),
    # Horror
    "horror-honest-reactions": StreamTitle(
        ("Horror mit Facecam – wie oft schreie ich heute?",
         "Horror on facecam – how often will I scream?"),
        ("Schau mir beim Gruseln zu – Facecam an", "Watch me get scared – facecam on"),
        first=("Zum ersten Mal {game}, blind – wie oft schreie ich?",
               "First time in {game}, blind – how often will I scream?")),
    "horror-courage-levels": StreamTitle(
        ("Mutprobe in drei Stufen – wie weit komme ich heute?",
         "Three-step courage test – how far will I get?"),
        ("Steig mit mir Stufe für Stufe ins Dunkle", "Step into the dark with me, level by level")),
    "horror-clue-board": StreamTitle(
        ("Spurensuche, Teil {n} – was ist hier wirklich passiert?",
         "Following the clues, part {n} – what really happened here?"),
        ("Rätsel mit: Teil {n} der Spurensuche", "Puzzle it out with me – part {n}"),
        first=("Zum ersten Mal {game}, blind – was steckt dahinter?",
               "First time in {game}, blind – what's really going on?"), mood="chill"),
    "horror-coop-night": StreamTitle(
        ("Koop-Horror mit Freunden – wer bleibt am längsten ruhig?",
         "Co-op horror with friends – who keeps it together longest?"),
        ("Schau zu, wie unsere Gruppe auseinanderfällt", "Watch our group fall apart")),
    "horror-chat-guess": StreamTitle(
        ("Schreck-Wetten mit dem Chat – wer ahnt es zuerst?",
         "Scare bets with chat – who calls it first?"),
        ("Tipp mit: Wann kommt der nächste Schreck?", "Place your bet: when's the next scare?")),
    # Cozy/Simulation
    "cozy-three-goals": StreamTitle(
        ("Drei kleine Ziele, Woche {n} – schaffen wir alle?",
         "Three small goals, week {n} – can we tick them all?"),
        ("Hak mit mir drei kleine Ziele ab, Woche {n}", "Tick off three small goals with me, week {n}")),
    "cozy-before-after": StreamTitle(
        ("Ein leerer Ort wird gemütlich – wie sieht er am Ende aus?",
         "Turning an empty spot cosy – how will it look by the end?"),
        ("Gestalte mit: Von leer zu gemütlich in einem Stream",
         "Decorate along: empty to cosy in one stream")),
    "cozy-starter-tips": StreamTitle(
        ("Gemütlich spielen mit Einsteiger-Tipps – neu im Spiel?",
         "Cosy play with starter tips – new to the game?"),
        ("Frisch angefangen? Spiel mit, ich zeig dir Tipps",
         "Just started? Play along and pick up some tips")),
    "cozy-one-rule": StreamTitle(
        ("Den ganzen Stream mit {regel} – bleibt's gemütlich?",
         "A whole stream with {regel} – can it stay cosy?"),
        ("Schau, was mit {regel} entsteht", "See what I can make with {regel}"), mood="funny"),
    "cozy-chat-names": StreamTitle(
        ("Der Chat gibt die Namen – wie heißt unser neuer Ort?",
         "Chat names everything – what's our new place called?"),
        ("Gib meinem neuen Ort einen Namen", "Help name my new place")),
    # Sandbox/Survival
    "sandbox-three-solutions": StreamTitle(
        ("Bau-Labor: drei Lösungen – welche gewinnt?",
         "Build lab: three solutions – which one wins?"),
        ("Tüftel mit: drei Wege zur selben Lösung", "Tinker along: three ways to the same goal")),
    "sandbox-fix-it": StreamTitle(
        ("Fehlersuche am eigenen Bau – läuft es heute endlich?",
         "Fixing my own build – will it finally work today?"),
        ("Hilf mir, den Fehler in meinem Bau zu finden", "Help me find what's wrong with my build")),
    "sandbox-big-project": StreamTitle(
        ("Großprojekt Tag {n} – wie weit kommen wir heute?",
         "Big build, day {n} – how far do we get today?"),
        ("Bau mit mir weiter – Großprojekt Tag {n}", "Keep building with me – big build, day {n}")),
    "sandbox-survival-start": StreamTitle(
        ("Neue Welt, Tag {n} – schaffen wir das Tagesziel?",
         "Fresh world, day {n} – do we hit today's goal?"),
        ("Überleb mit mir Tag {n} in der neuen Welt", "Survive day {n} with me in a fresh world")),
    "sandbox-chat-build": StreamTitle(
        ("Der Chat plant, ich baue – was entsteht heute?",
         "Chat plans, I build – what gets built today?"),
        ("Du schlägst vor, ich baue", "You suggest it, I build it"), mood="funny"),
    # Sport/Rennspiele
    "sports-one-technique": StreamTitle(
        ("Technik-Training, Tag {n} – klappt der Move heute?",
         "Skill practice, day {n} – will the move click today?"),
        ("Trainier mit mir einen Move, Tag {n}", "Practise one move with me, day {n}")),
    "sports-personal-best": StreamTitle(
        ("Jagd auf meine Bestmarke – klappt's heute?",
         "Chasing my personal best – is today the day?"),
        ("Drück mir die Daumen: neue Bestmarke gesucht",
         "Cross your fingers – going for a new best")),
    "sports-match-review": StreamTitle(
        ("Weniger Fehler, mehr Siege – wie viele werden es heute?",
         "Fewer mistakes, more wins – how many today?"),
        ("Komm mit – nach jedem Spiel zeige ich, wo's hakt",
         "Come along – after every game I show what went wrong"), ranked=True),
    "sports-career": StreamTitle(
        ("Meine Saison, Folge {n} – wie weit kommen wir?",
         "My season, episode {n} – how far can we go?"),
        ("Fiebere mit: Saison-Folge {n}", "Cheer me on: season episode {n}")),
    "sports-chat-tactic": StreamTitle(
        ("Der Chat stellt die Taktik – geht das gut?", "Chat calls the tactics – will it work?"),
        ("Du bestimmst, wie ich spiele", "You decide how I play"), mood="funny"),
    # Just Chatting
    "jc-three-points": StreamTitle(
        ("Drei Dinge über {thema} – welches überrascht dich?",
         "Three things about {thema} – which one surprises you?"),
        ("Quatsch mit mir über {thema}", "Let's talk about {thema}")),
    "jc-live-project": StreamTitle(
        ("Live-Projekt, Teil {n} – werde ich heute fertig?",
         "Live project, part {n} – will I finish today?"),
        ("Bastel mit mir weiter, Projekt Teil {n}", "Make stuff with me – project part {n}")),
    "jc-week-recap": StreamTitle(
        ("Wochenrückblick & Plan – wie war deine Woche?",
         "Week recap & next week's plan – how was yours?"),
        ("Erzähl mir von deiner Woche, ich erzähl dir meine",
         "Tell me about your week, I'll tell you mine")),
    "jc-learn-live": StreamTitle(
        ("Ich lerne {skill}, Tag {n} – wie weit komme ich heute?",
         "Learning {skill}, day {n} – how far do I get today?"),
        ("Lern mit mir {skill}, Tag {n}", "Learn {skill} with me, day {n}")),
    "jc-qna": StreamTitle(
        ("Kaffee, Quatschen und eure Fragen – was willst du wissen?",
         "Coffee, chat and your questions – what do you want to know?"),
        ("Frag mich, was du willst – ich antworte ehrlich", "Ask me anything – honest answers only")),
    "jc-topic-vote": StreamTitle(
        ("Der Chat wählt das Thema – worüber reden wir heute?",
         "Chat picks the topic – what are we talking about?"),
        ("Stimm ab, worüber wir heute reden", "Vote on today's topic"), mood="funny"),
    # Allgemein
    "general-first-impressions": StreamTitle(
        ("Erste Stunde in {game} – lohnt es sich?", "First hour in {game} – is it worth it?"),
        ("Probier {game} mit mir zum ersten Mal aus", "Try {game} with me for the first time"),
        first=("Zum ersten Mal {game} – lohnt es sich?", "First time playing {game} – worth it?")),
    "general-skill-diary": StreamTitle(
        ("Lern-Tagebuch, Tag {n} – schaffe ich mein Ziel?",
         "Learning diary, day {n} – do I hit my goal?"),
        ("Üb mit mir – Lern-Tagebuch, Tag {n}", "Practise with me – learning diary, day {n}")),
    "general-two-ways": StreamTitle(
        ("Zwei Wege, ein Ziel – welcher ist besser?", "Two routes, one goal – which is better?"),
        ("Rate mit: Welcher Weg bringt mich schneller ans Ziel?",
         "Guess along: which route gets me there faster?")),
    "general-moment-of-week": StreamTitle(
        ("Die Woche in Momenten – welcher war dein Favorit?",
         "The week in moments – which was your favourite?"),
        ("Schau mit mir auf die besten Momente der Woche",
         "Look back on the week's best moments with me")),
    "general-audience-choice": StreamTitle(
        ("Der Chat entscheidet alles – wohin geht's heute?",
         "Chat decides everything – where are we headed?"),
        ("Du entscheidest, wie es weitergeht", "You decide what happens next"), mood="funny"),
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
    tail_kind: Tail
    emoji: str

    @property
    def opening(self) -> str:
        """Der Anfang bis zum Gedankenstrich – daran unterscheiden sich die drei Titel."""
        return self.text.split(" – ")[0].removesuffix(f" {self.emoji}").strip()


def daypart(minute_of_day: int) -> tuple[str, str, str]:
    hour = minute_of_day // 60 % 24
    for limit, noun, noun_m, english in DAYPARTS:
        if hour < limit:
            return noun, noun_m, english
    return DAYPARTS[-1][1:]  # pragma: no cover


def emoji_for(genre: str | None, game: str, mood: Mood) -> str:
    key = genre or "general"
    if genre == "sports" and any(f" {alias} " in f" {normalize(game)} " for alias in _RACING):
        key = "racing"
    return EMOJIS.get(key, EMOJIS["general"])[mood]


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
    index = 0 if language == "de" else 1
    data = STREAM_TITLES[format_id]
    current = stream_mood(format_id, genre, mood)
    zeit, zeit_m, time = daypart(start_minute % 1440)
    fills = {key: value[index] for key, value in FILLS.get(format_id, {}).items()}
    values = {"game": game, "zeit": zeit, "zeit_m": zeit_m, "time": time, "n": counter,
              "k": rank_counter, "rank": rank_goal or "", **fills}
    emoji = emoji_for(genre, game, current)

    def text(sentence: str) -> str:
        return f"{sentence.format(**values)} {emoji}"

    ranked = data.ranked and genre in RANKED_GENRES
    if ranked and rank_goal:
        goal = RANK_GOAL[index]
    elif first_time and data.first:
        goal = data.first[index]
    else:
        goal = data.goal[index]
    if ranked and current == "ambitious":
        mood_entry = RANKED_GOAL_MOOD if rank_goal else RANKED_MOOD
    else:
        mood_entry = MOOD_TITLES.get(genre, MOOD_TITLES[None])[current]

    options = [
        TitleOption(text(goal), "goal", "goal", "question", emoji),
        TitleOption(text(mood_entry[index]), "mood", "mood", mood_entry[2], emoji),
        TitleOption(text(data.invite[index]), "invite", "goal", "invite", emoji),
    ]
    start = (counter - 1 if rotation is None else rotation) % len(options)
    return options[start:] + options[:start]


def clip_titles(format_id: str, language: str) -> list[str]:
    index = 0 if language == "de" else 1
    return [pair[index] for pair in CLIP_TITLES[format_id]]
