"""Stream-Titel: drei Varianten pro Format, damit Leute auf den Stream klicken.

Regeln (auch in agents/docs/content-strategist.md; Regeln 1, 3, 5 und 7 prüft ein Test):
1. Kein Spielname am Anfang – Twitch zeigt die Kategorie ohnehin an. Den Spielnamen nur, wenn
   er Teil des Hooks ist.
2. Der Hook steht in den ersten ~40 Zeichen (Übersichten schneiden oft ab): eine konkrete Frage,
   ein Einsatz, eine Herausforderung oder eine Mitmach-Einladung.
3. Keine Meta-Wörter, die nur das Format beschreiben („Analyse am Ende“, „Gesprächsrunde“,
   „Vergleich“, „Heute übe ich“).
4. Fortschritt nutzen: Serien und wiederkehrende Formate bekommen Zähler („Tag {n}“, „Teil {n}“),
   damit der Titel nicht jede Woche gleich ist.
5. Ehrlich: nur versprechen, was das Format liefert. Keine erfundenen Rekorde, kein
   „UNMÖGLICH“, kein „gleich passiert etwas“, keine Großbuchstaben-Wörter außer Abkürzungen,
   höchstens ein Ausrufezeichen, keine Emojis.
6. Duzen, kurz, gesprochene Sprache. Deutsch und Englisch jeweils eigenständig formuliert.
7. Höchstens 140 Zeichen (Twitch, hart), Ziel höchstens ~70 Zeichen.

Arten: ``question`` (Frage/Neugier), ``challenge`` (Einsatz/Herausforderung), ``join``
(Mitmachen – nur bei Formaten mit Chat). Platzhalter: ``{game}``, ``{n}`` (wie oft das Format in
dieser Woche schon dran war, ab 1) und feste Standardwerte aus ``FILLS``.
"""
from typing import Literal

TitleKind = Literal["question", "challenge", "join"]
Variant = tuple[TitleKind, str, str]  # (Art, Deutsch, Englisch)

TITLE_TARGET_CHARS = 70

FILLS: dict[str, dict[str, tuple[str, str]]] = {
    "shooter-chat-rule": {"regel": ("nur einer Waffe", "one weapon only")},
    "moba-one-number": {"ziel": ("70 Farm nach 10 Minuten", "70 CS at 10 minutes")},
    "cozy-one-rule": {"regel": ("nur einer Farbe", "one colour only")},
    "jc-three-points": {"thema": ("mein Hobby", "my hobby")},
    "jc-learn-live": {"skill": ("etwas Neues", "something new")},
}

TITLES: dict[str, tuple[Variant, ...]] = {
    # ---------------------------------------------------------------- Shooter
    "shooter-decision-review": (
        ("question", "Hätte ich diese Runde retten können?", "Could I have saved that round?"),
        ("challenge", "Jede verlorene Runde wird auseinandergenommen",
         "Every round I lose gets taken apart"),
        ("question", "Welcher Fehler kostet mich die meisten Runden?",
         "Which mistake costs me the most rounds?"),
    ),
    "shooter-micro-skill": (
        ("challenge", "Fadenkreuz-Training, Tag {n}: Sitzt es heute?",
         "Crosshair grind, day {n} – does it stick today?"),
        ("question", "Warum verliere ich an dieser Ecke immer?", "Why do I always lose this corner?"),
        ("challenge", "Einer schlechten Angewohnheit an den Kragen – Tag {n}",
         "Fixing one bad habit before the stream ends – day {n}"),
    ),
    "shooter-role-swap": (
        ("challenge", "Ich spiele die Rolle, die ich sonst meide", "Playing the role I always dodge"),
        ("question", "Wie schlecht bin ich abseits meiner Main-Rolle?", "How bad am I off my main role?"),
        ("challenge", "Neue Rolle, null Ausreden", "New role, zero excuses"),
    ),
    "shooter-chat-rule": (
        ("join", "Du wählst die Regel, ich muss damit gewinnen",
         "You pick the rule, I have to win with it"),
        ("challenge", "Jedes Match mit {regel} – reicht das zum Sieg?",
         "Every match with {regel} – can I still win?"),
        ("question", "Wie lange halte ich mit {regel} durch?", "How long can I last with {regel}?"),
    ),
    "shooter-coach": (
        ("question", "Ein Coach sieht meine schlechteste Runde – wie schlimm ist es?",
         "A coach watches my worst round – how bad is it?"),
        ("challenge", "Ein Tipp pro Runde: Werde ich besser?", "One coaching tip per round – does it help?"),
        ("challenge", "Coach im Ohr: Drehen wir das noch?", "Coach on comms – can we turn this around?"),
    ),
    # ---------------------------------------------------------------- Battle Royale
    "br-drop-study": (
        ("question", "Wo lande ich am besten? Zwei Orte, fünf Versuche",
         "Where should I drop? Two spots, five tries"),
        ("challenge", "Zwei Landeplätze, nur einer bleibt", "Two drop spots, only one stays"),
        ("question", "Heißer Landeplatz oder ruhige Ecke?", "Hot drop or quiet corner?"),
    ),
    "br-rotation": (
        ("question", "Rotieren oder bleiben? Jede Entscheidung erklärt",
         "Rotate or hold? Every call explained"),
        ("challenge", "Keine Glücks-Rotationen: jeder Weg mit Plan",
         "No lucky rotations – every move has a plan"),
        ("question", "Warum sterbe ich immer in der Zone?", "Why do I keep dying to the zone?"),
    ),
    "br-loadout-lab": (
        ("question", "Welche Ausrüstung bringt mich weiter? Test {n}",
         "Which loadout actually helps me? Test {n}"),
        ("challenge", "Ausrüstungs-Labor, Runde {n}: Notizen statt Bauchgefühl",
         "Loadout lab, round {n} – notes beat gut feeling"),
        ("question", "Bauchgefühl oder Zahlen – welche Ausrüstung gewinnt?",
         "Gut feeling or numbers – which loadout wins?"),
    ),
    "br-squad-comms": (
        ("question", "Spielen wir mit klaren Ansagen besser?", "Do clean callouts make us better?"),
        ("challenge", "Neue Regel im Squad: nur noch klare Ansagen", "New squad rule: clean callouts only"),
        ("challenge", "Unser Squad gegen das eigene Chaos", "Our squad versus our own chaos"),
    ),
    "br-chat-drop": (
        ("join", "Du wählst meinen Landeplatz", "You pick where I drop"),
        ("challenge", "Landeplatz vom Chat – keine Ausreden", "Chat picks the drop, no rerolls"),
        ("question", "Überlebe ich da, wo der Chat mich hinschickt?",
         "Can I survive wherever chat sends me?"),
    ),
    # ---------------------------------------------------------------- MOBA
    "moba-scene-review": (
        ("question", "Wo habe ich dieses Match verloren?", "Where did I actually lose that game?"),
        ("challenge", "Jede Niederlage bekommt eine Erklärung", "Every loss gets an explanation"),
        ("question", "Der eine Fehler, der mich jedes Match kostet",
         "The one mistake that costs me every game"),
    ),
    "moba-new-character": (
        ("challenge", "Neuer Charakter von null – Tag {n}", "New pick from zero – day {n}"),
        ("question", "Wie lange, bis der neue Charakter sitzt? Tag {n}",
         "How long until my new pick clicks? Day {n}"),
        ("challenge", "Ein Charakter, den ich nie gespielt habe", "Learning a character I've never touched"),
    ),
    "moba-one-number": (
        ("question", "Schaffe ich heute {ziel}?", "Can I hit {ziel} today?"),
        ("challenge", "Nur eine Zahl zählt: {ziel}", "Only one number counts: {ziel}"),
        ("question", "Neuer Bestwert beim Farmen oder wieder nicht?", "New farming best, or not again?"),
    ),
    "moba-chat-pick": (
        ("join", "Du wählst meinen Charakter", "You pick my character"),
        ("challenge", "Chat-Pick jedes Match – auch die, die ich nie spiele",
         "Chat picks every game, even ones I never play"),
        ("question", "Gewinne ich mit jedem Charakter, den du aussuchst?", "Can I win with whatever you pick?"),
    ),
    "moba-duo": (
        ("question", "Was sieht mein Duo, das ich übersehe?", "What does my duo see that I miss?"),
        ("challenge", "Duo mit Coach: ein Tipp pro Match", "Duo with a coach, one tip per game"),
        ("question", "Zieht mich mein Duo nach oben?", "Can my duo pull me up?"),
    ),
    # ---------------------------------------------------------------- Story/Singleplayer
    "story-first-playthrough": (
        ("question", "Erster Durchgang, Etappe {n}: Was erwartet mich?",
         "First playthrough, part {n} – what's waiting for me?"),
        ("challenge", "Blind gespielt, Etappe {n} – bitte keine Spoiler", "Going in blind, part {n} – no spoilers"),
        ("question", "Meine ehrliche erste Reaktion – Etappe {n}", "Honest first reactions, part {n}"),
    ),
    "story-attempt-counter": (
        ("question", "Wie viele Versuche brauche ich für diesen Abschnitt?",
         "How many tries will this section take me?"),
        ("challenge", "Versuch für Versuch bis zum Durchbruch", "Attempt after attempt until it clicks"),
        ("question", "Versuch 1 – wie viele werden es heute?", "Attempt 1 – how many will it take?"),
    ),
    "story-recap": (
        ("question", "Was ist bisher passiert? Die Geschichte in 5 Minuten",
         "What happened so far? The story in 5 minutes"),
        ("challenge", "Neu dabei? In 5 Minuten bist du im Bilde", "New here? Catch up in 5 minutes"),
        ("question", "Meine Theorie zur Geschichte – liege ich richtig?", "My theory about the story – am I right?"),
    ),
    "story-explore": (
        ("question", "Was übersieht man hier beim ersten Mal?", "What does everyone miss here the first time?"),
        ("challenge", "Kein Hetzen: Heute wird jede Ecke erkundet", "No rushing – every corner today"),
        ("question", "Drei Entdeckungen, die du vielleicht verpasst hast",
         "Three things you probably walked past"),
    ),
    "story-chat-choices": (
        ("join", "Du triffst die Entscheidungen in meiner Geschichte",
         "You make the choices in my playthrough"),
        ("question", "Wohin führt uns die Wahl des Chats?", "Where will chat's choices take us?"),
        ("challenge", "Jede Entscheidung per Abstimmung – ohne Ausnahme", "Every choice goes to a vote, no exceptions"),
    ),
    # ---------------------------------------------------------------- Horror
    "horror-honest-reactions": (
        ("question", "Wie lange halte ich ohne Schrei durch?", "How long until the first scream?"),
        ("challenge", "Erster Durchgang, Facecam an, keine Ausreden", "First time, facecam on, no excuses"),
        ("question", "Bin ich zu schreckhaft für dieses Spiel?", "Am I too jumpy for this one?"),
    ),
    "horror-courage-levels": (
        ("challenge", "Mutprobe Stufe 3: Licht aus, Ton lauter", "Level 3: lights off, volume up"),
        ("question", "Bis zu welcher Stufe halte ich durch?", "How far up the courage ladder can I go?"),
        ("challenge", "Drei Stufen Mut – jede ein Stück härter", "Three courage levels, each one worse"),
    ),
    "horror-clue-board": (
        ("question", "Was ist hier wirklich passiert? Teil {n}", "What really happened here? Part {n}"),
        ("challenge", "Hinweis für Hinweis zur Wahrheit – Teil {n}", "Clue by clue to the truth, part {n}"),
        ("question", "Wer steckt dahinter? Spur Nummer {n}", "Who's behind it? Following lead {n}"),
    ),
    "horror-coop-night": (
        ("question", "Wer von uns bleibt am längsten ruhig?", "Which of us keeps it together longest?"),
        ("challenge", "Koop-Nacht: Wir bleiben zusammen, versprochen", "Co-op night – we stick together, we promised"),
        ("challenge", "Wir, die Dunkelheit und kein Plan", "Us, the dark, and no plan"),
    ),
    "horror-chat-guess": (
        ("join", "Tipp ab, wann der nächste Schreck kommt", "Guess when the next scare hits"),
        ("question", "Sieht der Chat den Schreck vor mir kommen?", "Can chat see the scare coming before I do?"),
        ("challenge", "Chat gegen mich: Wer ahnt den Schreck zuerst?", "Chat vs me – who calls the scare first?"),
    ),
    # ---------------------------------------------------------------- Cozy/Simulation
    "cozy-three-goals": (
        ("challenge", "Drei kleine Ziele, Woche {n} – schaffe ich alle?",
         "Three small goals, week {n} – can I tick them all?"),
        ("question", "Wie viel schaffe ich heute? Drei Ziele, ganz entspannt",
         "How much can I get done? Three cosy goals"),
        ("challenge", "Gemütlich, aber mit Plan – Woche {n}", "Cosy, but with a plan – week {n}"),
    ),
    "cozy-before-after": (
        ("question", "Wie schön kann ich diesen leeren Ort machen?", "How nice can I make this empty spot?"),
        ("challenge", "Von leer zu gemütlich in einem Stream", "From empty to cosy in one stream"),
        ("question", "Vorher trostlos – und nachher?", "Bleak before – and after?"),
    ),
    "cozy-starter-tips": (
        ("question", "Was hätte ich am Anfang gern gewusst?", "Things I wish someone told me on day one"),
        ("challenge", "Drei Anfänger-Fehler, die du dir sparen kannst", "Three beginner mistakes you can skip"),
        ("question", "Neu im Spiel? Diese drei Dinge helfen sofort", "Just started? These three things help right away"),
    ),
    "cozy-one-rule": (
        ("question", "Geht gemütlich auch mit {regel}?", "Can it still be cosy with {regel}?"),
        ("challenge", "Den ganzen Stream mit {regel}", "A whole stream with {regel}"),
        ("question", "Wie weit komme ich mit {regel}?", "How far can I get with {regel}?"),
    ),
    "cozy-chat-names": (
        ("join", "Du gibst die Namen, ich baue", "You name it, I build it"),
        ("challenge", "Alles bekommt heute einen Namen aus dem Chat", "Everything gets a name from chat today"),
        ("question", "Wie soll unser neuer Ort heißen?", "What should we call our new place?"),
    ),
    # ---------------------------------------------------------------- Sandbox/Survival
    "sandbox-three-solutions": (
        ("question", "Welche Lösung ist die einfachste? Drei Versuche", "Which build is the simplest? Three tries"),
        ("challenge", "Eine Aufgabe, drei Wege – nur einer bleibt", "One problem, three builds, one survives"),
        ("question", "Geht das auch einfacher?", "Is there a simpler way?"),
    ),
    "sandbox-fix-it": (
        ("question", "Warum funktioniert mein Bau nicht?", "Why won't my build work?"),
        ("challenge", "Mein Bau ist kaputt – wir suchen den Fehler", "My build is broken – let's find out why"),
        ("question", "Was übersehe ich hier?", "What am I missing here?"),
    ),
    "sandbox-big-project": (
        ("challenge", "Großprojekt, Etappe {n}: Heute wächst es", "Big build, stage {n} – today it grows"),
        ("question", "Wie weit kommen wir heute? Etappe {n}", "How far do we get today? Stage {n}"),
        ("challenge", "Aus leerem Gelände wird ein Dorf – Etappe {n}", "Empty land to village, stage {n}"),
    ),
    "sandbox-survival-start": (
        ("question", "Neue Welt, Tag {n}: Schaffe ich das Tagesziel?", "New world, day {n} – can I hit today's goal?"),
        ("challenge", "Tag {n} in der neuen Welt – ein Ziel, keine Abkürzung",
         "Day {n} in a fresh world – one goal, no shortcuts"),
        ("question", "Überlebe ich Tag {n}?", "Do I make it through day {n}?"),
    ),
    "sandbox-chat-build": (
        ("join", "Du schlägst vor, ich baue", "You suggest it, I build it"),
        ("challenge", "Der Chat entscheidet, was hier entsteht", "Chat decides what gets built here"),
        ("question", "Was soll hier als Nächstes stehen?", "What should go here next?"),
    ),
    # ---------------------------------------------------------------- Sport/Rennspiele
    "sports-one-technique": (
        ("challenge", "Eine Technik, Tag {n}: Sitzt sie schon?", "One technique, day {n} – does it click yet?"),
        ("question", "Warum klappt dieser eine Move bei mir nie?", "Why can't I land this one move?"),
        ("challenge", "Training, bis es sitzt – Tag {n}", "Grinding one move until it clicks – day {n}"),
    ),
    "sports-personal-best": (
        ("question", "Knacke ich heute meine Bestmarke?", "Can I beat my personal best today?"),
        ("challenge", "Jagd auf meine eigene Bestmarke", "Chasing my own PB"),
        ("question", "Wie nah komme ich an meine Bestmarke?", "How close can I get to my best?"),
    ),
    "sports-match-review": (
        ("question", "Wo habe ich dieses Spiel verloren?", "Where did I lose that one?"),
        ("challenge", "Jede Niederlage wird zerlegt", "Every loss gets broken down"),
        ("question", "Der eine Fehler, der mich Spiele kostet", "The one mistake that keeps costing me games"),
    ),
    "sports-career": (
        ("question", "Meine Saison, Folge {n}: Wie weit komme ich?", "My season, episode {n} – how far can I go?"),
        ("challenge", "Saison-Serie, Folge {n}: Jedes Spiel zählt", "Season run, episode {n} – every game counts"),
        ("question", "Folge {n}: Hält mein Plan?", "Episode {n} – does my plan hold up?"),
    ),
    "sports-chat-tactic": (
        ("join", "Du wählst, wie ich spiele", "You pick how I play"),
        ("challenge", "Chat-Taktik jedes Spiel – auch die verrückten", "Chat's call every game, even the wild ones"),
        ("question", "Gewinne ich mit der Spielweise, die du aussuchst?", "Can I win with the playstyle you pick?"),
    ),
    # ---------------------------------------------------------------- Just Chatting
    "jc-three-points": (
        ("question", "Was hat mir {thema} beigebracht?", "What {thema} taught me"),
        ("challenge", "Drei Dinge über {thema}, die ich spät gelernt habe",
         "Three things about {thema} I learned the hard way"),
        ("question", "Lohnt sich {thema}? Meine ehrliche Meinung", "Is {thema} worth it? My honest take"),
    ),
    "jc-live-project": (
        ("challenge", "Von leer zu fertig in einem Stream – Teil {n}", "Blank to finished, part {n}"),
        ("question", "Werde ich heute fertig? Projekt, Teil {n}", "Will I finish today? Project part {n}"),
        ("challenge", "Ärmel hoch: Projekt, Teil {n}", "Sleeves up: project part {n}"),
    ),
    "jc-week-recap": (
        ("question", "Was war diese Woche los?", "So, how was this week?"),
        ("challenge", "Meine Woche in drei Momenten", "My week in three moments"),
        ("question", "Was kommt nächste Woche? Der Plan", "What's coming next week? The plan"),
    ),
    "jc-learn-live": (
        ("challenge", "Ich lerne {skill} von null – Tag {n}", "Learning {skill} from zero – day {n}"),
        ("question", "Schaffe ich das bis Stream-Ende? Tag {n}", "Can I get it by the end of stream? Day {n}"),
        ("question", "Wie schlecht bin ich am Anfang wirklich?", "How bad am I at the start, honestly?"),
    ),
    "jc-qna": (
        ("join", "Frag mich, was du willst – ich antworte ehrlich", "Ask me anything, honest answers"),
        ("question", "Welche Frage hat mir noch nie jemand gestellt?", "What has nobody ever asked me?"),
        ("challenge", "Fragen sammeln, ehrlich antworten", "Collecting questions, answering honestly"),
    ),
    "jc-topic-vote": (
        ("join", "Du wählst das Thema, ich rede", "You pick the topic, I talk"),
        ("question", "Welches Thema gewinnt heute?", "Which topic wins today?"),
        ("challenge", "Drei Themen, eine Abstimmung, offene Runde", "Three topics, one vote, open floor"),
    ),
    # ---------------------------------------------------------------- Allgemein
    "general-first-impressions": (
        ("question", "Lohnt sich {game} für mich? Meine erste Stunde", "Is {game} worth it for me? My first hour"),
        ("challenge", "Erste Stunde, ehrliches Urteil", "First hour, honest verdict"),
        ("question", "Weiterspielen oder aufhören?", "Keep playing or drop it?"),
    ),
    "general-skill-diary": (
        ("challenge", "Lern-Tagebuch, Tag {n}: Schaffe ich mein Ziel?", "Learning diary, day {n} – do I hit my goal?"),
        ("question", "Wie weit komme ich bis Stream-Ende?", "How far can I get by the end of stream?"),
        ("challenge", "Ein Ziel, ein Stream – Tag {n}", "One goal, one stream – day {n}"),
    ),
    "general-two-ways": (
        ("question", "Welcher Weg ist besser?", "Which way works better?"),
        ("challenge", "Zwei Wege zum Ziel – nur einer überzeugt", "Two routes, one winner"),
        ("question", "Schnell oder sicher? Ich probiere beides", "Fast or safe? I'm trying both"),
    ),
    "general-moment-of-week": (
        ("question", "Wie kam es zu diesem Moment?", "How did this moment even happen?"),
        ("challenge", "Mein Moment der Woche – mit Vorgeschichte", "My moment of the week, with the backstory"),
        ("question", "Der Moment, der mir die ganze Woche nachging", "The moment I couldn't stop thinking about"),
    ),
    "general-audience-choice": (
        ("join", "Du entscheidest, wie es weitergeht", "You decide what happens next"),
        ("question", "Welchen Weg wählt der Chat?", "Which way will chat send me?"),
        ("challenge", "Jeder Abschnitt per Abstimmung", "Every section goes to a vote"),
    ),
}


def render_titles(format_id: str, game: str, occurrence: int, language: str) -> list[str]:
    """Alle Varianten eines Formats, beginnend mit dem Haupttitel für dieses Vorkommen.

    ``occurrence`` zählt ab 1, wie oft das Format in dieser Woche schon dran war. Der Haupttitel
    rotiert damit, und Zähler wie „Tag {n}“ laufen mit.
    """
    index = 1 if language == "de" else 2
    fills = {key: value[0 if language == "de" else 1]
             for key, value in FILLS.get(format_id, {}).items()}
    texts = [variant[index].format(game=game, n=occurrence, **fills)
             for variant in TITLES[format_id]]
    start = (occurrence - 1) % len(texts)
    return texts[start:] + texts[:start]
