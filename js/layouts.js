// ============================================================
//  Layout-Baukasten (layouts.html): Formular → Vorschau → OBS-Export.
//  Die Gestaltung lebt in der URL des Overlays (siehe js/layout-core.js).
// ============================================================
(() => {
  "use strict";
  const L = window.SGE_LAYOUT;
  const T = (s) => (window.SGE_I18N ? window.SGE_I18N.t(s) : s);
  const $ = (id) => document.getElementById(id);
  const STORE = "sge-layout";

  const form = $("layout-form");
  const preview = $("preview");
  const stage = $("preview-stage");
  let scene = "start";

  // ---------- Bausteine ins Formular ----------
  const swatches = $("swatches");
  L.PRESET_COLORS.forEach((color) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "swatch";
    button.style.background = color;
    button.dataset.color = color;
    button.setAttribute("aria-label", color);
    swatches.appendChild(button);
  });

  const socialFields = $("social-fields");
  L.SOCIALS.forEach(([key, prefix]) => {
    const label = document.createElement("label");
    label.className = "field social-field";
    const span = document.createElement("span");
    span.textContent = prefix;
    const input = document.createElement("input");
    input.type = "text";
    input.id = `social-${key}`;
    input.maxLength = L.LIMITS.handle;
    input.spellcheck = false;
    input.setAttribute("aria-label", prefix);
    label.append(span, input);
    socialFields.appendChild(label);
  });

  // ---------- Formular <-> Einstellungen ----------
  function read() {
    const raw = {
      theme: form.querySelector("input[name=theme]:checked")?.value,
      color: $("color").value,
      name: $("name").value,
      start: $("start").value,
      pause: $("pause").value,
      end: $("end").value,
      next: $("next").value,
      countdown: $("countdown").value,
      lang: $("lang").value,
      cam: form.querySelector("input[name=cam]:checked")?.value,
      frame: form.querySelector("input[name=frame]:checked")?.value,
      fs: $("fs").checked,
      fi: $("fi").checked,
    };
    L.SOCIALS.forEach(([key]) => { raw[key] = $(`social-${key}`).value; });
    return L.normalize(raw);
  }

  function write(config) {
    const radio = form.querySelector(`input[name=theme][value="${config.theme}"]`);
    if (radio) radio.checked = true;
    const camRadio = form.querySelector(`input[name=cam][value="${config.cam}"]`);
    if (camRadio) camRadio.checked = true;
    const frameRadio = form.querySelector(`input[name=frame][value="${config.frame}"]`);
    if (frameRadio) frameRadio.checked = true;
    $("fs").checked = config.fs;
    $("fi").checked = config.fi;
    $("color").value = config.color;
    ["name", "start", "pause", "end", "next"].forEach((key) => { $(key).value = config[key]; });
    const countdown = $("countdown");
    if (![...countdown.options].some((o) => Number(o.value) === config.countdown)) {
      const option = new Option("", String(config.countdown));
      countdown.add(option);
    }
    countdown.value = String(config.countdown);
    $("lang").value = config.lang;
    L.SOCIALS.forEach(([key]) => { $(`social-${key}`).value = config[key]; });
  }

  function placeholders(config) {
    const texts = L.TEXTS[config.lang];
    $("start").placeholder = texts.start;
    $("pause").placeholder = texts.pause;
    $("end").placeholder = texts.end;
  }

  // ---------- Links ----------
  const overlayBase = () => new URL("overlay.html", location.href);
  function overlayUrl(config, sceneName) {
    const url = overlayBase();
    url.search = L.toParams(config, sceneName).toString();
    return url.toString();
  }
  function shareUrl(config) {
    const url = new URL("layouts.html", location.href);
    url.search = L.toParams(config).toString();
    return url.toString();
  }

  // ---------- Vorschau ----------
  function scalePreview() {
    const width = stage.clientWidth;
    preview.style.transform = `scale(${width / 1920})`;
  }
  let timer = 0;
  function update() {
    clearTimeout(timer);
    timer = setTimeout(() => {
      const config = read();
      placeholders(config);
      preview.src = overlayUrl(config, scene);
      stage.classList.toggle("is-live", scene === "live");
      stage.dataset.cam = config.cam;
      placeCam(config);
      $("fs").closest(".check-field").classList.toggle("is-off", config.frame !== "plain");
      $("fi").closest(".check-field").classList.toggle("is-off", config.frame !== "plain" || !config.fs);
      document.querySelectorAll(".swatch").forEach((s) =>
        s.classList.toggle("active", s.dataset.color === config.color));
      renderLinks(config);
      try { localStorage.setItem(STORE, L.toParams(config).toString()); } catch { /* privat/voll */ }
    }, 120);
  }

  // Platzhalter „Webcam“ in der Vorschau genau auf das Kamerabild legen (Maße aus layout-core)
  function placeCam(config) {
    const r = L.camRect(config.cam, config.frame);
    const box = document.querySelector(".preview-cam");
    box.style.left = `${(r.x / 1920) * 100}%`;
    box.style.top = `${(r.y / 1080) * 100}%`;
    box.style.width = `${(r.w / 1920) * 100}%`;
    box.style.height = `${(r.h / 1080) * 100}%`;
  }

  function sceneLabel(name, language) {
    const labels = {
      de: { start: "Startet gleich", live: "Live", pause: "Pause", end: "Ende" },
      en: { start: "Starting soon", live: "Live", pause: "Be right back", end: "Ending" },
    };
    return labels[language][name];
  }

  function renderLinks(config) {
    const list = $("link-list");
    list.replaceChildren();
    L.SCENES.forEach((name) => {
      const row = document.createElement("div");
      row.className = "link-row";
      const label = document.createElement("span");
      label.textContent = T(sceneLabel(name, "de"));
      const input = document.createElement("input");
      input.type = "text";
      input.readOnly = true;
      input.value = overlayUrl(config, name);
      input.setAttribute("aria-label", label.textContent);
      const button = document.createElement("button");
      button.type = "button";
      button.className = "btn btn-small btn-ghost";
      button.textContent = T("Kopieren");
      button.addEventListener("click", () => copy(input.value, button));
      row.append(label, input, button);
      list.appendChild(row);
    });
  }

  async function copy(text, button, status) {
    let ok = false;
    try {
      await navigator.clipboard.writeText(text);
      ok = true;
    } catch {
      // Fallback: Text markieren, damit man ihn selbst kopieren kann
      const field = document.createElement("textarea");
      field.value = text;
      document.body.appendChild(field);
      field.select();
      try { ok = document.execCommand("copy"); } catch { ok = false; }
      field.remove();
    }
    const message = ok ? T("Kopiert ✓") : T("Kopieren nicht möglich – bitte manuell markieren.");
    if (status) {
      status.textContent = message;
    } else if (button) {
      const before = button.textContent;
      button.textContent = message;
      setTimeout(() => { button.textContent = before; }, 1800);
    }
  }

  // ---------- OBS-Szenensammlung ----------
  const uuid = () => (crypto.randomUUID ? crypto.randomUUID()
    : "10000000-1000-4000-8000-100000000000".replace(/[018]/g, (c) =>
      (c ^ (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (c / 4)))).toString(16)));

  function source(name, id, settings) {
    return {
      name, uuid: uuid(), id, versioned_id: id, settings,
      mixers: id === "scene" ? 0 : 255, sync: 0, flags: 0, volume: 1.0, balance: 0.5,
      enabled: true, muted: false, "push-to-mute": false, "push-to-mute-delay": 0,
      "push-to-talk": false, "push-to-talk-delay": 0, hotkeys: {}, deinterlace_mode: 0,
      deinterlace_field_order: 0, monitoring_type: 0, private_settings: {},
    };
  }

  function item(src, index, { x = 0, y = 0, w = 0, h = 0, locked = false } = {}) {
    return {
      name: src.name, source_uuid: src.uuid, visible: true, locked, rot: 0.0,
      pos: { x, y }, scale: { x: 1.0, y: 1.0 }, align: 5,
      bounds_type: w ? 2 : 0, bounds_align: 0, bounds: { x: w, y: h },
      crop_left: 0, crop_top: 0, crop_right: 0, crop_bottom: 0,
      id: index, group_item_backup: false, scale_filter: "disable",
      blend_method: "default", blend_type: "normal",
      show_transition: { duration: 0 }, hide_transition: { duration: 0 }, private_settings: {},
    };
  }

  const AUDIO = {
    windows: { desktop: "wasapi_output_capture", mic: "wasapi_input_capture" },
    mac: { desktop: null, mic: "coreaudio_input_capture" },
    linux: { desktop: "pulse_output_capture", mic: "pulse_input_capture" },
  };

  function sceneCollection(config, os) {
    const language = config.lang;
    const names = Object.fromEntries(L.SCENES.map((name) => [name, sceneLabel(name, language)]));
    const sources = [];
    const scenes = [];
    const overlay = (name) => {
      const src = source(`Overlay – ${names[name]}`, "browser_source", {
        url: overlayUrl(config, name), width: 1920, height: 1080,
        css: "body { background-color: rgba(0, 0, 0, 0); margin: 0px auto; overflow: hidden; }",
        restart_when_active: true, shutdown: false, reroute_audio: false,
      });
      sources.push(src);
      return src;
    };
    const addScene = (name, items) => {
      const src = source(names[name], "scene", { id_counter: items.length, custom_size: false, items });
      scenes.push(src);
    };

    // Unterste Ebene zuerst: Spiel, Webcam, dann das Overlay obendrauf.
    const liveItems = [];
    if (os === "windows") {
      const game = source(language === "de" ? "Spielaufnahme" : "Game Capture", "game_capture",
        { capture_mode: "any_fullscreen" });
      const cam = source("Webcam", "dshow_input", {});
      sources.push(game, cam);
      // Webcam genau dort, wo der Rahmen der gewählten Ecke liegt (js/layout-core.js)
      liveItems.push(item(game, 1, { w: 1920, h: 1080 }), item(cam, 2, L.camRect(config.cam, config.frame)));
    }
    const liveOverlay = overlay("live");
    liveItems.push(item(liveOverlay, liveItems.length + 1, { locked: true }));

    addScene("start", [item(overlay("start"), 1, { locked: true })]);
    addScene("live", liveItems);
    addScene("pause", [item(overlay("pause"), 1, { locked: true })]);
    addScene("end", [item(overlay("end"), 1, { locked: true })]);

    const collection = {
      name: config.name ? `SGE Layout – ${config.name}` : "SGE Layout",
      current_scene: names.start,
      current_program_scene: names.start,
      scene_order: L.SCENES.map((name) => ({ name: names[name] })),
      sources: [...sources, ...scenes],
      groups: [],
      quick_transitions: [],
      transitions: [],
      saved_projectors: [],
      current_transition: "Fade",
      transition_duration: 300,
      preview_locked: false,
      scaling_enabled: false,
      scaling_level: 0,
      scaling_off_x: 0.0,
      scaling_off_y: 0.0,
      modules: {},
    };
    const audio = AUDIO[os];
    if (audio.desktop) {
      collection.DesktopAudioDevice1 = source(language === "de" ? "Desktop-Audio" : "Desktop Audio",
        audio.desktop, { device_id: "default" });
    }
    collection.AuxAudioDevice1 = source(language === "de" ? "Mikrofon" : "Mic/Aux", audio.mic,
      { device_id: "default" });
    return collection;
  }

  function download(config, os) {
    const data = JSON.stringify(sceneCollection(config, os), null, 2);
    const blob = new Blob([data], { type: "application/json" });
    const link = document.createElement("a");
    const slug = (config.name || "layout").replace(/[^A-Za-z0-9_-]+/g, "-").replace(/^-+|-+$/g, "") || "layout";
    link.href = URL.createObjectURL(blob);
    link.download = `SGE-${slug}-${os}.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  }

  // i18n.js übersetzt keine <option>-Texte – das passiert hier.
  function translateOptions() {
    const en = window.SGE_I18N && window.SGE_I18N.getLanguage() === "en";
    [...$("countdown").options].forEach((option) => {
      const minutes = Number(option.value);
      option.textContent = minutes === 0 ? (en ? "off" : "aus") : `${minutes} ${en ? "minutes" : "Minuten"}`;
    });
  }

  // i18n.js übersetzt keine title-Attribute – den Titel der Vorschau hier setzen.
  function previewTitle() {
    preview.title = T("Vorschau der Szene");
  }

  function osStep() {
    const os = $("os").value;
    const step = $("os-step");
    step.textContent = os === "windows"
      ? T("Windows: In der Szene „Live“ bei „Spielaufnahme“ und „Webcam“ per Doppelklick dein Spiel und deine Kamera auswählen.")
      : T("macOS/Linux: In der Szene „Live“ deine Spiel- oder Bildschirmaufnahme und die Webcam hinzufügen und unter das Overlay ziehen.");
  }

  // ---------- Ereignisse ----------
  form.addEventListener("input", update);
  form.addEventListener("change", update);
  swatches.addEventListener("click", (event) => {
    const button = event.target.closest(".swatch");
    if (!button) return;
    $("color").value = button.dataset.color;
    update();
  });
  $("scene-tabs").addEventListener("click", (event) => {
    const tab = event.target.closest("[data-scene]");
    if (!tab) return;
    scene = tab.dataset.scene;
    document.querySelectorAll("#scene-tabs .tab").forEach((t) => {
      const active = t === tab;
      t.classList.toggle("active", active);
      t.setAttribute("aria-selected", String(active));
    });
    update();
  });
  $("download").addEventListener("click", () => download(read(), $("os").value));
  $("os").addEventListener("change", osStep);
  $("share").addEventListener("click", () => copy(shareUrl(read()), null, $("share-status")));
  new ResizeObserver(scalePreview).observe(stage);
  document.addEventListener("sge:language", () => { previewTitle(); osStep(); translateOptions(); renderLinks(read()); });

  // ---------- Start: geteilter Link > gespeicherter Stand > Standard ----------
  let start = null;
  if (location.search.length > 1) {
    start = L.fromSearch(location.search);
  } else {
    try {
      const saved = localStorage.getItem(STORE);
      if (saved) start = L.fromSearch("?" + saved);
    } catch { /* kein Speicher */ }
  }
  if (!start) {
    const language = window.SGE_I18N && window.SGE_I18N.getLanguage() === "en" ? "en" : "de";
    start = L.normalize({ lang: language });
  }
  if (/Mac/i.test(navigator.platform || navigator.userAgent)) $("os").value = "mac";
  else if (/Linux/i.test(navigator.platform || "") && !/Android/i.test(navigator.userAgent)) $("os").value = "linux";
  write(start);
  previewTitle();
  translateOptions();
  osStep();
  scalePreview();
  update();

  window.SGE_LAYOUT_EXPORT = { sceneCollection, overlayUrl, shareUrl, read }; // für Tests
})();
