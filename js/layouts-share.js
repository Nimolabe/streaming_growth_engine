// ============================================================
//  Layout-Baukasten: Design im eigenen Profil zeigen
// ============================================================
import { loadLayout, saveLayout, removeLayout } from "./layout-profile.js";

const T = (s) => (window.SGE_I18N ? window.SGE_I18N.t(s) : s);
const $ = (id) => document.getElementById(id);
const save = $("profile-save");
const remove = $("profile-remove");
const status = $("profile-status");

let session = null;
let shared = false;
let busy = false;
let message = null; // { text, type, link }

function render() {
  save.textContent = T(shared ? "Im Profil aktualisieren" : "Im Profil zeigen");
  remove.textContent = T("Aus dem Profil entfernen");
  remove.hidden = !(session?.user && shared);
  save.disabled = remove.disabled = busy;
  status.replaceChildren();
  status.dataset.type = message?.type || "info";
  let text = message?.text;
  if (!text && session?.user && shared) text = "Dein Layout ist in deinem Profil sichtbar.";
  if (!text) return;
  status.append(T(text));
  if (message?.link || (!message && shared)) {
    const link = document.createElement("a");
    link.href = "profil.html";
    link.textContent = " " + T("Zum Profil →");
    status.appendChild(link);
  }
}

function errorText(err) {
  const code = String(err?.code || err?.message || "").toUpperCase();
  if (code.includes("PERMISSION_DENIED")) return "Das Teilen im Profil wird gerade eingerichtet. Bitte versuch es später noch einmal.";
  if (code.includes("TOO-LONG")) return "Die Texte sind zu lang für das Profil. Bitte kürzen.";
  return "Speichern fehlgeschlagen. Bitte versuch es noch einmal.";
}

async function run(task, success) {
  if (busy) return;
  busy = true;
  message = null;
  render();
  try {
    await task();
    message = success;
  } catch (err) {
    console.warn("Layout im Profil:", err);
    message = { text: errorText(err), type: "error" };
  } finally {
    busy = false;
    render();
  }
}

save.addEventListener("click", () => {
  if (!session?.user) {
    message = { text: "Melde dich an, um dein Layout im Profil zu zeigen." };
    render();
    document.getElementById("login-btn")?.click();
    return;
  }
  const L = window.SGE_LAYOUT;
  const params = L.toParams(window.SGE_LAYOUT_EXPORT.read()).toString();
  run(async () => {
    await saveLayout(session.app, session.user.uid, params);
    shared = true;
  }, { text: "Gespeichert ✓ – andere sehen dein Layout jetzt in deinem Profil.", type: "success", link: true });
});

remove.addEventListener("click", () => {
  if (!session?.user) return;
  run(async () => {
    await removeLayout(session.app, session.user.uid);
    shared = false;
  }, { text: "Entfernt." });
});

async function onAuth(detail) {
  const uid = detail?.user?.uid;
  session = uid ? detail : null;
  shared = false;
  message = null;
  render();
  if (!uid) return;
  try {
    const params = await loadLayout(session.app, uid);
    if (session?.user?.uid !== uid) return;
    shared = params !== null;
  } catch (err) {
    console.warn("Layout im Profil konnte nicht geladen werden:", err);
  }
  render();
}

document.addEventListener("sge:auth", (e) => onAuth(e.detail));
document.addEventListener("sge:language", render);
if (window.sgeAuth) onAuth(window.sgeAuth);
render();
