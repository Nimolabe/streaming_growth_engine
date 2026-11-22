// ============================================================
//  Layout-Baukasten: eigene Logos für die Socials am Rahmen
//  Datenbank: socialIcons/<uid>/<plattform> = "data:image/png;base64,…" (Regeln: database.rules.json)
//
//  Das Bild wird NUR im Browser verarbeitet: über ein Canvas in 128 × 128 eingepasst und in
//  eine einfarbig weiße Maske (PNG) umgerechnet. SVGs werden nur als Bild geladen und gezeichnet,
//  nie als Text ins DOM gesetzt – enthaltene Skripte laufen nicht und werden nicht gespeichert.
//  Verantwortlich für hochgeladene Bilder ist der Nutzer (Hinweis in layouts.html).
// ============================================================
import { getDb } from "./social.js";

const T = (s) => (window.SGE_I18N ? window.SGE_I18N.t(s) : s);
const $ = (id) => document.getElementById(id);

const box = $("icon-upload");
const rows = $("icon-rows");
const PLATFORMS = [["tw", "Twitch"], ["yt", "YouTube"], ["tt", "TikTok"], ["ig", "Instagram"], ["x", "X"]];
const SIZE = 128; // Kantenlänge der gespeicherten Maske
const MAX_FILE = 300 * 1024; // Eingabe höchstens 300 KB
const MAX_LEN = 40000; // gespeicherte Data-URL höchstens 40.000 Zeichen (wie in den Regeln)
const PREFIX = "data:image/png;base64,";
const TYPES = { "image/png": "png", "image/svg+xml": "svg", "image/webp": "webp" };
const UID_RE = /^[A-Za-z0-9]{10,128}$/;

let session = null; // { user, app }
let icons = {}; // Plattform -> Data-URL
const messages = new Map(); // Plattform oder "*" -> { text, type }
const busy = new Set();

// ---------- Bild → weiße Maske ----------
class IconError extends Error {}

function fileType(file) {
  const byType = TYPES[file.type];
  const ext = (file.name.split(".").pop() || "").toLowerCase();
  const byExt = { png: "png", svg: "svg", webp: "webp" }[ext];
  return byType || (!file.type && byExt) || null;
}

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => resolve({ img, url });
    img.onerror = () => { URL.revokeObjectURL(url); reject(new IconError("unreadable")); };
    img.src = url; // nur als Bild – ein SVG wird dabei nicht ausgeführt
  });
}

export async function imageToMask(file) {
  if (!fileType(file)) throw new IconError("type");
  if (file.size > MAX_FILE) throw new IconError("size");
  const { img, url } = await loadImage(file);
  try {
    // SVGs ohne feste Größe melden 0 × 0: dann auf die volle Fläche zeichnen
    const w = img.naturalWidth || SIZE;
    const h = img.naturalHeight || SIZE;
    const scale = Math.min(SIZE / w, SIZE / h);
    const dw = Math.max(1, Math.round(w * scale));
    const dh = Math.max(1, Math.round(h * scale));
    const dx = Math.floor((SIZE - dw) / 2);
    const dy = Math.floor((SIZE - dh) / 2);

    const canvas = document.createElement("canvas");
    canvas.width = SIZE;
    canvas.height = SIZE;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    ctx.drawImage(img, dx, dy, dw, dh);
    const src = ctx.getImageData(0, 0, SIZE, SIZE).data;

    // Hat das Bild selbst Transparenz? Nur die gezeichnete Fläche zählt, nicht der Rand.
    let see = 0;
    for (let y = dy; y < dy + dh; y++) {
      for (let x = dx; x < dx + dw; x++) if (src[(y * SIZE + x) * 4 + 3] < 200) see += 1;
    }
    const area = dw * dh;
    const useAlpha = see > area * 0.01;

    const out = ctx.createImageData(SIZE, SIZE);
    let ink = 0;
    for (let y = dy; y < dy + dh; y++) {
      for (let x = dx; x < dx + dw; x++) {
        const i = (y * SIZE + x) * 4;
        let a;
        if (useAlpha) {
          a = src[i + 3]; // Alphakanal ist die Form
        } else {
          // Ohne Transparenz: dunkle Pixel sind die Form (weich, damit Kanten glatt bleiben)
          const lum = 0.2126 * src[i] + 0.7152 * src[i + 1] + 0.0722 * src[i + 2];
          a = Math.max(0, Math.min(255, Math.round(((200 - lum) * 255) / 110)));
        }
        out.data[i] = 255;
        out.data[i + 1] = 255;
        out.data[i + 2] = 255;
        out.data[i + 3] = a;
        ink += a;
      }
    }
    const cover = ink / (255 * area);
    if (cover < 0.02 || cover > 0.9) throw new IconError("shape"); // fast leer oder fast vollflächig

    ctx.clearRect(0, 0, SIZE, SIZE);
    ctx.putImageData(out, 0, 0);
    const dataUrl = canvas.toDataURL("image/png");
    if (!dataUrl.startsWith(PREFIX)) throw new IconError("unreadable");
    if (dataUrl.length > MAX_LEN) throw new IconError("detail");
    return dataUrl;
  } finally {
    URL.revokeObjectURL(url);
  }
}

// ---------- Meldungen ----------
function errorText(err) {
  if (err instanceof IconError) {
    return {
      type: "Nur PNG, SVG oder WebP.",
      size: "Die Datei ist größer als 300 KB.",
      shape: "Bitte eine Version mit transparentem Hintergrund verwenden.",
      detail: "Das Logo ist zu detailreich. Bitte eine einfachere Version verwenden.",
      unreadable: "Das Bild konnte nicht gelesen werden.",
    }[err.message] || "Das Bild konnte nicht gelesen werden.";
  }
  const code = String(err?.code || err?.message || "").toUpperCase();
  if (code.includes("PERMISSION_DENIED")) return "Das Hochladen wird gerade eingerichtet. Bitte versuch es später noch einmal.";
  return "Speichern fehlgeschlagen. Bitte versuch es noch einmal.";
}

// ---------- Darstellung ----------
const visible = () => $("fs").checked;
const handle = (key) => ($(`social-${key}`)?.value || "").trim();

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

function statusLine(key) {
  const msg = messages.get(key);
  const p = el("p", "icon-status", msg ? T(msg.text) : "");
  p.dataset.type = msg?.type || "info";
  p.hidden = !msg;
  return p;
}

function row([key, label]) {
  const wrap = el("div", "icon-row");
  wrap.dataset.social = key;
  const name = el("span", "icon-name", label);
  const preview = el("span", "icon-preview");
  if (icons[key]) {
    const mark = el("span", "icon-mark");
    mark.style.webkitMaskImage = `url("${icons[key]}")`;
    mark.style.maskImage = `url("${icons[key]}")`;
    mark.setAttribute("role", "img");
    mark.setAttribute("aria-label", label);
    preview.appendChild(mark);
  } else {
    preview.appendChild(el("span", "icon-none", T("Kein Logo")));
  }
  const pick = el("label", "btn btn-small btn-ghost icon-pick");
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".png,.svg,.webp,image/png,image/svg+xml,image/webp";
  input.className = "icon-file";
  input.disabled = busy.has(key);
  input.addEventListener("change", () => { if (input.files[0]) upload(key, input.files[0]); input.value = ""; });
  pick.append(el("span", null, T("Bild wählen")), input);
  const actions = el("span", "icon-actions");
  actions.appendChild(pick);
  if (icons[key]) {
    const remove = el("button", "btn btn-small btn-ghost icon-remove", T("Entfernen"));
    remove.type = "button";
    remove.disabled = busy.has(key);
    remove.addEventListener("click", () => removeIcon(key));
    actions.appendChild(remove);
  }
  wrap.append(name, preview, actions, statusLine(key));
  return wrap;
}

function render() {
  if (!box) return;
  box.hidden = !visible();
  rows.replaceChildren();
  if (box.hidden) return;
  if (messages.has("*")) rows.appendChild(statusLine("*"));
  if (!session?.user) {
    const hint = el("p", "icon-login");
    hint.append(el("span", null, T("Melde dich an, um eigene Logos hochzuladen.")));
    const login = el("button", "btn btn-small", T("Anmelden"));
    login.type = "button";
    login.addEventListener("click", () => $("login-btn")?.click());
    rows.append(hint, login);
    return;
  }
  const filled = PLATFORMS.filter(([key]) => handle(key));
  if (!filled.length) {
    rows.appendChild(el("p", "icon-login", T("Trag zuerst bei den Socials einen Namen ein.")));
    return;
  }
  filled.forEach((p) => rows.appendChild(row(p)));
}

// ---------- Speichern / Entfernen ----------
async function upload(key, file) {
  if (!session?.user) { $("login-btn")?.click(); return; }
  busy.add(key);
  messages.delete(key);
  render();
  try {
    const dataUrl = await imageToMask(file);
    const { db, database } = await getDb(session.app);
    await db.set(db.ref(database, `socialIcons/${session.user.uid}/${key}`), dataUrl);
    icons[key] = dataUrl;
    messages.set(key, { text: "Logo gespeichert ✓", type: "success" });
    window.SGE_LAYOUT_EXPORT?.refresh(true);
  } catch (err) {
    if (!(err instanceof IconError)) console.warn("Logo hochladen:", err);
    messages.set(key, { text: errorText(err), type: "error" });
  } finally {
    busy.delete(key);
    render();
  }
}

async function removeIcon(key) {
  if (!session?.user) return;
  busy.add(key);
  messages.delete(key);
  render();
  try {
    const { db, database } = await getDb(session.app);
    await db.remove(db.ref(database, `socialIcons/${session.user.uid}/${key}`));
    delete icons[key];
    messages.set(key, { text: "Logo entfernt." });
    window.SGE_LAYOUT_EXPORT?.refresh(true);
  } catch (err) {
    console.warn("Logo entfernen:", err);
    messages.set(key, { text: errorText(err), type: "error" });
  } finally {
    busy.delete(key);
    render();
  }
}

// ---------- Anmeldung ----------
async function onAuth(detail) {
  const uid = detail?.user?.uid;
  session = uid ? detail : null;
  icons = {};
  messages.clear();
  // Die uid geht nur in die Overlay-Links (js/layouts.js), nie in Teilen-Link oder Profil.
  window.SGE_LAYOUT_UID = uid && UID_RE.test(uid) ? uid : null;
  render();
  window.SGE_LAYOUT_EXPORT?.refresh();
  if (!uid) return;
  try {
    const { db, database } = await getDb(session.app);
    const snap = await db.get(db.ref(database, `socialIcons/${uid}`));
    if (session?.user?.uid !== uid) return;
    const data = snap.exists() ? snap.val() : {};
    for (const [key] of PLATFORMS) {
      if (typeof data?.[key] === "string" && data[key].startsWith(PREFIX)) icons[key] = data[key];
    }
  } catch (err) {
    console.warn("Eigene Logos konnten nicht geladen werden:", err);
    const code = String(err?.code || err?.message || "").toUpperCase();
    if (code.includes("PERMISSION_DENIED")) messages.set("*", { text: errorText(err), type: "error" });
  }
  render();
}

if (box) {
  let timer = 0;
  const later = () => { clearTimeout(timer); timer = setTimeout(render, 150); };
  $("layout-form").addEventListener("input", later);
  $("layout-form").addEventListener("change", later);
  document.addEventListener("sge:language", render);
  document.addEventListener("sge:auth", (e) => onAuth(e.detail));
  if (window.sgeAuth) onAuth(window.sgeAuth);
  render();
}
