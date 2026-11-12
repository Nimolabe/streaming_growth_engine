// ============================================================
//  Profilseite
//  profil.html            → eigenes Profil (anmelden nötig), bearbeiten
//  profil.html?u=name     → öffentliches Profil eines Streamers
// ============================================================
import {
  getProfile, uidForUsername, saveProfile, isUsernameFree, usernameProblem,
  followInfo, setFollow, avatarStyle, initials, escapeHtml, profileUrl, PLATFORMS, askForUsername,
} from "./social.js";

const T = (s) => (window.SGE_I18N ? window.SGE_I18N.t(s) : s);
const root = document.getElementById("profile-root");
const wanted = new URLSearchParams(location.search).get("u");

let app = null;
let me = null;          // angemeldeter Nutzer (Firebase-User) oder null
let profile = null;     // angezeigtes Profil
let started = false;

function state(html) { root.innerHTML = `<div class="profile-state">${html}</div>`; }

function openAuth(register) {
  document.getElementById("login-btn")?.click();
  if (register) document.querySelector('.auth-tab[data-tab="register"]')?.click();
}

// ---------- Laden ----------
async function load() {
  if (!app) return;
  try {
    let uid = null;
    if (wanted) {
      uid = await uidForUsername(app, wanted);
      if (!uid) {
        state(`<h1>${escapeHtml(T("Profil nicht gefunden"))}</h1><p>${escapeHtml(T("Unter diesem Nutzernamen gibt es kein Profil."))} <strong>@${escapeHtml(wanted)}</strong></p><a class="btn" href="community.html">${escapeHtml(T("Streamer suchen"))}</a>`);
        return;
      }
    } else if (me) {
      uid = me.uid;
    } else {
      state(`<h1>${escapeHtml(T("Dein Profil"))}</h1><p>${escapeHtml(T("Melde dich an, um dein Profil zu sehen und zu bearbeiten."))}</p><div class="profile-state-actions"><button type="button" class="btn" data-act="login">${escapeHtml(T("Anmelden"))}</button><button type="button" class="btn btn-ghost" data-act="register">${escapeHtml(T("Registrieren"))}</button></div>`);
      root.querySelector('[data-act="login"]').addEventListener("click", () => openAuth(false));
      root.querySelector('[data-act="register"]').addEventListener("click", () => openAuth(true));
      return;
    }
    profile = await getProfile(app, uid);
    if (!profile || !profile.username) {
      if (me && uid === me.uid) {
        state(`<h1>${escapeHtml(T("Noch kein Profil"))}</h1><p>${escapeHtml(T("Wähle einen Nutzernamen, damit andere dich finden können."))}</p><button type="button" class="btn" data-act="create">${escapeHtml(T("Profil erstellen"))}</button>`);
        root.querySelector('[data-act="create"]').addEventListener("click", () => askForUsername(app, me));
      } else {
        state(`<h1>${escapeHtml(T("Profil nicht gefunden"))}</h1><a class="btn" href="community.html">${escapeHtml(T("Streamer suchen"))}</a>`);
      }
      return;
    }
    // Eigene Adresse in der Leiste mit Nutzernamen versehen (teilbarer Link)
    if (!wanted && me && profile.uid === me.uid) history.replaceState(null, "", profileUrl(profile.username));
    document.title = `${profile.name} (@${profile.username}) | Streaming Growth Engine`;
    const info = await followInfo(app, profile.uid, me && me.uid);
    view(info);
  } catch (err) {
    console.error("Profil konnte nicht geladen werden (Datenbank-Regeln veröffentlicht?):", err);
    state(`<h1>${escapeHtml(T("Ups"))}</h1><p>${escapeHtml(T("Das Profil konnte gerade nicht geladen werden. Lade die Seite neu."))}</p>`);
  }
}

// ---------- Ansicht ----------
function view(info) {
  const p = profile;
  const mine = me && me.uid === p.uid;
  const platform = PLATFORMS[p.platform] ? T(PLATFORMS[p.platform]) : "–";
  const games = (p.games || "").split(",").map((g) => g.trim()).filter(Boolean);
  const since = new Date(p.createdAt).toLocaleDateString(document.documentElement.lang === "en" ? "en-GB" : "de-DE", { month: "long", year: "numeric" });

  let actions = "";
  if (mine) actions = `<button type="button" class="btn" data-act="edit">${escapeHtml(T("Profil bearbeiten"))}</button>`;
  else if (me) actions = `<button type="button" class="btn ${info.iFollow ? "btn-ghost" : ""}" data-act="follow" aria-pressed="${info.iFollow}">${escapeHtml(info.iFollow ? T("Entfolgen") : T("Folgen"))}</button>`;
  else actions = `<button type="button" class="btn" data-act="login">${escapeHtml(T("Folgen"))}</button>`;
  actions += `<button type="button" class="btn btn-ghost" data-act="share">${escapeHtml(T("Link kopieren"))}</button>`;

  root.innerHTML = `
    <article class="profile">
      <div class="profile-banner" style="${avatarStyle(p.username)}" aria-hidden="true"></div>
      <div class="profile-main">
        <span class="avatar avatar-xl" style="${avatarStyle(p.username)}" aria-hidden="true">${escapeHtml(initials(p.name))}</span>
        <div class="profile-id">
          <h1>${escapeHtml(p.name)}</h1>
          <p class="profile-handle">@${escapeHtml(p.username)}</p>
        </div>
        <div class="profile-actions">${actions}</div>
      </div>
      <p class="profile-bio">${p.bio ? escapeHtml(p.bio) : `<span class="muted">${escapeHtml(mine ? T("Erzähl anderen, was du streamst – über „Profil bearbeiten“.") : T("Noch keine Beschreibung."))}</span>`}</p>
      <dl class="profile-stats">
        <div><dt>${escapeHtml(T("Follower"))}</dt><dd data-followers>${info.followers}</dd></div>
        <div><dt>${escapeHtml(T("Folgt"))}</dt><dd>${info.following}</dd></div>
        <div><dt>${escapeHtml(T("Plattform"))}</dt><dd>${escapeHtml(platform)}</dd></div>
        <div><dt>${escapeHtml(T("Dabei seit"))}</dt><dd>${escapeHtml(since)}</dd></div>
      </dl>
      ${games.length ? `<div class="profile-block"><h2>${escapeHtml(T("Lieblingsspiele"))}</h2><ul class="chips-list">${games.map((g) => `<li>${escapeHtml(g)}</li>`).join("")}</ul></div>` : ""}
      ${p.channel ? `<div class="profile-block"><h2>${escapeHtml(T("Kanal"))}</h2><a class="channel-link" href="${escapeHtml(p.channel)}" target="_blank" rel="noopener nofollow ugc">${escapeHtml(p.channel.replace(/^https:\/\//, ""))}</a></div>` : ""}
      <p class="share-note" role="status"></p>
    </article>`;

  const act = (name, fn) => root.querySelector(`[data-act="${name}"]`)?.addEventListener("click", fn);
  act("edit", edit);
  act("login", () => openAuth(false));
  act("share", async () => {
    const url = new URL(profileUrl(p.username), location.href).href;
    const note = root.querySelector(".share-note");
    try { await navigator.clipboard.writeText(url); note.textContent = T("Link kopiert."); }
    catch { note.textContent = url; }
  });
  act("follow", async (e) => {
    const btn = e.currentTarget;
    const follow = btn.getAttribute("aria-pressed") !== "true";
    btn.disabled = true;
    try {
      await setFollow(app, me.uid, p.uid, follow);
      btn.setAttribute("aria-pressed", String(follow));
      btn.textContent = follow ? T("Entfolgen") : T("Folgen");
      btn.classList.toggle("btn-ghost", follow);
      const el = root.querySelector("[data-followers]");
      el.textContent = Math.max(0, Number(el.textContent) + (follow ? 1 : -1));
    } catch (err) {
      console.error(err);
      root.querySelector(".share-note").textContent = T("Das hat nicht geklappt. Versuche es noch einmal.");
    } finally {
      btn.disabled = false;
    }
  });
}

// ---------- Bearbeiten ----------
function edit() {
  const p = profile;
  const opts = Object.entries(PLATFORMS).map(([k, v]) => `<option value="${k}" ${p.platform === k ? "selected" : ""}>${escapeHtml(T(v))}</option>`).join("");
  root.innerHTML = `
    <form class="profile profile-form" id="edit-form" novalidate>
      <h1>${escapeHtml(T("Profil bearbeiten"))}</h1>
      <p class="auth-message" id="edit-message" hidden></p>
      <div class="form-grid">
        <label class="field"><span>${escapeHtml(T("Nutzername"))}</span>
          <span class="handle-input"><span aria-hidden="true">@</span><input type="text" name="username" maxlength="20" required value="${escapeHtml(p.username)}" autocomplete="username"></span>
          <small class="sge-field-hint" id="username-hint">${escapeHtml(T("3–20 Zeichen: Buchstaben, Zahlen und _"))}</small>
        </label>
        <label class="field"><span>${escapeHtml(T("Anzeigename"))}</span>
          <input type="text" name="name" maxlength="30" required value="${escapeHtml(p.name)}">
        </label>
        <label class="field field-wide"><span>${escapeHtml(T("Über dich"))}</span>
          <textarea name="bio" maxlength="280" rows="4" placeholder="${escapeHtml(T("Was streamst du, wann bist du live?"))}">${escapeHtml(p.bio || "")}</textarea>
          <small class="sge-field-hint"><span data-count>${(p.bio || "").length}</span>/280</small>
        </label>
        <label class="field"><span>${escapeHtml(T("Hauptplattform"))}</span>
          <select name="platform"><option value="">${escapeHtml(T("Keine Angabe"))}</option>${opts}</select>
        </label>
        <label class="field"><span>${escapeHtml(T("Kanal-Link"))}</span>
          <input type="url" name="channel" maxlength="200" placeholder="https://twitch.tv/…" value="${escapeHtml(p.channel || "")}">
        </label>
        <label class="field field-wide"><span>${escapeHtml(T("Lieblingsspiele"))}</span>
          <input type="text" name="games" maxlength="120" placeholder="${escapeHtml(T("z. B. Valorant, Minecraft, EA FC"))}" value="${escapeHtml(p.games || "")}">
          <small class="sge-field-hint">${escapeHtml(T("Mit Komma trennen"))}</small>
        </label>
      </div>
      <div class="form-actions">
        <button type="submit" class="btn">${escapeHtml(T("Speichern"))}</button>
        <button type="button" class="btn btn-ghost" data-act="cancel">${escapeHtml(T("Abbrechen"))}</button>
      </div>
    </form>`;

  const f = document.getElementById("edit-form");
  const msg = document.getElementById("edit-message");
  const hint = document.getElementById("username-hint");
  const say = (t, type = "error") => { msg.textContent = t; msg.className = "auth-message " + type; msg.hidden = !t; };
  f.bio.addEventListener("input", () => { f.querySelector("[data-count]").textContent = f.bio.value.length; });
  f.querySelector('[data-act="cancel"]').addEventListener("click", () => load());

  // Verfügbarkeit des Nutzernamens live prüfen
  let t = null;
  f.username.addEventListener("input", () => {
    clearTimeout(t);
    const name = f.username.value.trim();
    const problem = usernameProblem(name);
    hint.className = "sge-field-hint";
    if (problem) { hint.textContent = problem; hint.classList.add("is-bad"); return; }
    if (name.toLowerCase() === p.usernameLower) { hint.textContent = T("Das ist dein aktueller Nutzername."); return; }
    hint.textContent = T("Wird geprüft …");
    t = setTimeout(async () => {
      const free = await isUsernameFree(app, name, me.uid).catch(() => null);
      if (f.username.value.trim() !== name) return;
      hint.textContent = free === null ? "" : free ? T("Nutzername ist frei.") : T("Dieser Nutzername ist schon vergeben.");
      hint.classList.add(free ? "is-good" : "is-bad");
    }, 350);
  });

  f.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(f).entries());
    const problem = usernameProblem(data.username.trim());
    if (problem) return say(problem);
    if (!data.name.trim()) return say(T("Bitte gib einen Anzeigenamen ein."));
    if (data.channel && !/^https:\/\/.{3,190}$/.test(data.channel.trim())) return say(T("Der Kanal-Link muss mit https:// beginnen."));
    const btn = f.querySelector('button[type="submit"]');
    btn.disabled = true;
    try {
      if (!(await isUsernameFree(app, data.username.trim(), me.uid))) return say(T("Dieser Nutzername ist schon vergeben."));
      profile = await saveProfile(app, me.uid, data, profile);
      const nav = document.getElementById("user-name");
      if (nav) { nav.textContent = "@" + profile.username; nav.href = profileUrl(profile.username); }
      history.replaceState(null, "", profileUrl(profile.username));
      const info = await followInfo(app, profile.uid, me.uid);
      view(info);
      root.querySelector(".share-note").textContent = T("Profil gespeichert.");
    } catch (err) {
      console.error(err);
      say(T("Speichern hat nicht geklappt. Bitte versuche es noch einmal."));
    } finally {
      btn.disabled = false;
    }
  });
  f.username.focus();
}

// ---------- Start ----------
function onAuth(detail) {
  if (!detail || !detail.app) return;
  app = detail.app;
  const before = me && me.uid;
  me = detail.user || null;
  if (!started || before !== (me && me.uid)) { started = true; load(); }
}
document.addEventListener("sge:auth", (e) => onAuth(e.detail));
document.addEventListener("sge:profile", () => { if (!wanted && started && (!profile || !profile.username)) load(); });
if (window.sgeAuth) onAuth(window.sgeAuth);
setTimeout(() => { if (!app) state(`<h1>${escapeHtml(T("Ups"))}</h1><p>${escapeHtml(T("Das Profil konnte gerade nicht geladen werden. Lade die Seite neu."))}</p>`); }, 10000);
