// ============================================================
//  Layout-Baukasten – gemeinsamer Kern für Editor (layouts.html)
//  und Overlay (overlay.html, als Browser-Quelle in OBS).
//  Die ganze Gestaltung steckt in der URL – kein Server, kein Konto nötig.
//  Alle Eingaben werden streng geprüft, weil Links geteilt werden.
// ============================================================
(() => {
  "use strict";

  const SCENES = ["start", "live", "pause", "end"];
  const THEMES = ["neon", "minimal", "bold"];
  // Facecam-Ecke in der Live-Szene: oben/unten × links/rechts. "bl" ist der alte Standard.
  const CAMS = ["tl", "tr", "bl", "br"];
  // Art des Facecam-Rahmens: "color" = farbiger Rahmen mit Namensschild (Standard, wie bisher),
  // "plain" = schlichter dunkler Rahmen mit Leiste oben (Socials) und unten (Kanalname).
  const FRAMES = ["color", "plain"];

  // ---------- Geometrie der Facecam (einzige Stelle für alle Maße) ----------
  // Kamerabild in drei Größen (16:9): klein (Standard, wie bisher), mittel, groß.
  // Die ganze Facecam-Gruppe hält in jeder Ecke seitlich 60 px Abstand, oben beginnt sie bei
  // y=112, unten endet sie bei y=968. Klein + farbig + unten links ergibt genau die alte
  // Position (x=60, y=640).
  const CAM_SIZES = { s: { w: 480, h: 270 }, m: { w: 640, h: 360 }, l: { w: 800, h: 450 } };
  const CAM_SIZE = CAM_SIZES.s;
  const EDGE = { side: 60, top: 112, bottom: 968 };
  const LABEL_H = 58; // Namensschild unter dem farbigen Rahmen
  // Schlichter Rahmen: 6 px Saum; Leiste unten (Kanalname) 42 px; oben 42 px nur mit
  // Socials am Rahmen, sonst nur ein Saum wie an den Seiten.
  const PLAIN = { side: 6, bar: 42 };
  const corner = (cam) => (CAMS.includes(cam) ? cam : "bl");

  // Ränder des schlichten Rahmens (oben, Seite, unten) für eine Einstellung
  function plainBorders(config) {
    return { top: config.fs ? PLAIN.bar : PLAIN.side, side: PLAIN.side, bottom: PLAIN.bar };
  }

  // Äußerer Rahmen (was das Overlay zeichnet). Erwartet geprüfte Einstellungen (normalize).
  function frameRect(config) {
    const c = corner(config.cam);
    const size = CAM_SIZES[config.cs] || CAM_SIZE;
    const plain = config.frame === "plain";
    const b = plainBorders(config);
    const w = plain ? size.w + 2 * b.side : size.w;
    const h = plain ? size.h + b.top + b.bottom : size.h;
    const groupH = plain ? h : h + LABEL_H;
    const x = c.endsWith("l") ? EDGE.side : 1920 - EDGE.side - w;
    const y = c.startsWith("t") ? EDGE.top : EDGE.bottom - groupH;
    return { x, y, w, h };
  }
  // Fläche des Kamerabilds (wohin die Webcam in OBS gehört). Beim farbigen Rahmen
  // ist das wie bisher das Rechteck des Rahmens selbst.
  function camRect(config) {
    const outer = frameRect(config);
    if (config.frame !== "plain") return outer;
    const b = plainBorders(config);
    return { x: outer.x + b.side, y: outer.y + b.top, w: outer.w - 2 * b.side, h: outer.h - b.top - b.bottom };
  }
  const SOCIALS = [
    // key, Anzeige-Präfix
    ["tw", "twitch.tv/"],
    ["yt", "youtube.com/@"],
    ["tt", "tiktok.com/@"],
    ["ig", "instagram.com/"],
    ["x", "x.com/"],
  ];
  const PRESET_COLORS = ["#8b7cf6", "#ff4655", "#20c997", "#f5b301", "#4dabf7", "#ff7ac6"];
  const LIMITS = { name: 25, text: 60, next: 40, handle: 30 };
  // Socials am schlichten Rahmen: Plattformname + Schreibweise des Namens, Logo-Datei
  const FRAME_SOCIALS = {
    tw: { label: "Twitch", prefix: "/", icon: "twitch" },
    yt: { label: "YouTube", prefix: "/@", icon: "youtube" },
    tt: { label: "TikTok", prefix: "@", icon: "tiktok" },
    ig: { label: "Instagram", prefix: "@", icon: "instagram" },
    x: { label: "X", prefix: "@", icon: "x" },
  };

  const TEXTS = {
    de: {
      start: "Gleich geht's los", pause: "Kurze Pause – bin gleich zurück",
      end: "Danke fürs Zuschauen!", nextLabel: "Nächster Stream", soon: "Jeden Moment …",
    },
    en: {
      start: "Starting soon", pause: "Be right back",
      end: "Thanks for watching!", nextLabel: "Next stream", soon: "Any moment now …",
    },
  };

  const DEFAULTS = {
    scene: "start", name: "", theme: "neon", color: "#8b7cf6", lang: "de", cam: "bl", frame: "color", cs: "s", fs: false, fi: false,
    start: "", pause: "", end: "", next: "", countdown: 5,
    tw: "", yt: "", tt: "", ig: "", x: "",
  };

  const CONTROL = new RegExp("[\\u0000-\\u001f\\u007f\\u2028\\u2029]", "g");
  const cleanText = (value, limit) =>
    String(value ?? "").replace(CONTROL, " ").replace(/\s+/g, " ").trim().slice(0, limit);
  const cleanHandle = (value) =>
    String(value ?? "").trim().replace(/^@/, "").replace(/[^A-Za-z0-9_.]/g, "").slice(0, LIMITS.handle);
  const cleanColor = (value) => {
    const color = String(value ?? "").trim().toLowerCase();
    return /^#[0-9a-f]{6}$/.test(color) ? color : DEFAULTS.color;
  };

  // Eingaben (Objekt oder URLSearchParams) → geprüfte Einstellungen
  function normalize(input) {
    const get = (key) => (input instanceof URLSearchParams ? input.get(key) : input?.[key]);
    const config = { ...DEFAULTS };
    const scene = get("scene") ?? get("s");
    if (SCENES.includes(scene)) config.scene = scene;
    const theme = get("theme") ?? get("t");
    if (THEMES.includes(theme)) config.theme = theme;
    const cam = get("cam");
    if (CAMS.includes(cam)) config.cam = cam;
    const frame = get("frame");
    if (FRAMES.includes(frame)) config.frame = frame;
    const cs = get("cs");
    if (["s", "m", "l"].includes(cs)) config.cs = cs;
    const on = (value) => value === true || value === "1";
    config.fs = on(get("fs"));
    config.fi = on(get("fi"));
    const lang = get("lang") ?? get("l");
    if (lang === "de" || lang === "en") config.lang = lang;
    config.name = cleanText(get("name") ?? get("n"), LIMITS.name);
    config.color = cleanColor(get("color") ?? get("c"));
    config.start = cleanText(get("start") ?? get("ms"), LIMITS.text);
    config.pause = cleanText(get("pause") ?? get("mp"), LIMITS.text);
    config.end = cleanText(get("end") ?? get("me"), LIMITS.text);
    config.next = cleanText(get("next") ?? get("nx"), LIMITS.next);
    const minutes = Number.parseInt(get("countdown") ?? get("cd") ?? DEFAULTS.countdown, 10);
    config.countdown = Number.isFinite(minutes) ? Math.min(30, Math.max(0, minutes)) : DEFAULTS.countdown;
    for (const [key] of SOCIALS) config[key] = cleanHandle(get(key));
    return config;
  }

  // Einstellungen → kurze URL-Parameter (leere Werte und Standardwerte fallen weg)
  function toParams(config, scene) {
    const c = normalize(config);
    const params = new URLSearchParams();
    const put = (key, value, fallback = "") => {
      if (value !== "" && value !== fallback) params.set(key, String(value));
    };
    if (scene) params.set("s", scene);
    put("t", c.theme, DEFAULTS.theme);
    put("c", c.color.slice(1), DEFAULTS.color.slice(1));
    put("l", c.lang, DEFAULTS.lang);
    put("cam", c.cam, DEFAULTS.cam);
    put("frame", c.frame, DEFAULTS.frame);
    put("cs", c.cs, DEFAULTS.cs);
    if (c.fs) params.set("fs", "1");
    if (c.fi) params.set("fi", "1");
    put("n", c.name);
    put("ms", c.start);
    put("mp", c.pause);
    put("me", c.end);
    put("nx", c.next);
    put("cd", c.countdown, DEFAULTS.countdown);
    for (const [key] of SOCIALS) put(key, c[key]);
    return params;
  }

  // Farbe in URL ohne „#“: beim Einlesen ergänzen
  function fromSearch(search) {
    const params = new URLSearchParams(search);
    const color = params.get("c");
    if (color && /^[0-9a-fA-F]{6}$/.test(color)) params.set("c", "#" + color);
    return normalize(params);
  }

  function socialsOf(config) {
    return SOCIALS.filter(([key]) => config[key]).map(([key, prefix]) => ({ key, text: prefix + config[key] }));
  }

  // Socials für die obere Leiste des schlichten Rahmens, z. B. "Twitch /name"
  function frameSocialsOf(config) {
    return SOCIALS.filter(([key]) => config[key]).map(([key]) => {
      const meta = FRAME_SOCIALS[key];
      const handle = meta.prefix + config[key];
      return { key, name: config[key], label: meta.label, handle, text: `${meta.label} ${handle}`, icon: meta.icon };
    });
  }

  function textFor(config, key) {
    const own = config[key];
    return own || TEXTS[config.lang][key];
  }

  // Lesbare Schriftfarbe auf der Akzentfarbe (WCAG-Leuchtdichte)
  function contrastOn(hex) {
    const channel = (i) => {
      const v = parseInt(hex.slice(i, i + 2), 16) / 255;
      return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
    };
    const luminance = 0.2126 * channel(1) + 0.7152 * channel(3) + 0.0722 * channel(5);
    return luminance > 0.4 ? "#0b0a12" : "#ffffff";
  }

  // Farben aus der Akzentfarbe ableiten (ohne color-mix, damit auch ältere OBS-Browser
  // es können). Liefert u. a. eine Textfarbe, die auf dunklem Grund sicher lesbar ist.
  function rgbOf(hex) {
    return [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
  }
  function luminance([r, g, b]) {
    const ch = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b);
  }
  const contrast = (a, b) => {
    const [l1, l2] = [luminance(a), luminance(b)].sort((x, y) => y - x);
    return (l1 + 0.05) / (l2 + 0.05);
  };
  const mix = (a, b, t) => a.map((v, i) => Math.round(v + (b[i] - v) * t));
  const hexOf = (rgb) => "#" + rgb.map((v) => v.toString(16).padStart(2, "0")).join("");
  function palette(hex) {
    const accent = rgbOf(hex);
    const dark = [11, 10, 18]; // Grundfarbe der dunklen Hintergründe
    // So weit mit Weiß aufhellen, bis der Kontrast auf dem dunklen Grund mindestens 4,5 ist
    let text = accent;
    for (let t = 0; t <= 1.0001 && contrast(text, dark) < 4.5; t += 0.05) text = mix(accent, [255, 255, 255], t);
    return {
      rgb: accent.join(", "),
      text: hexOf(text),
      glowRgb: text.join(", "), // Leuchtfarbe: wie text, also auch bei dunklen Akzenten sichtbar
      deep: hexOf(mix(accent, dark, 0.55)),
      soft: hexOf(mix(accent, [255, 255, 255], 0.35)),
      onAccent: contrastOn(hex),
    };
  }

  window.SGE_LAYOUT = {
    SCENES, THEMES, CAMS, FRAMES, CAM_SIZE, CAM_SIZES, PLAIN, SOCIALS, FRAME_SOCIALS, PRESET_COLORS, LIMITS, TEXTS, DEFAULTS,
    normalize, toParams, fromSearch, socialsOf, textFor, contrastOn, camRect, frameRect, plainBorders, frameSocialsOf, palette,
  };
})();
