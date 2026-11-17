// ============================================================
//  Beta-Warteliste (zuerst für den Clip Hunter)
//  Datenbank: waitlist/<feature>/<uid> = { createdAt, platform? }
//  Gespeichert wird nur, DASS sich ein angemeldeter Account vormerkt –
//  keine zusätzliche E-Mail-Adresse. Regeln: database.rules.json
// ============================================================
import { getDb } from "./social.js";

const T = (s) => (window.SGE_I18N ? window.SGE_I18N.t(s) : s);
const FEATURES = new Set(["clipHunter"]);
const PLATFORMS = new Set(["twitch", "youtube", "kick", "tiktok", "andere"]);

const boxes = [...document.querySelectorAll("[data-waitlist]")].filter((box) =>
  FEATURES.has(box.dataset.waitlist)
);

let session = null; // { user, app }
const joined = new Map(); // feature -> true/false/undefined (unbekannt)
const pending = new Set(); // Features, für die sich jemand vor der Anmeldung vormerken wollte
const busy = new Set();
const messages = new Map(); // feature -> { text, type }

function setMessage(feature, text, type = "info") {
  if (text) messages.set(feature, { text, type });
  else messages.delete(feature);
}

function render() {
  for (const box of boxes) {
    const feature = box.dataset.waitlist;
    const join = box.querySelector("[data-waitlist-join]");
    const leave = box.querySelector("[data-waitlist-leave]");
    const status = box.querySelector("[data-waitlist-status]");
    const isJoined = Boolean(session?.user) && joined.get(feature) === true;
    const working = busy.has(feature);

    join.hidden = isJoined;
    join.disabled = working;
    join.textContent = T("Für die Beta vormerken");
    leave.hidden = !isJoined;
    leave.disabled = working;
    leave.textContent = T("Austragen");

    const message = messages.get(feature);
    let text = "";
    let type = "info";
    if (message) {
      ({ text, type } = message);
    } else if (isJoined) {
      text = T("✓ Du bist vorgemerkt. Wir melden uns, sobald die Beta startet.");
      type = "success";
    } else if (!session?.user) {
      text = T("Kostenlos. Du brauchst nur einen Account.");
    }
    status.textContent = text;
    status.dataset.type = type;
    status.hidden = !text;
    box.classList.toggle("is-joined", isJoined);
  }
}

function errorText(err) {
  const code = String(err?.code || err?.message || "").toUpperCase();
  if (code.includes("PERMISSION_DENIED")) {
    return T("Die Warteliste wird gerade eingerichtet. Bitte versuch es später noch einmal.");
  }
  if (code.includes("NETWORK") || code.includes("DISCONNECTED")) {
    return T("Keine Verbindung. Prüfe dein Internet.");
  }
  return T("Das hat nicht geklappt. Bitte versuch es noch einmal.");
}

async function load(feature) {
  if (!session?.user) return;
  const uid = session.user.uid;
  try {
    const { db, database } = await getDb(session.app);
    const snap = await db.get(db.ref(database, `waitlist/${feature}/${uid}`));
    if (session?.user?.uid !== uid) return; // inzwischen abgemeldet / gewechselt
    joined.set(feature, snap.exists());
  } catch (err) {
    // Lesen scheitert z. B., solange die Regeln noch nicht veröffentlicht sind.
    console.warn("Warteliste konnte nicht geladen werden:", err);
    joined.delete(feature);
  }
  render();
}

// Plattform aus dem öffentlichen Profil (falls angegeben) – hilft bei der Beta-Planung.
async function profilePlatform(db, database, uid) {
  try {
    const snap = await db.get(db.ref(database, `profiles/${uid}/platform`));
    return snap.exists() ? String(snap.val()) : "";
  } catch {
    return "";
  }
}

async function join(feature) {
  if (!session?.user) {
    pending.add(feature);
    setMessage(feature, T("Melde dich an – danach wirst du automatisch vorgemerkt."));
    render();
    document.getElementById("login-btn")?.click();
    return;
  }
  if (busy.has(feature)) return;
  busy.add(feature);
  setMessage(feature, "");
  render();
  try {
    const { db, database } = await getDb(session.app);
    const entry = { createdAt: db.serverTimestamp() };
    const platform = await profilePlatform(db, database, session.user.uid);
    if (PLATFORMS.has(platform)) entry.platform = platform;
    await db.set(db.ref(database, `waitlist/${feature}/${session.user.uid}`), entry);
    joined.set(feature, true);
  } catch (err) {
    console.warn("Vormerken fehlgeschlagen:", err);
    setMessage(feature, errorText(err), "error");
  } finally {
    busy.delete(feature);
    render();
  }
}

async function leave(feature) {
  if (!session?.user || busy.has(feature)) return;
  busy.add(feature);
  setMessage(feature, "");
  render();
  try {
    const { db, database } = await getDb(session.app);
    await db.remove(db.ref(database, `waitlist/${feature}/${session.user.uid}`));
    joined.set(feature, false);
    setMessage(feature, T("Du bist ausgetragen."));
  } catch (err) {
    console.warn("Austragen fehlgeschlagen:", err);
    setMessage(feature, errorText(err), "error");
  } finally {
    busy.delete(feature);
    render();
  }
}

for (const box of boxes) {
  const feature = box.dataset.waitlist;
  box.querySelector("[data-waitlist-join]").addEventListener("click", () => join(feature));
  box.querySelector("[data-waitlist-leave]").addEventListener("click", () => leave(feature));
}

function onAuth(detail) {
  const previous = session?.user?.uid;
  session = detail && detail.user ? detail : null;
  if (session?.user?.uid !== previous) {
    joined.clear();
    messages.clear();
  }
  render();
  if (!session?.user) return;
  for (const box of boxes) {
    const feature = box.dataset.waitlist;
    if (pending.delete(feature)) join(feature);
    else load(feature);
  }
}

if (boxes.length) {
  document.addEventListener("sge:auth", (e) => onAuth(e.detail));
  document.addEventListener("sge:language", render);
  if (window.sgeAuth) onAuth(window.sgeAuth);
  render();
}
