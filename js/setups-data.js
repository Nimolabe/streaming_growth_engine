// ============================================================
//  Daten für die Setups-Seite
//  Neue Produkte oder Setups einfach hier ergänzen.
//
//  Preise sind Richtpreise in Euro (Stand: Ende 2026) und können abweichen.
//  "score" ist unsere Einschätzung von Qualität/Preis-Leistung (1–10).
// ============================================================

// ---------- Streaming-Kategorien ----------
export const CATEGORIES = {
  gaming:   { label: "Gaming",        icon: "🎮" },
  chatting: { label: "Just Chatting", icon: "💬" },
  irl:      { label: "IRL",           icon: "🌍" },
  music:    { label: "Musik",         icon: "🎵" },
  creative: { label: "Kreativ / Art", icon: "🎨" },
};

// ---------- Bereiche (zum Gruppieren der Bauteile) ----------
export const GROUPS = {
  bild:      { label: "Bild",           icon: "🎥" },
  ton:       { label: "Ton",            icon: "🔊" },
  technik:   { label: "Technik",        icon: "🧠" },
  steuerung: { label: "Steuerung",      icon: "🕹️" },
  software:  { label: "Software",       icon: "🧩" },
  komfort:   { label: "Komfort",        icon: "🛋️" },
  unterwegs: { label: "Unterwegs (IRL)", icon: "🎒" },
};

// ---------- Bauteile eines Setups ----------
// group        = Bereich aus GROUPS
// defaultState = Vorauswahl im Budget-Planer: "need" (brauche ich), "owned" (habe ich schon), "skip" (brauche ich nicht)
//                PC/Konsole und Bildschirm haben die meisten schon, deshalb "owned".
export const TYPES = {
  kamera:      { label: "Kamera",              icon: "📷", group: "bild" },
  licht:       { label: "Licht",               icon: "💡", group: "bild" },
  greenscreen: { label: "Green Screen",        icon: "🟩", group: "bild" },
  mikrofon:    { label: "Mikrofon",            icon: "🎙️", group: "ton" },
  mikrofonarm: { label: "Mikrofonarm",         icon: "🦾", group: "ton" },
  headset:     { label: "Headset / Kopfhörer", icon: "🎧", group: "ton" },
  interface:   { label: "Audio-Interface",     icon: "🎚️", group: "ton" },
  pc:          { label: "PC / Konsole",        icon: "💻", group: "technik", defaultState: "owned" },
  bildschirm:  { label: "Bildschirm",          icon: "🖥️", group: "technik", defaultState: "owned" },
  capture:     { label: "Capture Card",        icon: "📺", group: "technik" },
  maus:        { label: "Maus",                icon: "🖱️", group: "steuerung" },
  tastatur:    { label: "Tastatur",            icon: "⌨️", group: "steuerung" },
  streamdeck:  { label: "Stream Deck",         icon: "🎛️", group: "steuerung" },
  software:    { label: "Streaming-Software",  icon: "💿", group: "software" },
  stuhl:       { label: "Stuhl",               icon: "🪑", group: "komfort" },
  schreibtisch:{ label: "Schreibtisch",        icon: "🗄️", group: "komfort" },
  zubehoer:    { label: "Powerbank & Zubehör", icon: "🔋", group: "unterwegs" },
};

// ---------- Was braucht man pro Kategorie? ----------
// weight   = wie wichtig das Teil für diese Kategorie ist (höher = wichtiger)
// required = Pflicht-Teil: muss im Setup enthalten sein (außer man hat es schon oder braucht es nicht)
export const NEEDS = {
  gaming: [
    { type: "pc", weight: 3, required: true },
    { type: "mikrofon", weight: 3, required: true },
    { type: "headset", weight: 2, required: true },
    { type: "software", weight: 1, required: true },
    { type: "bildschirm", weight: 1.5 },
    { type: "kamera", weight: 2 },
    { type: "licht", weight: 1.5 },
    { type: "maus", weight: 1.2 },
    { type: "tastatur", weight: 1 },
    { type: "mikrofonarm", weight: 0.8 },
    { type: "streamdeck", weight: 0.6 },
    { type: "stuhl", weight: 0.5 },
    { type: "greenscreen", weight: 0.3 },
  ],
  chatting: [
    { type: "pc", weight: 3, required: true },
    { type: "mikrofon", weight: 3, required: true },
    { type: "kamera", weight: 3, required: true },
    { type: "licht", weight: 2.5, required: true },
    { type: "software", weight: 1, required: true },
    { type: "bildschirm", weight: 1 },
    { type: "mikrofonarm", weight: 1 },
    { type: "headset", weight: 1 },
    { type: "streamdeck", weight: 0.6 },
    { type: "greenscreen", weight: 0.5 },
    { type: "stuhl", weight: 0.4 },
  ],
  irl: [
    { type: "kamera", weight: 3, required: true },
    { type: "mikrofon", weight: 3, required: true },
    { type: "zubehoer", weight: 1.5 },
  ],
  music: [
    { type: "pc", weight: 3, required: true },
    { type: "mikrofon", weight: 3, required: true },
    { type: "headset", weight: 2.5, required: true },
    { type: "software", weight: 1, required: true },
    { type: "interface", weight: 2 },
    { type: "kamera", weight: 2 },
    { type: "licht", weight: 1 },
    { type: "mikrofonarm", weight: 1 },
    { type: "bildschirm", weight: 0.8 },
    { type: "stuhl", weight: 0.4 },
  ],
  creative: [
    { type: "pc", weight: 3, required: true },
    { type: "mikrofon", weight: 3, required: true },
    { type: "software", weight: 1, required: true },
    { type: "kamera", weight: 2 },
    { type: "licht", weight: 1.5 },
    { type: "headset", weight: 1.5 },
    { type: "bildschirm", weight: 1.2 },
    { type: "streamdeck", weight: 1 },
    { type: "mikrofonarm", weight: 0.8 },
    { type: "stuhl", weight: 0.6 },
    { type: "schreibtisch", weight: 0.4 },
  ],
};

// ---------- Hardware-Katalog ----------
// cats     = für welche Kategorien das Produkt geeignet ist
// requires = funktioniert nur zusammen mit diesem Typ (z. B. XLR-Mikro → Interface)
// platform = nur bei PC / Konsole: "pc" oder "konsole"
// billing  = nur bei Software: "gratis", "einmalig" oder "abo" (dann ist price der Preis pro Monat)
export const PRODUCTS = [
  // Mikrofone
  { id: "fifine-k669b", type: "mikrofon", name: "Fifine K669B", price: 30, score: 5, cats: ["gaming", "chatting", "creative"], note: "Günstiger USB-Einstieg, klingt deutlich besser als jedes Headset-Mikro." },
  { id: "fifine-am8", type: "mikrofon", name: "Fifine AmpliGame AM8", price: 60, score: 6.5, cats: ["gaming", "chatting", "creative", "music"], note: "USB und XLR: wächst mit, wenn du später ein Interface kaufst." },
  { id: "quadcast-s", type: "mikrofon", name: "HyperX QuadCast S", price: 130, score: 7.5, cats: ["gaming", "chatting", "creative"], note: "Beliebter Allrounder mit Mute-Taste und Shock-Mount." },
  { id: "wave-3", type: "mikrofon", name: "Elgato Wave:3", price: 150, score: 8, cats: ["gaming", "chatting", "creative"], note: "Mit Software-Mixer für Spiel, Musik und Chat." },
  { id: "podmic-usb", type: "mikrofon", name: "Rode PodMic USB", price: 200, score: 8.5, cats: ["gaming", "chatting", "creative", "music"], note: "Broadcast-Klang, USB und XLR, sehr robust." },
  { id: "shure-mv7plus", type: "mikrofon", name: "Shure MV7+", price: 280, score: 9, cats: ["gaming", "chatting", "creative", "music"], note: "Profi-Klang mit guter Hintergrund-Unterdrückung." },
  { id: "shure-sm7b", type: "mikrofon", name: "Shure SM7B", price: 400, score: 9.5, cats: ["music", "chatting"], note: "Studio-Klassiker. Braucht ein Audio-Interface mit viel Gain.", requires: "interface" },
  { id: "dji-mic-mini", type: "mikrofon", name: "DJI Mic Mini", price: 90, score: 7.5, cats: ["irl"], note: "Winziges Funkmikro, perfekt für unterwegs." },
  { id: "rode-wireless-go3", type: "mikrofon", name: "Rode Wireless GO (Gen 3)", price: 230, score: 8.5, cats: ["irl"], note: "Funkmikro mit interner Aufnahme als Backup." },

  // Headsets / Kopfhörer
  { id: "cloud-stinger2", type: "headset", name: "HyperX Cloud Stinger 2", price: 45, score: 5.5, cats: ["gaming", "chatting", "creative"], note: "Leicht und günstig, solide für den Start." },
  { id: "cloud-iii", type: "headset", name: "HyperX Cloud III", price: 100, score: 7.5, cats: ["gaming", "chatting", "creative"], note: "Sehr bequem für lange Streams." },
  { id: "dt770-pro", type: "headset", name: "Beyerdynamic DT 770 Pro", price: 140, score: 8.5, cats: ["music", "gaming", "creative"], note: "Geschlossener Studio-Kopfhörer, top für Musik und Spiele." },
  { id: "arctis-nova7", type: "headset", name: "SteelSeries Arctis Nova 7", price: 180, score: 8.5, cats: ["gaming", "chatting"], note: "Kabellos mit langer Akkulaufzeit." },

  // Kameras
  { id: "c920", type: "kamera", name: "Logitech C920", price: 60, score: 5.5, cats: ["gaming", "chatting", "creative", "music"], note: "Der Webcam-Klassiker. Mit gutem Licht völlig ausreichend." },
  { id: "elgato-facecam", type: "kamera", name: "Elgato Facecam", price: 130, score: 7, cats: ["gaming", "chatting", "creative", "music"], note: "Scharfes 1080p60-Bild, viele Einstellungen." },
  { id: "mx-brio", type: "kamera", name: "Logitech MX Brio", price: 200, score: 8, cats: ["gaming", "chatting", "creative", "music"], note: "4K-Webcam mit gutem Bild auch bei wenig Licht." },
  { id: "sony-zv-e10", type: "kamera", name: "Sony ZV-E10 (mit Objektiv)", price: 650, score: 9.5, cats: ["chatting", "creative", "music"], note: "Echte Systemkamera mit unscharfem Hintergrund. Braucht Netzteil-Adapter und ggf. Capture." },
  { id: "osmo-mobile", type: "kamera", name: "DJI Osmo Mobile 6 (Handy-Gimbal)", price: 130, score: 6, cats: ["irl"], note: "Macht dein Smartphone zur stabilen IRL-Kamera." },
  { id: "gopro-13", type: "kamera", name: "GoPro HERO13", price: 400, score: 8, cats: ["irl"], note: "Robust und wasserdicht, ideal für Action." },
  { id: "osmo-pocket3", type: "kamera", name: "DJI Osmo Pocket 3", price: 500, score: 9, cats: ["irl", "chatting"], note: "Mini-Kamera mit Gimbal und großem Sensor, sehr beliebt bei IRL-Streamern." },

  // Licht
  { id: "ringlight-10", type: "licht", name: "Neewer Ringlicht 10\"", price: 35, score: 5, cats: ["gaming", "chatting", "creative", "music"], note: "Günstig und sofort ein besseres Bild." },
  { id: "keylight-mini", type: "licht", name: "Elgato Key Light Mini", price: 100, score: 7, cats: ["gaming", "chatting", "creative", "music"], note: "Kompakt, per App steuerbar, mit Akku." },
  { id: "keylight", type: "licht", name: "Elgato Key Light", price: 170, score: 8.5, cats: ["gaming", "chatting", "creative", "music"], note: "Großes, weiches Licht für ein professionelles Bild." },

  // Mäuse
  { id: "g203", type: "maus", name: "Logitech G203", price: 25, score: 6, cats: ["gaming"], note: "Unschlagbares Preis-Leistungs-Verhältnis." },
  { id: "deathadder-v3", type: "maus", name: "Razer DeathAdder V3", price: 80, score: 8.5, cats: ["gaming"], note: "Ergonomisch und sehr leicht." },
  { id: "superlight2", type: "maus", name: "Logitech G Pro X Superlight 2", price: 150, score: 9.5, cats: ["gaming"], note: "Kabellose Pro-Maus, beliebt in E-Sports." },

  // Tastaturen
  { id: "redragon-k552", type: "tastatur", name: "Redragon K552", price: 40, score: 5.5, cats: ["gaming"], note: "Günstige mechanische Tastatur." },
  { id: "keychron-v1", type: "tastatur", name: "Keychron V1", price: 90, score: 7.5, cats: ["gaming", "creative"], note: "Kompakt, hochwertig und anpassbar." },
  { id: "wooting-60he", type: "tastatur", name: "Wooting 60HE", price: 180, score: 9, cats: ["gaming"], note: "Analoge Schalter mit extrem schneller Reaktion." },

  // Stream-Controller
  { id: "streamdeck-neo", type: "streamdeck", name: "Elgato Stream Deck Neo", price: 90, score: 7, cats: ["gaming", "chatting", "creative"], note: "8 Tasten für Szenen, Sounds und Mute." },
  { id: "streamdeck-mk2", type: "streamdeck", name: "Elgato Stream Deck MK.2", price: 150, score: 8.5, cats: ["gaming", "chatting", "creative", "music"], note: "15 Tasten, der Standard unter Streamern." },

  // Capture Cards
  { id: "ugreen-capture", type: "capture", name: "UGREEN HDMI Capture", price: 25, score: 5, cats: ["gaming"], note: "Simpler USB-Stick für Konsolen, mit kleiner Verzögerung." },
  { id: "hd60x", type: "capture", name: "Elgato HD60 X", price: 170, score: 8.5, cats: ["gaming"], note: "Konsole in 1080p60 streamen, mit Passthrough ohne Verzögerung." },

  // Audio-Interfaces
  { id: "umc22", type: "interface", name: "Behringer UMC22", price: 45, score: 5.5, cats: ["music"], note: "Günstigster Einstieg für XLR-Mikrofone." },
  { id: "scarlett-solo", type: "interface", name: "Focusrite Scarlett Solo", price: 120, score: 8, cats: ["music", "chatting"], note: "Sehr beliebt, sauberer Klang, einfach zu bedienen." },

  // Zubehör
  { id: "powerbank-20k", type: "zubehoer", name: "Anker Powerbank 20.000 mAh", price: 50, score: 6.5, cats: ["irl"], note: "Damit Handy und Kamera den ganzen Stream durchhalten." },

  // ---------- Neu in Phase 1 (Richtpreise, werden mit echten Quellen noch geprüft) ----------

  // PC / Konsole (als ein Teil gerechnet)
  { id: "pc-einsteiger", type: "pc", platform: "pc", name: "Gaming-PC Einsteiger (z. B. Ryzen 5, RTX 5060)", price: 850, score: 6.5, cats: ["gaming", "chatting", "music", "creative"], note: "Reicht für 1080p-Streams der meisten Spiele. Richtwert für Fertig-PC oder Eigenbau." },
  { id: "pc-mittel", type: "pc", platform: "pc", name: "Gaming-PC Mittelklasse (z. B. Ryzen 7, RTX 5070)", price: 1300, score: 8, cats: ["gaming", "chatting", "music", "creative"], note: "Spielen und Streamen gleichzeitig ohne Ruckler, auch bei neuen Spielen." },
  { id: "pc-highend", type: "pc", platform: "pc", name: "Gaming-PC High-End (z. B. Ryzen 7 9800X3D, RTX 5080)", price: 2300, score: 9.5, cats: ["gaming", "creative"], note: "Für 1440p/4K-Gaming mit Stream in hoher Qualität." },
  { id: "ps5", type: "pc", platform: "konsole", name: "PlayStation 5", price: 500, score: 8, cats: ["gaming"], note: "Kann direkt streamen. Mit Capture Card und PC wird der Stream deutlich besser." },
  { id: "xbox-series-s", type: "pc", platform: "konsole", name: "Xbox Series S", price: 350, score: 6.5, cats: ["gaming"], note: "Günstigste aktuelle Konsole, ideal mit Game Pass." },
  { id: "switch-2", type: "pc", platform: "konsole", name: "Nintendo Switch 2", price: 470, score: 7.5, cats: ["gaming"], note: "Zum Streamen braucht man eine Capture Card." },

  // Bildschirme
  { id: "aoc-24g4x", type: "bildschirm", name: "AOC Gaming 24G4X (24\", 180 Hz)", price: 130, score: 6.5, cats: ["gaming", "chatting", "music", "creative"], note: "Günstiger, schneller Gaming-Monitor in Full HD." },
  { id: "lg-27gs75q", type: "bildschirm", name: "LG UltraGear 27GS75Q (27\", 1440p)", price: 230, score: 8, cats: ["gaming", "chatting", "music", "creative"], note: "Mehr Platz und schärferes Bild, gut für Spiel und Chat nebeneinander." },
  { id: "dell-p2425h", type: "bildschirm", name: "Dell P2425H (24\", Zweitmonitor)", price: 150, score: 7, cats: ["gaming", "chatting", "music", "creative"], note: "Als zweiter Bildschirm für Chat, OBS und Alerts." },

  // Streaming-Software
  { id: "obs", type: "software", billing: "gratis", name: "OBS Studio", price: 0, score: 9, cats: ["gaming", "chatting", "music", "creative"], note: "Der kostenlose Standard. Sehr flexibel, viele Plugins." },
  { id: "streamlabs-desktop", type: "software", billing: "gratis", name: "Streamlabs Desktop", price: 0, score: 7, cats: ["gaming", "chatting", "music", "creative"], note: "Einsteigerfreundlich, Alerts und Overlays schon eingebaut." },
  { id: "streamelements", type: "software", billing: "gratis", name: "StreamElements (Overlays & Alerts)", price: 0, score: 7.5, cats: ["gaming", "chatting", "music", "creative"], note: "Kostenlose Overlays, Alerts und Chatbot, läuft zusammen mit OBS." },
  { id: "streamlabs-ultra", type: "software", billing: "abo", name: "Streamlabs Ultra", price: 20, score: 7, cats: ["gaming", "chatting", "music", "creative"], note: "Premium-Overlays, Apps und Multistreaming. Lohnt sich erst später." },

  // Mikrofonarme
  { id: "tonor-t20", type: "mikrofonarm", name: "Tonor T20 Mikrofonarm", price: 25, score: 5.5, cats: ["gaming", "chatting", "music", "creative"], note: "Günstig, bringt das Mikro nah an den Mund." },
  { id: "wave-arm-lp", type: "mikrofonarm", name: "Elgato Wave Mic Arm LP", price: 100, score: 8, cats: ["gaming", "chatting", "music", "creative"], note: "Flacher Arm, verdeckt das Gesicht vor der Kamera nicht." },
  { id: "rode-psa1plus", type: "mikrofonarm", name: "Rode PSA1+", price: 110, score: 8.5, cats: ["gaming", "chatting", "music", "creative"], note: "Sehr stabil, auch für schwere Mikros wie das SM7B." },

  // Green Screens
  { id: "neewer-greenscreen", type: "greenscreen", name: "Neewer faltbarer Green Screen", price: 60, score: 5.5, cats: ["gaming", "chatting", "creative"], note: "Günstiger Einstieg zum Freistellen." },
  { id: "elgato-greenscreen", type: "greenscreen", name: "Elgato Green Screen", price: 170, score: 8.5, cats: ["gaming", "chatting", "creative"], note: "In Sekunden aufgebaut, faltenfrei." },

  // Stühle
  { id: "ikea-markus", type: "stuhl", name: "IKEA Markus", price: 180, score: 6.5, cats: ["gaming", "chatting", "music", "creative"], note: "Bequemer Bürostuhl mit Netzrücken für lange Streams." },
  { id: "secretlab-titan", type: "stuhl", name: "Secretlab Titan Evo", price: 550, score: 9, cats: ["gaming", "chatting", "creative"], note: "Sehr beliebt bei Streamern, viele Einstellmöglichkeiten." },

  // Schreibtische
  { id: "flexispot-e5", type: "schreibtisch", name: "FlexiSpot E5 (höhenverstellbar)", price: 260, score: 7.5, cats: ["gaming", "chatting", "music", "creative"], note: "Im Sitzen und Stehen streamen, gut für den Rücken." },
];

// ---------- Setups von Streamern ----------
// WICHTIG: Das sind erfundene BEISPIEL-Setups, um die Funktion zu zeigen.
// Echte Setups von Streamern bitte nur mit Quelle (z. B. Twitch-Panel, Video) eintragen:
// source: "https://..."
export const STREAMERS = [
  { id: "nachtfalke", name: "NachtfalkeTV", cat: "gaming", followers: 48200, since: 2019, games: "Valorant, CS2", tip: "Investiere zuerst in Mikro und Licht. Die Kamera kann warten.", items: ["pc-highend", "lg-27gs75q", "dell-p2425h", "obs", "rode-psa1plus", "shure-mv7plus", "arctis-nova7", "mx-brio", "keylight", "superlight2", "wooting-60he", "streamdeck-mk2"] },
  { id: "startersam", name: "StarterSam", cat: "gaming", followers: 850, since: 2025, games: "Minecraft, Fortnite", tip: "Mein Zubehör hat unter 250 € gekostet, der PC war gebraucht. Fang einfach an!", items: ["pc-einsteiger", "aoc-24g4x", "obs", "fifine-k669b", "cloud-stinger2", "c920", "ringlight-10", "g203", "redragon-k552"] },
  { id: "konsolenkoenigin", name: "KonsolenKönigin", cat: "gaming", followers: 12600, since: 2022, games: "EA FC, Call of Duty (PS5)", tip: "Mit Passthrough spielst du ohne Verzögerung, während der Stream läuft.", items: ["ps5", "pc-einsteiger", "aoc-24g4x", "obs", "fifine-am8", "cloud-iii", "elgato-facecam", "hd60x", "keylight-mini"] },
  { id: "lenalounge", name: "LenaLiveLounge", cat: "chatting", followers: 31500, since: 2020, games: "Just Chatting, Reactions", tip: "Bei Just Chatting bist DU der Content: gutes Licht ist alles.", items: ["pc-mittel", "lg-27gs75q", "obs", "rode-psa1plus", "elgato-greenscreen", "shure-sm7b", "scarlett-solo", "sony-zv-e10", "keylight", "streamdeck-mk2"] },
  { id: "quickchat", name: "QuickChatQuinn", cat: "chatting", followers: 2300, since: 2024, games: "Just Chatting, Q&A", tip: "Ein Key Light Mini hat mein Bild mehr verbessert als jede Kamera.", items: ["pc-einsteiger", "streamlabs-desktop", "fifine-am8", "c920", "keylight-mini"] },
  { id: "urbanwalks", name: "UrbanWalksBerlin", cat: "irl", followers: 19800, since: 2021, games: "IRL, Travel", tip: "Nimm immer eine zweite Powerbank mit. Immer.", items: ["osmo-pocket3", "rode-wireless-go3", "powerbank-20k"] },
  { id: "spazierpaul", name: "SpazierPaul", cat: "irl", followers: 1400, since: 2025, games: "IRL, Wandern", tip: "Dein Handy reicht für den Anfang. Ein Gimbal macht das Bild ruhig.", items: ["osmo-mobile", "dji-mic-mini", "powerbank-20k"] },
  { id: "beatbaukasten", name: "BeatBaukasten", cat: "music", followers: 9400, since: 2021, games: "Music Production, Live-Beats", tip: "Für Musik zählt der Ton doppelt. Spar nicht am Interface.", items: ["pc-mittel", "aoc-24g4x", "obs", "rode-psa1plus", "shure-sm7b", "scarlett-solo", "dt770-pro", "elgato-facecam", "keylight-mini"] },
  { id: "cozypixel", name: "CozyPixelArt", cat: "creative", followers: 6700, since: 2023, games: "Pixel Art, Illustration", tip: "Eine zweite Kamera auf die Hände macht Art-Streams viel spannender.", items: ["pc-mittel", "lg-27gs75q", "obs", "wave-arm-lp", "ikea-markus", "podmic-usb", "elgato-facecam", "keylight-mini", "cloud-iii", "streamdeck-neo"] },
];
