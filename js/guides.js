// ============================================================
//  Guides-Seite: Inhalte auf Deutsch und Englisch, ohne Abhängigkeiten.
//  Texte werden nur per textContent eingesetzt (kein HTML aus Daten).
//  Fakten mit Ablaufdatum (Affiliate-Bedingungen, Bitraten) tragen ein
//  „Stand“ und eine offizielle Quelle – bei Änderungen hier anpassen.
// ============================================================
(() => {
  "use strict";

  const GUIDES = [
    {
      id: "plattform", icon: "🎯", minutes: 4,
      title: { de: "Die richtige Plattform wählen", en: "Choosing the right platform" },
      intro: {
        de: "Die Plattform entscheidet, wie neue Zuschauer dich finden. Für den Start reicht eine – Kurzvideos bringen zusätzliche Reichweite.",
        en: "Your platform decides how new viewers find you. One is enough to start – short videos add extra reach.",
      },
      sections: [
        {
          table: {
            head: [{ de: "Plattform", en: "Platform" }, { de: "So wirst du gefunden", en: "How people find you" }, { de: "Passt gut zu", en: "Good fit for" }],
            rows: [
              ["Twitch", { de: "Live-Verzeichnis nach Kategorien, Raids anderer Streamer", en: "Live directory by category, raids from other streamers" }, { de: "Gaming, Just Chatting, viel Interaktion im Chat", en: "Gaming, Just Chatting, lots of chat interaction" }],
              ["YouTube", { de: "Suche, Empfehlungen, Aufzeichnungen und Shorts", en: "Search, recommendations, replays and Shorts" }, { de: "Inhalte, die auch später noch angesehen werden", en: "Content people still watch later" }],
              ["Kick", { de: "Live-Verzeichnis nach Kategorien", en: "Live directory by category" }, { de: "Kleinere Plattform – in vielen Kategorien weniger Kanäle gleichzeitig live", en: "Smaller platform – fewer channels live at once in many categories" }],
            ],
          },
        },
        {
          h: { de: "So entscheidest du", en: "How to decide" },
          list: [
            { de: "Such dein Spiel oder Thema auf der Plattform: Wie viele Kanäle sind gerade live, und wie viele Zuschauer haben sie?", en: "Search your game or topic on the platform: how many channels are live right now, and how many viewers do they have?" },
            { de: "In Kategorien mit wenigen Live-Kanälen stehst du in der Liste weit oben. In riesigen Kategorien gehst du als neuer Kanal unter.", en: "In categories with few live channels you appear near the top of the list. In huge categories a new channel gets buried." },
            { de: "Bleib die ersten Monate bei einer Plattform. Mehrere gleichzeitig verteilen deinen kleinen Chat auf mehrere Fenster.", en: "Stick to one platform for the first months. Streaming to several at once splits your small chat across windows." },
            { de: "Kurzvideos (TikTok, YouTube Shorts, Reels) sind auf jeder Plattform der stärkste Weg zu neuen Zuschauern.", en: "Short videos (TikTok, YouTube Shorts, Reels) are the strongest way to reach new viewers, whatever platform you choose." },
          ],
        },
        { tip: { de: "Faustregel: Gaming und Live-Interaktion → Twitch. Lernen, Tutorials und Inhalte zum Nachschauen → YouTube.", en: "Rule of thumb: gaming and live interaction → Twitch. Learning, tutorials and watch-later content → YouTube." } },
      ],
    },
    {
      id: "obs", icon: "🎛️", minutes: 8,
      title: { de: "OBS in 20 Minuten einrichten", en: "Set up OBS in 20 minutes" },
      intro: {
        de: "OBS Studio ist kostenlos und das Standard-Programm zum Streamen. Mit diesen Schritten bist du startklar.",
        en: "OBS Studio is free and the standard streaming software. These steps get you ready to go live.",
      },
      sections: [
        {
          h: { de: "Installieren und verbinden", en: "Install and connect" },
          steps: [
            { de: "OBS Studio nur von obsproject.com herunterladen, nicht von Drittseiten.", en: "Download OBS Studio only from obsproject.com, not from third-party sites." },
            { de: "Beim ersten Start den Assistenten zur automatischen Konfiguration laufen lassen und „Für das Streamen optimieren“ wählen. Er misst Rechner und Leitung.", en: "On first launch, run the auto-configuration wizard and choose “Optimize for streaming”. It measures your PC and connection." },
            { de: "Unter Einstellungen → Stream die Plattform wählen und das Konto verbinden oder den Streamschlüssel einfügen.", en: "Under Settings → Stream, pick your platform and connect your account or paste your stream key." },
          ],
        },
        { warn: { de: "Der Streamschlüssel ist wie ein Passwort: niemandem geben und nie im Stream zeigen. Wurde er sichtbar, sofort im Dashboard der Plattform zurücksetzen.", en: "Your stream key is like a password: never share it or show it on stream. If it was visible, reset it in your platform dashboard right away." } },
        {
          h: { de: "Vier Szenen, die jeder braucht", en: "Four scenes everyone needs" },
          list: [
            { de: "Startet gleich: Bild oder Countdown mit Musik, Mikrofon stumm.", en: "Starting soon: image or countdown with music, mic muted." },
            { de: "Live: Spiel oder Bildschirm, Webcam und Alerts.", en: "Live: game or screen, webcam and alerts." },
            { de: "Pause: Bild mit Musik, Mikrofon und Spiel stumm.", en: "Break: image with music, mic and game muted." },
            { de: "Ende: Danke, nächster Stream-Termin, und wen du gleich raidest.", en: "Ending: thanks, next stream date and who you are about to raid." },
          ],
          link: { href: "layouts.html", label: { de: "Alle vier Szenen fertig gestalten: Layout-Baukasten →", en: "Design all four scenes in minutes: layout builder →" } },
        },
        {
          h: { de: "Quellen in der Live-Szene", en: "Sources in your live scene" },
          list: [
            { de: "Spielaufnahme (oder Bildschirmaufnahme, wenn das Spiel nicht erkannt wird)", en: "Game Capture (or Display Capture if the game isn't detected)" },
            { de: "Videoaufnahmegerät für die Webcam", en: "Video Capture Device for your webcam" },
            { de: "Audioeingabe für das Mikrofon und Desktop-Audio für Spiel und Musik", en: "Audio Input for your mic and Desktop Audio for game and music" },
            { de: "Die Reihenfolge der Quellen sind Ebenen: Was oben steht, liegt im Bild vorn.", en: "Source order means layers: whatever is at the top sits in front." },
          ],
        },
        {
          h: { de: "Ausgabe-Einstellungen für Twitch", en: "Output settings for Twitch" },
          p: { de: "Einstellungen → Ausgabe → Ausgabemodus „Erweitert“. Deinen Upload misst ein Speedtest; plane etwa das Anderthalbfache der Bitrate ein.", en: "Settings → Output → Output Mode “Advanced”. Measure your upload with a speed test and allow about one and a half times the bitrate." },
          table: {
            head: [{ de: "Upload", en: "Upload" }, { de: "Auflösung", en: "Resolution" }, { de: "Videobitrate", en: "Video bitrate" }],
            rows: [
              [{ de: "ab 9 Mbit/s", en: "9 Mbps or more" }, "1080p, 60 FPS", "6.000 kbps|6,000 kbps"],
              [{ de: "ab 7 Mbit/s", en: "7 Mbps or more" }, "720p, 60 FPS", "4.500 kbps|4,500 kbps"],
              [{ de: "ab 5 Mbit/s", en: "5 Mbps or more" }, "720p, 30 FPS", "3.000 kbps|3,000 kbps"],
            ],
          },
        },
        {
          h: { de: "Diese Werte bleiben immer gleich", en: "These values never change" },
          list: [
            { de: "Bitratensteuerung: CBR (konstante Bitrate)", en: "Rate control: CBR (constant bitrate)" },
            { de: "Keyframe-Intervall: 2 Sekunden", en: "Keyframe interval: 2 seconds" },
            { de: "Encoder: Hardware (NVIDIA NVENC, AMD oder Intel Quick Sync), wenn vorhanden – das entlastet den Prozessor", en: "Encoder: hardware (NVIDIA NVENC, AMD or Intel Quick Sync) if available – it takes load off your CPU" },
            { de: "Audio: AAC mit 128 bis 160 kbps", en: "Audio: AAC at 128 to 160 kbps" },
          ],
        },
        { tip: { de: "Test ohne Publikum: „Aufnahme starten“ statt Stream, zwei Minuten spielen, ansehen. Ruckelt es, zuerst die FPS senken, dann die Auflösung.", en: "Test without an audience: click “Start Recording” instead of streaming, play for two minutes, watch it back. If it stutters, lower FPS first, then resolution." } },
      ],
      asOf: { de: "Stand: November 2026", en: "As of November 2026" },
      sources: [
        { label: { de: "Twitch: Broadcasting Guidelines", en: "Twitch: Broadcasting Guidelines" }, url: "https://help.twitch.tv/s/article/broadcasting-guidelines" },
        { label: { de: "OBS Studio (offizielle Seite)", en: "OBS Studio (official site)" }, url: "https://obsproject.com/" },
      ],
    },
    {
      id: "erster-stream", icon: "✅", minutes: 3,
      title: { de: "Checkliste für den ersten Stream", en: "Checklist for your first stream" },
      intro: {
        de: "Die meisten Pannen beim ersten Stream sind vermeidbar. Geh die Liste in Ruhe durch.",
        en: "Most first-stream mishaps are avoidable. Go through this list calmly.",
      },
      sections: [
        {
          h: { de: "Einen Tag vorher", en: "One day before" },
          list: [
            { de: "YouTube: Livestreaming aktivieren und Telefonnummer bestätigen – die erste Freischaltung kann bis zu 24 Stunden dauern.", en: "YouTube: enable live streaming and verify your phone number – the first activation can take up to 24 hours." },
            { de: "Twitch: Zwei-Faktor-Anmeldung einschalten. Sie schützt dein Konto und wird später für Affiliate gebraucht.", en: "Twitch: turn on two-factor authentication. It protects your account and you'll need it for Affiliate later." },
            { de: "Titel, Kategorie und Tags vorbereiten.", en: "Prepare your title, category and tags." },
          ],
        },
        {
          h: { de: "30 Minuten vorher", en: "30 minutes before" },
          list: [
            { de: "Mikrofon: Im OBS-Audiomixer bei lautem Sprechen im gelben Bereich, nie im roten.", en: "Microphone: in the OBS audio mixer, loud speech reaches yellow, never red." },
            { de: "Spiel leiser als deine Stimme – Zuschauer müssen dich immer verstehen.", en: "Game quieter than your voice – viewers must always understand you." },
            { de: "Benachrichtigungen aus (Discord, Windows, Handy) und private Fenster schließen.", en: "Turn off notifications (Discord, Windows, phone) and close private windows." },
            { de: "Nichts Privates im Bild: keine E-Mails, Adressen oder Passwörter.", en: "Nothing private on screen: no emails, addresses or passwords." },
            { de: "Wasser hinstellen.", en: "Have water nearby." },
          ],
        },
        {
          h: { de: "Während des Streams", en: "While you're live" },
          list: [
            { de: "Mit der Szene „Startet gleich“ beginnen – so kommen die ersten Leute rechtzeitig an.", en: "Start with the “Starting soon” scene so the first people arrive in time." },
            { de: "Neue Leute im Chat mit Namen begrüßen.", en: "Greet new people in chat by name." },
            { de: "Laut denken und kommentieren, auch bei null Zuschauern – Aufzeichnungen und Clips leben davon.", en: "Think out loud and commentate, even with zero viewers – replays and clips depend on it." },
            { de: "Zum Schluss den nächsten Termin nennen und einen anderen Kanal raiden.", en: "At the end, announce your next stream and raid another channel." },
          ],
        },
        {
          h: { de: "Danach", en: "Afterwards" },
          list: [
            { de: "Zehn Minuten der Aufzeichnung ansehen und eine Sache für nächstes Mal verbessern.", en: "Watch ten minutes of the replay and improve one thing for next time." },
            { de: "Die besten Momente als Kurzvideo schneiden.", en: "Cut your best moments into short videos." },
          ],
          link: { href: "index.html#features", label: { de: "Bald automatisch: der Clip Hunter →", en: "Soon automatic: Clip Hunter →" } },
        },
      ],
      asOf: { de: "Stand: November 2026", en: "As of November 2026" },
      sources: [
        { label: { de: "YouTube-Hilfe: Livestreaming", en: "YouTube Help: live streaming" }, url: "https://support.google.com/youtube/answer/2474026" },
      ],
    },
    {
      id: "zeitplan", icon: "📅", minutes: 3,
      title: { de: "Ein Zeitplan, der funktioniert", en: "A schedule that works" },
      intro: {
        de: "Zuschauer kommen wieder, wenn sie wissen, wann du live bist. Regelmäßigkeit schlägt Länge.",
        en: "Viewers come back when they know when you're live. Consistency beats length.",
      },
      sections: [
        {
          list: [
            { de: "Feste Tage und eine feste Startzeit, zum Beispiel Dienstag, Donnerstag und Sonntag um 19 Uhr.", en: "Fixed days and a fixed start time, for example Tuesday, Thursday and Sunday at 7 pm." },
            { de: "Lieber dreimal zwei bis drei Stunden als einmal acht Stunden.", en: "Three streams of two to three hours beat one eight-hour stream." },
            { de: "Wähle Zeiten, die du drei Monate lang durchhältst – auch in stressigen Wochen.", en: "Pick times you can keep up for three months – even in busy weeks." },
            { de: "Trag den Plan in den Twitch-Zeitplan oder als YouTube-Termin ein und kündige Pausen an.", en: "Put the plan in your Twitch schedule or as a scheduled YouTube stream, and announce breaks." },
            { de: "Verteile Streams auf verschiedene Tage – das zählt nebenbei auch für Affiliate.", en: "Spread streams across different days – it also counts towards Affiliate." },
          ],
        },
        { tip: { de: "Ein Stream, der ausfällt, kostet mehr als einer, der kürzer ist. Lieber eine Stunde streamen als gar nicht.", en: "A cancelled stream costs more than a shorter one. Better to stream for an hour than not at all." } },
      ],
    },
    {
      id: "wachstum", icon: "🚀", minutes: 5,
      title: { de: "Die ersten Zuschauer gewinnen", en: "Winning your first viewers" },
      intro: {
        de: "Am Anfang findet dich kaum jemand zufällig. Diese Hebel bringen die ersten Leute in deinen Chat – und halten sie dort.",
        en: "At first, hardly anyone finds you by chance. These levers bring the first people into your chat – and keep them there.",
      },
      sections: [
        {
          h: { de: "Gefunden werden", en: "Getting found" },
          list: [
            { de: "Titel konkret statt „Stream!“ – sag, was gerade passiert: „Erster Run auf Schwer – schaffen wir Boss 3?“", en: "Concrete titles instead of “Stream!” – say what's happening: “First hard-mode run – can we beat boss 3?”" },
            { de: "Kategorie mit wenigen Live-Kanälen wählen, in der du trotzdem gern spielst.", en: "Pick a category with few live channels that you still enjoy." },
            { de: "Passende Tags setzen, inklusive Sprache.", en: "Use fitting tags, including your language." },
          ],
        },
        {
          h: { de: "Kurzvideos", en: "Short videos" },
          list: [
            { de: "Zwei bis drei Kurzvideos pro Woche aus deinen besten Momenten (TikTok, Shorts, Reels).", en: "Two to three short videos per week from your best moments (TikTok, Shorts, Reels)." },
            { de: "Hochformat. In den ersten zwei Sekunden muss klar sein, worum es geht.", en: "Vertical format. Within the first two seconds it must be clear what it's about." },
            { de: "Den Kanal in der Bio verlinken und Streamzeiten nennen.", en: "Link your channel in your bio and mention your stream times." },
          ],
          link: { href: "index.html#features", label: { de: "Highlights automatisch finden: Clip Hunter →", en: "Find highlights automatically: Clip Hunter →" } },
        },
        {
          h: { de: "Community", en: "Community" },
          list: [
            { de: "Andere kleine Streamer besuchen und ehrlich mitreden – kein „Follow gegen Follow“.", en: "Visit other small streamers and genuinely join the conversation – no “follow for follow”." },
            { de: "Am Ende jedes Streams raiden. Wer raidet, wird oft zurückgeraidet.", en: "Raid at the end of every stream. Those who raid often get raided back." },
            { de: "Einen Discord-Server erst starten, wenn regelmäßig dieselben Leute im Chat sind.", en: "Only start a Discord server once the same people show up in chat regularly." },
          ],
          link: { href: "community.html", label: { de: "Andere Streamer in der Community finden →", en: "Find other streamers in the community →" } },
        },
        {
          h: { de: "Zuschauer halten", en: "Keeping viewers" },
          list: [
            { de: "Begrüßen, Fragen stellen, Chat-Nachrichten vorlesen und beantworten.", en: "Greet people, ask questions, read chat messages out loud and reply." },
            { de: "Stille Zuschauer („Lurker“) sind normal – sie zählen trotzdem. Ein kurzes Danke reicht.", en: "Silent viewers (“lurkers”) are normal – they still count. A quick thank-you is enough." },
          ],
        },
      ],
    },
    {
      id: "affiliate", icon: "💜", minutes: 3,
      title: { de: "Twitch Affiliate: was du brauchst", en: "Twitch Affiliate: what you need" },
      intro: {
        de: "Affiliate ist die erste Stufe, mit der du auf Twitch Geld verdienen kannst, etwa mit Subs und Bits. Twitch hat die Hürden im Juni 2026 gesenkt.",
        en: "Affiliate is the first tier that lets you earn money on Twitch, for example with subs and Bits. Twitch lowered the requirements in June 2026.",
      },
      sections: [
        {
          table: {
            head: [{ de: "Bedingung", en: "Requirement" }, { de: "Wert", en: "Value" }],
            rows: [
              [{ de: "Follower", en: "Followers" }, { de: "25 insgesamt", en: "25 in total" }],
              [{ de: "Gestreamte Zeit", en: "Time streamed" }, { de: "4 Stunden in den letzten 30 Tagen", en: "4 hours in the last 30 days" }],
              [{ de: "Verschiedene Streaming-Tage", en: "Different streaming days" }, { de: "4 in den letzten 30 Tagen", en: "4 in the last 30 days" }],
              [{ de: "Zuschauer", en: "Viewers" }, { de: "im Schnitt 3 gleichzeitig an 4 Tagen", en: "an average of 3 concurrent viewers on 4 days" }],
            ],
          },
        },
        {
          list: [
            { de: "Den Fortschritt zeigt das Creator-Dashboard unter den Erfolgen („Weg zum Affiliate“).", en: "Your progress is shown in the Creator Dashboard under Achievements (“Path to Affiliate”)." },
            { de: "Sind alle Bedingungen erfüllt, lädt Twitch dich ein. Danach folgen Vertrag sowie Steuer- und Auszahlungsdaten.", en: "Once you meet all requirements, Twitch invites you. Then come the agreement plus tax and payout details." },
            { de: "Die Zwei-Faktor-Anmeldung vorher einschalten.", en: "Turn on two-factor authentication beforehand." },
            { de: "Viele ältere Anleitungen nennen noch 50 Follower und 7 Tage – diese Zahlen sind veraltet.", en: "Many older guides still say 50 followers and 7 days – those numbers are outdated." },
          ],
        },
        { tip: { de: "Die schwerste Hürde ist der Zuschauer-Schnitt. Kürzere Streams, in denen deine Stammzuschauer dabei sind, halten den Schnitt oben – ein sehr langer Stream zieht ihn eher nach unten.", en: "The hardest part is the viewer average. Shorter streams with your regulars present keep it up – one very long stream tends to pull it down." } },
      ],
      asOf: { de: "Stand: November 2026", en: "As of November 2026" },
      sources: [
        { label: { de: "Twitch-Hilfe: Dem Affiliate-Programm beitreten", en: "Twitch Help: Joining the Affiliate Program" }, url: "https://help.twitch.tv/s/article/joining-the-affiliate-program" },
      ],
    },
  ];

  const UI = {
    de: { read: "Min. Lesezeit", sources: "Quellen", tip: "Tipp", warn: "Achtung", contents: "Inhalt", top: "Nach oben ↑" },
    en: { read: "min read", sources: "Sources", tip: "Tip", warn: "Heads up", contents: "Contents", top: "Back to top ↑" },
  };

  const lang = () => (window.SGE_I18N && window.SGE_I18N.getLanguage() === "en" ? "en" : "de");
  // Text in der aktuellen Sprache; "de|en" in einem String für Zahlenformate.
  const txt = (value, language) => {
    if (value == null) return "";
    if (typeof value === "string") {
      const parts = value.split("|");
      return parts.length === 2 ? parts[language === "en" ? 1 : 0] : value;
    }
    return value[language] || value.de || "";
  };
  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  };

  function renderTable(table, language) {
    const wrap = el("div", "guide-table-wrap");
    const node = el("table", "guide-table");
    const head = el("tr");
    table.head.forEach((cell) => head.appendChild(el("th", null, txt(cell, language))));
    const thead = el("thead");
    thead.appendChild(head);
    const tbody = el("tbody");
    table.rows.forEach((row) => {
      const tr = el("tr");
      row.forEach((cell) => tr.appendChild(el("td", null, txt(cell, language))));
      tbody.appendChild(tr);
    });
    node.append(thead, tbody);
    wrap.appendChild(node);
    return wrap;
  }

  function renderSection(section, language, ui) {
    const frag = document.createDocumentFragment();
    if (section.h) frag.appendChild(el("h3", null, txt(section.h, language)));
    if (section.p) frag.appendChild(el("p", null, txt(section.p, language)));
    if (section.table) frag.appendChild(renderTable(section.table, language));
    for (const kind of ["steps", "list"]) {
      if (!section[kind]) continue;
      const list = el(kind === "steps" ? "ol" : "ul", kind === "steps" ? "guide-steps" : "guide-list");
      section[kind].forEach((item) => list.appendChild(el("li", null, txt(item, language))));
      frag.appendChild(list);
    }
    for (const kind of ["tip", "warn"]) {
      if (!section[kind]) continue;
      const box = el("p", `guide-note guide-${kind}`);
      box.append(el("strong", null, ui[kind] + ": "), document.createTextNode(txt(section[kind], language)));
      frag.appendChild(box);
    }
    if (section.link) {
      const link = el("a", "guide-link", txt(section.link.label, language));
      link.href = section.link.href;
      frag.appendChild(link);
    }
    return frag;
  }

  function render() {
    const root = document.getElementById("guides");
    const toc = document.getElementById("guides-toc");
    if (!root || !toc) return;
    const language = lang();
    const ui = UI[language];

    toc.replaceChildren();
    toc.setAttribute("aria-label", ui.contents);
    GUIDES.forEach((guide) => {
      const link = el("a", "guide-chip", `${guide.icon} ${txt(guide.title, language)}`);
      link.href = `#${guide.id}`;
      toc.appendChild(link);
    });

    root.replaceChildren();
    GUIDES.forEach((guide) => {
      const article = el("article", "guide box");
      article.id = guide.id;
      const head = el("header", "guide-head");
      head.append(el("span", "guide-icon", guide.icon), el("h2", null, txt(guide.title, language)));
      const meta = el("p", "guide-meta", `${guide.minutes} ${ui.read}`);
      if (guide.asOf) meta.textContent += ` · ${txt(guide.asOf, language)}`;
      article.append(head, meta, el("p", "guide-intro", txt(guide.intro, language)));
      guide.sections.forEach((section) => article.appendChild(renderSection(section, language, ui)));
      if (guide.sources) {
        const sources = el("p", "guide-sources", `${ui.sources}: `);
        guide.sources.forEach((source, index) => {
          if (index) sources.appendChild(document.createTextNode(" · "));
          const link = el("a", null, txt(source.label, language));
          link.href = source.url;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          sources.appendChild(link);
        });
        article.appendChild(sources);
      }
      const top = el("a", "guide-top", ui.top);
      top.href = "#top";
      article.appendChild(top);
      root.appendChild(article);
    });
  }

  // Beim Öffnen mit Sprungmarke (z. B. guides.html#obs) erst nach dem Aufbau hinscrollen.
  function first() {
    render();
    const id = decodeURIComponent(location.hash.slice(1));
    const target = id && document.getElementById(id);
    if (target) target.scrollIntoView({ behavior: "instant", block: "start" });
  }

  document.addEventListener("sge:language", render);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", first);
  else first();
  window.SGE_GUIDES = GUIDES; // für Tests und spätere Erweiterungen
})();
