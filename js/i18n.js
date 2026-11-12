// Country preference and lightweight website localization (German/English MVP).
// No automatic geolocation or IP lookup: country is selected by the user.
(() => {
  "use strict";
  const KEY_COUNTRY = "sge-country";
  const KEY_LANG = "sge-language";
  const DEFAULT_COUNTRY = "DE";
  const countries = [
    ["DE", "Deutschland"], ["AT", "Österreich"], ["CH", "Schweiz / Suisse"],
    ["GB", "United Kingdom"], ["US", "United States"], ["IE", "Ireland"],
    ["FR", "France"], ["ES", "España"], ["IT", "Italia"],
    ["NL", "Nederland"], ["BE", "België / Belgique"], ["PL", "Polska"],
    ["TR", "Türkiye"], ["PT", "Portugal"], ["BR", "Brasil"],
    ["CA", "Canada"], ["AU", "Australia"], ["OTHER", "Anderes Land / Other"]
  ];
  // Countries do not uniquely identify a language. This is only a default suggestion.
  const countryLanguage = { DE:"de", AT:"de", CH:"de", GB:"en", US:"en", IE:"en", CA:"en", AU:"en" };
  const browserLanguage = (navigator.language || "de").toLowerCase().startsWith("de") ? "de" : "en";
  const storedCountry = localStorage.getItem(KEY_COUNTRY);
  let country = storedCountry || DEFAULT_COUNTRY;
  let manualLanguage = localStorage.getItem(KEY_LANG);
  let language = manualLanguage || (storedCountry ? (countryLanguage[country] || "en") : browserLanguage);
  const english = new Map(Object.entries({
    "Features":"Features", "Setups":"Setups", "Erste Schritte":"Getting started", "Community":"Community",
    "Anmelden":"Log in", "Abmelden":"Log out", "Registrieren":"Sign up", "Kostenlos registrieren":"Sign up for free",
    "Level 1: Dein Stream beginnt":"Level 1: Your streaming journey begins",
    "Vom ersten Stream":"From your first stream", "zur":"to your", "eigenen Community":"own community",
    "Die Streaming Growth Engine hilft neuen Streamern, schneller zu wachsen: mit Guides, Tools und einer Community, die dich pusht.":"Streaming Growth Engine helps new streamers grow with guides, tools, and a supportive community.",
    "Quest starten":"Start your journey", "Mehr erfahren":"Learn more", "Kostenlos":"Free",
    "Auf Deutsch":"Available in English", "Neue Tools":"New tools",
    "Dein":"Your", "Loadout":"Loadout", "Stream-Setup":"Streaming setup", "Wachstum":"Growth", "Tools":"Tools",
    "Finde das beste Setup für dein Budget und schau dir an, womit andere streamen.":"Find the best setup for your budget and see what other streamers use.",
    "Zum Setup-Finder →":"Explore setup finder →",
    "Strategien für mehr Zuschauer: Zeitplan, Titel, Kategorien und Social Media.":"Strategies for more viewers: schedules, titles, categories, and social media.",
    "Hilfreiche Tools und Bots, die dir Arbeit abnehmen.":"Helpful tools and bots that save you time.",
    "Kommt bald.":"Coming soon.",
    "Vernetze dich mit anderen Streamern, raide euch gegenseitig und wachst zusammen.":"Connect with other streamers, support each other and grow together.",
    "Erste":"First", "Quests":"Quests",
    "Plattform wählen":"Choose a platform", "Twitch, YouTube oder Kick: finde heraus, was zu dir passt.":"Twitch, YouTube or Kick: find what works for you.",
    "Setup einrichten":"Set up your gear", "Streaming-Software installieren und deine erste Szene bauen.":"Install streaming software and create your first scene.",
    "Zeitplan festlegen":"Set a schedule", "Regelmäßigkeit schlägt Länge. Plane feste Stream-Tage.":"Consistency matters more than length. Set regular streaming days.",
    "Dein erster Stream. Der wichtigste Schritt von allen.":"Your first stream. The most important step of all.",
    "Bereit für":"Ready for", "Level 2":"Level 2",
    "Erstelle deinen Account und starte deine Streamer-Reise.":"Create your account and start your streaming journey.",
    "Account erstellen":"Create an account", "Willkommen zurück":"Welcome back",
    "Streamer-Name":"Streamer name", "E-Mail":"Email", "Passwort":"Password",
    "Passwort vergessen?":"Forgot password?", "oder":"or", "Mit Google fortfahren":"Continue with Google",
    "Menü öffnen":"Open menu", "Schließen":"Close",
    "z. B. NightOwlTV":"e.g. NightOwlTV", "du@beispiel.de":"you@example.com",
    "Mindestens 6 Zeichen":"At least 6 characters",
    "Finde dein":"Find your", "perfektes Setup":"perfect setup",
    "Lass dir Setups für dein Budget vorschlagen, schau dir an, womit andere Streamer streamen, und vergleiche Hardware.":"Get setup suggestions for your budget, explore streamer gear and compare hardware.",
    "💶 Budget-Planer":"💶 Budget planner", "⭐ Streamer-Setups":"⭐ Streamer setups", "🧰 Hardware-Katalog":"🧰 Hardware catalog",
    "Dein Budget":"Your budget", "Was willst du streamen?":"What do you want to stream?",
    "Ich spiele auf einer Konsole (PS5, Xbox, Switch)":"I play on a console (PS5, Xbox, Switch)",
    "Das habe ich schon":"I already own", "Ohne PC/Konsole gerechnet. Preise sind Richtwerte.":"Excluding PC/console. Prices are estimates.",
    "💡 Wo zuerst investieren?":"💡 What should you upgrade first?",
    "Mikrofon":"Microphone", "Licht":"Lighting", "Kamera":"Camera", "Komfort":"Comfort",
    "Zuschauer verzeihen schlechtes Bild, aber keinen schlechten Ton.":"Viewers may forgive poor video, but not poor audio.",
    "Eine günstige Webcam mit gutem Licht schlägt eine teure Kamera im Dunkeln.":"A budget webcam with good lighting beats an expensive camera in the dark.",
    "Erst upgraden, wenn Ton und Licht stimmen.":"Upgrade only after audio and lighting are good.",
    "Stream-Controller, Maus und Tastatur machen das Streamen angenehmer, aber nicht besser.":"Controllers, mice and keyboards can make streaming easier, but do not necessarily improve the stream.",
    "Suche":"Search", "Enthält":"Contains", "Alle Bauteile":"All components", "Max. Gesamtpreis":"Maximum total price",
    "Egal":"Any", "★ Nur meine Favoriten":"★ Favorites only",
    "Hinweis: Die Setups unten sind":"Note: The setups below are", "Beispiele":"examples",
    ", um die Funktion zu zeigen. Echte Streamer-Setups ergänzen wir mit Quelle.":", to demonstrate this feature. Real streamer setups will include sources.",
    "Geeignet für":"Suitable for", "Alle Kategorien":"All categories", "Max. Preis:":"Maximum price:",
    "Sortieren":"Sort by", "Beste Bewertung":"Top rated", "Preis aufsteigend":"Price: low to high",
    "Preis absteigend":"Price: high to low", "Preis-Leistung":"Value for money",
    "Name, Spiel oder Produkt …":"Name, game or product …", "Budget-Regler":"Budget slider", "Budget in Euro":"Budget in euros",
    "Land":"Country", "Sprache":"Language", "Sprache der Website":"Website language",
    "Die Sprache wird anhand deines Landes vorgeschlagen. Du kannst sie jederzeit ändern.":"We suggest a language based on your country. You can change it anytime.",
    "Stream-Chat":"Stream chat", "Neuer Follower":"New follower", "Zeitplan":"Schedule",
    "Beispiel einer Stream-Vorschau":"Example of a stream preview", "Weiter scrollen":"Scroll down",
    "Nutzername":"Username", "3–20 Zeichen: Buchstaben, Zahlen und _. Darüber finden dich andere.":"3–20 characters: letters, numbers and _. This is how others find you.", "z. B. nightowl_tv":"e.g. nightowl_tv", "Bitte wähle einen Nutzernamen.":"Please choose a username.", "Der Nutzername muss 3 bis 20 Zeichen lang sein.":"Your username must be 3 to 20 characters long.", "Erlaubt sind nur Buchstaben, Zahlen und Unterstrich (_).":"Only letters, numbers and underscores (_) are allowed.", "Dieser Nutzername ist schon vergeben.":"This username is already taken.", "Speichern hat nicht geklappt. Bitte versuche es noch einmal.":"Saving didn't work. Please try again.", "Wähle deinen Nutzernamen":"Choose your username", "Damit andere dich finden können, braucht jedes Profil einen eigenen Nutzernamen.":"Every profile needs its own username so others can find you.", "3–20 Zeichen: Buchstaben, Zahlen und _":"3–20 characters: letters, numbers and _", "Anzeigename":"Display name", "Profil erstellen":"Create profile", "Später":"Later", "Andere":"Other", "Finde":"Find", "Streamer":"streamers", "Suche nach Nutzernamen oder Namen, schau dir Profile an und folge anderen Streamern.":"Search by username or name, check out profiles and follow other streamers.", "Profile suchen":"Search profiles", "@nutzername oder Name …":"@username or name …", "Neu dabei":"New members", "Wird geladen …":"Loading …", "Noch keine Profile. Sei der Erste!":"No profiles yet. Be the first!", "Profile konnten gerade nicht geladen werden. Lade die Seite neu.":"Profiles couldn't be loaded right now. Please reload the page.", "Suchergebnisse":"Search results", "Suche läuft …":"Searching …", "1 Profil gefunden":"1 profile found", "Profile gefunden":"profiles found", "Kein Profil gefunden für":"No profile found for", "Die Suche hat nicht geklappt. Versuche es noch einmal.":"The search didn't work. Please try again.", "Erstelle dein Profil, damit andere dich finden.":"Create your profile so others can find you.", "Angemeldet als":"Signed in as", "Mein Profil":"My profile", "Profil wird geladen …":"Loading profile …", "Profil nicht gefunden":"Profile not found", "Unter diesem Nutzernamen gibt es kein Profil.":"There is no profile with this username.", "Streamer suchen":"Find streamers", "Dein Profil":"Your profile", "Melde dich an, um dein Profil zu sehen und zu bearbeiten.":"Log in to see and edit your profile.", "Noch kein Profil":"No profile yet", "Wähle einen Nutzernamen, damit andere dich finden können.":"Choose a username so others can find you.", "Ups":"Oops", "Das Profil konnte gerade nicht geladen werden. Lade die Seite neu.":"The profile couldn't be loaded right now. Please reload the page.", "Profil bearbeiten":"Edit profile", "Entfolgen":"Unfollow", "Folgen":"Follow", "Link kopieren":"Copy link", "Erzähl anderen, was du streamst – über „Profil bearbeiten“.":"Tell others what you stream – use “Edit profile”.", "Noch keine Beschreibung.":"No description yet.", "Follower":"Followers", "Folgt":"Following", "Plattform":"Platform", "Dabei seit":"Member since", "Lieblingsspiele":"Favorite games", "Kanal":"Channel", "Link kopiert.":"Link copied.", "Das hat nicht geklappt. Versuche es noch einmal.":"That didn't work. Please try again.", "Über dich":"About you", "Was streamst du, wann bist du live?":"What do you stream, when are you live?", "Hauptplattform":"Main platform", "Keine Angabe":"Not specified", "Kanal-Link":"Channel link", "z. B. Valorant, Minecraft, EA FC":"e.g. Valorant, Minecraft, EA FC", "Mit Komma trennen":"Separate with commas", "Speichern":"Save", "Abbrechen":"Cancel", "Das ist dein aktueller Nutzername.":"This is your current username.", "Wird geprüft …":"Checking …", "Nutzername ist frei.":"Username is available.", "Bitte gib einen Anzeigenamen ein.":"Please enter a display name.", "Der Kanal-Link muss mit https:// beginnen.":"The channel link must start with https://.", "Profil gespeichert.":"Profile saved.", "Bitte gib einen Streamer-Namen ein.":"Please enter a streamer name."
  }));
  // Remember original text nodes so switching back is lossless.
  const originals = new WeakMap();
  const originalAttributes = new WeakMap();
  let scanning = false;
  function translateRoot(root = document.body) {
    if (!root || scanning) return;
    scanning = true;
    try {
      const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
      let node;
      while ((node = w.nextNode())) {
        if (["SCRIPT", "STYLE", "TEXTAREA", "OPTION"].includes(node.parentElement?.tagName)) continue;
        if (!originals.has(node)) originals.set(node, node.nodeValue);
        const original = originals.get(node);
        const trimmed = original.trim();
        const value = language === "en" ? english.get(trimmed) : null;
        const result = value === undefined || value === null ? original : original.replace(trimmed, value);
        if (node.nodeValue !== result) node.nodeValue = result;
      }
      root.querySelectorAll?.("[placeholder],[aria-label]").forEach(el => {
        if (!originalAttributes.has(el)) originalAttributes.set(el, {
          placeholder: el.getAttribute("placeholder"), aria: el.getAttribute("aria-label")
        });
        const base = originalAttributes.get(el);
        for (const [attr, val] of [["placeholder",base.placeholder],["aria-label",base.aria]]) {
          const key = attr === "aria" ? "aria-label" : attr;
          if (val !== null) el.setAttribute(key, language === "en" ? english.get(val) || val : val);
        }
      });
      document.documentElement.lang = language;
      document.querySelectorAll("[data-sge-language]").forEach(el => { if (el.value !== language) el.value = language; });
    } finally { scanning = false; }
  }
  function setLanguage(next, manual = true) {
    if (!["de", "en"].includes(next)) return;
    language = next;
    if (manual) { manualLanguage = next; localStorage.setItem(KEY_LANG, next); }
    translateRoot();
    document.dispatchEvent(new CustomEvent("sge:language", {detail:{language}}));
  }
  function setCountry(next) {
    country = next;
    localStorage.setItem(KEY_COUNTRY, next);
    if (!manualLanguage) setLanguage(countryLanguage[next] || "en", false);
  }
  function init() {
    const navs = document.querySelectorAll(".nav-links");
    navs.forEach(nav => {
      const wrap = document.createElement("label");
      wrap.className = "sge-language-switch";
      wrap.innerHTML = '<span class="sr-only">Sprache der Website</span><select data-sge-language aria-label="Sprache der Website"><option value="de">Deutsch</option><option value="en">English</option></select>';
      nav.insertBefore(wrap, nav.querySelector("#login-btn"));
      wrap.querySelector("select").addEventListener("change", e => setLanguage(e.target.value));
    });
    document.querySelectorAll("#name-field").forEach(field => {
      const countryField = document.createElement("label");
      countryField.className = "field sge-country-field";
      countryField.hidden = true;
      countryField.innerHTML = '<span>Land</span><select id="sge-country" autocomplete="country" required></select>';
      field.insertAdjacentElement("afterend", countryField);
      const selector = countryField.querySelector("select");
      countries.forEach(([code, name]) => selector.add(new Option(name, code)));
      selector.value = country;
      selector.addEventListener("change", e => setCountry(e.target.value));
      const langField = document.createElement("label");
      langField.className = "field sge-registration-language";
      langField.hidden = true;
      langField.innerHTML = '<span>Sprache</span><select id="sge-registration-language"><option value="de">Deutsch</option><option value="en">English</option></select><small class="sge-field-hint">Die Sprache wird anhand deines Landes vorgeschlagen. Du kannst sie jederzeit ändern.</small>';
      countryField.insertAdjacentElement("afterend", langField);
      langField.querySelector("select").value = language;
      langField.querySelector("select").addEventListener("change", e => setLanguage(e.target.value));
    });
    document.querySelectorAll("[data-tab]").forEach(tab => tab.addEventListener("click", () => {
      const reg = tab.dataset.tab === "register";
      document.querySelectorAll(".sge-country-field,.sge-registration-language").forEach(el => { el.hidden = !reg; });
    }));
    document.querySelectorAll("[data-open-auth]").forEach(btn => btn.addEventListener("click", () => {
      const reg = btn.dataset.openAuth === "register";
      document.querySelectorAll(".sge-country-field,.sge-registration-language").forEach(el => { el.hidden = !reg; });
      document.querySelectorAll("#sge-country").forEach(el => el.value = country);
    }));
    const observer = new MutationObserver(() => translateRoot());
    observer.observe(document.body, {subtree:true, childList:true});
    translateRoot();
  }
  document.addEventListener("DOMContentLoaded", init);
  window.SGE_I18N = { t: key => language === "en" ? (english.get(key) || key) : key, setLanguage, getLanguage: () => language, getCountry: () => country, setCountry, refresh: translateRoot };
})();
