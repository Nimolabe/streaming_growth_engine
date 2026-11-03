// ============================================================
//  Setups-Seite: Budget-Planer, Streamer-Setups, Hardware-Katalog
// ============================================================
import { CATEGORIES, TYPES, NEEDS, PRODUCTS, STREAMERS } from "./setups-data.js";

const $ = (id) => document.getElementById(id);
const byId = Object.fromEntries(PRODUCTS.map((p) => [p.id, p]));
const euro = (n) => n.toLocaleString("de-DE") + " €";
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
// Findet die Kombination mit dem höchsten (Gewicht × Bewertung),
// die ins Budget passt. Bei so wenigen Produkten probieren wir einfach alle durch.
function planSetup(budget, cat, onConsole, owned) {
  let needs = NEEDS[cat].filter((n) => !owned.has(n.type));
  if (cat === "gaming" && onConsole && !owned.has("capture")) {
    needs = [...needs, { type: "capture", weight: 2.5, required: true }];
  }

  const options = needs.map((n) => {
    const list = PRODUCTS.filter((p) => p.type === n.type && p.cats.includes(cat)).sort((a, b) => a.price - b.price);
    return n.required ? list : [null, ...list];
  });

  // Mindestbudget = günstigstes Teil jedes Pflicht-Bauteils
  const minNeeded = options.reduce((sum, o) => sum + (o[0] ? o[0].price : 0), 0);
  if (minNeeded > budget) return { ok: false, minNeeded };

  let best = { value: -1, total: Infinity, items: [] };
  const chosen = [];
  (function search(i, total, value) {
    if (total > budget) return;
    if (i === options.length) {
      // Teile, die ein anderes Teil voraussetzen (z. B. XLR-Mikro → Interface)
      const picked = chosen.filter(Boolean);
      const usable = picked.every(
        (p) => !p.requires || owned.has(p.requires) || picked.some((q) => q.type === p.requires)
      );
      if (!usable) return;
      if (value > best.value || (value === best.value && total < best.total)) {
        best = { value, total, items: picked };
      }
      return;
    }
    for (const p of options[i]) {
      // Liste ist nach Preis sortiert → ab hier wird es nur teurer
      if (p && total + p.price > budget) break;
      chosen[i] = p;
      search(i + 1, total + (p ? p.price : 0), value + (p ? p.score * needs[i].weight : 0));
    }
    chosen[i] = undefined;
  })(0, 0, 0);

  return { ok: true, ...best, needs };
}

const budgetRange = $("budget-range");
const budgetNumber = $("budget-number");
const consoleRow = $("console-row");

$("budget-cats").innerHTML = Object.entries(CATEGORIES)
  .map(([k, c], i) => chip("budget-cat", k, `${c.icon} ${c.label}`, i === 0))
  .join("");

function renderOwnedChips() {
  const cat = currentCat();
  const types = NEEDS[cat].map((n) => n.type);
  if (cat === "gaming" && $("budget-console").checked) types.push("capture");
  const before = new Set([...document.querySelectorAll('[name="owned"]:checked')].map((i) => i.value));
  $("budget-owned").innerHTML = types
    .map((t) => chip("owned", t, `${TYPES[t].icon} ${TYPES[t].label}`, before.has(t), "checkbox"))
    .join("");
}

const currentCat = () => document.querySelector('[name="budget-cat"]:checked').value;

function renderBudget() {
  const budget = Math.max(0, Number(budgetNumber.value) || 0);
  const cat = currentCat();
  const onConsole = $("budget-console").checked;
  consoleRow.hidden = cat !== "gaming";
  const owned = new Set([...document.querySelectorAll('[name="owned"]:checked')].map((i) => i.value));

  const res = planSetup(budget, cat, onConsole, owned);
  const out = $("budget-result");

  if (!res.ok) {
    out.innerHTML = `<div class="box empty">
      <h3>Das wird knapp 😅</h3>
      <p>Für ein ${esc(CATEGORIES[cat].label)}-Setup brauchst du mindestens <strong>${euro(res.minNeeded)}</strong>.</p>
      <button type="button" class="btn btn-small" id="set-min">Budget auf ${euro(res.minNeeded)} setzen</button>
    </div>`;
    $("set-min").onclick = () => setBudget(res.minNeeded);
    return;
  }

  if (!res.items.length) {
    out.innerHTML = `<div class="box empty"><h3>Du hast schon alles! 🎉</h3><p>Dann bleibt nur noch eins: Go Live.</p></div>`;
    return;
  }

  const avg = res.items.reduce((s, p) => s + p.score, 0) / res.items.length;
  const r = rating(avg);
  const rest = budget - res.total;
  const missing = res.needs.filter((n) => !res.items.some((p) => p.type === n.type));

  // Upgrade-Tipp: Was bekäme man für 100 € mehr?
  let upgrade = "";
  const up = planSetup(budget + 100, cat, onConsole, owned);
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
            <span class="item-price">ca. ${euro(p.price)}</span>
          </li>`
        )
        .join("")}
    </ul>
    ${missing.length ? `<p class="hint">Noch nicht drin (optional): ${missing.map((n) => TYPES[n.type].label).join(", ")}. Kannst du später nachrüsten.</p>` : ""}
    ${rest > 0 ? `<p class="hint">Übrig: <strong>${euro(rest)}</strong>, gut für Kabel, Halterungen oder einen Mikrofonarm.</p>` : ""}
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
  if (e.target.name === "budget-cat" || e.target.id === "budget-console") renderOwnedChips();
  renderBudget();
});

renderOwnedChips();
renderBudget();

// ============================================================
//  2) Streamer-Setups
// ============================================================
let favorites = new Set();
let favApi = null; // wird gesetzt, sobald jemand eingeloggt ist

const setupTotal = (s) => s.items.reduce((sum, id) => sum + (byId[id]?.price || 0), 0);

$("streamer-cats").innerHTML =
  chip("streamer-cat", "", "Alle", true) +
  Object.entries(CATEGORIES).map(([k, c]) => chip("streamer-cat", k, `${c.icon} ${c.label}`, false)).join("");
$("streamer-type").innerHTML += Object.entries(TYPES)
  .map(([k, t]) => `<option value="${k}">${t.icon} ${esc(t.label)}</option>`)
  .join("");

function renderStreamers() {
  const q = $("streamer-search").value.trim().toLowerCase();
  const cat = document.querySelector('[name="streamer-cat"]:checked').value;
  const type = $("streamer-type").value;
  const maxPrice = Number($("streamer-price").value) || Infinity;
  const onlyFavs = $("streamer-favs").checked;

  const list = STREAMERS.filter((s) => {
    const products = s.items.map((id) => byId[id]).filter(Boolean);
    if (cat && s.cat !== cat) return false;
    if (type && !products.some((p) => p.type === type)) return false;
    if (setupTotal(s) > maxPrice) return false;
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
  const products = s.items.map((id) => byId[id]).filter(Boolean);
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
            <span class="item-price">${euro(p.price)}</span>
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
      value: (a, b) => b.score / b.price - a.score / a.price,
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
              <strong>ca. ${euro(p.price)}</strong>
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
