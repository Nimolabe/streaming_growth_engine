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

// ---------- Hardware-Typen ----------
export const TYPES = {
  mikrofon:   { label: "Mikrofon",       icon: "🎙️" },
  headset:    { label: "Headset / Kopfhörer", icon: "🎧" },
  kamera:     { label: "Kamera",         icon: "📷" },
  licht:      { label: "Licht",          icon: "💡" },
  maus:       { label: "Maus",           icon: "🖱️" },
  tastatur:   { label: "Tastatur",       icon: "⌨️" },
  streamdeck: { label: "Stream-Controller", icon: "🎛️" },
  capture:    { label: "Capture Card",   icon: "📺" },
  interface:  { label: "Audio-Interface", icon: "🎚️" },
  zubehoer:   { label: "Zubehör",        icon: "🔋" },
};

// ---------- Was braucht man pro Kategorie? ----------
// weight   = wie wichtig das Teil für diese Kategorie ist (höher = wichtiger)
// required = muss im Setup enthalten sein
export const NEEDS = {
  gaming: [
    { type: "mikrofon", weight: 3, required: true },
    { type: "headset", weight: 2, required: true },
    { type: "kamera", weight: 2 },
    { type: "licht", weight: 1.5 },
    { type: "maus", weight: 1.2 },
    { type: "tastatur", weight: 1 },
    { type: "streamdeck", weight: 0.6 },
  ],
  chatting: [
    { type: "mikrofon", weight: 3, required: true },
    { type: "kamera", weight: 3, required: true },
    { type: "licht", weight: 2.5, required: true },
    { type: "headset", weight: 1 },
    { type: "streamdeck", weight: 0.6 },
  ],
  irl: [
    { type: "kamera", weight: 3, required: true },
    { type: "mikrofon", weight: 3, required: true },
    { type: "zubehoer", weight: 1.5 },
  ],
  music: [
    { type: "mikrofon", weight: 3, required: true },
    { type: "headset", weight: 2.5, required: true },
    { type: "interface", weight: 2 },
    { type: "kamera", weight: 2 },
    { type: "licht", weight: 1 },
  ],
  creative: [
    { type: "mikrofon", weight: 3, required: true },
    { type: "kamera", weight: 2 },
    { type: "licht", weight: 1.5 },
    { type: "headset", weight: 1.5 },
    { type: "streamdeck", weight: 1 },
  ],
};

// ---------- Hardware-Katalog ----------
// cats     = für welche Kategorien das Produkt geeignet ist
// requires = funktioniert nur zusammen mit diesem Typ (z. B. XLR-Mikro → Interface)
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
];

// ---------- Setups von Streamern ----------
// WICHTIG: Das sind erfundene BEISPIEL-Setups, um die Funktion zu zeigen.
// Echte Setups von Streamern bitte nur mit Quelle (z. B. Twitch-Panel, Video) eintragen:
// source: "https://..."
export const STREAMERS = [
  { id: "nachtfalke", name: "NachtfalkeTV", cat: "gaming", followers: 48200, since: 2019, games: "Valorant, CS2", tip: "Investiere zuerst in Mikro und Licht. Die Kamera kann warten.", items: ["shure-mv7plus", "arctis-nova7", "mx-brio", "keylight", "superlight2", "wooting-60he", "streamdeck-mk2"] },
  { id: "startersam", name: "StarterSam", cat: "gaming", followers: 850, since: 2025, games: "Minecraft, Fortnite", tip: "Mein ganzes Setup hat unter 250 € gekostet. Fang einfach an!", items: ["fifine-k669b", "cloud-stinger2", "c920", "ringlight-10", "g203", "redragon-k552"] },
  { id: "konsolenkoenigin", name: "KonsolenKönigin", cat: "gaming", followers: 12600, since: 2022, games: "EA FC, Call of Duty (PS5)", tip: "Mit Passthrough spielst du ohne Verzögerung, während der Stream läuft.", items: ["fifine-am8", "cloud-iii", "elgato-facecam", "hd60x", "keylight-mini"] },
  { id: "lenalounge", name: "LenaLiveLounge", cat: "chatting", followers: 31500, since: 2020, games: "Just Chatting, Reactions", tip: "Bei Just Chatting bist DU der Content: gutes Licht ist alles.", items: ["shure-sm7b", "scarlett-solo", "sony-zv-e10", "keylight", "streamdeck-mk2"] },
  { id: "quickchat", name: "QuickChatQuinn", cat: "chatting", followers: 2300, since: 2024, games: "Just Chatting, Q&A", tip: "Ein Key Light Mini hat mein Bild mehr verbessert als jede Kamera.", items: ["fifine-am8", "c920", "keylight-mini"] },
  { id: "urbanwalks", name: "UrbanWalksBerlin", cat: "irl", followers: 19800, since: 2021, games: "IRL, Travel", tip: "Nimm immer eine zweite Powerbank mit. Immer.", items: ["osmo-pocket3", "rode-wireless-go3", "powerbank-20k"] },
  { id: "spazierpaul", name: "SpazierPaul", cat: "irl", followers: 1400, since: 2025, games: "IRL, Wandern", tip: "Dein Handy reicht für den Anfang. Ein Gimbal macht das Bild ruhig.", items: ["osmo-mobile", "dji-mic-mini", "powerbank-20k"] },
  { id: "beatbaukasten", name: "BeatBaukasten", cat: "music", followers: 9400, since: 2021, games: "Music Production, Live-Beats", tip: "Für Musik zählt der Ton doppelt. Spar nicht am Interface.", items: ["shure-sm7b", "scarlett-solo", "dt770-pro", "elgato-facecam", "keylight-mini"] },
  { id: "cozypixel", name: "CozyPixelArt", cat: "creative", followers: 6700, since: 2023, games: "Pixel Art, Illustration", tip: "Eine zweite Kamera auf die Hände macht Art-Streams viel spannender.", items: ["podmic-usb", "elgato-facecam", "keylight-mini", "cloud-iii", "streamdeck-neo"] },
];
