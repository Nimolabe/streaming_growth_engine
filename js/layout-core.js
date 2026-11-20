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
  // Webcam-Rahmen (außen, inkl. Rahmenlinie) im 1920 × 1080-Bild. Unten links bleibt genau
  // wie vor der Einführung von "cam" (x=60, y=640), damit bestehende OBS-Szenen weiter passen.
  // Seitlich 60 px Abstand; Rahmen + Namensschild (58 px darunter) halten oben und unten
  // denselben Abstand von 112 px zum Bildrand.
  const CAM_SIZE = { w: 480, h: 270 };
  const CAM_RECTS = {
    tl: { x: 60, y: 112 }, tr: { x: 1380, y: 112 },
    bl: { x: 60, y: 640 }, br: { x: 1380, y: 640 },
  };
  const camRect = (cam) => ({ ...(CAM_RECTS[cam] || CAM_RECTS.bl), ...CAM_SIZE });
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
    scene: "start", name: "", theme: "neon", color: "#8b7cf6", lang: "de", cam: "bl",
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
    SCENES, THEMES, CAMS, CAM_SIZE, SOCIALS, PRESET_COLORS, LIMITS, TEXTS, DEFAULTS,
    normalize, toParams, fromSearch, socialsOf, textFor, contrastOn, camRect, palette,
  };
})();
