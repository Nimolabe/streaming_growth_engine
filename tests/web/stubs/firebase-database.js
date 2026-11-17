// Nachbau von firebase-database.js für die Browser-Tests.
// Die Daten liegen als JSON im localStorage ("__sgeDb").
// window.__deny = true lässt jede Anfrage mit PERMISSION_DENIED scheitern
// (wie bei noch nicht veröffentlichten Firebase-Regeln).
const KEY = "__sgeDb";
const TIMESTAMP = { ".sv": "timestamp" };

function load() {
  try { return JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch { return {}; }
}
function store(data) {
  localStorage.setItem(KEY, JSON.stringify(data ?? {}));
}
const parts = (path) => String(path || "").split("/").filter(Boolean);
const clone = (v) => (v === undefined ? null : JSON.parse(JSON.stringify(v)));

function check() {
  if (window.__deny) {
    const err = new Error("PERMISSION_DENIED: Permission denied");
    err.code = "PERMISSION_DENIED";
    throw err;
  }
}

function resolve(value) {
  if (value && typeof value === "object") {
    if (value[".sv"] === "timestamp") return Date.now();
    const out = Array.isArray(value) ? [] : {};
    for (const [k, v] of Object.entries(value)) {
      const r = resolve(v);
      if (r !== null && r !== undefined) out[k] = r;
    }
    return Object.keys(out).length ? out : null;
  }
  return value === undefined ? null : value;
}

function getAt(data, path) {
  let node = data;
  for (const p of parts(path)) {
    if (node === null || typeof node !== "object" || !(p in node)) return null;
    node = node[p];
  }
  return node ?? null;
}

function setAt(data, path, value) {
  const keys = parts(path);
  if (!keys.length) return resolve(value) || {};
  const chain = [data];
  let node = data;
  for (const k of keys.slice(0, -1)) {
    if (node[k] === null || typeof node[k] !== "object") node[k] = {};
    node = node[k];
    chain.push(node);
  }
  const last = keys[keys.length - 1];
  const v = resolve(value);
  if (v === null) delete node[last];
  else node[last] = v;
  // Leere Zwischenknoten entfernen (wie Firebase)
  for (let i = keys.length - 2; i >= 0; i--) {
    if (Object.keys(chain[i + 1]).length) break;
    delete chain[i][keys[i]];
  }
  return data;
}

function snapshot(key, value, order = null) {
  const val = clone(value);
  return {
    key,
    exists: () => val !== null,
    val: () => clone(val),
    forEach(cb) {
      if (val === null || typeof val !== "object") return false;
      for (const k of order || Object.keys(val)) {
        if (cb(snapshot(k, val[k])) === true) return true;
      }
      return false;
    },
  };
}

export function getDatabase(app) {
  return { app };
}
export function ref(database, path = "") {
  const keys = parts(path);
  return { database, path: keys.join("/"), key: keys.length ? keys[keys.length - 1] : null, constraints: [] };
}
export function serverTimestamp() {
  return { ...TIMESTAMP };
}

export const orderByChild = (field) => ({ type: "orderByChild", field });
export const startAt = (value) => ({ type: "startAt", value });
export const endAt = (value) => ({ type: "endAt", value });
export const limitToFirst = (n) => ({ type: "limitToFirst", n });
export const limitToLast = (n) => ({ type: "limitToLast", n });
export function query(r, ...constraints) {
  return { ...r, constraints: [...(r.constraints || []), ...constraints] };
}

function compare(a, b) {
  const rank = (v) => (v === null || v === undefined ? 0 : typeof v === "boolean" ? 1 : typeof v === "number" ? 2 : 3);
  return rank(a) - rank(b) || (a < b ? -1 : a > b ? 1 : 0);
}

export async function get(r) {
  check();
  const value = getAt(load(), r.path);
  if (!r.constraints.length || value === null || typeof value !== "object") return snapshot(r.key, value);
  let field = null;
  let entries = Object.entries(value);
  for (const c of r.constraints) if (c.type === "orderByChild") field = c.field;
  const of = ([k, v]) => (field ? (v && typeof v === "object" ? v[field] ?? null : null) : k);
  entries.sort((x, y) => compare(of(x), of(y)) || (x[0] < y[0] ? -1 : 1));
  for (const c of r.constraints) {
    if (c.type === "startAt") entries = entries.filter((e) => compare(of(e), c.value) >= 0);
    if (c.type === "endAt") entries = entries.filter((e) => compare(of(e), c.value) <= 0);
  }
  for (const c of r.constraints) {
    if (c.type === "limitToFirst") entries = entries.slice(0, c.n);
    if (c.type === "limitToLast") entries = entries.slice(-c.n);
  }
  return snapshot(r.key, Object.fromEntries(entries), entries.map(([k]) => k));
}

export async function set(r, value) {
  check();
  store(setAt(load(), r.path, value));
}
export async function remove(r) {
  check();
  store(setAt(load(), r.path, null));
}
export async function update(r, values) {
  check();
  let data = load();
  for (const [path, value] of Object.entries(values || {})) {
    data = setAt(data, [r.path, path].filter(Boolean).join("/"), value);
  }
  store(data);
}
