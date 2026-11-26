// Wochenplan-Seite (wochenplan.html): Formular → buildPlan() aus js/strategist-core.js → Plan.
//
// - Gerechnet wird NUR über buildPlan() – derselbe Kern, der per Paritätstest an Python gebunden
//   ist. Diese Datei kümmert sich nur um Formular, Darstellung, Kalender, Link und Speicher.
// - Alle Texte aus Daten und Plan per textContent (nie innerHTML). Der Ergebnisbereich trägt
//   translate="no": js/i18n.js übersetzt dort nichts, die Seite setzt jeden Text selbst in der
//   Sprache der Website (Beschriftungen über SGE_I18N.t, der Plan selbst kommt schon übersetzt).
// - Keine Anfragen an fremde Hosts: nur data/content-strategist.json vom eigenen Server.
// - Glücksspiel wird nie geplant (Fallstrick 15): buildPlan lehnt es ab, hier wird nur die
//   Meldung am Feld gezeigt; Vorschläge enthalten nie Glücksspiel.
import { buildPlan, isGamblingName, StrategistError } from "./strategist-core.js";

const STORAGE_KEY = "sge-wochenplan";
const SHARE_PREFIX = "p=";       // komprimiert (deflate-raw + base64url)
const SHARE_PLAIN_PREFIX = "j="; // Rückfall ohne CompressionStream
const MAX_SHARE_CHARS = 6000;
const MAX_GAMES = 5;
const MAX_WINDOWS = 21;
const DAYS = {
  de: ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
  en: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
};
const QUICK = {
  evenings: [0, 1, 2, 3, 4].map((day) => ({ day, start: "18:00", end: "22:00" })),
  weekend: [5, 6].map((day) => ({ day, start: "14:00", end: "18:00" })),
};
const DEFAULT_WINDOWS = [{ day: 0, start: "18:00", end: "22:00" }];
// Genre-Wörter, die als Spielvorschlag keinen Sinn ergeben.
const NOT_A_GAME = new Set(["horror", "cozy", "indie", "indie games", "talk", "chatting", "podcast",
  "podcasts", "talk shows", "talk shows podcasts", "travel outdoors", "metroidvania", "sims"]);

const i18n = window.SGE_I18N;
const T = (key) => (i18n ? i18n.t(key) : key);
const lang = () => (i18n ? i18n.getLanguage() : "de");

const $ = (selector) => document.querySelector(selector);
const form = $("#wp-form");
const gamesBox = $("#wp-games");
const windowsBox = $("#wp-windows");
const result = $("#wp-result");
const errorBox = $("#wp-errors");
const statusLine = $("#wp-status");

let data = null;
let shown = false; // Plan oder Fehler sichtbar → beim Sprachwechsel neu rechnen
let lastPlan = null;
let lastRequest = null;

// ------------------------------------------------------------------ kleine Helfer

function el(tag, options = {}, children = []) {
  const node = document.createElement(tag);
  if (options.className) node.className = options.className;
  if (options.text !== undefined && options.text !== null) node.textContent = String(options.text);
  for (const [key, value] of Object.entries(options.attrs || {})) node.setAttribute(key, value);
  for (const child of children) if (child) node.append(child);
  return node;
}

function storageGet() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function storageSet(value) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
  } catch {
    /* Kein Speicher (privates Fenster): dann eben nur bis zum Neuladen */
  }
}

async function copyText(text) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    /* weiter mit dem Rückfall */
  }
  const area = el("textarea", { attrs: { readonly: "", "aria-hidden": "true" } });
  area.value = text;
  area.style.position = "fixed";
  area.style.opacity = "0";
  document.body.append(area);
  area.select();
  let ok = false;
  try {
    ok = document.execCommand("copy");
  } catch {
    ok = false;
  }
  area.remove();
  return ok;
}

function copyButton(getText, label = "Kopieren") {
  const button = el("button", { className: "wp-copy", text: T(label), attrs: { type: "button" } });
  button.addEventListener("click", async () => {
    const ok = await copyText(getText());
    button.textContent = ok ? T("Kopiert ✓") : T("Kopieren nicht möglich – bitte manuell markieren.");
    button.dataset.copied = ok ? "1" : "0";
    setTimeout(() => { button.textContent = T(label); }, 2500);
  });
  return button;
}

// ------------------------------------------------------------------ Formular: Zeilen

function updateRowButtons() {
  const games = gamesBox.querySelectorAll(".wp-row");
  games.forEach((row) => { row.querySelector(".wp-remove").hidden = games.length === 1; });
  $("#wp-add-game").hidden = games.length >= MAX_GAMES;
  const windows = windowsBox.querySelectorAll(".wp-row");
  windows.forEach((row) => { row.querySelector(".wp-remove").hidden = windows.length === 1; });
  $("#wp-add-window").hidden = windows.length >= MAX_WINDOWS;
  gamesBox.querySelectorAll("input").forEach((input, index) => {
    input.setAttribute("aria-label", `${T("Spiel")} ${index + 1}`);
  });
}

function addGameRow(value = "") {
  if (gamesBox.children.length >= MAX_GAMES) return null;
  const input = el("input", { attrs: { type: "text", list: "wp-game-list", maxlength: "80", autocomplete: "off",
    placeholder: T("z. B. Minecraft") } });
  input.value = value;
  const remove = el("button", { className: "wp-remove", text: "✕", attrs: { type: "button", "aria-label": T("Entfernen") } });
  const row = el("div", { className: "wp-row wp-row-game" }, [input, remove]);
  remove.addEventListener("click", () => { row.remove(); updateRowButtons(); });
  gamesBox.append(row);
  updateRowButtons();
  return input;
}

function fillDayOptions(select) {
  const names = DAYS[lang()];
  if (!select.options.length) names.forEach((_, day) => select.add(new Option("", String(day))));
  [...select.options].forEach((option, day) => { option.textContent = names[day]; });
}

function addWindowRow({ day = 0, start = "18:00", end = "22:00" } = {}) {
  if (windowsBox.children.length >= MAX_WINDOWS) return null;
  const select = el("select", { attrs: { "aria-label": T("Wochentag") } });
  fillDayOptions(select);
  select.value = String(day);
  const from = el("input", { attrs: { type: "time", "aria-label": T("Von"), step: "900" } });
  from.value = start;
  const to = el("input", { attrs: { type: "time", "aria-label": T("Bis"), step: "900" } });
  to.value = end;
  const remove = el("button", { className: "wp-remove", text: "✕", attrs: { type: "button", "aria-label": T("Entfernen") } });
  const row = el("div", { className: "wp-row wp-row-window" },
    [select, from, el("span", { className: "wp-to", text: "–", attrs: { "aria-hidden": "true" } }), to, remove]);
  remove.addEventListener("click", () => { row.remove(); updateRowButtons(); });
  windowsBox.append(row);
  updateRowButtons();
  return row;
}

function readWindows() {
  return [...windowsBox.querySelectorAll(".wp-row")].map((row) => {
    const [select, from, to] = row.querySelectorAll("select, input");
    return { day: Number(select.value), start: from.value, end: to.value };
  });
}

function applyQuick(name) {
  const existing = readWindows();
  // Einzige Zeile mit dem Standardwert wird ersetzt, sonst wird ergänzt (ohne Doppelte).
  const onlyDefault = existing.length === 1 && JSON.stringify(existing[0]) === JSON.stringify(DEFAULT_WINDOWS[0]);
  if (onlyDefault) windowsBox.replaceChildren();
  const have = onlyDefault ? [] : existing;
  for (const window of QUICK[name]) {
    if (!have.some((w) => w.day === window.day && w.start === window.start && w.end === window.end)) {
      addWindowRow(window);
    }
  }
}

// ------------------------------------------------------------------ Formular ↔ Anfrage

function numberValue(input) {
  const text = input.value.trim();
  return text === "" ? "" : Number.isFinite(Number(text)) ? Number(text) : text;
}

// Formular → Anfrage wie der API-Body (ohne Sprache; die kommt von der Website).
function readForm() {
  const request = {
    games: [...gamesBox.querySelectorAll("input")].map((input) => input.value).filter((value) => value.trim() !== ""),
    windows: readWindows(),
    hours_per_week: numberValue($("#wp-hours")),
    streams_per_week: numberValue($("#wp-streams")),
    goal: $("#wp-goal").value,
    experience: $("#wp-experience").value,
  };
  const optional = {
    average_viewers: numberValue($("#wp-viewers")),
    active_chatters: numberValue($("#wp-chatters")),
    week_number: numberValue($("#wp-week")),
    mood: $("#wp-mood").value,
    rank_goal: $("#wp-rank-goal").value,
    current_rank: $("#wp-current-rank").value,
  };
  for (const [key, value] of Object.entries(optional)) if (value !== "") request[key] = value;
  const commands = $("#wp-commands").value.split(/[\s,]+/u).filter(Boolean);
  if (commands.length) request.commands = commands;
  if ($("#wp-first-time").checked) request.first_time = true;
  if ($("#wp-collab").checked) request.collab_partner = true;
  return request;
}

const SELECTS = { goal: ["discovery", "community", "consistency"], experience: ["beginner", "intermediate", "advanced"],
  mood: ["", "chill", "ambitious", "funny"] };

// Geprüfte Werte aus Speicher oder Link ins Formular (nur Grundtypen, Längen begrenzt).
function fillForm(raw) {
  if (!raw || typeof raw !== "object") return false;
  const text = (value, max) => (typeof value === "string" ? value.slice(0, max) : "");
  const num = (value) => (typeof value === "number" && Number.isFinite(value) ? String(value) : "");
  const games = Array.isArray(raw.games) ? raw.games.filter((g) => typeof g === "string").slice(0, MAX_GAMES) : [];
  gamesBox.replaceChildren();
  (games.length ? games : [""]).forEach((game) => addGameRow(text(game, 80)));
  const windows = Array.isArray(raw.windows) ? raw.windows.slice(0, MAX_WINDOWS) : [];
  windowsBox.replaceChildren();
  const valid = windows.filter((w) => w && Number.isInteger(w.day) && w.day >= 0 && w.day <= 6 &&
    typeof w.start === "string" && typeof w.end === "string");
  (valid.length ? valid : DEFAULT_WINDOWS).forEach((w) => addWindowRow({ day: w.day, start: text(w.start, 5), end: text(w.end, 5) }));
  $("#wp-hours").value = num(raw.hours_per_week) || "8";
  $("#wp-streams").value = num(raw.streams_per_week) || "3";
  $("#wp-viewers").value = num(raw.average_viewers) || "0";
  $("#wp-chatters").value = num(raw.active_chatters) || "0";
  $("#wp-week").value = num(raw.week_number) || "1";
  for (const [key, values] of Object.entries(SELECTS)) {
    const value = typeof raw[key] === "string" && values.includes(raw[key]) ? raw[key] : values[0];
    $(`#wp-${key}`).value = value;
  }
  $("#wp-rank-goal").value = text(raw.rank_goal, 20);
  $("#wp-current-rank").value = text(raw.current_rank, 20);
  $("#wp-commands").value = Array.isArray(raw.commands)
    ? raw.commands.filter((c) => typeof c === "string").slice(0, 3).join(" ").slice(0, 70) : "";
  $("#wp-first-time").checked = raw.first_time === true;
  $("#wp-collab").checked = raw.collab_partner === true;
  const hasMore = raw.mood || raw.rank_goal || raw.current_rank || (raw.commands && raw.commands.length) ||
    raw.first_time || raw.collab_partner || (raw.week_number && raw.week_number !== 1);
  if (hasMore) $("#wp-more").open = true;
  return true;
}

// ------------------------------------------------------------------ Fehler anzeigen

const FIELD_ERRORS = {
  games: "Bitte 1 bis 5 Spiele angeben, jeweils 2 bis 80 Zeichen.",
  hours_per_week: "Bitte 2 bis 60 Stunden angeben.",
  streams_per_week: "Bitte 1 bis 7 Streams angeben.",
  average_viewers: "Bitte eine ganze Zahl ab 0 angeben.",
  active_chatters: "Bitte eine ganze Zahl ab 0 angeben.",
  week_number: "Bitte eine Woche von 1 bis 520 angeben.",
  rank_goal: "Nur Buchstaben, Ziffern, Leerzeichen und +, höchstens 20 Zeichen.",
  current_rank: "Nur Buchstaben, Ziffern, Leerzeichen und +, höchstens 20 Zeichen.",
  commands: "Bis zu 3 Befehle wie !discord – nur Kleinbuchstaben, Ziffern und _.",
};
const FIELD_IDS = { games: "games", hours_per_week: "hours", streams_per_week: "streams", average_viewers: "viewers",
  active_chatters: "chatters", week_number: "week", rank_goal: "rank-goal", current_rank: "current-rank",
  commands: "commands", windows: "windows" };

function clearErrors() {
  errorBox.hidden = true;
  errorBox.replaceChildren();
  form.querySelectorAll(".wp-field-error").forEach((node) => { node.hidden = true; node.textContent = ""; });
  form.querySelectorAll("[aria-invalid]").forEach((node) => node.removeAttribute("aria-invalid"));
}

function fieldError(key, message, inputs = []) {
  const id = FIELD_IDS[key];
  const target = id ? $(`#wp-${id}-error`) : null;
  if (target) {
    target.textContent = message;
    target.hidden = false;
  }
  const field = id ? document.getElementById(`wp-${id}`) : null;
  const marked = inputs.length ? inputs : field && field.matches("input, select") ? [field] : [];
  marked.forEach((input) => {
    input.setAttribute("aria-invalid", "true");
    if (target && !input.getAttribute("aria-describedby")?.includes(target.id)) {
      input.setAttribute("aria-describedby", `${input.getAttribute("aria-describedby") || ""} ${target.id}`.trim());
    }
  });
  return marked[0] || null;
}

function showTop(messages) {
  errorBox.replaceChildren(...messages.map((message) => el("p", { text: message })));
  errorBox.hidden = false;
}

function showError(error, request) {
  result.hidden = true;
  lastPlan = null;
  let focus = null;
  if (error.kind === "validation") {
    const [key, index, part] = String(error.loc || "").split(".");
    if (key === "windows") {
      const rows = [...windowsBox.querySelectorAll(".wp-row")];
      const row = index !== undefined ? rows[Number(index)] : null;
      let message = T("Bitte mindestens ein Zeitfenster angeben.");
      let inputs = [];
      if (row) {
        const [select, from, to] = row.querySelectorAll("select, input");
        if (part === "day") {
          message = T("Bitte einen Wochentag wählen.");
          inputs = [select];
        } else if (part === "start" || part === "end") {
          message = T("Bitte Beginn und Ende als Uhrzeit angeben, z. B. 18:00 bis 22:00.");
          inputs = [part === "start" ? from : to];
        } else {
          message = T("Beginn und Ende sind gleich – das Zeitfenster braucht eine Dauer.");
          inputs = [from, to];
        }
      }
      focus = fieldError("windows", message, inputs);
    } else if (key === "games") {
      const inputs = [...gamesBox.querySelectorAll("input")];
      const empty = !request.games.length;
      focus = fieldError("games", T(empty ? "Bitte mindestens ein Spiel angeben." : FIELD_ERRORS.games),
        empty ? inputs.slice(0, 1) : inputs.filter((input) => {
          const size = [...input.value.trim()].length;
          return input.value.trim() !== "" && (size < 2 || size > 80);
        }));
    } else if (FIELD_ERRORS[key]) {
      if (FIELD_IDS[key] && ["mood", "rank_goal", "current_rank", "commands", "week_number"].includes(key)) $("#wp-more").open = true;
      focus = fieldError(key, T(FIELD_ERRORS[key]));
    }
    showTop([T("Bitte prüfe die markierten Felder.")]);
  } else {
    // Planfehler: Glücksspiel, zu wenig Zeit oder zu wenige Zeitfenster – Text kommt aus dem Kern.
    showTop([error.message]);
    const gambling = [...gamesBox.querySelectorAll("input")].filter((input) => input.value.trim() && isGamblingName(input.value, data));
    if (gambling.length && request.games.every((game) => isGamblingName(game, data))) {
      focus = fieldError("games", error.message, gambling);
    } else if (/^(Zu wenig Zeit|Not enough time)/u.test(error.message)) {
      focus = fieldError("hours_per_week", error.message);
    } else {
      focus = fieldError("windows", error.message, [...windowsBox.querySelectorAll("input")].slice(0, 1));
    }
  }
  statusLine.textContent = T("Der Plan konnte nicht erstellt werden.");
  return focus;
}

// ------------------------------------------------------------------ Plan berechnen und zeigen

function compute({ focusResult = false } = {}) {
  if (!data) return;
  clearErrors();
  const request = readForm();
  let plan;
  try {
    plan = buildPlan({ ...request, language: lang() }, data);
  } catch (error) {
    if (!(error instanceof StrategistError)) {
      showTop([T("Da ist etwas schiefgelaufen. Bitte lade die Seite neu.")]);
      shown = true;
      return;
    }
    const target = showError(error, request);
    shown = true;
    if (focusResult) {
      // Erst die Meldung oben zeigen (die feste Navigation verdeckt sonst das Feld), dann den
      // Fokus ohne Springen aufs erste markierte Feld setzen.
      errorBox.scrollIntoView({ block: "start" });
      target?.focus({ preventScroll: true });
    }
    return;
  }
  lastPlan = plan;
  lastRequest = request;
  shown = true;
  storageSet({ v: 1, request });
  renderPlan(plan);
  statusLine.textContent = `${T("Dein Wochenplan ist fertig")}: ${plan.streams.length} ${T(plan.streams.length === 1 ? "Stream" : "Streams")}.`;
  if (focusResult) {
    result.focus({ preventScroll: true });
    result.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function section(title, children, className = "") {
  return el("div", { className }, [el("h4", { text: T(title) }), ...children]);
}

function list(items, ordered = false) {
  return el(ordered ? "ol" : "ul", {}, items.map((item) => el("li", { text: item })));
}

function sessionText(session) {
  return `${session.label} ${session.start}–${session.end} · ${session.minutes} min`;
}

function titleRow(text, main) {
  return el("div", { className: `wp-title${main ? " wp-title-main" : ""}` },
    [el("span", { text }), copyButton(() => text)]);
}

function streamCard(stream) {
  const tags = el("div", { className: "wp-tags" }, [
    ...stream.tags.map((tag) => el("span", { className: "wp-tag", text: tag })),
    copyButton(() => stream.tags.join(", "), "Tags kopieren"),
  ]);
  const prep = section("Vorbereitung", [
    el("p", { className: "wp-dim", text: sessionText(stream.preparation) }),
    list(stream.prep_steps),
  ]);
  const clip = section("Clip danach", [
    el("p", { className: "wp-dim", text: stream.clip_day }),
    el("p", { text: stream.clip_idea }),
    el("p", {}, [el("strong", { text: `${T("Hook")}: ` }), document.createTextNode(stream.hook)]),
    el("p", { className: "wp-dim", text: T("Titel-Ideen fürs Kurzvideo:") }),
    list(stream.clip_title_ideas),
  ]);
  const flow = section("Ablauf", [list(stream.run_of_show, true),
    stream.break_note ? el("p", { className: "wp-dim", text: stream.break_note }) : null]);
  const why = el("details", { className: "wp-why" }, [
    el("summary", { text: T("Warum dieser Vorschlag?") }),
    el("p", { text: stream.why }),
    el("p", { text: stream.timing_reason }),
    el("p", {}, [el("strong", { text: `${T("Woran du es misst")}: ` }), document.createTextNode(stream.measurement)]),
  ]);
  return el("article", { className: "wp-card", attrs: { "data-stream": String(stream.number) } }, [
    el("p", { className: "wp-when", text: sessionText(stream.stream) }),
    el("h3", { text: stream.game }),
    el("p", { className: "wp-format", text: `${stream.format_name} · ${stream.genre_label}` }),
    section("Titel", [titleRow(stream.title, true)]),
    section("Alternativen", stream.title_alternatives.map((title) => titleRow(title, false))),
    section("Tags", [tags]),
    flow,
    prep,
    clip,
    why,
  ]);
}

function renderPlan(plan) {
  const total = plan.budget.stream_minutes;
  const hours = Math.floor(total / 60);
  const minutes = total % 60;
  const streamWord = T(plan.streams.length === 1 ? "Stream" : "Streams");
  const summary = `${plan.streams.length} ${streamWord} · ${hours} ${T("Std.")}${minutes ? ` ${minutes} min` : ""} ${T("live")} · ` +
    plan.games.map((game) => `${game.name} (${game.genre_label})`).join(", ");

  const shareInput = el("input", { attrs: { type: "text", readonly: "", "aria-label": T("Link zu diesem Plan") } });
  const shareRow = el("div", { className: "wp-share", attrs: { hidden: "" } }, [shareInput, copyButton(() => shareInput.value)]);
  const actionStatus = el("p", { className: "wp-action-status", attrs: { "aria-live": "polite" } });
  const icsButton = el("button", { className: "btn btn-small", text: T("Als Kalender herunterladen"), attrs: { type: "button", id: "wp-ics" } });
  const printButton = el("button", { className: "btn btn-small btn-ghost", text: T("Plan drucken"), attrs: { type: "button", id: "wp-print" } });
  const shareButton = el("button", { className: "btn btn-small btn-ghost", text: T("Link teilen"), attrs: { type: "button", id: "wp-share" } });
  icsButton.addEventListener("click", () => {
    const monday = upcomingMonday(new Date());
    downloadIcs(buildIcs(plan, monday));
    actionStatus.textContent = `${T("Kalender für die Woche ab")} ${formatDate(monday)} ${T("heruntergeladen.")}`;
  });
  printButton.addEventListener("click", () => window.print());
  shareButton.addEventListener("click", async () => {
    const url = await shareUrl(lastRequest);
    shareInput.value = url;
    shareRow.hidden = false;
    const ok = await copyText(url);
    actionStatus.textContent = ok ? T("Link kopiert.") : T("Link erstellt – bitte manuell kopieren.");
  });

  const notes = el("ul", { className: "wp-notes", attrs: { "aria-label": T("Hinweise") } }, [
    el("li", { className: "wp-notes-title", text: T("Hinweise") }),
    ...plan.notes.map((note) => el("li", { text: note })),
  ]);

  const extra = [];
  extra.push(el("section", {}, [
    el("h3", { text: `${T("Wochenrückblick")} · ${plan.review.day}${plan.review.minutes ? ` · ${plan.review.minutes} min` : ""}` }),
    list(plan.review.questions, true),
  ]));
  if (plan.series) {
    extra.push(el("section", {}, [
      el("h3", { text: `${T("Mini-Serie")}: ${plan.series.format_name} · ${plan.series.game}` }),
      list(plan.series.episodes, true),
    ]));
  }
  const budget = plan.budget;
  const rows = [
    ["Streamzeit", budget.stream_minutes], ["Vorbereitung", budget.preparation_minutes], ["Clips", budget.clip_minutes],
    ["Wochenrückblick", budget.review_minutes], ["Nicht verplant", budget.unplanned_minutes],
  ];
  extra.push(el("section", {}, [
    el("h3", { text: `${T("Zeitbudget")} · ${budget.weekly_minutes} min` }),
    el("dl", { className: "wp-budget" }, rows.flatMap(([label, value]) => [el("dt", { text: T(label) }), el("dd", { text: `${value} min` })])),
  ]));

  result.replaceChildren(
    el("h2", { text: T("Dein Wochenplan"), attrs: { id: "wp-result-title" } }),
    el("p", { className: "wp-summary", text: summary }),
    el("div", { className: "wp-actions" }, [icsButton, printButton, shareButton]),
    shareRow,
    actionStatus,
    notes,
    el("div", { className: "wp-cards" }, plan.streams.map(streamCard)),
    el("div", { className: "wp-extra" }, extra),
    el("p", { className: "wp-small", text: plan.twitch_limits }),
    el("ul", { className: "wp-small" }, plan.limitations.map((text) => el("li", { text }))),
  );
  result.hidden = false;
}

// ------------------------------------------------------------------ Kalender (.ics, Ortszeit)

function upcomingMonday(today) {
  const date = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const offset = (8 - date.getDay()) % 7; // Montag heute → 0, sonst der nächste Montag
  date.setDate(date.getDate() + offset);
  return date;
}

function formatDate(date) {
  return lang() === "de"
    ? `${String(date.getDate()).padStart(2, "0")}.${String(date.getMonth() + 1).padStart(2, "0")}.${date.getFullYear()}`
    : `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function atSession(monday, session) {
  const [hours, minutes] = session.start.split(":").map(Number);
  return new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + session.day, hours, minutes);
}

// Ohne Zeitzone („floating“): Kalender zeigen die Termine in der Ortszeit des Geräts.
function icsLocal(date) {
  const p = (n) => String(n).padStart(2, "0");
  return `${date.getFullYear()}${p(date.getMonth() + 1)}${p(date.getDate())}T${p(date.getHours())}${p(date.getMinutes())}00`;
}

function icsText(text) {
  return String(text).replace(/\\/g, "\\\\").replace(/;/g, "\\;").replace(/,/g, "\\,").replace(/\r?\n/g, "\\n");
}

// Zeilen nach RFC 5545 bei 75 Bytes (UTF-8) falten, ohne Zeichen zu zerteilen.
function fold(line) {
  const encoder = new TextEncoder();
  const out = [];
  let current = "";
  let bytes = 0;
  for (const ch of line) {
    const size = encoder.encode(ch).length;
    const limit = out.length ? 74 : 75;
    if (bytes + size > limit) {
      out.push(current);
      current = "";
      bytes = 0;
    }
    current += ch;
    bytes += size;
  }
  out.push(current);
  return out.join("\r\n ");
}

export function buildIcs(plan, monday, now = new Date()) {
  const stamp = now.toISOString().replace(/[-:]/g, "").replace(/\.\d+Z$/u, "Z");
  const lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Streaming Growth Engine//Wochenplan//DE", "CALSCALE:GREGORIAN"];
  const event = (uid, start, minutes, summary, description) => {
    const end = new Date(start.getTime() + minutes * 60000);
    lines.push("BEGIN:VEVENT", `UID:${uid}@streaming-growth-engine`, `DTSTAMP:${stamp}`,
      `DTSTART:${icsLocal(start)}`, `DTEND:${icsLocal(end)}`, `SUMMARY:${icsText(summary)}`,
      `DESCRIPTION:${icsText(description)}`, "END:VEVENT");
  };
  const week = icsLocal(monday).slice(0, 8);
  for (const stream of plan.streams) {
    const start = atSession(monday, stream.stream);
    let prep = atSession(monday, stream.preparation);
    if (prep > start) prep = new Date(prep.getFullYear(), prep.getMonth(), prep.getDate() - 7, prep.getHours(), prep.getMinutes());
    event(`wochenplan-${week}-${stream.number}-prep`, prep, stream.preparation.minutes,
      `${T("Vorbereitung")}: ${stream.game}`, stream.prep_steps.join("\n"));
    event(`wochenplan-${week}-${stream.number}-stream`, start, stream.stream.minutes,
      `${T("Stream")}: ${stream.game} – ${stream.format_name}`,
      [stream.title, "", ...stream.run_of_show.map((step, i) => `${i + 1}. ${step}`), "", `${T("Tags")}: ${stream.tags.join(", ")}`].join("\n"));
  }
  lines.push("END:VCALENDAR");
  return lines.map(fold).join("\r\n") + "\r\n";
}

function downloadIcs(text) {
  const url = URL.createObjectURL(new Blob([text], { type: "text/calendar;charset=utf-8" }));
  const link = el("a", { attrs: { href: url, download: lang() === "de" ? "wochenplan.ics" : "weekly-plan.ics" } });
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ------------------------------------------------------------------ Link teilen (#p=…)

function toBase64Url(bytes) {
  let binary = "";
  bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/u, "");
}

function fromBase64Url(text) {
  if (!/^[A-Za-z0-9_-]*$/u.test(text)) throw new Error("ungültige Zeichen");
  const binary = atob(text.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((text.length + 3) % 4));
  return Uint8Array.from(binary, (ch) => ch.charCodeAt(0));
}

async function streamBytes(stream, limit) {
  const reader = stream.getReader();
  const chunks = [];
  let size = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.length;
    if (size > limit) {
      await reader.cancel();
      throw new Error("zu groß");
    }
    chunks.push(value);
  }
  const out = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    out.set(chunk, offset);
    offset += chunk.length;
  }
  return out;
}

export async function encodeRequest(request) {
  const bytes = new TextEncoder().encode(JSON.stringify(request));
  if (typeof CompressionStream === "function") {
    const packed = await streamBytes(new Blob([bytes]).stream().pipeThrough(new CompressionStream("deflate-raw")), 1e6);
    return SHARE_PREFIX + toBase64Url(packed);
  }
  return SHARE_PLAIN_PREFIX + toBase64Url(bytes);
}

export async function decodeRequest(hash) {
  const code = hash.replace(/^#/u, "");
  if (code.length > MAX_SHARE_CHARS) throw new Error("zu lang");
  let bytes;
  if (code.startsWith(SHARE_PREFIX) && typeof DecompressionStream === "function") {
    const packed = fromBase64Url(code.slice(SHARE_PREFIX.length));
    bytes = await streamBytes(new Blob([packed]).stream().pipeThrough(new DecompressionStream("deflate-raw")), 20000);
  } else if (code.startsWith(SHARE_PLAIN_PREFIX)) {
    bytes = fromBase64Url(code.slice(SHARE_PLAIN_PREFIX.length));
  } else {
    throw new Error("unbekanntes Format");
  }
  const value = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("kein Objekt");
  return value;
}

async function shareUrl(request) {
  return `${location.origin}${location.pathname}#${await encodeRequest(request)}`;
}

// ------------------------------------------------------------------ Sprache, Start

function relabel() {
  form.querySelectorAll("option[data-de]").forEach((option) => { option.textContent = T(option.dataset.de); });
  windowsBox.querySelectorAll("select").forEach(fillDayOptions);
  gamesBox.querySelectorAll("input").forEach((input) => input.setAttribute("placeholder", T("z. B. Minecraft")));
  updateRowButtons();
}

function fillSuggestions() {
  const names = new Set();
  const title = (text) => text.replace(/(^|\s)(\p{L})/gu, (_, space, ch) => space + ch.toUpperCase());
  Object.values(data.category_aliases).forEach((name) => names.add(name));
  for (const [genre, label] of Object.entries(data.genres.labels)) if (genre === "just_chatting") names.add(label[0]);
  for (const aliases of Object.values(data.genres.aliases)) {
    for (const alias of aliases) {
      const words = alias.split(" ");
      if (alias.length < 5 || NOT_A_GAME.has(alias) || words.some((word) => word.length === 1 && !/\d/u.test(word))) continue;
      if (/[^\p{L}\p{N} ]/u.test(alias)) continue;
      names.add(title(alias));
    }
  }
  const list = $("#wp-game-list");
  [...names].filter((name) => !isGamblingName(name, data))
    .sort((a, b) => a.localeCompare(b, "de"))
    .forEach((name) => list.append(el("option", { attrs: { value: name } })));
}

async function loadFromHash() {
  if (!location.hash || location.hash.length < 3) return false;
  try {
    const request = await decodeRequest(location.hash);
    fillForm(request);
    compute({ focusResult: true });
  } catch {
    clearErrors();
    showTop([T("Dieser Link ist ungültig oder beschädigt. Du kannst den Plan einfach neu erstellen.")]);
  }
  return true;
}

async function init() {
  form.querySelectorAll("option").forEach((option) => { option.dataset.de = option.textContent; });
  addGameRow();
  addWindowRow(DEFAULT_WINDOWS[0]);
  $("#wp-add-game").addEventListener("click", () => addGameRow()?.focus());
  $("#wp-add-window").addEventListener("click", () => {
    const last = readWindows().at(-1) || DEFAULT_WINDOWS[0];
    addWindowRow({ ...last, day: (last.day + 1) % 7 })?.querySelector("select").focus();
  });
  form.querySelectorAll("[data-quick]").forEach((button) => button.addEventListener("click", () => applyQuick(button.dataset.quick)));
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    compute({ focusResult: true });
  });
  document.addEventListener("sge:language", () => {
    relabel();
    if (shown) compute();
  });
  relabel();

  try {
    const response = await fetch("data/content-strategist.json");
    if (!response.ok) throw new Error(String(response.status));
    data = await response.json();
  } catch {
    showTop([T("Der Wochenplan konnte nicht geladen werden. Bitte lade die Seite neu.")]);
    $("#wp-submit").disabled = true;
    return;
  }
  fillSuggestions();
  if (!(await loadFromHash())) {
    const saved = storageGet();
    if (saved && saved.v === 1) fillForm(saved.request);
  }
  window.addEventListener("hashchange", () => { loadFromHash(); });
  document.documentElement.dataset.wochenplan = "ready";
}

init();

// Für Browser-Tests: den zuletzt gezeigten Plan und die Kalenderdatei abrufen.
window.SGE_WOCHENPLAN = { plan: () => lastPlan, request: () => lastRequest, buildIcs, encodeRequest, decodeRequest };
