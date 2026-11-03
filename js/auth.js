// ============================================================
//  Anmeldung mit Firebase Authentication
//  (E-Mail/Passwort + Google)
// ============================================================
import { firebaseConfig } from "./firebase-config.js";

const SDK = "https://www.gstatic.com/firebasejs/10.12.2";

// ---------- Elemente ----------
const $ = (id) => document.getElementById(id);
const modal = $("auth-modal");
const title = $("auth-title");
const form = $("auth-form");
const nameField = $("name-field");
const nameInput = $("auth-name");
const emailInput = $("auth-email");
const passwordInput = $("auth-password");
const submitBtn = $("auth-submit");
const forgotBtn = $("forgot-btn");
const googleBtn = $("google-btn");
const message = $("auth-message");
const loginBtn = $("login-btn");
const userMenu = $("user-menu");
const userName = $("user-name");
const logoutBtn = $("logout-btn");

let mode = "login"; // "login" | "register"
let auth = null;
let fb = null; // Firebase-Auth-Funktionen

// ---------- Fenster öffnen / schließen ----------
function openModal(newMode = "login") {
  setMode(newMode);
  hideMessage();
  modal.hidden = false;
  document.body.style.overflow = "hidden";
  setTimeout(() => (mode === "register" ? nameInput : emailInput).focus(), 50);
}
function closeModal() {
  modal.hidden = true;
  document.body.style.overflow = "";
  form.reset();
}
function setMode(newMode) {
  mode = newMode;
  const isReg = mode === "register";
  title.textContent = isReg ? "Account erstellen" : "Willkommen zurück";
  submitBtn.textContent = isReg ? "Registrieren" : "Anmelden";
  nameField.hidden = !isReg;
  forgotBtn.hidden = isReg;
  passwordInput.autocomplete = isReg ? "new-password" : "current-password";
  document.querySelectorAll(".auth-tab").forEach((t) =>
    t.classList.toggle("active", t.dataset.tab === mode)
  );
  hideMessage();
}

document.querySelectorAll("[data-open-auth]").forEach((el) =>
  el.addEventListener("click", () => openModal(el.dataset.openAuth))
);
document.querySelectorAll("[data-close-auth]").forEach((el) =>
  el.addEventListener("click", closeModal)
);
document.querySelectorAll(".auth-tab").forEach((t) =>
  t.addEventListener("click", () => setMode(t.dataset.tab))
);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !modal.hidden) closeModal();
});

// ---------- Meldungen ----------
function showMessage(text, type = "error") {
  message.textContent = text;
  message.className = "auth-message " + type;
  message.hidden = false;
}
function hideMessage() {
  message.hidden = true;
}
function setBusy(busy) {
  [submitBtn, googleBtn, forgotBtn].forEach((b) => (b.disabled = busy));
}

const ERRORS = {
  "auth/invalid-email": "Diese E-Mail-Adresse ist ungültig.",
  "auth/missing-email": "Bitte gib deine E-Mail-Adresse ein.",
  "auth/missing-password": "Bitte gib ein Passwort ein.",
  "auth/weak-password": "Das Passwort muss mindestens 6 Zeichen haben.",
  "auth/email-already-in-use": "Mit dieser E-Mail gibt es schon einen Account. Melde dich an.",
  "auth/invalid-credential": "E-Mail oder Passwort ist falsch.",
  "auth/wrong-password": "E-Mail oder Passwort ist falsch.",
  "auth/user-not-found": "E-Mail oder Passwort ist falsch.",
  "auth/too-many-requests": "Zu viele Versuche. Bitte warte kurz.",
  "auth/popup-closed-by-user": "Google-Anmeldung abgebrochen.",
  "auth/popup-blocked": "Das Popup wurde blockiert. Bitte erlaube Popups für diese Seite.",
  "auth/network-request-failed": "Keine Verbindung. Prüfe dein Internet.",
  "auth/operation-not-allowed": "Diese Anmeldemethode ist in Firebase noch nicht aktiviert.",
  "auth/unauthorized-domain": "Diese Domain ist in Firebase nicht freigegeben (Authentication → Einstellungen → Autorisierte Domains).",
};
const errorText = (err) => ERRORS[err.code] || "Etwas ist schiefgelaufen: " + (err.message || err);

// ---------- Firebase laden ----------
const configMissing = Object.values(firebaseConfig).some((v) => String(v).includes("HIER_EINFUEGEN"));

async function initFirebase() {
  if (configMissing) {
    console.warn("Firebase ist noch nicht konfiguriert → js/firebase-config.js ausfüllen.");
    return;
  }
  try {
    const { initializeApp } = await import(`${SDK}/firebase-app.js`);
    fb = await import(`${SDK}/firebase-auth.js`);
    const app = initializeApp(firebaseConfig);
    auth = fb.getAuth(app);
    auth.languageCode = "de";
    fb.onAuthStateChanged(auth, (user) => {
      updateUI(user);
      // Andere Seiten-Skripte (z. B. Favoriten auf setups.html) informieren
      window.sgeAuth = { user, app };
      document.dispatchEvent(new CustomEvent("sge:auth", { detail: window.sgeAuth }));
    });
  } catch (err) {
    console.error("Firebase konnte nicht geladen werden:", err);
  }
}

function ready() {
  if (auth) return true;
  showMessage(
    configMissing
      ? "Die Anmeldung ist noch nicht eingerichtet (Firebase-Konfiguration fehlt)."
      : "Die Anmeldung konnte nicht geladen werden. Bitte lade die Seite neu."
  );
  return false;
}

// ---------- Navigation anpassen ----------
function updateUI(user) {
  if (user) {
    userName.textContent = user.displayName || user.email;
    loginBtn.hidden = true;
    userMenu.hidden = false;
  } else {
    loginBtn.hidden = false;
    userMenu.hidden = true;
  }
}

// ---------- Aktionen ----------
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!ready()) return;
  const email = emailInput.value.trim();
  const password = passwordInput.value;
  const name = nameInput.value.trim();

  if (mode === "register" && !name) return showMessage("Bitte gib einen Streamer-Namen ein.");

  setBusy(true);
  try {
    if (mode === "register") {
      const cred = await fb.createUserWithEmailAndPassword(auth, email, password);
      await fb.updateProfile(cred.user, { displayName: name });
      updateUI(cred.user);
    } else {
      await fb.signInWithEmailAndPassword(auth, email, password);
    }
    closeModal();
  } catch (err) {
    showMessage(errorText(err));
  } finally {
    setBusy(false);
  }
});

googleBtn.addEventListener("click", async () => {
  if (!ready()) return;
  setBusy(true);
  try {
    await fb.signInWithPopup(auth, new fb.GoogleAuthProvider());
    closeModal();
  } catch (err) {
    showMessage(errorText(err));
  } finally {
    setBusy(false);
  }
});

forgotBtn.addEventListener("click", async () => {
  if (!ready()) return;
  const email = emailInput.value.trim();
  if (!email) return showMessage("Gib zuerst deine E-Mail-Adresse ein.");
  setBusy(true);
  try {
    await fb.sendPasswordResetEmail(auth, email);
    showMessage("Falls ein Account existiert, haben wir dir eine E-Mail zum Zurücksetzen geschickt.", "success");
  } catch (err) {
    showMessage(errorText(err));
  } finally {
    setBusy(false);
  }
});

logoutBtn.addEventListener("click", () => auth && fb.signOut(auth));

initFirebase();
