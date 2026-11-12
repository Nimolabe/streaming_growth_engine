// ============================================================
//  Community-Seite: Profile suchen und neue Streamer entdecken
// ============================================================
import { searchProfiles, latestProfiles, profileCard, profileUrl, escapeHtml, myProfile } from "./social.js";

const T = (s) => (window.SGE_I18N ? window.SGE_I18N.t(s) : s);
const input = document.getElementById("search-input");
const form = document.getElementById("search-form");
const list = document.getElementById("results");
const status = document.getElementById("results-status");
const title = document.getElementById("results-title");
const meCta = document.getElementById("me-cta");

let app = null;
let latest = null;
let requestId = 0;

function render(profiles) {
  list.innerHTML = profiles.map(profileCard).join("");
}

async function showLatest() {
  title.textContent = T("Neu dabei");
  status.textContent = T("Wird geladen …");
  try {
    latest = latest || (await latestProfiles(app, 12));
    render(latest);
    status.textContent = latest.length ? "" : T("Noch keine Profile. Sei der Erste!");
  } catch (err) {
    console.error("Profile konnten nicht geladen werden (Datenbank-Regeln veröffentlicht?):", err);
    status.textContent = T("Profile konnten gerade nicht geladen werden. Lade die Seite neu.");
  }
}

async function search(q) {
  const id = ++requestId;
  title.textContent = T("Suchergebnisse");
  status.textContent = T("Suche läuft …");
  try {
    const results = await searchProfiles(app, q);
    if (id !== requestId) return; // eine neuere Suche ist schon unterwegs
    render(results);
    status.textContent = results.length
      ? (results.length === 1 ? T("1 Profil gefunden") : `${results.length} ${T("Profile gefunden")}`)
      : `${T("Kein Profil gefunden für")} „${q}“.`;
  } catch (err) {
    if (id !== requestId) return;
    console.error(err);
    status.textContent = T("Die Suche hat nicht geklappt. Versuche es noch einmal.");
  }
}

let timer = null;
function onInput() {
  clearTimeout(timer);
  const q = input.value.trim();
  if (!app) return;
  if (!q) { requestId++; showLatest(); return; }
  timer = setTimeout(() => search(q), 250);
}
input.addEventListener("input", onInput);
form.addEventListener("submit", (e) => { e.preventDefault(); clearTimeout(timer); const q = input.value.trim(); if (q && app) search(q); });

// Hinweis auf das eigene Profil
function updateMe(user, profile) {
  if (!user) {
    meCta.hidden = false;
    meCta.innerHTML = `<p>${escapeHtml(T("Erstelle dein Profil, damit andere dich finden."))}</p><button type="button" class="btn btn-small" data-open-auth="register">${escapeHtml(T("Kostenlos registrieren"))}</button>`;
    // Anmeldefenster öffnen und direkt auf "Registrieren" stellen
    meCta.querySelector("[data-open-auth]").addEventListener("click", () => {
      document.getElementById("login-btn")?.click();
      document.querySelector('.auth-tab[data-tab="register"]')?.click();
    });
  } else if (profile && profile.username) {
    meCta.hidden = false;
    meCta.innerHTML = `<p>${escapeHtml(T("Angemeldet als"))} <strong>@${escapeHtml(profile.username)}</strong></p><a class="btn btn-small btn-ghost" href="${profileUrl(profile.username)}">${escapeHtml(T("Mein Profil"))}</a>`;
  } else {
    meCta.hidden = true;
  }
}

let currentUser = null;
function start(detail) {
  if (!detail || !detail.app) return;
  currentUser = detail.user;
  const first = !app;
  app = detail.app;
  updateMe(currentUser, myProfile);
  if (first) {
    const q = new URLSearchParams(location.search).get("q");
    if (q) { input.value = q; search(q); } else showLatest();
  }
}
document.addEventListener("sge:auth", (e) => start(e.detail));
document.addEventListener("sge:profile", (e) => updateMe(currentUser, e.detail));
if (window.sgeAuth) start(window.sgeAuth);
status.textContent = T("Wird geladen …");
setTimeout(() => { if (!app) status.textContent = T("Profile konnten gerade nicht geladen werden. Lade die Seite neu."); }, 10000);
