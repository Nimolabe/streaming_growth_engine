// Animationen der Startseite: weiches Scrollen (Lenis) + GSAP ScrollTrigger.
// Alle Inhalte sind auch ohne dieses Skript sichtbar. Wer "Bewegung reduzieren"
// eingestellt hat, bekommt eine ruhige Seite ohne Effekte.
// Wichtig: Texte werden nie in einzelne Buchstaben zerlegt, damit die
// Übersetzung in js/i18n.js weiter funktioniert.
(() => {
  "use strict";
  const root = document.documentElement;
  const nav = document.querySelector(".nav");
  const navLinks = document.querySelector(".nav-links");
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const lang = () => (window.SGE_I18N ? window.SGE_I18N.getLanguage() : "de");

  // ---------- Navigation: transparent über dem Hero, beim Runterscrollen ausblenden ----------
  let lastY = window.scrollY;
  function updateNav(y) {
    if (!nav) return;
    nav.classList.toggle("is-solid", y > 30);
    const menuOpen = navLinks && navLinks.classList.contains("open");
    if (y > lastY + 2 && y > window.innerHeight * 0.6 && !menuOpen) nav.classList.add("is-hidden");
    else if (y < lastY - 2 || y < 80) nav.classList.remove("is-hidden");
    lastY = y;
  }
  updateNav(window.scrollY);

  // ---------- Stream-Chat (läuft auch ohne GSAP, nur nicht bei reduzierter Bewegung) ----------
  const CHAT = [
    { n: "pixelpaula", c: "#ff7a8a", de: "erster! 🎉", en: "first! 🎉" },
    { n: "Raidmaster", c: "#7ee08f", de: "Raid incoming 🚀", en: "raid incoming 🚀" },
    { n: "kekskrümel", c: "#ffd166", de: "der Ton ist mega klar", en: "audio is super clean" },
    { n: "NightOwlTV", c: "#a99cff", de: "wann streamst du wieder?", en: "when's the next stream?" },
    { n: "lowping_lea", c: "#5ecbff", de: "GG, was für ein Clip", en: "GG, what a clip" },
    { n: "Zuschauer42", c: "#ff9f5a", de: "hab gefollowt ❤️", en: "just followed ❤️" },
    { n: "glitchgustav", c: "#7ee08f", de: "Overlay sieht stark aus", en: "overlay looks great" },
    { n: "mod_mia", c: "#ff7a8a", de: "Willkommen im Stream!", en: "welcome to the stream!" },
  ];
  const chatList = $(".chat-list");
  let chatIndex = 0;
  function addChat() {
    if (!chatList) return;
    const m = CHAT[chatIndex++ % CHAT.length];
    const li = document.createElement("li");
    const b = document.createElement("b");
    b.style.color = m.c;
    b.textContent = m.n;
    li.append(b, document.createTextNode(m[lang()] || m.de));
    chatList.appendChild(li);
    while (chatList.children.length > 9) chatList.firstElementChild.remove();
    if (window.gsap && !reduce) gsap.from(li, { autoAlpha: 0, y: 14, duration: .45, ease: "power3.out" });
  }
  // Startbestand, damit der Chat nicht leer ist
  for (let i = 0; i < 4; i++) addChat();

  if (reduce || !window.gsap || !window.ScrollTrigger) {
    root.classList.remove("motion");
    const v = $("[data-viewers]");
    if (v) v.textContent = "1.284";
    window.addEventListener("scroll", () => updateNav(window.scrollY), { passive: true });
    return;
  }
  window.__motionReady = true;
  gsap.registerPlugin(ScrollTrigger);

  // ---------- Lenis ----------
  let lenis = null;
  if (window.Lenis) {
    lenis = new Lenis({ duration: 1.15, easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)), smoothWheel: true });
    window.lenis = lenis;
    lenis.on("scroll", (e) => { ScrollTrigger.update(); updateNav(e.scroll); });
    gsap.ticker.add((time) => lenis.raf(time * 1000));
    gsap.ticker.lagSmoothing(0);
    // Beim Anmelde-Fenster das Scrollen der Seite anhalten
    const modal = $("#auth-modal");
    if (modal) new MutationObserver(() => (modal.hidden ? lenis.start() : lenis.stop())).observe(modal, { attributes: true, attributeFilter: ["hidden"] });
  } else {
    window.addEventListener("scroll", () => updateNav(window.scrollY), { passive: true });
  }

  // Sprungmarken weich anscrollen
  document.addEventListener("click", (e) => {
    const a = e.target.closest('a[href^="#"]');
    if (!a || !lenis) return;
    const hash = a.getAttribute("href");
    if (hash === "#") { e.preventDefault(); lenis.scrollTo(0, { duration: 1.4 }); return; }
    const target = document.querySelector(hash);
    if (!target) return;
    e.preventDefault();
    nav && nav.classList.remove("is-hidden");
    lenis.scrollTo(target, { offset: -70, duration: 1.4 });
  });

  intro();
  liveStream();
  scenes();
  window.addEventListener("load", () => ScrollTrigger.refresh());

  // ---------- Einstieg ----------
  function intro() {
    const tl = gsap.timeline({ defaults: { ease: "power4.out" } });
    tl.fromTo(nav, { autoAlpha: 0, y: -20 }, { autoAlpha: 1, y: 0, duration: .8, clearProps: "transform" }, .2)
      .fromTo(".hero h1 .line > span", { autoAlpha: 1, yPercent: 110 }, { yPercent: 0, duration: 1.1, stagger: .12 }, .15)
      .fromTo(".hero [data-hero]", { autoAlpha: 0, y: 24 }, { autoAlpha: 1, y: 0, duration: .9, stagger: .08 }, .45)
      .fromTo(".stream", { autoAlpha: 0, y: 60, rotateY: -22, rotateX: 10 },
        { autoAlpha: 1, y: 0, rotateY: -9, rotateX: 3, duration: 1.6, ease: "expo.out" }, .35)
      .from(".stream-hud > *", { autoAlpha: 0, y: -10, duration: .5, stagger: .1 }, 1.1)
      .from(".page-home .scroll-cue", { autoAlpha: 0, duration: .8 }, 1.4);
  }

  // ---------- Live-Effekte im Stream-Fenster ----------
  function liveStream() {
    const vEl = $("[data-viewers]");
    const fmt = (n) => Math.round(n).toLocaleString(lang() === "en" ? "en-US" : "de-DE");
    const viewers = { n: 0 };
    if (vEl) {
      gsap.to(viewers, {
        n: 1284, duration: 2.6, delay: .9, ease: "power2.out",
        onUpdate: () => { vEl.textContent = fmt(viewers.n); },
        onComplete: () => {
          // danach leicht schwanken, wie bei einem echten Stream
          setInterval(() => {
            gsap.to(viewers, { n: viewers.n + gsap.utils.random(-6, 14, 1), duration: 1.2, onUpdate: () => { vEl.textContent = fmt(viewers.n); } });
          }, 2600);
        },
      });
    }
    setInterval(addChat, 1900);

    const follow = $(".stream-follow");
    if (follow) {
      gsap.set(follow, { autoAlpha: 0, x: -30 });
      gsap.timeline({ repeat: -1, repeatDelay: 5, delay: 2.4 })
        .to(follow, { autoAlpha: 1, x: 0, duration: .6, ease: "back.out(1.6)" })
        .to(follow, { autoAlpha: 0, x: -20, duration: .4, ease: "power2.in" }, "+=2.8");
    }
  }

  // ---------- Szenen beim Scrollen ----------
  function scenes() {
    // Hero: Stream-Fenster richtet sich beim Wegscrollen auf, Text gleitet nach oben
    const heroST = { trigger: ".hero", start: "top top", end: "bottom top", scrub: true };
    gsap.to(".hero-content", { yPercent: -18, autoAlpha: .2, ease: "none", scrollTrigger: heroST });
    gsap.to(".stream", { rotateY: 0, rotateX: 0, scale: 1.06, yPercent: -6, ease: "none", scrollTrigger: heroST });
    gsap.to(".hero-glow", { opacity: .3, ease: "none", scrollTrigger: heroST });
    gsap.to(".page-home .scroll-cue", { autoAlpha: 0, ease: "none", scrollTrigger: { trigger: ".hero", start: "top top", end: "15% top", scrub: true } });

    marquee();

    // Überschriften gleiten herein (als Ganzes, übersetzungssicher)
    $$(".page-home .section-title, .cta h2").forEach((el) => {
      gsap.from(el, { autoAlpha: 0, y: 50, duration: 1.1, ease: "power4.out", scrollTrigger: { trigger: el, start: "top 88%", once: true } });
    });

    // Loadout-Karten: gestaffelt herein, Bilder öffnen sich von unten
    const cards = $$(".card-media");
    gsap.from(cards, {
      autoAlpha: 0, y: 70, duration: 1, ease: "power3.out", stagger: .1,
      scrollTrigger: { trigger: ".cards", start: "top 82%", once: true },
    });
    gsap.from(cards.map((c) => $(".card-img", c)), {
      clipPath: "inset(100% 0% 0% 0%)", duration: 1.3, ease: "power4.inOut", stagger: .1,
      scrollTrigger: { trigger: ".cards", start: "top 82%", once: true },
    });
    tiltCards(cards);

    quests();

    // Setup-Teaser: Bild öffnet sich zum Vollbild
    gsap.timeline({ scrollTrigger: { trigger: ".showcase", start: "top 85%", end: "center center", scrub: 1 }, defaults: { ease: "none" } })
      .fromTo(".showcase-frame", { clipPath: "inset(6% 7% 6% 7% round 28px)" }, { clipPath: "inset(0% 0% 0% 0% round 0px)" }, 0)
      .fromTo(".showcase-frame img", { scale: 1.3 }, { scale: 1 }, 0);
    gsap.from(".showcase-copy > *", {
      autoAlpha: 0, y: 40, duration: 1, ease: "power3.out", stagger: .1,
      scrollTrigger: { trigger: ".showcase-copy", start: "top 85%", once: true },
    });

    // Abschluss: großes "Level 2" wächst im Hintergrund
    gsap.fromTo(".cta-level", { scale: .7, autoAlpha: 0 }, {
      scale: 1.05, autoAlpha: 1, ease: "none",
      scrollTrigger: { trigger: ".cta", start: "top bottom", end: "center center", scrub: true },
    });
    gsap.from(".cta > p:not(.cta-level), .cta .btn", {
      autoAlpha: 0, y: 30, duration: .9, ease: "power3.out", stagger: .1,
      scrollTrigger: { trigger: ".cta h2", start: "top 85%", once: true },
    });
  }

  // Quests: jede erreichte Quest wird abgehakt, XP-Leiste und Level steigen
  function quests() {
    const items = $$(".quests li");
    const xpEl = $("[data-xp]"), lvlEl = $("[data-level]");
    const bar = $(".xp-bar span");
    const MAX = 1100;
    const xpOf = (li) => parseInt($(".xp", li).textContent.replace(/\D/g, ""), 10) || 0;
    const shown = { xp: 0 };
    const update = () => {
      const done = items.filter((li) => li.classList.contains("is-done"));
      const xp = done.reduce((s, li) => s + xpOf(li), 0);
      gsap.to(shown, { xp, duration: .8, ease: "power2.out", overwrite: true, onUpdate: () => { xpEl.textContent = Math.round(shown.xp); } });
      gsap.to(bar, { scaleX: xp / MAX, duration: .8, ease: "power3.out", overwrite: true });
      const level = done.length === items.length ? 2 : 1;
      if (lvlEl.textContent !== String(level)) {
        lvlEl.textContent = level;
        gsap.fromTo(lvlEl, { scale: 1.8, color: "#8b7cf6" }, { scale: 1, color: "#e6e7ea", duration: .7, ease: "back.out(2)" });
      }
    };
    items.forEach((li) => {
      ScrollTrigger.create({
        trigger: li, start: "top 62%",
        onEnter: () => { li.classList.add("is-done"); update(); },
        onLeaveBack: () => { li.classList.remove("is-done"); update(); },
      });
      gsap.fromTo(li, { autoAlpha: 0, x: 40 }, { autoAlpha: 1, x: 0, duration: .9, ease: "power3.out", clearProps: "opacity,visibility,transform", scrollTrigger: { trigger: li, start: "top 92%", once: true } });
    });
  }

  // Karten kippen leicht mit der Maus (nur mit Maus, nicht auf Touch)
  function tiltCards(cards) {
    if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;
    cards.forEach((card) => {
      const rx = gsap.quickTo(card, "rotateX", { duration: .5, ease: "power3" });
      const ry = gsap.quickTo(card, "rotateY", { duration: .5, ease: "power3" });
      gsap.set(card, { transformPerspective: 900 });
      card.addEventListener("pointermove", (e) => {
        const r = card.getBoundingClientRect();
        const px = (e.clientX - r.left) / r.width, py = (e.clientY - r.top) / r.height;
        card.style.setProperty("--mx", px * 100 + "%");
        card.style.setProperty("--my", py * 100 + "%");
        rx((.5 - py) * 8);
        ry((px - .5) * 10);
      });
      card.addEventListener("pointerleave", () => { rx(0); ry(0); });
    });
  }

  // Laufband: schneller beim Scrollen, dreht mit der Scrollrichtung
  function marquee() {
    const track = $(".marquee-track");
    if (!track) return;
    let loop = track.scrollWidth / 4, x = 0, dir = 1, speed = 1;
    window.addEventListener("resize", () => { loop = track.scrollWidth / 4; });
    gsap.ticker.add((time, delta) => {
      const v = lenis ? lenis.velocity : 0;
      if (lenis && lenis.direction) dir = lenis.direction;
      speed += (1 + Math.min(Math.abs(v) * .3, 8) - speed) * .08;
      x = gsap.utils.wrap(-loop, 0, x - 70 * speed * dir * (delta / 1000));
      track.style.transform = `translate3d(${x}px,0,0)`;
    });
  }
})();
