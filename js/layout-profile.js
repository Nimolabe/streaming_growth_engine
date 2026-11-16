// ============================================================
//  Layouts im Profil teilen (Realtime Database)
//    layouts/<uid> = { params, updatedAt }   – für alle lesbar, nur der Besitzer schreibt
//  „params“ sind die URL-Parameter des Baukastens. Sie werden beim Anzeigen
//  immer neu geprüft (SGE_LAYOUT.fromSearch), nie ungeprüft verwendet.
// ============================================================
import { getDb } from "./social.js";

export const MAX_PARAMS = 2000;

export async function loadLayout(app, uid) {
  const { db, database } = await getDb(app);
  const snap = await db.get(db.ref(database, `layouts/${uid}/params`));
  return snap.exists() && typeof snap.val() === "string" ? snap.val() : null;
}

export async function saveLayout(app, uid, params) {
  if (params.length > MAX_PARAMS) throw new Error("too-long");
  const { db, database } = await getDb(app);
  await db.set(db.ref(database, `layouts/${uid}`), { params, updatedAt: db.serverTimestamp() });
}

export async function removeLayout(app, uid) {
  const { db, database } = await getDb(app);
  await db.remove(db.ref(database, `layouts/${uid}`));
}

// Gespeicherte Parameter → geprüfte, neu erzeugte Parameter (oder null)
export function sanitize(params, scene) {
  const L = window.SGE_LAYOUT;
  if (!L || typeof params !== "string") return null;
  return L.toParams(L.fromSearch("?" + params), scene).toString();
}
