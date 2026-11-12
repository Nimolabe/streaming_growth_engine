// ============================================================
//  Social-Funktionen: Nutzernamen, öffentliche Profile, Suche, Folgen
//  Datenbank-Struktur (Realtime Database, Regeln in database.rules.json):
//    usernames/<name in Kleinbuchstaben> = uid        (macht Nutzernamen eindeutig)
//    profiles/<uid> = { name, nameLower, username, usernameLower,
//                       bio, platform, channel, games, createdAt }
//    following/<uid>/<zielUid> = true
//    followers/<zielUid>/<uid> = true
// ============================================================
const SDK = "https://www.gstatic.com/firebasejs/10.12.2";
const T = (s) => (window.SGE_I18N ? window.SGE_I18N.t(s) : s);

let mod = null;
let database = null;
export async function getDb(app) {
  if (!mod) mod = await import(`${SDK}/firebase-database.js`);
  if (!database) database = mod.getDatabase(app);
  return { db: mod, database };
}

// ---------- Nutzernamen ----------
export const USERNAME_RE = /^[A-Za-z0-9_]{3,20}$/;
export const PLATFORMS = {
  twitch: "Twitch", youtube: "YouTube", kick: "Kick", tiktok: "TikTok", andere: "Andere",
};

export function usernameProblem(name) {
  if (!name) return T("Bitte wähle einen Nutzernamen.");
  if (name.length < 3 || name.length > 20) return T("Der Nutzername muss 3 bis 20 Zeichen lang sein.");
  if (!USERNAME_RE.test(name)) return T("Erlaubt sind nur Buchstaben, Zahlen und Unterstrich (_).");
  return "";
}

export async function isUsernameFree(app, name, myUid = null) {
  const { db, database } = await getDb(app);
  const snap = await db.get(db.ref(database, `usernames/${name.toLowerCase()}`));
  return !snap.exists() || (myUid && snap.val() === myUid);
}

export async function uidForUsername(app, name) {
  const { db, database } = await getDb(app);
  const snap = await db.get(db.ref(database, `usernames/${String(name).toLowerCase()}`));
  return snap.exists() ? snap.val() : null;
}

// ---------- Profile ----------
export async function getProfile(app, uid) {
  const { db, database } = await getDb(app);
  const snap = await db.get(db.ref(database, `profiles/${uid}`));
  return snap.exists() ? { uid, ...snap.val() } : null;
}

// Speichert das Profil und reserviert den Nutzernamen in einem Schritt.
// Wird der Nutzername geändert, wird der alte freigegeben.
export async function saveProfile(app, uid, data, previous = null) {
  const { db, database } = await getDb(app);
  const username = data.username.trim();
  const lower = username.toLowerCase();
  const name = (data.name || username).trim().slice(0, 30);
  const profile = {
    name,
    nameLower: name.toLowerCase(),
    username,
    usernameLower: lower,
    bio: (data.bio || "").trim().slice(0, 280),
    platform: data.platform || "",
    channel: (data.channel || "").trim(),
    games: (data.games || "").trim().slice(0, 120),
    createdAt: previous && previous.createdAt ? previous.createdAt : Date.now(),
  };
  const updates = {
    [`profiles/${uid}`]: profile,
    [`usernames/${lower}`]: uid,
  };
  if (previous && previous.usernameLower && previous.usernameLower !== lower) {
    updates[`usernames/${previous.usernameLower}`] = null;
  }
  await db.update(db.ref(database), updates);
  return { uid, ...profile };
}

// Suche nach Nutzername oder Anzeigename (Anfang des Namens, ohne Groß/Klein)
export async function searchProfiles(app, query, limit = 20) {
  const q = query.trim().toLowerCase().replace(/^@/, "");
  if (!q) return [];
  const { db, database } = await getDb(app);
  const base = db.ref(database, "profiles");
  const byField = (field) => db.get(db.query(base, db.orderByChild(field), db.startAt(q), db.endAt(q + ""), db.limitToFirst(limit)));
  const [a, b] = await Promise.all([byField("usernameLower"), byField("nameLower")]);
  const found = new Map();
  [a, b].forEach((snap) => snap.forEach((child) => { found.set(child.key, { uid: child.key, ...child.val() }); }));
  return [...found.values()]
    .sort((x, y) => (x.usernameLower.startsWith(q) ? 0 : 1) - (y.usernameLower.startsWith(q) ? 0 : 1) || x.usernameLower.localeCompare(y.usernameLower))
    .slice(0, limit);
}

export async function latestProfiles(app, limit = 12) {
  const { db, database } = await getDb(app);
  const snap = await db.get(db.query(db.ref(database, "profiles"), db.orderByChild("createdAt"), db.limitToLast(limit)));
  const list = [];
  snap.forEach((child) => { list.push({ uid: child.key, ...child.val() }); });
  return list.reverse();
}

// ---------- Folgen ----------
export async function setFollow(app, me, target, follow) {
  const { db, database } = await getDb(app);
  const value = follow ? true : null;
  // Zuerst "following" (die Regel für "followers" prüft diesen Eintrag)
  if (follow) {
    await db.set(db.ref(database, `following/${me}/${target}`), true);
    await db.set(db.ref(database, `followers/${target}/${me}`), true);
  } else {
    await db.set(db.ref(database, `followers/${target}/${me}`), value);
    await db.set(db.ref(database, `following/${me}/${target}`), value);
  }
}

export async function followInfo(app, uid, me = null) {
  const { db, database } = await getDb(app);
  const [followers, following] = await Promise.all([
    db.get(db.ref(database, `followers/${uid}`)),
    db.get(db.ref(database, `following/${uid}`)),
  ]);
  return {
    followers: followers.exists() ? Object.keys(followers.val()).length : 0,
    following: following.exists() ? Object.keys(following.val()).length : 0,
    iFollow: !!(me && followers.exists() && followers.val()[me]),
  };
}

// ---------- Darstellung ----------
export function avatarStyle(username = "") {
  let h = 0;
  for (const c of username.toLowerCase()) h = (h * 31 + c.charCodeAt(0)) % 360;
  return `background: linear-gradient(135deg, hsl(${h} 70% 62%), hsl(${(h + 50) % 360} 70% 45%));`;
}
export function initials(name = "?") {
  return name.trim().split(/\s+/).map((w) => w[0]).join("").slice(0, 2).toUpperCase() || "?";
}
export function escapeHtml(s = "") {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
export function profileUrl(username) {
  return `profil.html?u=${encodeURIComponent(username)}`;
}

// Profilkarte für Suche und Listen
export function profileCard(p) {
  const platform = PLATFORMS[p.platform] ? `<span class="pc-platform pf-${p.platform}">${escapeHtml(T(PLATFORMS[p.platform]))}</span>` : "";
  return `<a class="profile-card" href="${profileUrl(p.username)}">
    <span class="avatar" style="${avatarStyle(p.username)}" aria-hidden="true">${escapeHtml(initials(p.name))}</span>
    <span class="pc-text"><strong>${escapeHtml(p.name)}</strong><span class="pc-handle">@${escapeHtml(p.username)}</span></span>
    ${platform}
  </a>`;
}

// ============================================================
//  Nutzername nachholen: Wer angemeldet ist, aber noch keinen
//  Nutzernamen hat (z. B. nach Google-Anmeldung), wird einmal gefragt.
// ============================================================
let signupPromise = null;
let signupResolve = null;
export function beginSignup() { signupPromise = new Promise((r) => { signupResolve = r; }); }
export function endSignup() { if (signupResolve) signupResolve(); signupPromise = null; signupResolve = null; }

export let myProfile = null;

function navProfileLink(profile) {
  const el = document.getElementById("user-name");
  if (!el) return;
  if (profile) {
    el.textContent = "@" + profile.username;
    if (el.tagName === "A") el.href = profileUrl(profile.username);
  }
}

function onboardingDialog(app, user) {
  if (document.getElementById("username-modal")) return;
  const suggestion = (user.displayName || (user.email || "").split("@")[0] || "")
    .replace(/[^A-Za-z0-9_]/g, "").slice(0, 20);
  const wrap = document.createElement("div");
  wrap.className = "modal";
  wrap.id = "username-modal";
  wrap.innerHTML = `
    <div class="modal-backdrop"></div>
    <div class="modal-box" role="dialog" aria-modal="true" aria-labelledby="un-title" data-lenis-prevent>
      <h2 id="un-title">Wähle deinen Nutzernamen</h2>
      <p class="modal-lead">Damit andere dich finden können, braucht jedes Profil einen eigenen Nutzernamen.</p>
      <p class="auth-message" id="un-message" hidden></p>
      <form id="un-form" novalidate>
        <label class="field"><span>Nutzername</span>
          <span class="handle-input"><span aria-hidden="true">@</span><input type="text" id="un-username" maxlength="20" autocomplete="username" required></span>
          <small class="sge-field-hint">3–20 Zeichen: Buchstaben, Zahlen und _</small>
        </label>
        <label class="field"><span>Anzeigename</span>
          <input type="text" id="un-name" maxlength="30" autocomplete="nickname">
        </label>
        <button type="submit" class="btn btn-block" id="un-submit">Profil erstellen</button>
      </form>
      <button type="button" class="link-btn un-later" id="un-later">Später</button>
    </div>`;
  document.body.appendChild(wrap);
  const $ = (id) => document.getElementById(id);
  $("un-username").value = suggestion.length >= 3 ? suggestion : "";
  $("un-name").value = user.displayName || "";
  const msg = (t) => { $("un-message").textContent = t; $("un-message").className = "auth-message error"; $("un-message").hidden = !t; };
  const close = () => { wrap.remove(); document.body.style.overflow = ""; if (window.lenis) window.lenis.start(); };
  document.body.style.overflow = "hidden";
  if (window.lenis) window.lenis.stop();
  $("un-later").addEventListener("click", close);
  $("un-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = $("un-username").value.trim();
    const problem = usernameProblem(username);
    if (problem) return msg(problem);
    $("un-submit").disabled = true;
    try {
      if (!(await isUsernameFree(app, username, user.uid))) return msg(T("Dieser Nutzername ist schon vergeben."));
      myProfile = await saveProfile(app, user.uid, { username, name: $("un-name").value.trim() || username });
      navProfileLink(myProfile);
      document.dispatchEvent(new CustomEvent("sge:profile", { detail: myProfile }));
      close();
    } catch (err) {
      console.error(err);
      msg(T("Speichern hat nicht geklappt. Bitte versuche es noch einmal."));
    } finally {
      $("un-submit").disabled = false;
    }
  });
  setTimeout(() => $("un-username").focus(), 50);
}

document.addEventListener("sge:auth", async (e) => {
  const { user, app } = e.detail || {};
  myProfile = null;
  if (!user || !app) return;
  if (signupPromise) await signupPromise;
  try {
    myProfile = await getProfile(app, user.uid);
    if (myProfile && myProfile.username) navProfileLink(myProfile);
    document.dispatchEvent(new CustomEvent("sge:profile", { detail: myProfile }));
    const asked = sessionStorage.getItem("sge-username-asked") === user.uid;
    if ((!myProfile || !myProfile.username) && !asked) {
      sessionStorage.setItem("sge-username-asked", user.uid);
      onboardingDialog(app, user);
    }
  } catch (err) {
    console.error("Profil konnte nicht geladen werden:", err);
  }
});

// Für Seiten, die den Dialog gezielt öffnen wollen (z. B. Profilseite)
export function askForUsername(app, user) { onboardingDialog(app, user); }
