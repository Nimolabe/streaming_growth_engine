"""Stream-Titel nach echten Twitch-Vorbildern (Recherche: DE-Streamer in Valorant, Fortnite, LoL,
Minecraft, Just Chatting, Stardew, Elden Ring, Phasmophobia; vom Nutzer bestätigt).

Regeln (auch in agents/docs/content-strategist.md; Tests prüfen 1, 2, 4, 5 und 6):
1. Bausteine mit " | " statt ganzer Sätze: [Emoji + Hook] | [Fortschritt/Info] | [Twist/Einladung].
   2–4 Bausteine.
2. Genau ein Emoji, am ANFANG des Titels. Es steht im Text selbst; nichts wird angehängt.
3. Persönlichkeit und Selbstironie sind ausdrücklich erwünscht („90 % Hoffnung, 10 % Skill“).
4. Höchstens 2 Wörter pro Titel in GROSSBUCHSTABEN (Abkürzungen wie LoL, CS2, MMR zählen nicht).
5. Höchstens ein „!“ („?!“ zählt als eins). Bezug auf den ganzen Stream, nie auf eine einzelne
   Runde, Szene oder ein Match („diese Runde“ … sind verboten).
6. Ziel ≤ 70 Zeichen ohne Befehle (bei normalen Spielnamen), hart ≤ 140 (Twitch).
7. Chat-Formate sprechen den Chat mit „Ihr“ an, Einladungen mit „du“.

Eigene Chat-Befehle (``commands``, z. B. ``!discord``) werden mit " | " ans Ende gehängt. Würde
der Titel dadurch länger als 140 Zeichen, fallen die Befehle weg, nie der Titel selbst.

Platzhalter: {n} {k} {rank} {from} {game} {zeit} {zeit_m} {time} {regel} {ziel} {thema} {skill}.
Pro Stream gibt es drei Titel, die sich im ersten Baustein unterscheiden:
``goal`` (Ziel/Fortschritt), ``mood`` (Stimmung des Genres) und ``invite`` (Einladung).

Die früheren, auf einen Moment bezogenen Titel leben als Ideen für den Clip-Titel weiter
(``CLIP_TITLES``), denn ein Kurzvideo zeigt genau einen Moment.
"""
import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

from .twitch_limits import TITLE_MAX_CHARS

Mood = Literal["chill", "ambitious", "funny"]
Approach = Literal["goal", "mood", "invite"]
Text = tuple[str, str]  # (Deutsch, Englisch)

TITLE_TARGET_CHARS = 70
SEPARATOR = " | "
MAX_COMMANDS = 3
COMMAND_RE = re.compile(r"^![a-z0-9_]{1,20}$")

GENRE_MOOD: dict[str | None, Mood] = {
    "shooter": "ambitious", "battle_royale": "ambitious", "moba": "ambitious",
    "story": "chill", "horror": "funny", "cozy": "chill", "sandbox": "chill",
    "sports": "ambitious", "just_chatting": "chill", None: "chill",
}
RANKED_GENRES = frozenset({"shooter", "battle_royale", "moba", "sports"})

DAYPARTS = (  # (bis Stunde, Deutsch, Deutsch männlich, Englisch)
    (5, "Nacht", "Abend", "night"), (12, "Vormittag", "Vormittag", "morning"),
    (17, "Nachmittag", "Nachmittag", "afternoon"), (22, "Abend", "Abend", "evening"),
    (24, "Nacht", "Abend", "night"),
)

# Stimmungs-Titel pro Genre (None = kein Genre erkannt): (Deutsch, Englisch).
MOOD_TITLES: dict[str | None, dict[str, Text]] = {
    "shooter": {
        "chill": ("🎯 Chilliges {game} & Quatschen | Komm rein und sag Hallo!",
                 "🎯 Chill {game} & chatting | Come say hi!"),
        "ambitious": ("🔴 Ranked Grind | Heute wird GESCHWITZT",
                     "🔴 Ranked grind | SWEATY games today"),
        "funny": ("😂 Chaos-{zeit} in {game} | Skill optional",
                 "😂 Chaos {time} in {game} | Skill optional")},
    "battle_royale": {
        "chill": ("🪂 Entspannte Runden & Quatschen | Sag Hallo!",
                 "🪂 Chill games & chatting | Say hi!"),
        "ambitious": ("🏆 Erst ein Sieg, dann Feierabend | Komm rein!",
                     "🏆 One win, then I'm done | Come in!"),
        "funny": ("😂 Chaos-Drops in {game} | Wo landen wir diesmal?",
                 "😂 Chaotic drops in {game} | Where do we land this time?")},
    "moba": {
        "chill": ("☕ Entspanntes {game} & Quatschen | Sag Hallo!",
                 "☕ Laid-back {game} & chatting | Say hi!"),
        "ambitious": ("🔴 Ranked Grind | Heute wird geklettert",
                     "🔴 Ranked grind | Climbing today"),
        "funny": ("😂 Chaos-{zeit} in {game} | Wer feedet zuerst?",
                 "😂 Chaos {time} in {game} | Who feeds first?")},
    "story": {
        "chill": ("📖 Gemütlicher Story-{zeit_m} | Komm mit auf die Reise",
                 "📖 Cosy story {time} | Come along for the ride"),
        "ambitious": ("🗡️ Heute geht's WEIT voran | Komm mit!",
                     "🗡️ BIG progress today | Come along!"),
        "funny": ("😅 Lachen und Leiden in {game} | Leidest du mit?",
                 "😅 Laughing and suffering through {game} | You with me?")},
    "horror": {
        "chill": ("🕯️ Gemütlicher Grusel-{zeit_m} | Trau dich rein",
                 "🕯️ A cosy horror {time} | Come in if you dare"),
        "ambitious": ("👻 Horror-{zeit} mit Licht aus | Hältst du durch?",
                     "👻 Horror {time}, lights off | Can you handle it?"),
        "funny": ("😱 Horror-{zeit} in {game} | Lachen oder schreien?",
                 "😱 Horror {time} in {game} | Laughing or screaming?")},
    "cozy": {
        "chill": ("☕ Gemütlicher {zeit_m} in {game} | Kaffee & Quatschen",
                 "☕ Cosy {time} in {game} | Coffee & chatting"),
        "ambitious": ("🌱 Fleißiger {zeit_m} in {game} | Was schaffen wir alles?",
                     "🌱 Busy {time} in {game} | How much can we get done?"),
        "funny": ("😄 Gemütliches Chaos in {game} | Was geht heute schief?",
                 "😄 Cosy chaos in {game} | What goes wrong today?")},
    "sandbox": {
        "chill": ("⛏️ Entspannt bauen in {game} | Komm rein und chill mit!",
                 "⛏️ Chill building in {game} | Come hang out!"),
        "ambitious": ("🏰 Bau-{zeit} | Heute wird RICHTIG was geschafft",
                     "🏰 Build {time} | Getting LOTS done today"),
        "funny": ("😂 Bau-Chaos in {game} | Hält das am Ende?",
                 "😂 Building chaos in {game} | Will it hold?")},
    "sports": {
        "chill": ("⚽ Lockeres {game} & Quatschen | Sag Hallo!",
                 "⚽ Easygoing {game} & chatting | Say hi!"),
        "ambitious": ("🔴 Heute wird GESCHWITZT | Fiebere mit!",
                     "🔴 SWEATY games today | Cheer me on!"),
        "funny": ("😂 Spaß-{zeit} in {game} | Wer lacht zuletzt?",
                 "😂 Fun {time} in {game} | Who laughs last?")},
    "just_chatting": {
        "chill": ("☕ Kaffee & Quatschen | Komm rein und sag Hallo!",
                 "☕ Coffee & chatting | Come say hi!"),
        "ambitious": ("💬 Großes Thema heute | Red mit!",
                     "💬 Big topic today | Join the conversation!"),
        "funny": ("😂 Quatsch-{zeit} | Worüber lachen wir heute?",
                 "😂 Silly chat {time} | What are we laughing about?")},
    None: {
        "chill": ("🎮 Entspannt {game} zocken | Sag Hallo!",
                 "🎮 Chilling with {game} | Say hi!"),
        "ambitious": ("✨ Mit Ziel in {game} | Schaffe ich es heute?",
                     "✨ Playing {game} with a goal | Can I make it today?"),
        "funny": ("😂 Chaos in {game} | Was passiert als Nächstes?",
                 "😂 Chaos in {game} | What happens next?")},
}

# Ranked (nur Ranked-Formate in Shooter, Battle Royale, MOBA, Sport).
RANKED_MOOD: Text = ("🔴 Ranked-{zeit} | Heute wird geklettert – komm mit!",
                     "🔴 Ranked {time} | Climbing today – come along!")
RANKED_GOAL_MOOD: Text = ("🔴 Road to {rank} | Heute wird GEGRINDET",
                          "🔴 Road to {rank} | GRINDING today")
RANK_GOAL: Text = ("🔴 Ranked Grind | Tag {k} | Road to {rank}",
                   "🔴 Ranked grind | Day {k} | Road to {rank}")
RANK_JOURNEY: Text = ("🔴 Von {from} nach {rank} | Tag {k} | Komm rein!",
                      "🔴 From {from} to {rank} | Day {k} | Come in!")

FILLS: dict[str, dict[str, Text]] = {
    "shooter-chat-rule": {"regel": ("nur einer Waffe", "one weapon only")},
    "moba-one-number": {"ziel": ("70 Last Hits in 10 Minuten", "70 last hits by 10 minutes")},
    "cozy-one-rule": {"regel": ("nur einer Farbe", "one colour only")},
    "jc-three-points": {"thema": ("mein Hobby", "my hobby")},
    "jc-learn-live": {"skill": ("etwas Neues", "something new")},
}


@dataclass(frozen=True)
class StreamTitle:
    goal: Text                  # Ziel/Fortschritt des Streams
    invite: Text                # Einladung
    first: Text | None = None   # „Zum ersten Mal …“ (nur mit first_time)
    ranked: bool = False        # Ranked-Format: Rang-Ziel möglich
    mood: Mood | None = None    # Standard-Stimmung des Formats (sonst die des Genres)


STREAM_TITLES: dict[str, StreamTitle] = {
    "shooter-decision-review": StreamTitle(
        ("🔴 Ranked mit Köpfchen | Tag {n} | Heute wird nicht getiltet",
         "🔴 Big-brain ranked | Day {n} | No tilting today"),
        ("🧠 Erst denken, dann peeken | Ranked | Klappt das heute?",
         "🧠 Think first, peek second | Ranked | Will it work?"),
        ranked=True),
    "shooter-micro-skill": StreamTitle(
        ("🎯 Aim-Woche, Tag {n} | Heute trifft ALLES. Hoffentlich.",
         "🎯 Aim week, day {n} | Today EVERYTHING hits. Hopefully."),
        ("🎯 Fadenkreuz-Training | Tag {n} | Mein Aim braucht Hilfe",
         "🎯 Crosshair training | Day {n} | My aim needs help"),
        ranked=True),
    "shooter-role-swap": StreamTitle(
        ("😬 Heute spiele ich die Rolle, die ich hasse | Das wird was",
         "😬 Playing the role I hate today | This will be fun"),
        ("🔁 Rollentausch | Raus aus der Komfortzone | Komm rein und leide mit!",
         "🔁 Role swap | Out of my comfort zone | Come suffer with me!")),
    "shooter-chat-rule": StreamTitle(
        ("😂 Jedes Match mit {regel} | Ihr habt das so gewollt",
         "😂 Every match with {regel} | You asked for this"),
        ("🎲 Der Chat macht die Regeln | Ich muss trotzdem gewinnen",
         "🎲 Chat makes the rules | I still have to win"),
        mood="funny"),
    "shooter-coach": StreamTitle(
        ("🎧 Coach im Ohr | Ranked | Werde ich heute endlich besser?",
         "🎧 Coach on comms | Ranked | Do I finally get better?"),
        ("🎧 Live-Coaching | Hör mit, was ich alles falsch mache",
         "🎧 Live coaching | Hear everything I do wrong")),
    "br-drop-study": StreamTitle(
        ("🪂 Neuer Lieblings-Drop gesucht | Tag {n} | Hot Drop oder Ecke?",
         "🪂 Searching for a new favourite drop | Day {n} | Hot drop or corner?"),
        ("🪂 Landeplatz-Test | Zwei Orte, ein Sieger | Rate mit!",
         "🪂 Drop test | Two spots, one winner | Guess along!"),
        ranked=True),
    "br-rotation": StreamTitle(
        ("🏆 Erst ein Sieg, dann Feierabend | Wie lange dauert's heute?",
         "🏆 One win, then I'm done | How long will it take today?"),
        ("🏆 Siegjagd mit Plan | Jede Zone zählt | Komm rein!",
         "🏆 Win hunt with a plan | Every zone counts | Come in!"),
        ranked=True),
    "br-loadout-lab": StreamTitle(
        ("🔬 Loadout-Labor | Test {n} | Welche Kombi holt den SIEG?",
         "🔬 Loadout lab | Test {n} | Which combo gets the WIN?"),
        ("🔬 Zwei Loadouts, ein Gewinner | Tüftel mit!",
         "🔬 Two loadouts, one winner | Tinker with me!"),
        ranked=True),
    "br-squad-comms": StreamTitle(
        ("📢 Squad-{zeit} | Heute holen wir den Sieg zusammen",
         "📢 Squad {time} | We're getting that win together"),
        ("📢 Squad mit Ansagen | Endlich sagt mal jemand was Sinnvolles",
         "📢 Squad with comms | Finally someone makes a useful call")),
    "br-chat-drop": StreamTitle(
        ("😂 Ihr wählt jeden Landeplatz | Das kann ja heiter werden",
         "😂 You pick every drop | This is going to be fun"),
        ("🎯 Chat wählt den Drop | Überlebe ich das? Eher nicht.",
         "🎯 Chat picks the drop | Will I survive? Probably not."),
        mood="funny"),
    "moba-scene-review": StreamTitle(
        ("🔴 Ranked-{zeit} | Tag {n} | Heute wird geklettert",
         "🔴 Ranked {time} | Day {n} | Climbing today"),
        ("⚔️ Weniger feeden, mehr gewinnen | Ranked | Der Plan steht",
         "⚔️ Less feeding, more winning | Ranked | That's the plan"),
        ranked=True),
    "moba-new-character": StreamTitle(
        ("⚔️ Neuer Main, Tag {n} | 90 % Hoffnung, 10 % Skill",
         "⚔️ New main, day {n} | 90% hope, 10% skill"),
        ("🆕 Ich lerne einen neuen Main | Komm rein und lach mit!",
         "🆕 Learning a new main | Come laugh along!")),
    "moba-one-number": StreamTitle(
        ("🌾 Farm-Challenge | {ziel} | Schaffe ich das HEUTE?",
         "🌾 Farm challenge | {ziel} | Can I do it TODAY?"),
        ("🌾 Last-Hit-Grind ohne Gnade | Tag {n} | Zähl mit!",
         "🌾 No-mercy last-hit grind | Day {n} | Count along!"),
        ranked=True),
    "moba-chat-pick": StreamTitle(
        ("😂 Ihr wählt meinen Charakter | Gewinne ich trotzdem?",
         "😂 You pick my character | Can I still win?"),
        ("🎲 Chat-Picks only | Sucht mir was Schlimmes aus",
         "🎲 Chat picks only | Pick me something awful"),
        mood="funny"),
    "moba-duo": StreamTitle(
        ("👥 Duo-{zeit} mit Profi | Trägt er mich heute nach oben?",
         "👥 Duo {time} with a pro | Will they carry me up?"),
        ("👥 Duo-Queue mit Coach | Hör mit, wie ich lerne",
         "👥 Duo queue with a coach | Listen to me learn")),
    "story-first-playthrough": StreamTitle(
        ("📖 Erster Durchgang | Teil {n} | Keine Spoiler!",
         "📖 First playthrough | Part {n} | No spoilers!"),
        ("🗡️ Blind weiter | Teil {n} | Was erwartet uns heute?",
         "🗡️ Going in blind | Part {n} | What's waiting today?"),
        first=("🗡️ Zum ersten Mal {game} | Blind | Keine Spoiler!",
               "🗡️ First time playing {game} | Blind | No spoilers!")),
    "story-attempt-counter": StreamTitle(
        ("💀 Heute fällt der Boss | Ich gebe nicht auf. Vielleicht.",
         "💀 The boss goes down today | Not giving up. Probably."),
        ("💀 Todeszähler läuft | Wie oft sterbe ich HEUTE?",
         "💀 Death counter is running | How often do I die TODAY?"),
        mood="ambitious"),
    "story-recap": StreamTitle(
        ("📖 Neu hier? 5-Minuten-Rückblick | Dann geht's weiter!",
         "📖 New here? 5-minute recap | Then we continue!"),
        ("📖 Story-{zeit} | Teil {n} | Wohin führt uns die Geschichte?",
         "📖 Story {time} | Part {n} | Where does the story take us?")),
    "story-explore": StreamTitle(
        ("🧭 Jede Ecke, jedes Geheimnis | Heute wird nichts übersprungen",
         "🧭 Every corner, every secret | Skipping nothing today"),
        ("🧭 Langsam & gründlich | Entdeck mit mir!",
         "🧭 Slow & thorough | Explore with me!")),
    "story-chat-choices": StreamTitle(
        ("😅 Ihr trefft jede Entscheidung | Wie schlimm endet das?",
         "😅 You make every choice | How badly does this end?"),
        ("🎲 Chat schreibt meine Geschichte | Stimm ab!",
         "🎲 Chat writes my story | Come vote!"),
        mood="funny"),
    "horror-honest-reactions": StreamTitle(
        ("👻 Licht aus, Ton laut | Wie oft schreie ich heute?",
         "👻 Lights off, sound up | How often will I scream?"),
        ("😱 Horror mit Facecam | Komm rein, wenn du dich traust!",
         "😱 Horror on facecam | Come in if you dare!"),
        first=("👻 Zum ersten Mal {game} | Blind | Wie oft schreie ich?",
               "👻 First time {game} | Blind | How often will I scream?")),
    "horror-courage-levels": StreamTitle(
        ("🕯️ Mutprobe | Stufe für Stufe dunkler | Wie weit komme ich?",
         "🕯️ Courage test | Darker every level | How far do I get?"),
        ("😱 Ich bin ein ANGSTHASE | Mutprobe-{zeit} | Halt mir die Hand",
         "😱 I'm a total SCAREDY-CAT | Courage {time} | Hold my hand")),
    "horror-clue-board": StreamTitle(
        ("🕯️ Spurensuche | Teil {n} | Lösen wir heute das Rätsel?",
         "🕯️ Mystery hunt | Part {n} | Do we crack it today?"),
        ("🔎 Gruseliges Rätsel | Ermittle mit!",
         "🔎 Creepy mystery | Investigate with me!"),
        first=("🕯️ Zum ersten Mal {game} | Blind | Was steckt dahinter?",
               "🕯️ First time {game} | Blind | What's behind it all?"),
        mood="chill"),
    "horror-coop-night": StreamTitle(
        ("👻 Koop-Horror mit Freunden | Wer schreit zuerst?",
         "👻 Co-op horror with friends | Who screams first?"),
        ("😂 Horror-Squad am Start | Wir sterben alle. Gemeinsam.",
         "😂 Horror squad assembled | We all die. Together.")),
    "horror-chat-guess": StreamTitle(
        ("😱 Schreck-Wetten | Wer ahnt den nächsten Jumpscare?",
         "😱 Scare bets | Who calls the next jumpscare?"),
        ("🎲 Tipp mit, wann's knallt | Komm rein, wenn du dich traust!",
         "🎲 Guess when it hits | Come in if you dare!")),
    "cozy-three-goals": StreamTitle(
        ("🌱 Drei kleine Ziele | Woche {n} | Schaffen wir alle?",
         "🌱 Three small goals | Week {n} | Can we do them all?"),
        ("☕ Gemütlich Ziele abhaken | Kaffee & Quatschen",
         "☕ Cosy goal-checking | Coffee & chatting")),
    "cozy-before-after": StreamTitle(
        ("🏡 Großer Umbau | Wie schön wird's bis Stream-Ende?",
         "🏡 Big makeover | How pretty will it be by the end?"),
        ("🏡 Vorher: trostlos. Nachher: ? | Gib mir Tipps!",
         "🏡 Before: bleak. After: ? | Give me tips!")),
    "cozy-starter-tips": StreamTitle(
        ("🌱 Neu in {game}? | Gemütlich starten mit Tipps",
         "🌱 New to {game}? | A cosy start with tips"),
        ("☕ Frisch angefangen? | Wir starten zusammen!",
         "☕ Just started? | Let's start together!")),
    "cozy-one-rule": StreamTitle(
        ("😄 Alles mit {regel} | Bleibt's trotzdem gemütlich?",
         "😄 Everything in {regel} | Still cosy?"),
        ("🎨 Gemütlich, aber mit Regel | Was kann da schon schiefgehen?",
         "🎨 Cosy, with a rule | What could possibly go wrong?"),
        mood="funny"),
    "cozy-chat-names": StreamTitle(
        ("🏷️ Ihr gebt die Namen | Wie heißt unser neues Zuhause?",
         "🏷️ You name it | What's our new home called?"),
        ("🏷️ Namens-{zeit} | Tauf mit!",
         "🏷️ Naming {time} | Help name everything!")),
    "sandbox-three-solutions": StreamTitle(
        ("⛏️ Drei Wege, ein Problem | Welcher Bau gewinnt?",
         "⛏️ Three ways, one problem | Which build wins?"),
        ("🔧 Bau-Labor geöffnet | Tüftel mit!",
         "🔧 Build lab is open | Tinker with me!")),
    "sandbox-fix-it": StreamTitle(
        ("🔧 Warum läuft mein Bau nicht?! | Heute wird's gelöst",
         "🔧 Why won't my build work?! | Fixing it today"),
        ("🔧 Fehlersuche live | Hilf mir, bevor ich alles abreiße",
         "🔧 Live troubleshooting | Help me before I tear it all down")),
    "sandbox-big-project": StreamTitle(
        ("🏰 Großprojekt | Tag {n} | Wie weit kommen wir heute?",
         "🏰 Mega build | Day {n} | How far do we get today?"),
        ("🏰 Wir bauen was GROSSES | Tag {n} | Schau zu!",
         "🏰 Building something BIG | Day {n} | Come watch!")),
    "sandbox-survival-start": StreamTitle(
        ("⛏️ Neue Welt | Tag {n} | Überleben wir die Nacht?",
         "⛏️ New world | Day {n} | Do we survive the night?"),
        ("🔥 Survival von null | Tag {n} | Überleb mit!",
         "🔥 Survival from scratch | Day {n} | Survive with me!")),
    "sandbox-chat-build": StreamTitle(
        ("😂 {game}, aber der Chat baut | Das kann nur schiefgehen",
         "😂 {game}, but chat builds | What could go wrong"),
        ("🏗️ Ihr plant, ich baue | Was kommt dabei raus?",
         "🏗️ You plan, I build | What will we end up with?"),
        mood="funny"),
    "sports-one-technique": StreamTitle(
        ("⚽ Trick-Training | Tag {n} | Sitzt der Move HEUTE?",
         "⚽ Skill training | Day {n} | Does the move land TODAY?"),
        ("💪 Training statt Ausreden | Tag {n} | Komm rein!",
         "💪 Practice, not excuses | Day {n} | Come in!")),
    "sports-personal-best": StreamTitle(
        ("🏁 Jagd auf meine Bestmarke | Heute fällt sie. Oder?",
         "🏁 Chasing my personal best | It falls today. Right?"),
        ("🏁 Neue Bestmarke gesucht | Drück mir die Daumen!",
         "🏁 New personal best wanted | Cross your fingers!")),
    "sports-match-review": StreamTitle(
        ("🔴 Ranked-{zeit} | Tag {n} | Wie viele Siege holen wir?",
         "🔴 Ranked {time} | Day {n} | How many wins today?"),
        ("🏆 Heute ohne Controller-Wurf | Ranked | Versprochen.",
         "🏆 No controller throwing today | Ranked | Promise."),
        ranked=True),
    "sports-career": StreamTitle(
        ("🏆 Karriere-Modus | Folge {n} | Was passiert heute?",
         "🏆 Career mode | Episode {n} | What happens today?"),
        ("📺 Die Saison läuft | Folge {n} | Fiebere mit!",
         "📺 The season's on | Episode {n} | Cheer along!")),
    "sports-chat-tactic": StreamTitle(
        ("😂 Ihr bestimmt die Taktik | Geht das gut? Nein.",
         "😂 You call the tactics | Will this work? No."),
        ("📋 Chat ist Trainer | Gib die Ansage!",
         "📋 Chat is the coach | Call the shots!"),
        mood="funny"),
    "jc-three-points": StreamTitle(
        ("☕ Drei Dinge über {thema} | Rate mal, was kommt!",
         "☕ Three things about {thema} | Guess what's coming!"),
        ("💬 Kaffee & {thema} | Komm rein und quatsch mit!",
         "💬 Coffee & {thema} | Come chat with me!")),
    "jc-live-project": StreamTitle(
        ("🛠️ Live-Projekt | Teil {n} | Werde ich heute fertig?",
         "🛠️ Live project | Part {n} | Will I finish today?"),
        ("🛠️ Basteln & Quatschen | Teil {n} | Schau zu!",
         "🛠️ Crafting & chatting | Part {n} | Come hang out!")),
    "jc-week-recap": StreamTitle(
        ("☕ Was für eine Woche | Und wie war deine?",
         "☕ What a week | How was yours?"),
        ("💬 Wochenrückblick | Erzähl mir von deiner Woche!",
         "💬 Week in review | Tell me about your week!")),
    "jc-learn-live": StreamTitle(
        ("📚 Ich lerne {skill} | Tag {n} | Wie PEINLICH wird's heute?",
         "📚 Learning {skill} | Day {n} | How EMBARRASSING will it get?"),
        ("📚 Live lernen von null | Tag {n} | Lach mit!",
         "📚 Learning live from zero | Day {n} | Laugh along!")),
    "jc-qna": StreamTitle(
        ("❓ Frag mich ALLES | Ich antworte ehrlich",
         "❓ Ask me ANYTHING | Honest answers only"),
        ("☕ Kaffee, Quatschen & eure Fragen | Komm rein!",
         "☕ Coffee, chats & your questions | Come in!")),
    "jc-topic-vote": StreamTitle(
        ("🗳️ Ihr wählt das Thema | Worüber reden wir heute?",
         "🗳️ You pick the topic | What are we talking about?"),
        ("😂 Chat bestimmt das Thema | Ich bereue es jetzt schon",
         "😂 Chat picks the topic | I already regret this"),
        mood="funny"),
    "general-first-impressions": StreamTitle(
        ("🎮 Erste Stunde in {game} | Lohnt sich das?",
         "🎮 First hour of {game} | Is it worth it?"),
        ("🎮 Neues Spiel, null Ahnung | Schaut rein!",
         "🎮 New game, no clue | Come watch!"),
        first=("🎮 Zum ersten Mal {game} | Blind | Lohnt sich das?",
               "🎮 First time playing {game} | Blind | Worth it?")),
    "general-skill-diary": StreamTitle(
        ("📈 Trainingstag {n} | Schaffe ich heute mein Ziel?",
         "📈 Practice day {n} | Do I hit my goal today?"),
        ("📈 Jeden Tag ein bisschen besser | Tag {n}",
         "📈 A bit better every day | Day {n}")),
    "general-two-ways": StreamTitle(
        ("🔀 Zwei Wege, ein Ziel | Welcher ist schneller?",
         "🔀 Two routes, one goal | Which is faster?"),
        ("🔀 Ich teste beide Wege | Tipp mit!",
         "🔀 Testing both ways | Place your bet!")),
    "general-moment-of-week": StreamTitle(
        ("⭐ Die besten Momente der Woche | Welcher war deiner?",
         "⭐ Best moments of the week | Which was yours?"),
        ("⭐ Highlight-{zeit} | Stimm für den besten Moment!",
         "⭐ Highlight {time} | Vote for the best moment!")),
    "general-audience-choice": StreamTitle(
        ("🗳️ Ihr entscheidet, wie's weitergeht | Wohin heute?",
         "🗳️ You decide what's next | Where to today?"),
        ("😂 Chat am Steuer | Was soll da schon passieren?",
         "😂 Chat's in control | What could possibly happen?"),
        mood="funny"),
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
    """Ein Titel mit seinen Bausteinen (für Tests und Begründungen)."""

    text: str               # ohne Befehle
    approach: Approach
    commands: str = ""      # angehängte Befehle oder leer

    @property
    def full(self) -> str:
        return f"{self.text}{SEPARATOR}{self.commands}" if self.commands else self.text

    @property
    def blocks(self) -> list[str]:
        return self.text.split(SEPARATOR)

    @property
    def emoji(self) -> str:
        return self.text.split(" ", 1)[0]

    @property
    def opening(self) -> str:
        """Der erste Baustein ohne Emoji – daran unterscheiden sich die drei Titel."""
        return self.blocks[0].split(" ", 1)[1] if " " in self.blocks[0] else self.blocks[0]


def is_emoji(token: str) -> bool:
    return bool(token) and all(
        unicodedata.category(ch) in ("So", "Sk", "Mn", "Cf") or ch == "️" for ch in token)


def daypart(minute_of_day: int) -> tuple[str, str, str]:
    hour = minute_of_day // 60 % 24
    for limit, noun, noun_m, english in DAYPARTS:
        if hour < limit:
            return noun, noun_m, english
    return DAYPARTS[-1][1:]  # pragma: no cover


def stream_mood(format_id: str, genre: str | None, requested: Mood | None) -> Mood:
    if requested:
        return requested
    return STREAM_TITLES[format_id].mood or GENRE_MOOD.get(genre, "chill")


def check_commands(commands: list[str]) -> list[str]:
    """Eigene Chat-Befehle prüfen: höchstens 3, jeder wie ``!discord``."""
    if len(commands) > MAX_COMMANDS:
        raise ValueError(f"Höchstens {MAX_COMMANDS} Befehle / at most {MAX_COMMANDS} commands")
    for command in commands:
        if not COMMAND_RE.match(command):
            raise ValueError(f"Ungültiger Befehl / invalid command: {command!r} "
                             "(Form: !name, Kleinbuchstaben, Ziffern, _)")
    return list(dict.fromkeys(commands))


def build_titles(format_id: str, genre: str | None, game: str, language: str, *,
                 counter: int = 1, start_minute: int = 18 * 60, mood: Mood | None = None,
                 rank_goal: str | None = None, current_rank: str | None = None,
                 rank_counter: int = 1, first_time: bool = False, rotation: int | None = None,
                 commands: list[str] | None = None) -> list[TitleOption]:
    """Drei Titel für den ganzen Stream (Ziel, Stimmung, Einladung); der erste ist der Haupttitel.

    ``counter`` zählt Folgen dieses Formats über die Wochen („Tag {n}“); ``rank_counter`` die
    Ranked-Streams mit Rang-Ziel. ``rotation`` wählt, welcher Ansatz Haupttitel ist (Standard:
    nach ``counter``). ``commands`` werden angehängt, solange der Titel ≤ 140 Zeichen bleibt.
    """
    index = 0 if language == "de" else 1
    data = STREAM_TITLES[format_id]
    current = stream_mood(format_id, genre, mood)
    zeit, zeit_m, time = daypart(start_minute % 1440)
    fills = {key: value[index] for key, value in FILLS.get(format_id, {}).items()}
    values = {"game": game, "zeit": zeit, "zeit_m": zeit_m, "time": time, "n": counter,
              "k": rank_counter, "rank": rank_goal or "", "from": current_rank or "", **fills}

    ranked = data.ranked and genre in RANKED_GENRES
    if ranked and rank_goal:
        goal = (RANK_JOURNEY if current_rank else RANK_GOAL)[index]
    elif first_time and data.first:
        goal = data.first[index]
    else:
        goal = data.goal[index]
    genre_mood = MOOD_TITLES.get(genre, MOOD_TITLES[None])[current][index]
    mood_text = genre_mood
    if ranked and current == "ambitious":
        mood_text = (RANKED_GOAL_MOOD if rank_goal else RANKED_MOOD)[index]
        # Beginnt das Ziel schon mit demselben Baustein („🔴 Ranked-Abend“), nimm den
        # Stimmungs-Titel des Genres – die drei Titel sollen sich im Anfang unterscheiden.
        if mood_text.format(**values).split(SEPARATOR)[0] == goal.format(**values).split(
                SEPARATOR)[0]:
            mood_text = genre_mood

    suffix = " ".join(check_commands(commands or []))
    options = []
    for approach, template in (("goal", goal), ("mood", mood_text), ("invite", data.invite[index])):
        text = template.format(**values)
        fits = suffix and len(text) + len(SEPARATOR) + len(suffix) <= TITLE_MAX_CHARS
        options.append(TitleOption(text, approach, suffix if fits else ""))
    start = (counter - 1 if rotation is None else rotation) % len(options)
    return options[start:] + options[:start]


def clip_titles(format_id: str, language: str) -> list[str]:
    index = 0 if language == "de" else 1
    return [pair[index] for pair in CLIP_TITLES[format_id]]
