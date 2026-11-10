// ============================================================
//  Setups-Seite: Budget-Planer, Streamer-Setups, Hardware-Katalog
// ============================================================
import { CATEGORIES, GROUPS, TYPES, NEEDS, PRODUCTS, STREAMERS } from "./setups-data.js";

const $ = (id) => document.getElementById(id);
const byId = Object.fromEntries(PRODUCTS.map((p) => [p.id, p]));
const euro = (n) => n.toLocaleString("de-DE") + " €";
// Software kann gratis sein oder ein Abo (Preis pro Monat)
const priceLabel = (p, prefix = "ca. ") =>
  p.billing === "gratis" || p.price === 0 ? "gratis" : p.billing === "abo" ? `${euro(p.price)}/Monat` : prefix + euro(p.price);
const esc = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function rating(score) {
  if (score >= 8.5) return { label: "Top", cls: "r-top" };
  if (score >= 7) return { label: "Sehr gut", cls: "r-great" };
  if (score >= 5.5) return { label: "Gut", cls: "r-good" };
  return { label: "Einstieg", cls: "r-entry" };
}

function chip(group, value, label, active, type = "radio") {
  return `<label class="chip"><input type="${type}" name="${group}" value="${esc(value)}" ${active ? "checked" : ""}><span>${label}</span></label>`;
}

// ============================================================
//  Tabs (mit #hash, damit man Links teilen kann)
// ============================================================
const PANELS = ["budget", "streamer", "katalog"];
function showPanel(name) {
  if (!PANELS.includes(name)) name = "budget";
  PANELS.forEach((p) => ($("panel-" + p).hidden = p !== name));
  document.querySelectorAll(".tab").forEach((t) => {
    const on = t.dataset.panel === name;
    t.classList.toggle("active", on);
    t.setAttribute("aria-selected", on);
  });
}
document.querySelectorAll(".tab").forEach((t) =>
  t.addEventListener("click", () => {
    history.replaceState(null, "", "#" + t.dataset.panel);
    showPanel(t.dataset.panel);
  })
);
window.addEventListener("hashchange", () => showPanel(location.hash.slice(1)));
showPanel(location.hash.slice(1));

// ============================================================
//  1) Budget-Planer
// ============================================================
// Jedes Bauteil hat einen von drei Zuständen:
//   need  = brauche ich  → wird ins Budget eingerechnet
//   owned = habe ich schon → 0 €, wird als vorhanden angezeigt
//   skip  = brauche ich nicht → fällt komplett raus
const STATES = [
  { value: "need", label: "Brauche ich" },
  { value: "owned", label: "Habe ich" },
  { value: "skip", label: "Nicht nötig" },
];
const partState = {}; // merkt sich die Auswahl pro Bauteil, auch beim Kategorie-Wechsel
const stateOf = (type) => partState[type] || TYPES[type].defaultState || "need";

// Welche Bauteile gehören zur aktuellen Auswahl?
function partsFor(cat, onConsole) {
  const parts = NEEDS[cat].map((n) => ({ ...n }));
  if (cat === "gaming" && onConsole) parts.push({ type: "capture", weight: 2.5, required: true });
  return parts;
}

// Passende Produkte für ein Bauteil (Abo-Software zählt nicht ins einmalige Budget)
function productsFor(type, cat, onConsole) {
  return PRODUCTS.filter(
    (p) =>
      p.type === type &&
      p.cats.includes(cat) &&
      p.billing !== "abo" &&
      (type !== "pc" || p.platform === (onConsole ? "konsole" : "pc"))
  );
}

// Findet die Kombination mit dem höchsten (Gewicht × Bewertung), die ins Budget passt.
// Rechenweg: "Rucksack-Problem" mit einer Tabelle über alle Euro-Beträge bis zum Budget.
// Das ist auch mit vielen Bauteilen schnell, im Gegensatz zum Durchprobieren aller Kombinationen.
function planSetup(budget, cat, onConsole) {
  budget = Math.floor(budget);
  const needs = partsFor(cat, onConsole).filter((n) => stateOf(n.type) === "need");
  const needIndex = Object.fromEntries(needs.map((n, i) => [n.type, i]));

  // Jede Gruppe = eine Liste von Optionen { items, cost, value }. "Nichts" ist eine Option bei optionalen Teilen.
  const groups = needs.map((n) => {
    const opts = productsFor(n.type, cat, onConsole)
      .filter((p) => !p.requires || stateOf(p.requires) === "owned" || p.requires in needIndex)
      .map((p) => ({ items: [p], cost: p.price, value: p.score * n.weight }));
    return { types: [n.type], required: !!n.required, opts: n.required ? opts : [{ items: [], cost: 0, value: 0 }, ...opts] };
  });

  // Teile, die ein anderes Teil voraussetzen (z. B. XLR-Mikro → Interface): beide Gruppen zusammenlegen
  const merged = new Set();
  groups.forEach((g, i) => {
    if (merged.has(i)) return;
    const reqTypes = new Set(g.opts.flatMap((o) => o.items.map((p) => p.requires)).filter((t) => t && stateOf(t) !== "owned"));
    reqTypes.forEach((t) => {
      const j = needIndex[t];
      if (j === undefined || j === i || merged.has(j)) return;
      const other = groups[j];
      const combos = [];
      for (const a of g.opts)
        for (const b of other.opts) {
          if (a.items.some((p) => p.requires === t) && !b.items.length) continue;
          combos.push({ items: [...a.items, ...b.items], cost: a.cost + b.cost, value: a.value + b.value });
        }
      g.opts = combos;
      g.types.push(...other.types);
      merged.add(j);
    });
  });
  const active = groups.filter((g, i) => !merged.has(i) && g.opts.length);
  const impossible = groups.filter((g, i) => !merged.has(i) && !g.opts.length).flatMap((g) => g.types);

  // Mindestbudget = günstigste Option jeder Gruppe
  const minNeeded = active.reduce((sum, g) => sum + Math.min(...g.opts.map((o) => o.cost)), 0);
  if (minNeeded > budget) return { ok: false, minNeeded };

  // dp[c] = bester Wert bei genau c Euro Gesamtpreis
  let dp = new Float64Array(budget + 1).fill(-Infinity);
  dp[0] = 0;
  const picks = [];
  for (const g of active) {
    const next = new Float64Array(budget + 1).fill(-Infinity);
    const pick = new Int16Array(budget + 1).fill(-1);
    for (let c = 0; c <= budget; c++) {
      if (dp[c] === -Infinity) continue;
      g.opts.forEach((o, k) => {
        const nc = c + o.cost;
        if (nc > budget) return;
        const v = dp[c] + o.value;
        if (v > next[nc]) {
          next[nc] = v;
          pick[nc] = k;
        }
      });
    }
    dp = next;
    picks.push(pick);
  }

  // Höchster Wert; bei Gleichstand der günstigere Preis
  let total = 0;
  for (let c = 1; c <= budget; c++) if (dp[c] > dp[total] + 1e-9) total = c;
  const items = [];
  for (let gi = active.length - 1, c = total; gi >= 0; gi--) {
    const o = active[gi].opts[picks[gi][c]];
    items.push(...o.items);
    c -= o.cost;
  }
  const order = Object.keys(TYPES);
  items.sort((a, b) => order.indexOf(a.type) - order.indexOf(b.type));
  return { ok: true, value: dp[total], total, items, needs, impossible };
}

const budgetRange = $("budget-range");
const budgetNumber = $("budget-number");
const consoleRow = $("console-row");
const currentCat = () => document.querySelector('[name="budget-cat"]:checked').value;

$("budget-cats").innerHTML = Object.entries(CATEGORIES)
  .map(([k, c], i) => chip("budget-cat", k, `${c.icon} ${c.label}`, i === 0))
  .join("");

// Liste aller Bauteile, gruppiert nach Bereich, mit drei Zuständen zum Anhaken
function renderParts() {
  const cat = currentCat();
  const parts = partsFor(cat, $("budget-console").checked);
  const html = Object.entries(GROUPS)
    .map(([g, info]) => {
      const rows = parts.filter((n) => TYPES[n.type].group === g);
      if (!rows.length) return "";
      return `<div class="part-group">
        <p class="part-group-title">${info.icon} ${esc(info.label)}</p>
        ${rows
          .map((n) => {
            const t = TYPES[n.type];
            const state = stateOf(n.type);
            return `<div class="part-row state-${state}">
              <span class="part-name"><span class="item-icon">${t.icon}</span>${esc(t.label)}${n.required ? ' <small class="req">Pflicht</small>' : ""}</span>
              <div class="seg" role="radiogroup" aria-label="${esc(t.label)}">
                ${STATES.map(
                  (s) => `<label><input type="radio" name="state-${n.type}" value="${s.value}" ${state === s.value ? "checked" : ""}><span>${s.label}</span></label>`
                ).join("")}
              </div>
            </div>`;
          })
          .join("")}
      </div>`;
    })
    .join("");
  $("budget-parts").innerHTML = html;
}

function renderBudget() {
  const budget = Math.max(0, Number(budgetNumber.value) || 0);
  const cat = currentCat();
  const onConsole = $("budget-console").checked;
  consoleRow.hidden = cat !== "gaming";

  const res = planSetup(budget, cat, onConsole);
  const out = $("budget-result");
  const parts = partsFor(cat, onConsole);
  const owned = parts.filter((n) => stateOf(n.type) === "owned");
  const ownedHtml = owned.length
    ? `<p class="hint owned-line">✅ Schon vorhanden: ${owned.map((n) => `${TYPES[n.type].icon} ${esc(TYPES[n.type].label)}`).join(", ")}</p>`
    : "";

  if (!res.ok) {
    out.innerHTML = `<div class="box empty">
      <h3>Das wird knapp 😅</h3>
      <p>Für ein ${esc(CATEGORIES[cat].label)}-Setup mit deiner Auswahl brauchst du mindestens <strong>${euro(res.minNeeded)}</strong>.</p>
      <button type="button" class="btn btn-small" id="set-min">Budget auf ${euro(res.minNeeded)} setzen</button>
      ${ownedHtml}
    </div>`;
    $("set-min").onclick = () => setBudget(res.minNeeded);
    return;
  }

  if (!res.items.length) {
    out.innerHTML = `<div class="box empty"><h3>Du hast schon alles! 🎉</h3><p>Dann bleibt nur noch eins: Go Live.</p>${ownedHtml}</div>`;
    return;
  }

  const avg = res.items.reduce((s, p) => s + p.score, 0) / res.items.length;
  const r = rating(avg);
  const rest = budget - res.total;
  const missing = res.needs.filter((n) => !res.items.some((p) => p.type === n.type));

  // Upgrade-Tipp: Was bekäme man für 100 € mehr?
  let upgrade = "";
  const up = planSetup(budget + 100, cat, onConsole);
  if (up.ok && up.value > res.value) {
    // Nur echte Verbesserungen zeigen: neuer Bauteil-Typ oder besser bewertet
    const current = Object.fromEntries(res.items.map((p) => [p.type, p]));
    const added = up.items.filter((p) => !current[p.type] || p.score > current[p.type].score);
    if (added.length) {
      upgrade = `<div class="upgrade">⬆️ <strong>Mit 100 € mehr</strong> bekommst du: ${added.map((p) => esc(p.name)).join(", ")}
        <button type="button" class="link-btn" id="budget-up">Anzeigen</button></div>`;
    }
  }

  out.innerHTML = `<div class="box">
    <div class="result-head">
      <div>
        <p class="eyebrow">Dein ${esc(CATEGORIES[cat].label)}-Setup</p>
        <h3>${euro(res.total)} <small>von ${euro(budget)}</small></h3>
      </div>
      <span class="rating ${r.cls}">${r.label}</span>
    </div>
    <div class="meter"><span style="width:${Math.min(100, (res.total / Math.max(budget, 1)) * 100)}%"></span></div>
    <ul class="item-list">
      ${res.items
        .map(
          (p) => `<li>
            <span class="item-icon">${TYPES[p.type].icon}</span>
            <div class="item-main"><strong>${esc(p.name)}</strong><small>${esc(TYPES[p.type].label)} · ${esc(p.note)}</small></div>
            <span class="item-price">${priceLabel(p)}</span>
          </li>`
        )
        .join("")}
    </ul>
    ${ownedHtml}
    ${missing.length ? `<p class="hint">Noch nicht drin (optional): ${missing.map((n) => TYPES[n.type].label).join(", ")}. Kannst du später nachrüsten.</p>` : ""}
    ${res.impossible.length ? `<p class="hint">Für ${res.impossible.map((t) => TYPES[t].label).join(", ")} haben wir in dieser Kategorie noch keine Produkte.</p>` : ""}
    ${rest > 0 ? `<p class="hint">Übrig: <strong>${euro(rest)}</strong>, gut für Kabel und Halterungen.</p>` : ""}
    ${upgrade}
  </div>`;

  const upBtn = $("budget-up");
  if (upBtn) upBtn.onclick = () => setBudget(budget + 100);
}

function setBudget(v) {
  budgetNumber.value = v;
  budgetRange.value = Math.min(v, Number(budgetRange.max));
  renderBudget();
}

budgetRange.addEventListener("input", () => {
  budgetNumber.value = budgetRange.value;
  renderBudget();
});
budgetNumber.addEventListener("input", () => {
  budgetRange.value = Math.min(Number(budgetNumber.value) || 0, Number(budgetRange.max));
  renderBudget();
});
$("budget-form").addEventListener("change", (e) => {
  if (e.target.name?.startsWith("state-")) {
    const type = e.target.name.slice(6);
    partState[type] = e.target.value;
    e.target.closest(".part-row").className = `part-row state-${e.target.value}`;
  }
  if (e.target.name === "budget-cat" || e.target.id === "budget-console") renderParts();
  renderBudget();
});

renderParts();
renderBudget();

// ============================================================
//  2) Streamer-Setups
// ============================================================
let favorites = new Set();
let favApi = null; // wird gesetzt, sobald jemand eingeloggt ist

const setupTotal = (s) =>
  s.items.reduce((sum, id) => sum + (byId[id] && byId[id].billing !== "abo" ? byId[id].price : 0), 0);

$("streamer-cats").innerHTML =
  chip("streamer-cat", "", "Alle", true) +
  Object.entries(CATEGORIES).map(([k, c]) => chip("streamer-cat", k, `${c.icon} ${c.label}`, false)).join("");
// Bauteile im Filter "Enthält" nach Bereich gruppieren
$("streamer-type").innerHTML += Object.entries(GROUPS)
  .map(
    ([g, info]) =>
      `<optgroup label="${esc(info.label)}">${Object.entries(TYPES)
        .filter(([, t]) => t.group === g)
        .map(([k, t]) => `<option value="${k}">${t.icon} ${esc(t.label)}</option>`)
        .join("")}</optgroup>`
  )
  .join("");

function renderStreamers() {
  const q = $("streamer-search").value.trim().toLowerCase();
  const cat = document.querySelector('[name="streamer-cat"]:checked').value;
  const type = $("streamer-type").value;
  // Budget-Bereich, z. B. "500-1000" oder "3000-" (= ab 3.000 €)
  const [minPrice, maxPrice] = ($("streamer-price").value || "0-").split("-").map((v, i) => (v === "" ? (i ? Infinity : 0) : Number(v)));
  const onlyFavs = $("streamer-favs").checked;

  const list = STREAMERS.filter((s) => {
    const products = s.items.map((id) => byId[id]).filter(Boolean);
    if (cat && s.cat !== cat) return false;
    if (type && !products.some((p) => p.type === type)) return false;
    const total = setupTotal(s);
    if (total < minPrice || total > maxPrice) return false;
    if (onlyFavs && !favorites.has(s.id)) return false;
    if (q) {
      const hay = [s.name, s.games, CATEGORIES[s.cat].label, ...products.map((p) => p.name)].join(" ").toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });

  $("streamer-count").textContent = `${list.length} ${list.length === 1 ? "Setup" : "Setups"}`;
  $("streamer-grid").innerHTML = list.length
    ? list.map((s) => streamerCard(s, type)).join("")
    : `<div class="box empty"><p>${onlyFavs && !favApi ? "Melde dich an, um Favoriten zu speichern." : "Keine Setups gefunden. Probier andere Filter."}</p></div>`;
}

function streamerCard(s, highlightType) {
  const order = Object.keys(TYPES);
  const products = s.items
    .map((id) => byId[id])
    .filter(Boolean)
    .sort((a, b) => order.indexOf(a.type) - order.indexOf(b.type));
  const total = setupTotal(s);
  const isFav = favorites.has(s.id);
  return `<article class="setup-card">
    <header>
      <div class="avatar">${esc(s.name[0])}</div>
      <div class="setup-title">
        <h3>${esc(s.name)}</h3>
        <small>${CATEGORIES[s.cat].icon} ${esc(CATEGORIES[s.cat].label)} · ${s.followers.toLocaleString("de-DE")} Follower · seit ${s.since}</small>
      </div>
      <button type="button" class="fav-btn ${isFav ? "on" : ""}" data-fav="${esc(s.id)}" aria-pressed="${isFav}" aria-label="${isFav ? "Aus Favoriten entfernen" : "Zu Favoriten hinzufügen"}" title="Favorit">${isFav ? "★" : "☆"}</button>
    </header>
    <p class="games">${esc(s.games)}</p>
    <ul class="item-list compact">
      ${products
        .map(
          (p) => `<li class="${highlightType && p.type === highlightType ? "hl" : ""}">
            <span class="item-icon">${TYPES[p.type].icon}</span>
            <div class="item-main"><strong>${esc(p.name)}</strong></div>
            <span class="item-price">${priceLabel(p, "")}</span>
          </li>`
        )
        .join("")}
    </ul>
    <blockquote>„${esc(s.tip)}“</blockquote>
    <footer>
      <span>Gesamt ca. <strong>${euro(total)}</strong></span>
      ${s.source ? `<a href="${esc(s.source)}" target="_blank" rel="noopener">Quelle ↗</a>` : `<span class="badge">Beispiel</span>`}
    </footer>
  </article>`;
}

["streamer-search", "streamer-type", "streamer-price", "streamer-favs"].forEach((id) =>
  $(id).addEventListener("input", renderStreamers)
);
$("streamer-cats").addEventListener("change", renderStreamers);

$("streamer-grid").addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-fav]");
  if (!btn) return;
  if (!favApi) {
    document.querySelector('[data-open-auth="login"]')?.click();
    return;
  }
  const id = btn.dataset.fav;
  const add = !favorites.has(id);
  add ? favorites.add(id) : favorites.delete(id);
  renderStreamers();
  try {
    await favApi.save(id, add);
  } catch (err) {
    console.error("Favorit konnte nicht gespeichert werden:", err);
    add ? favorites.delete(id) : favorites.add(id);
    renderStreamers();
  }
});

renderStreamers();

// ---------- Favoriten in Firebase (users/<uid>/favorites) ----------
async function onAuth({ user, app }) {
  if (!user) {
    favApi = null;
    favorites = new Set();
    renderStreamers();
    return;
  }
  try {
    const db = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-database.js");
    const database = db.getDatabase(app);
    const path = (id = "") => db.ref(database, `users/${user.uid}/favorites/${id}`);
    const snap = await db.get(path());
    favorites = new Set(Object.keys(snap.val() || {}));
    favApi = { save: (id, add) => (add ? db.set(path(id), true) : db.remove(path(id))) };
  } catch (err) {
    console.error("Favoriten konnten nicht geladen werden:", err);
  }
  renderStreamers();
}
document.addEventListener("sge:auth", (e) => onAuth(e.detail));
if (window.sgeAuth) onAuth(window.sgeAuth);

// ============================================================
//  3) Hardware-Katalog
// ============================================================
$("catalog-types").innerHTML =
  chip("catalog-type", "", "Alle", true) +
  Object.entries(TYPES).map(([k, t]) => chip("catalog-type", k, `${t.icon} ${t.label}`, false)).join("");
$("catalog-cat").innerHTML += Object.entries(CATEGORIES)
  .map(([k, c]) => `<option value="${k}">${c.icon} ${esc(c.label)}</option>`)
  .join("");

function renderCatalog() {
  const type = document.querySelector('[name="catalog-type"]:checked').value;
  const cat = $("catalog-cat").value;
  const max = Number($("catalog-price").value);
  const sort = $("catalog-sort").value;
  $("catalog-price-label").textContent = max >= Number($("catalog-price").max) ? "egal" : euro(max);
  const unlimited = max >= Number($("catalog-price").max);

  const list = PRODUCTS.filter(
    (p) => (!type || p.type === type) && (!cat || p.cats.includes(cat)) && (unlimited || p.price <= max)
  ).sort(
    {
      score: (a, b) => b.score - a.score || a.price - b.price,
      "price-asc": (a, b) => a.price - b.price,
      "price-desc": (a, b) => b.price - a.price,
      value: (a, b) => b.score / Math.max(b.price, 1) - a.score / Math.max(a.price, 1),
    }[sort]
  );

  $("catalog-count").textContent = `${list.length} ${list.length === 1 ? "Produkt" : "Produkte"}`;
  $("catalog-grid").innerHTML = list.length
    ? list
        .map((p) => {
          const r = rating(p.score);
          return `<article class="product-card">
            <div class="product-top">
              <span class="item-icon">${TYPES[p.type].icon}</span>
              <span class="rating ${r.cls}">${r.label}</span>
            </div>
            <small class="eyebrow">${esc(TYPES[p.type].label)}</small>
            <h3>${esc(p.name)}</h3>
            <p>${esc(p.note)}</p>
            <div class="score"><span style="width:${p.score * 10}%"></span></div>
            <div class="product-foot">
              <strong>${priceLabel(p)}</strong>
              <span class="cats">${p.cats.map((c) => `<span title="${esc(CATEGORIES[c].label)}">${CATEGORIES[c].icon}</span>`).join("")}</span>
            </div>
          </article>`;
        })
        .join("")
    : `<div class="box empty"><p>Keine Produkte gefunden. Probier andere Filter.</p></div>`;
}

$("catalog-types").addEventListener("change", renderCatalog);
["catalog-cat", "catalog-price", "catalog-sort"].forEach((id) => $(id).addEventListener("input", renderCatalog));
renderCatalog();
