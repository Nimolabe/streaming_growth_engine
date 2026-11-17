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
    scene: "start", name: "", theme: "neon", color: "#8b7cf6", lang: "de",
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

  window.SGE_LAYOUT = {
    SCENES, THEMES, SOCIALS, PRESET_COLORS, LIMITS, TEXTS, DEFAULTS,
    normalize, toParams, fromSearch, socialsOf, textFor, contrastOn,
  };
})();
