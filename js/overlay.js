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

  body.className = `theme-${config.theme} scene-${config.scene} cam-${config.cam}`;
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

  function live() {
    const cam = el("div", "cam-frame");
    const rect = L.camRect(config.cam);
    cam.style.left = `${rect.x}px`;
    cam.style.top = `${rect.y}px`;
    if (config.name) cam.appendChild(el("span", "cam-label", config.name));
    root.appendChild(cam);
    if (!socials.length) return;
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
