// ============================================================
//  Admin-Seite des Setup-Agenten
//  Liest Firestore (nur mit Admin-Recht, siehe firestore.rules) und schreibt ausschließlich
//  Vorschläge (change_proposals). Übernommen werden sie vom Agenten (stündlicher Lauf),
//  der dabei prüft und alles im Änderungsprotokoll festhält.
// ============================================================
const SDK = "https://www.gstatic.com/firebasejs/10.12.2";
const $ = (id) => document.getElementById(id);
const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const euro = (cents) => (cents == null ? "unbekannt" : (cents / 100).toLocaleString("de-DE", { style: "currency", currency: "EUR" }));
const when = (iso) => (iso ? new Date(iso).toLocaleString("de-DE", { dateStyle: "medium", timeStyle: "short" }) : "–");
const nowIso = () => new Date().toISOString();

const CATEGORIES = { gaming: "Gaming", chatting: "Just Chatting", irl: "IRL", music: "Musik", creative: "Kreativ / Art" };
const PLATFORMS = ["twitch", "tiktok", "youtube", "kick", "other"];
const PRODUCT_CATS = ["mikrofon", "mikrofonarm", "audio_interface", "kamera", "objektiv", "licht", "headset", "maus", "tastatur",
  "bildschirm", "cpu", "gpu", "ram", "mainboard", "pc", "capture", "streamdeck", "greenscreen", "stuhl", "schreibtisch",
  "zubehoer", "software_streaming", "software_audio", "software_plugin", "sonstiges"];
const SOURCE_TYPES = {
  official_statement: "Eigene Aussage des Streamers", own_setup_page: "Eigene Setup-Seite", video_statement: "Nennt es selbst im Video/Stream",
  manufacturer: "Herstellerangabe", video_visual: "Nur im Bild sichtbar", third_party: "Andere Quelle (Artikel o. ä.)",
};
const STATUS_LABEL = { confirmed: "bestätigt", probable: "wahrscheinlich", outdated: "veraltet", conflicting: "widersprüchlich", unknown: "unbekannt",
  pending: "offen", approved: "freigegeben", rejected: "abgelehnt", superseded: "überholt" };
const AVAILABILITY = { in_stock: "lieferbar", out_of_stock: "nicht lieferbar", discontinued: "eingestellt", unknown: "unbekannt" };

let fs = null, db = null, me = null;
const cache = { streamer: [], product: [], setup_claim: [], offer: [], source: [], source_registry: [] };
const COLLECTION = { streamer: "streamers", product: "products", setup_claim: "setup_claims", offer: "offers",
  source: "sources", source_registry: "source_registry" };

// ------------------------------------------------------------ Anmeldung
async function onAuth({ user, app }) {
  const gate = $("admin-gate");
  [$("admin-tabs"), $("admin-status")].forEach((el) => (el.hidden = true));
  document.querySelectorAll(".panel").forEach((p) => (p.hidden = true));
  if (!user) {
    gate.hidden = false;
    gate.textContent = "Bitte melde dich mit einem Admin-Konto an.";
    return;
  }
  const token = await user.getIdTokenResult(true);
  if (token.claims.admin !== true) {
    gate.hidden = false;
    gate.textContent = "Dieses Konto hat keine Admin-Berechtigung. Ein Admin kann sie mit „python -m setup_agent set-admin“ vergeben.";
    return;
  }
  me = { type: "admin", id: user.uid };
  fs = await import(`${SDK}/firebase-firestore.js`);
  db = fs.getFirestore(app);
  gate.hidden = true;
  $("admin-tabs").hidden = false;
  await Promise.all([loadAll(), loadStatus()]);
  showPanel(location.hash.slice(1) || "queue");
}
document.addEventListener("sge:auth", (e) => onAuth(e.detail).catch(fail));
if (window.sgeAuth) onAuth(window.sgeAuth).catch(fail);

function fail(err) {
  console.error(err);
  const gate = $("admin-gate");
  gate.hidden = false;
  gate.textContent = "Fehler beim Laden: " + (err.code === "permission-denied" ? "keine Berechtigung (Sicherheitsregeln prüfen)." : err.message);
}

// ------------------------------------------------------------ Tabs
const PANELS = ["queue", "new", "data", "sources", "audit"];
function showPanel(name) {
  if (!PANELS.includes(name)) name = "queue";
  PANELS.forEach((p) => ($("panel-" + p).hidden = p !== name));
  document.querySelectorAll("#admin-tabs .tab").forEach((t) => t.classList.toggle("active", t.dataset.panel === name));
  ({ queue: renderQueue, new: renderNew, data: renderData, sources: renderSources, audit: renderAudit })[name]();
}
document.querySelectorAll("#admin-tabs .tab").forEach((t) =>
  t.addEventListener("click", () => {
    history.replaceState(null, "", "#" + t.dataset.panel);
    showPanel(t.dataset.panel);
  })
);

// ------------------------------------------------------------ Laden
async function loadAll() {
  await Promise.all(Object.entries(COLLECTION).map(async ([kind, coll]) => {
    const snap = await fs.getDocs(fs.collection(db, coll));
    cache[kind] = snap.docs.map((d) => ({ ...d.data(), _id: d.id }));
  }));
  const pending = await fs.getDocs(fs.query(fs.collection(db, "change_proposals"), fs.where("status", "==", "pending")));
  $("queue-count").textContent = pending.size ? `(${pending.size})` : "";
}

async function loadStatus() {
  const snap = await fs.getDoc(fs.doc(db, "meta", "agent"));
  const runs = snap.exists() ? snap.data().runs || {} : {};
  const age = (job) => (runs[job] ? (Date.now() - new Date(runs[job].at)) / 36e5 : Infinity);
  const warn = [];
  if (age("apply") > 3) warn.push("Der stündliche Lauf (Freigaben übernehmen) war seit über 3 Stunden nicht aktiv.");
  if (age("weekly") > 14 * 24) warn.push("Die wöchentliche Prüfung lief seit über 14 Tagen nicht. GitHub deaktiviert geplante Läufe nach 60 Tagen ohne Aktivität im Repository.");
  const el = $("admin-status");
  el.hidden = false;
  el.className = "box " + (warn.length ? "warn-box" : "ok-box");
  el.innerHTML = `<strong>Agent-Läufe:</strong> ${["apply", "weekly", "prices"].map((j) =>
    `${j}: ${runs[j] ? when(runs[j].at) + (runs[j].ok ? "" : " ⚠️") : "noch nie"}`).join(" · ")}${warn.map((w) => `<p>⚠️ ${esc(w)}</p>`).join("")}`;
}

// ------------------------------------------------------------ Vorschläge anlegen und entscheiden
async function propose({ entity_type, entity_id = "new", operation, payload, base_version = null, reason, approveNow }) {
  const ref = await fs.addDoc(fs.collection(db, "change_proposals"), {
    entity_type, entity_id, operation, payload, base_version, reason, evidence_source_ids: [], origin: "admin",
    created_by: me, created_at: nowIso(), status: "pending", decided_by: null, decided_at: null, decision_note: null,
    applied_at: null, apply_error: null,
  });
  if (approveNow) await decide(ref.id, true, null);
  return ref.id;
}

async function decide(id, approve, note) {
  await fs.updateDoc(fs.doc(db, "change_proposals", id), {
    status: approve ? "approved" : "rejected", decided_by: me, decided_at: nowIso(), decision_note: note || null,
  });
}

async function renderQueue() {
  const status = $("queue-status").value;
  const snap = await fs.getDocs(fs.query(fs.collection(db, "change_proposals"), fs.where("status", "==", status)));
  const items = snap.docs.map((d) => ({ ...d.data(), id: d.id })).sort((a, b) => String(b.created_at).localeCompare(a.created_at));
  $("queue-list").innerHTML = items.length
    ? items.map(proposalCard).join("")
    : `<div class="box empty"><p>Keine Vorschläge mit Status „${esc(STATUS_LABEL[status])}“.</p></div>`;
}
$("queue-status").addEventListener("change", renderQueue);

function proposalCard(p) {
  const target = label(p.entity_type, p.entity_id);
  const applied = p.status === "approved"
    ? p.applied_at ? `<p class="ok">✅ Übernommen am ${when(p.applied_at)}</p>`
      : p.apply_error ? `<p class="bad">❌ Nicht übernommen: ${esc(p.apply_error)}</p>` : `<p class="hint">⏳ Wartet auf den nächsten Lauf.</p>`
    : "";
  return `<article class="box proposal" data-id="${esc(p.id)}">
    <header><span class="badge">${esc(p.operation)}</span> <strong>${esc(p.entity_type)}</strong> <span class="mono">${esc(target)}</span>
      <span class="rating">${esc(STATUS_LABEL[p.status] || p.status)}</span></header>
    <p>${esc(p.reason)}</p>
    <p class="hint">von ${esc(p.created_by?.type)} ${esc(p.created_by?.id)} (${esc(p.origin)}) · ${when(p.created_at)}${p.base_version ? ` · basiert auf Version ${p.base_version}` : ""}</p>
    <details><summary>Änderung ansehen</summary><pre>${esc(JSON.stringify(p.payload, null, 2))}</pre></details>
    ${p.decision_note ? `<p class="hint">Notiz: ${esc(p.decision_note)}</p>` : ""}
    ${applied}
    ${p.status === "pending" ? `<div class="decide">
      <input type="text" class="note" placeholder="Notiz (bei Ablehnung Pflicht)">
      <button type="button" class="btn btn-small" data-approve>Freigeben</button>
      <button type="button" class="btn btn-small btn-ghost" data-reject>Ablehnen</button></div>` : ""}
  </article>`;
}

$("queue-list").addEventListener("click", async (e) => {
  const card = e.target.closest(".proposal");
  if (!card || !(e.target.matches("[data-approve]") || e.target.matches("[data-reject]"))) return;
  const approve = e.target.matches("[data-approve]");
  const note = card.querySelector(".note").value.trim();
  if (!approve && note.length < 3) {
    card.querySelector(".note").focus();
    card.querySelector(".note").placeholder = "Bitte Begründung eingeben (mind. 3 Zeichen)";
    return;
  }
  e.target.disabled = true;
  try {
    await decide(card.dataset.id, approve, note);
    await loadAll();
    renderQueue();
  } catch (err) {
    alert("Konnte nicht gespeichert werden: " + err.message);
    e.target.disabled = false;
  }
});

function label(kind, id) {
  if (id === "new") return "(neu)";
  const item = cache[kind]?.find((x) => x._id === id);
  if (!item) return id;
  return { streamer: item.display_name, product: `${item.manufacturer} ${item.model}`, setup_claim: `${item.streamer_id}: ${item.raw_name}`,
    offer: `${item.retailer} – ${item.product_id}`, source: item.url, source_registry: item.domain }[kind] || id;
}

// ------------------------------------------------------------ Neu anlegen (Formulare)
const opts = (pairs, selected) => pairs.map(([v, l]) => `<option value="${esc(v)}" ${v === selected ? "selected" : ""}>${esc(l)}</option>`).join("");
const field = (name, title, input, hint = "") => `<label class="field"><span>${esc(title)}</span>${input}${hint ? `<small class="hint">${esc(hint)}</small>` : ""}</label>`;
const text = (name, attrs = "") => `<input type="text" name="${name}" ${attrs}>`;
const select = (name, pairs, attrs = "") => `<select name="${name}" ${attrs}>${opts(pairs)}</select>`;
const checks = (name, pairs) => `<div class="chips small">${pairs.map(([v, l]) => `<label class="chip"><input type="checkbox" name="${name}" value="${esc(v)}"><span>${esc(l)}</span></label>`).join("")}</div>`;
const productPairs = () => cache.product.map((p) => [p._id, `${p.manufacturer} ${p.model}`]).sort((a, b) => a[1].localeCompare(b[1]));
const streamerPairs = () => cache.streamer.map((s) => [s._id, s.display_name]);

const EVIDENCE_ROW = () => `<fieldset class="evidence">
  ${field("", "Quellen-URL", `<input type="url" name="ev_url" required placeholder="https://…">`)}
  ${field("", "Quellentyp", select("ev_type", Object.entries(SOURCE_TYPES)))}
  ${field("", "Datum der Aussage", `<input type="date" name="ev_date" required max="${new Date().toISOString().slice(0, 10)}">`)}
  ${field("", "Zeitmarke im Video", text("ev_ts", 'placeholder="00:12:34"'), "optional")}
  ${field("", "Eigene Notiz", text("ev_note", 'maxlength="280"'), "optional, kein kopierter Text")}
</fieldset>`;

const FORMS = {
  streamer: { title: "Streamer", html: () =>
    field("", "Anzeigename", text("display_name", "required maxlength=60")) +
    field("", "Hauptplattform", select("platform", PLATFORMS.map((p) => [p, p]))) +
    field("", "Kanalname (Handle)", text("handle", "required")) +
    field("", "Kanal-URL", `<input type="url" name="url" required>`) +
    field("", "Kategorien", checks("categories", Object.entries(CATEGORIES))) +
    field("", "Hauptsprache", text("primary_language", 'maxlength="2" placeholder="de"'), "ISO-Code, optional"),
    build: (f) => {
      const handle = f.get("handle").trim();
      const slug = handle.toLowerCase().normalize("NFKD").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
      return { entity_type: "streamer", payload: {
        id: `${f.get("platform")}-${slug}`, display_name: f.get("display_name").trim(),
        platforms: [{ platform: f.get("platform"), handle, url: f.get("url").trim() }],
        categories: f.getAll("categories"), primary_language: f.get("primary_language").trim() || null } };
    } },
  product: { title: "Produkt", html: () =>
    field("", "Hersteller", text("manufacturer", "required")) +
    field("", "Exakte Modellbezeichnung", text("model", "required")) +
    field("", "Kategorie", select("category", PRODUCT_CATS.map((c) => [c, c]))) +
    field("", "Variante", text("variant"), "optional") +
    field("", "Andere Schreibweisen", text("aliases", 'placeholder="Shure SM-7B, SM 7B"'), "kommagetrennt, optional") +
    field("", "EAN/GTIN", text("gtin", 'inputmode="numeric"'), "optional") +
    field("", "Technische Daten", `<textarea name="specs" rows="3" placeholder="anschluss=XLR"></textarea>`, "eine pro Zeile: name=wert"),
    build: (f) => ({ entity_type: "product", payload: {
      manufacturer: f.get("manufacturer").trim(), model: f.get("model").trim(), category: f.get("category"),
      variant: f.get("variant").trim() || null, gtin: f.get("gtin").trim() || null,
      aliases: f.get("aliases").split(",").map((s) => s.trim()).filter(Boolean),
      specs: Object.fromEntries(f.get("specs").split("\n").map((l) => l.split("=")).filter((p) => p.length === 2 && p[0].trim()).map(([k, v]) => [k.trim(), v.trim()])) } }) },
  claim: { title: "Setup-Angabe", html: () =>
    field("", "Streamer", select("streamer_id", streamerPairs(), "required")) +
    field("", "Kategorie", select("category", PRODUCT_CATS.map((c) => [c, c]))) +
    field("", "Rolle", text("role", 'value="primary" pattern="[a-z][a-z0-9_]*"'), "primary, secondary, irl …") +
    field("", "Produkt", select("product_id", [["", "— nicht eindeutig / nicht im Katalog —"], ...productPairs()])) +
    field("", "Bezeichnung wie in der Quelle", text("raw_name", "required")) +
    `<div id="evidence-rows">${EVIDENCE_ROW()}</div><button type="button" class="link-btn" id="add-evidence">+ weitere Quelle</button>`,
    build: (f) => {
      const urls = f.getAll("ev_url"), types = f.getAll("ev_type"), dates = f.getAll("ev_date"), ts = f.getAll("ev_ts"), notes = f.getAll("ev_note");
      const evidence = urls.map((u, i) => ({ source_url: u.trim(), source_type: types[i], observed_at: new Date(dates[i] + "T00:00:00Z").toISOString(),
        retrieved_at: nowIso(), media_timestamp: ts[i].trim() || null, note: notes[i].trim() || null })).filter((e) => e.source_url);
      return { entity_type: "setup_claim", payload: { streamer_id: f.get("streamer_id"), category: f.get("category"),
        role: f.get("role").trim() || "primary", product_id: f.get("product_id") || null, raw_name: f.get("raw_name").trim(), evidence } };
    } },
  offer: { title: "Angebot", html: () =>
    field("", "Produkt", select("product_id", productPairs(), "required")) +
    field("", "Händler", text("retailer", "required")) +
    field("", "Produktlink (https)", `<input type="url" name="url" required>`) +
    field("", "Preis in €", `<input type="number" name="price" step="0.01" min="0">`, "leer = unbekannt") +
    field("", "Verfügbarkeit", select("availability", Object.entries(AVAILABILITY))),
    build: (f) => { const price = f.get("price"); const now = nowIso();
      return { entity_type: "offer", payload: { product_id: f.get("product_id"), retailer: f.get("retailer").trim(), url: f.get("url").trim(),
        price: price === "" ? null : { amount_minor: Math.round(Number(price) * 100), currency: "EUR" }, availability: f.get("availability"),
        checked_at: price === "" ? null : now, last_success_at: price === "" ? null : now, price_source: "manual" } }; } },
  price: { title: "Preis ändern", html: () =>
    field("", "Angebot", select("offer", cache.offer.map((o) => [o._id, `${label("product", o.product_id)} – ${o.retailer} (${euro(o.price?.amount_minor)})`]), "required")) +
    field("", "Neuer Preis in €", `<input type="number" name="price" step="0.01" min="0">`, "leer = unbekannt") +
    field("", "Verfügbarkeit", select("availability", Object.entries(AVAILABILITY))),
    build: (f) => { const o = cache.offer.find((x) => x._id === f.get("offer")); const price = f.get("price");
      return { entity_type: "offer", entity_id: o._id, operation: "update", base_version: o.version, payload: {
        price: price === "" ? null : { amount_minor: Math.round(Number(price) * 100), currency: "EUR" }, availability: f.get("availability") } }; } },
  source: { title: "Quelle", html: () =>
    field("", "URL", `<input type="url" name="url" required>`) +
    field("", "Quellentyp", select("source_type", Object.entries(SOURCE_TYPES))) +
    field("", "Gehört zu Streamer", select("streamer_id", [["", "— keinem —"], ...streamerPairs()])) +
    field("", "Titel", text("title", "maxlength=200"), "optional"),
    build: (f) => ({ entity_type: "source", payload: { url: f.get("url").trim(), source_type: f.get("source_type"),
      streamer_id: f.get("streamer_id") || null, title: f.get("title").trim() || null } }) },
  source_registry: { title: "Zugelassene Domain", html: () =>
    field("", "Domain", text("domain", 'required placeholder="beispiel.de"')) +
    field("", "Erlaubte Quellentypen", checks("source_types", Object.entries(SOURCE_TYPES))) +
    field("", "Zugriffsart", select("access_method", [["manual", "nur manuell"], ["official_api", "offizielle API"], ["rss", "RSS-Feed"], ["http_allowed", "Seitenabruf erlaubt"]])) +
    `<label class="check"><input type="checkbox" name="auto_fetch_allowed"> Automatischer Abruf erlaubt (Nutzungsbedingungen geprüft)</label>` +
    field("", "Link zu den Nutzungsbedingungen", `<input type="url" name="terms_url">`, "optional") +
    field("", "Mindestabstand zwischen Abrufen (Stunden)", `<input type="number" name="min_interval_hours" value="168" min="1">`) +
    field("", "Notizen", text("notes", "maxlength=500"), "optional"),
    build: (f) => { const auto = f.get("auto_fetch_allowed") === "on";
      return { entity_type: "source_registry", payload: { domain: f.get("domain").trim().toLowerCase().replace(/^www\./, ""),
        source_types: f.getAll("source_types"), access_method: f.get("access_method"), auto_fetch_allowed: auto,
        terms_url: f.get("terms_url").trim() || null, terms_reviewed_at: auto ? nowIso() : null,
        min_interval_hours: Number(f.get("min_interval_hours")) || 168, notes: f.get("notes").trim() || null } }; } },
};
let currentForm = "claim";

function renderNew() {
  $("new-kind").innerHTML = Object.entries(FORMS).map(([k, v]) =>
    `<label class="chip"><input type="radio" name="new-kind" value="${k}" ${k === currentForm ? "checked" : ""}><span>${esc(v.title)}</span></label>`).join("");
  $("new-form").innerHTML = FORMS[currentForm].html() +
    field("", "Begründung", text("reason", 'required minlength="3" placeholder="Woher stammt die Information?"')) +
    `<label class="check"><input type="checkbox" name="approve_now" checked> Direkt freigeben (sonst prüft ein zweiter Admin)</label>
     <button type="submit" class="btn">Vorschlag speichern</button>`;
  $("new-msg").textContent = "";
}
$("new-kind").addEventListener("change", (e) => { currentForm = e.target.value; renderNew(); });
$("new-form").addEventListener("click", (e) => {
  if (e.target.id === "add-evidence") $("evidence-rows").insertAdjacentHTML("beforeend", EVIDENCE_ROW());
});
$("new-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  const msg = $("new-msg");
  try {
    const spec = FORMS[currentForm].build(f);
    if (spec.entity_type === "setup_claim" && !spec.payload.evidence.length) throw new Error("Mindestens eine Quelle ist Pflicht.");
    if (spec.entity_type === "streamer" && !spec.payload.categories.length) throw new Error("Bitte mindestens eine Kategorie wählen.");
    await propose({ operation: "create", ...spec, reason: f.get("reason").trim(), approveNow: f.get("approve_now") === "on" });
    msg.className = "admin-msg ok";
    msg.textContent = "Gespeichert. Der Agent prüft und übernimmt es beim nächsten Lauf (stündlich). Ergebnis unter „Vorschläge“.";
    await loadAll();
    renderNew();
    msg.className = "admin-msg ok";
    msg.textContent = "Gespeichert. Der Agent prüft und übernimmt es beim nächsten Lauf (stündlich).";
  } catch (err) {
    msg.className = "admin-msg bad";
    msg.textContent = "Nicht gespeichert: " + err.message;
  }
});

// ------------------------------------------------------------ Daten ansehen, korrigieren, zurückziehen
let dataKind = "setup_claim";
const DATA_KINDS = { setup_claim: "Setup-Angaben", streamer: "Streamer", product: "Produkte", offer: "Angebote" };

function renderData() {
  $("data-kind").innerHTML = Object.entries(DATA_KINDS).map(([k, v]) =>
    `<label class="chip"><input type="radio" name="data-kind" value="${k}" ${k === dataKind ? "checked" : ""}><span>${esc(v)} (${cache[k].length})</span></label>`).join("");
  const rows = cache[dataKind];
  $("data-list").innerHTML = rows.length ? rows.map((r) => `<article class="box data-row" data-id="${esc(r._id)}">
      <header><strong>${esc(label(dataKind, r._id))}</strong> <span class="mono">${esc(r._id)}</span> <span class="hint">v${esc(r.version)}</span></header>
      ${dataKind === "setup_claim" ? `<p><span class="rating">${esc(STATUS_LABEL[r.status])}</span> ${r.published ? "🌐 öffentlich" : "🔒 nicht öffentlich"} · ${esc(r.reason)}</p>
        <p class="hint">${(r.evidence || []).map((e) => `<a href="${esc(e.source_url)}" target="_blank" rel="noopener">${esc(SOURCE_TYPES[e.source_type])}</a> (${when(e.observed_at)})`).join(" · ")}</p>` : ""}
      ${dataKind === "offer" ? `<p>${euro(r.price?.amount_minor)} · ${esc(AVAILABILITY[r.availability])} · zuletzt erfolgreich ${when(r.last_success_at)}${r.failed_checks ? ` · ⚠️ ${r.failed_checks} Fehlversuche` : ""}</p>` : ""}
      <details><summary>Korrigieren</summary>
        <textarea rows="3" class="changes" placeholder='{"feld": "neuer Wert"}'></textarea>
        <input type="text" class="why" placeholder="Begründung (Pflicht)">
        <button type="button" class="btn btn-small" data-fix>Korrektur vorschlagen</button>
        <button type="button" class="btn btn-small btn-ghost" data-retire>Zurückziehen</button>
      </details>
    </article>`).join("") : `<div class="box empty"><p>Noch keine Einträge.</p></div>`;
}
$("data-kind").addEventListener("change", (e) => { dataKind = e.target.value; renderData(); });
$("data-list").addEventListener("click", async (e) => {
  const row = e.target.closest(".data-row");
  if (!row || !(e.target.matches("[data-fix]") || e.target.matches("[data-retire]"))) return;
  const item = cache[dataKind].find((x) => x._id === row.dataset.id);
  const reason = row.querySelector(".why").value.trim();
  if (reason.length < 3) return row.querySelector(".why").focus();
  try {
    const retire = e.target.matches("[data-retire]");
    const payload = retire ? {} : JSON.parse(row.querySelector(".changes").value || "{}");
    await propose({ entity_type: dataKind, entity_id: item._id, operation: retire ? "retire" : "update", payload,
      base_version: item.version, reason, approveNow: false });
    e.target.closest("details").innerHTML = `<p class="ok">Vorschlag angelegt – bitte unter „Vorschläge“ freigeben.</p>`;
    loadAll();
  } catch (err) {
    alert("Nicht gespeichert: " + err.message);
  }
});

// ------------------------------------------------------------ Quellen
function renderSources() {
  const reg = cache.source_registry.map((r) => `<article class="box"><header><strong>${esc(r.domain)}</strong>
      ${r.enabled === false ? '<span class="badge">deaktiviert</span>' : ""} <span class="badge">${r.auto_fetch_allowed ? "automatisch" : "nur manuell"}</span></header>
      <p class="hint">${(r.source_types || []).map((t) => esc(SOURCE_TYPES[t])).join(", ")} · alle ${esc(r.min_interval_hours)} h${r.notes ? " · " + esc(r.notes) : ""}</p></article>`).join("");
  const src = cache.source.map((s) => `<article class="box"><header><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title || s.url)}</a>
      <span class="badge">${esc(SOURCE_TYPES[s.source_type])}</span></header>
      <p class="hint">${s.streamer_id ? esc(label("streamer", s.streamer_id)) + " · " : ""}zuletzt geprüft ${when(s.last_checked_at)} ${s.last_check_ok === false ? "❌ fehlgeschlagen" : s.last_check_ok ? "✅" : ""}</p></article>`).join("");
  $("sources-list").innerHTML = `<h3>Zugelassene Domains</h3>${reg || '<p class="hint">Noch keine.</p>'}<h3>Quellen</h3>${src || '<p class="hint">Noch keine.</p>'}`;
}

// ------------------------------------------------------------ Änderungsprotokoll
async function renderAudit() {
  const id = $("audit-id").value.trim();
  const coll = fs.collection(db, "audit_log");
  const snap = await fs.getDocs(id ? fs.query(coll, fs.where("entity_id", "==", id)) : fs.query(coll, fs.orderBy("at", "desc"), fs.limit(50)));
  const items = snap.docs.map((d) => d.data()).sort((a, b) => String(b.at).localeCompare(a.at));
  $("audit-list").innerHTML = items.length ? items.map((a) => `<article class="box">
      <header><span class="badge">${esc(a.action)}</span> <strong>${esc(a.entity_type)}</strong> <span class="mono">${esc(a.entity_id)}</span>
        <span class="hint">${when(a.at)} · ${esc(a.actor?.type)} ${esc(a.actor?.id)}</span></header>
      <p>${esc(a.reason)}</p>
      ${Object.keys(a.changes || {}).length ? `<details><summary>${Object.keys(a.changes).length} Feld(er) geändert</summary><pre>${esc(JSON.stringify(a.changes, null, 2))}</pre></details>` : ""}
    </article>`).join("") : `<div class="box empty"><p>Keine Einträge.</p></div>`;
}
let auditTimer;
$("audit-id").addEventListener("input", () => { clearTimeout(auditTimer); auditTimer = setTimeout(renderAudit, 300); });
