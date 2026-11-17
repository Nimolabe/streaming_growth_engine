// Nachbau von firebase-auth.js für die Browser-Tests.
// Anmelden im Test: window.__setUser({ uid: "u1", displayName: "Anna" }); abmelden: window.__setUser(null).
// Der Nutzer bleibt im localStorage ("__sgeUser"), damit er einen Seitenwechsel übersteht.
const KEY = "__sgeUser";
const listeners = new Set();
const auths = [];

function stored() {
  try { return JSON.parse(localStorage.getItem(KEY) || "null"); } catch { return null; }
}
function makeUser(u) {
  if (!u) return null;
  return { email: null, displayName: null, emailVerified: true, ...u, uid: String(u.uid) };
}

let current = makeUser(stored());

function notify() {
  auths.forEach((a) => { a.currentUser = current; });
  listeners.forEach((cb) => cb(current));
}

window.__setUser = (u) => {
  current = makeUser(u);
  if (current) localStorage.setItem(KEY, JSON.stringify(current));
  else localStorage.removeItem(KEY);
  notify();
  return current;
};

export function getAuth(app) {
  const auth = { app, currentUser: current, languageCode: null };
  auths.push(auth);
  return auth;
}
export function onAuthStateChanged(auth, cb) {
  listeners.add(cb);
  setTimeout(() => cb(current), 0);
  return () => listeners.delete(cb);
}
export async function signOut() {
  window.__setUser(null);
}
export class GoogleAuthProvider {}

function notAvailable() {
  const err = new Error("Im Test nicht verfügbar – window.__setUser() verwenden.");
  err.code = "auth/operation-not-allowed";
  return Promise.reject(err);
}
export const signInWithEmailAndPassword = notAvailable;
export const createUserWithEmailAndPassword = notAvailable;
export const signInWithPopup = notAvailable;
export const sendPasswordResetEmail = notAvailable;
export async function updateProfile(user, data) {
  Object.assign(user, data);
}
