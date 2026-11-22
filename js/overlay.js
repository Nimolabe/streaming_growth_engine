// ============================================================
//  Overlay für OBS (Browser-Quelle 1920 × 1080).
//  Liest die Gestaltung aus der URL (js/layout-core.js) und baut
//  die Szene nur mit textContent auf – geteilte Links können kein HTML einschleusen.
// ============================================================
(() => {
  "use strict";
  const L = window.SGE_LAYOUT;
  const config = L.fromSearch(location.search);
  const root = document.getElementById("overlay");
  const body = document.body;

  body.className = `theme-${config.theme} scene-${config.scene} cam-${config.cam} frame-${config.frame}`;
  const colors = L.palette(config.color);
  body.style.setProperty("--accent", config.color);
  body.style.setProperty("--accent-rgb", colors.rgb);
  body.style.setProperty("--accent-text", colors.text);
  body.style.setProperty("--glow-rgb", colors.glowRgb);
  body.style.setProperty("--accent-deep", colors.deep);
  body.style.setProperty("--accent-soft", colors.soft);
  body.style.setProperty("--on-accent", colors.onAccent);
  document.documentElement.lang = config.lang;

  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  };
  const socials = L.socialsOf(config);

  function socialList() {
    const list = el("ul", "socials");
    socials.forEach((item) => {
      const li = el("li", `social social-${item.key}`);
      li.append(el("span", "dot"), el("span", null, item.text));
      list.appendChild(li);
    });
    return list;
  }

  function fullScreen(titleKey) {
    const screen = el("div", "screen");
    const bg = el("div", "bg");
    // Hintergrund-Elemente je Stil (gezeichnet in css/overlay.css)
    const decor = {
      neon: ["horizon", "floor", "streak streak-1", "streak streak-2", "streak streak-3"],
      minimal: ["dots", "arc", "ring", "rule", "rule-2", "square"],
      bold: ["stripes", "band", "slab", "wedge"],
    }[config.theme];
    decor.forEach((name) => {
      const part = el("span", name);
      if (name === "floor") part.appendChild(el("span", "grid"));
      if (name === "stripes") part.appendChild(el("span", "stripes-inner"));
      bg.appendChild(part);
    });
    const center = el("div", "center");
    if (config.name) center.appendChild(el("p", "kicker", config.name));
    const title = L.textFor(config, titleKey);
    center.appendChild(el("h1", title.length > 26 ? "title is-long" : "title", title));
    const sub = el("p", "sub");
    center.appendChild(sub);
    screen.append(bg, center);
    if (socials.length) screen.appendChild(socialList());
    root.appendChild(screen);
    return sub;
  }

  function countdown(sub) {
    if (!config.countdown) return;
    const end = Date.now() + config.countdown * 60_000;
    const tick = () => {
      const left = Math.max(0, Math.round((end - Date.now()) / 1000));
      sub.classList.toggle("is-time", left > 0);
      sub.textContent = left > 0
        ? `${Math.floor(left / 60)}:${String(left % 60).padStart(2, "0")}`
        : L.TEXTS[config.lang].soon;
      if (left > 0) setTimeout(tick, 250);
    };
    tick();
  }

  // ---------- Socials am schlichten Rahmen ----------
  // Logos sind eigene Uploads des Streamers: socialIcons/<uid>/<plattform> in der Realtime
  // Database, gelesen per einfachem GET (ohne Firebase-SDK). Nur geprüfte PNG-Data-URLs werden
  // verwendet; fehlt etwas oder scheitert der Abruf, bleibt der Text stehen.
  const ICON_PREFIX = "data:image/png;base64,";
  const ICON_RE = /^data:image\/png;base64,[A-Za-z0-9+/]+={0,2}$/;
  const UID_RE = /^[A-Za-z0-9]{10,128}$/;
  const iconUrl = new Map(); // Plattform-Schlüssel -> geprüfte Data-URL, die sich als Bild laden ließ

  async function loadIcons(done) {
    const uid = new URLSearchParams(location.search).get("u");
    if (!config.fi || !uid || !UID_RE.test(uid)) return;
    try {
      const { firebaseConfig } = await import("./firebase-config.js");
      const base = String(firebaseConfig.databaseURL || "").replace(/\/+$/, "");
      if (!/^https:\/\/[a-z0-9.-]+$/.test(base)) return;
      const res = await fetch(`${base}/socialIcons/${uid}.json`, { cache: "no-store" });
      if (!res.ok) return;
      const data = await res.json();
      if (!data || typeof data !== "object") return;
      for (const [key] of L.SOCIALS) {
        const value = data[key];
        if (typeof value !== "string" || value.length > 40000 || !value.startsWith(ICON_PREFIX) || !ICON_RE.test(value)) continue;
        // Nur übernehmen, was sich wirklich als Bild laden lässt
        const probe = new Image();
        probe.onload = () => { iconUrl.set(key, value); done(); };
        probe.src = value;
      }
    } catch {
      // Kein Netz, Regeln noch nicht veröffentlicht o. Ä.: Text bleibt stehen
    }
  }

  function frameSocialItem(item) {
    const entry = el("span", "fs-item");
    entry.dataset.social = item.key;
    entry.dataset.len = String(item.name.length);
    const url = config.fi ? iconUrl.get(item.key) : null;
    if (url) {
      // Mit Logo: nur Logo + Name, ohne Plattformwort
      entry.classList.add("has-icon");
      const icon = el("span", "fs-icon");
      icon.style.webkitMaskImage = `url("${url}")`;
      icon.style.maskImage = `url("${url}")`;
      icon.setAttribute("role", "img");
      icon.setAttribute("aria-label", item.label);
      entry.append(icon, el("span", "fs-text", item.handle));
    } else {
      entry.append(el("span", "fs-text", item.text));
    }
    return entry;
  }

  // Handles bis zu dieser Länge werden nie gekürzt (lieber weniger Einträge pro Seite)
  const FULL_HANDLE = 15;

  function frameSocials(bar) {
    const items = L.frameSocialsOf(config);
    if (!items.length) return;
    const row = el("div", "fs-row");
    bar.appendChild(row);
    // Höchstens 3 Einträge mit Logos, höchstens 2 als Text (ein fehlendes Logo → Text-Regel).
    const maxPerPage = () => (config.fi && items.every((i) => iconUrl.get(i.key)) ? 3 : 2);
    const fits = () => [...row.children].every((entry) => {
      const text = entry.querySelector(".fs-text");
      return Number(entry.dataset.len) > FULL_HANDLE || text.scrollWidth <= text.clientWidth;
    });
    let start = 0;
    let shown = 0;
    const render = () => {
      if (start >= items.length) start = 0;
      // So viele wie vollständig passen, aber nicht mehr als erlaubt
      for (let n = Math.min(maxPerPage(), items.length - start); n >= 1; n -= 1) {
        row.dataset.count = String(n);
        row.replaceChildren(...items.slice(start, start + n).map(frameSocialItem));
        shown = n;
        if (n === 1 || fits()) break;
      }
    };
    render();
    if (document.fonts) document.fonts.ready.then(render); // Breiten erst mit der echten Schrift
    loadIcons(render);
    setInterval(() => {
      if (items.length <= shown) return;
      row.classList.add("is-hidden"); // sanft ausblenden (opacity)
      setTimeout(() => {
        start += shown;
        render();
        row.classList.remove("is-hidden");
      }, 600);
    }, 8000);
  }

  function live() {
    const plain = config.frame === "plain";
    const rect = L.frameRect(config);
    const cam = el("div", plain ? "cam-frame is-plain" : "cam-frame");
    cam.style.left = `${rect.x}px`;
    cam.style.top = `${rect.y}px`;
    cam.style.width = `${rect.w}px`;
    cam.style.height = `${rect.h}px`;
    if (plain) {
      const b = L.plainBorders(config);
      cam.style.borderWidth = `${b.top}px ${b.side}px ${b.bottom}px`;
      const bottom = el("div", "cam-bar cam-bar-bottom");
      if (config.name) bottom.appendChild(el("span", "cam-name", config.name));
      bottom.appendChild(el("span", "cam-ticks"));
      // Obere Leiste nur mit Socials am Rahmen; sonst bleibt oben nur der schmale Saum.
      if (config.fs) {
        const top = el("div", "cam-bar cam-bar-top");
        frameSocials(top);
        cam.appendChild(top);
      }
      cam.append(bottom, el("span", "cam-strokes"));
    } else if (config.name) {
      cam.appendChild(el("span", "cam-label", config.name));
    }
    root.appendChild(cam);
    // Stehen die Socials am Rahmen, entfällt der Hinweis in der Ecke.
    if (!socials.length || (plain && config.fs)) return;
    // Sitzt die Facecam unten rechts, weicht der Hinweis nach unten links aus.
    const badge = el("div", config.cam === "br" ? "social-badge is-left" : "social-badge");
    const text = el("span", "social-text");
    badge.append(el("span", "dot"), text);
    root.appendChild(badge);
    let index = 0;
    const show = () => {
      text.textContent = socials[index % socials.length].text;
      badge.classList.remove("swap");
      void badge.offsetWidth; // Animation neu starten
      badge.classList.add("swap");
      index += 1;
    };
    show();
    if (socials.length > 1) setInterval(show, 8000);
  }

  if (config.scene === "live") {
    live();
  } else if (config.scene === "start") {
    countdown(fullScreen("start"));
  } else if (config.scene === "pause") {
    fullScreen("pause");
  } else {
    const sub = fullScreen("end");
    if (config.next) sub.textContent = `${L.TEXTS[config.lang].nextLabel}: ${config.next}`;
  }
})();
