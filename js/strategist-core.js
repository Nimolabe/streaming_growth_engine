// Content Strategist – Planer-Kern für die Website (ES-Modul, ohne DOM, ohne Netzwerk, ohne Zufall).
//
// Entscheidung des Nutzers („Weg A“): Der Planer läuft im Browser, die INHALTE (Genres, Formate,
// Titel, Twitch-Grenzen, Glücksspiel-Liste) kommen als JSON-Export aus Python
// (data/content-strategist.json, erzeugt mit
// `python -m streaming_agents.content_strategist export-web`). Diese Datei enthält nur die
// LOGIK – eine genaue Übertragung von agents/streaming_agents/content_strategist/planner.py,
// titles.py, twitch_limits.py, genres.py und der Eingabeprüfung aus models.py.
//
// buildPlan(request, data) liefert denselben Plan wie build_plan(request, surface="web") in Python:
// gleiche Felder, gleiche Reihenfolge, gleiche Hinweise und Fehlermeldungen (DE/EN). Das prüft der
// Paritätstest (tests/fixtures/strategist-parity.json). Nicht enthalten ist der Kategorie-Check:
// er braucht das Twitch-Secret und läuft nie im Browser – also keine Messungen.
//
// Stolperfallen Python ↔ JavaScript (bewusst behandelt, siehe die Helfer unten):
// - Zeichenlänge: Python len() zählt Codepoints, JS .length UTF-16-Einheiten → cpLen/cpSlice.
// - Groß-/Kleinschreibung: Python casefold() faltet z. B. „ß“ → „ss“, JS toLowerCase() nicht
//   → casefold().
// - Unicode: Python \w ist Unicode-fähig, JS \w nur ASCII → \p{L}\p{N} mit u-Flag; Python \d
//   erkennt alle Dezimalziffern (z. B. „１８“) → \p{Nd} plus digitValue().
// - Leerzeichen: Python split()/strip() nutzen str.isspace() (inkl. \x1c–\x1f, \x85, ohne ﻿),
//   JS \s ist anders → PY_SPACE.
// - Sortierung: Python sorted() ist stabil und vergleicht Tupel; JS sort() ist seit ES2019 stabil
//   → Vergleich über compareTuples().
// - Ganzzahlen: Python // rundet ab, % ist nie negativ → floorDiv/mod.
// - Wochentage/Mitternacht: Wochenminuten (Mo 0:00 = 0) wie in Python, Modulo immer positiv.
// - String.replace(…, text) deutet „$&“ im Ersatztext → Platzhalter immer per Funktion ersetzen.

export const CORE_VERSION = 1;

// ------------------------------------------------------------------ Helfer (Python-Verhalten)

// Python str.isspace(): Whitespace für split()/strip() (ohne ﻿, aber mit \x1c–\x1f und \x85).
const PY_SPACE_CLASS = "\\t\\n\\v\\f\\r \\x1c-\\x1f\\x85\\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000";
const PY_SPACE = new RegExp(`[${PY_SPACE_CLASS}]+`, "u");
const PY_STRIP = new RegExp(`^[${PY_SPACE_CLASS}]+|[${PY_SPACE_CLASS}]+$`, "gu");

function pySplit(text) {
  return text.split(PY_SPACE).filter((part) => part !== "");
}

function pyStrip(text) {
  return text.replace(PY_STRIP, "");
}

function squash(text) {
  // Python: " ".join(text.split())
  return pySplit(text).join(" ");
}

// Codepoints statt UTF-16-Einheiten (Emojis zählen wie in Python als ein bzw. zwei Zeichen).
function cpLen(text) {
  return [...text].length;
}

function cpSlice(text, start, end) {
  return [...text].slice(start, end).join("");
}

// Python str.casefold(): toLowerCase() plus die vollen Faltungen, die toLowerCase() nicht kennt.
// Nicht abgedeckt sind seltene Sonderfälle (Cherokee-Kleinbuchstaben, armenische Ligaturen);
// die kommen in Spielnamen praktisch nicht vor.
const FOLD_EXTRA = {
  "ß": "ss", "ẞ": "ss", "ς": "σ", "ſ": "s", "µ": "μ", "ŉ": "ʼn", "ǰ": "ǰ",
  "ϐ": "β", "ϑ": "θ", "ϕ": "φ", "ϖ": "π", "ϰ": "κ", "ϱ": "ρ", "ϵ": "ε", "ẛ": "ṡ",
  "ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st",
  "ͅ": "ι", "ι": "ι",
};
const FOLD_RE = new RegExp(`[${Object.keys(FOLD_EXTRA).join("")}]`, "gu");

export function casefold(text) {
  return text.toLowerCase().replace(FOLD_RE, (ch) => FOLD_EXTRA[ch]);
}

// Python upper() für den ersten Buchstaben („ß“ → „SS“ wie in Python).
function upperFirst(text) {
  const chars = [...text];
  return chars.length ? chars[0].toUpperCase() + chars.slice(1).join("") : text;
}

function floorDiv(a, b) {
  return Math.floor(a / b);
}

function mod(a, b) {
  return ((a % b) + b) % b;
}

function compareTuples(a, b) {
  for (let i = 0; i < Math.min(a.length, b.length); i += 1) {
    const x = a[i];
    const y = b[i];
    if (x === y) continue;
    if (typeof x === "boolean") return (x ? 1 : 0) - (y ? 1 : 0);
    if (typeof x === "string") return x < y ? -1 : 1; // nur ASCII/BMP-Werte im Planer
    return x < y ? -1 : 1;
  }
  return a.length - b.length;
}

function sameWindow(a, b) {
  return a[0] === b[0] && a[1] === b[1];
}

function indexOfWindow(list, window) {
  return list.findIndex((item) => sameWindow(item, window));
}

// Platzhalter {name} ersetzen wie Python str.format (Werte werden nicht erneut ausgewertet).
function fill(template, values) {
  return template.replace(/\{(\w+)\}/g, (match, key) => {
    if (!(key in values)) throw new Error(`Platzhalter fehlt: ${key}`);
    return String(values[key]);
  });
}

function t(pair, language) {
  return language === "de" ? pair[0] : pair[1];
}

// Python \w bzw. [^\W_] für Unicode.
const WORD_RUN = /[^\p{L}\p{N}_]+/gu;
const ALNUM_RUN = /[\p{L}\p{N}]+/gu;
const TAG_RE = /^[\p{L}\p{N}]+$/u;
const COMPOUND_RE = /^[\p{L}\p{N}]+(?:[ -][\p{L}\p{N}]+)*$/u;
const RANK_RE = /^[\p{L}\p{N}][\p{L}\p{N}_ +]*$/u;

// genres.normalize bzw. category_check.aliases.normalize (identisches Ergebnis).
export function normalize(name) {
  const text = casefold(name).replaceAll("&", " ").replace(WORD_RUN, " ");
  return squash(text.replaceAll("_", " "));
}

// Python repr() für Texte (in Fehlermeldungen): einfache Anführungszeichen, Steuerzeichen escaped.
const NON_PRINTABLE = /[\p{Cc}\p{Cf}\p{Co}\p{Cn}\p{Cs}\p{Zl}\p{Zp}\p{Zs}]/u;

function pyRepr(value) {
  if (value === null || value === undefined) return "None";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : String(value);
  if (typeof value === "boolean") return value ? "True" : "False";
  if (typeof value !== "string") return String(value);
  const quote = value.includes("'") && !value.includes('"') ? '"' : "'";
  let out = "";
  for (const ch of value) {
    const cp = ch.codePointAt(0);
    if (ch === "\\") out += "\\\\";
    else if (ch === quote) out += `\\${quote}`;
    else if (ch === "\n") out += "\\n";
    else if (ch === "\r") out += "\\r";
    else if (ch === "\t") out += "\\t";
    else if (ch !== " " && NON_PRINTABLE.test(ch)) {
      if (cp <= 0xff) out += `\\x${cp.toString(16).padStart(2, "0")}`;
      else if (cp <= 0xffff) out += `\\u${cp.toString(16).padStart(4, "0")}`;
      else out += `\\U${cp.toString(16).padStart(8, "0")}`;
    } else out += ch;
  }
  return quote + out + quote;
}

// Zahlenwert einer Unicode-Dezimalziffer (Python int("１８") == 18). Unicode garantiert, dass
// Ziffern (Nd) in zusammenhängenden Zehnerblöcken 0–9 stehen.
const DIGIT = /^\p{Nd}$/u;

function digitValue(ch) {
  let cp = ch.codePointAt(0);
  const start = cp;
  while (DIGIT.test(String.fromCodePoint(cp - 1))) cp -= 1;
  return (start - cp) % 10;
}

function parseDigits(text) {
  let value = 0;
  for (const ch of text) value = value * 10 + digitValue(ch);
  return value;
}

// ------------------------------------------------------------------ Fehler

export class StrategistError extends Error {
  // kind: "validation" (Eingabe ungültig, wie pydantic) oder "plan" (wie PlanError in Python).
  constructor(kind, message, loc = null) {
    super(message);
    this.name = "StrategistError";
    this.kind = kind;
    this.loc = loc;
  }
}

function invalid(loc, message) {
  return new StrategistError("validation", message, loc);
}

function planError(message) {
  return new StrategistError("plan", message);
}

// ------------------------------------------------------------------ Eingabeprüfung (models.py)

function checkData(data) {
  if (!data || data.format !== 1 || !Array.isArray(data.formats)) {
    throw new Error("data/content-strategist.json fehlt oder hat ein unbekanntes Format");
  }
}

export function parseDay(value, data) {
  if (typeof value === "number" && Number.isInteger(value)) {
    if (value >= 0 && value <= 6) return value;
    throw new Error("Wochentag 0–6 (0 = Montag) / weekday 0–6 (0 = Monday)");
  }
  if (typeof value === "string") {
    const key = casefold(pyStrip(value)).replace(/\.+$/u, "");
    if (Object.hasOwn(data.input.day_aliases, key)) return data.input.day_aliases[key];
  }
  throw new Error(`Unbekannter Wochentag / unknown weekday: ${pyRepr(value)}`);
}

const TIME_RE = /^(\p{Nd}{1,2})(?::(\p{Nd}{2}))?$/u;

export function parseClock(value, data) {
  const help = data.input.clock_help;
  if (typeof value === "boolean") throw new Error(help);
  if (typeof value === "number") {
    if (!Number.isInteger(value)) throw new Error(`${help}: ${pyRepr(value)}`);
    if (value < 0 || value > 24) throw new Error(`${help}: ${pyRepr(value)}`);
    return value * 60;
  }
  const text = typeof value === "string" ? pyStrip(value) : pyRepr(value);
  const match = TIME_RE.exec(text);
  if (!match) throw new Error(`${help}: ${pyRepr(value)}`);
  const hours = parseDigits(match[1]);
  const minutes = match[2] ? parseDigits(match[2]) : 0;
  const total = hours * 60 + minutes;
  if (minutes >= 60 || total > 24 * 60) {
    throw new Error(`Ungültige Uhrzeit / invalid time: ${pyRepr(value)} (${help})`);
  }
  return total;
}

function formatClock(minutes) {
  return `${String(floorDiv(minutes, 60)).padStart(2, "0")}:${String(minutes % 60).padStart(2, "0")}`;
}

// pydantic-Meldungen für eingebaute Prüfungen (Typ, Grenzen, Auswahl, Pflichtfeld).
const MISSING = "Field required";

function literalMessage(options) {
  const quoted = options.map((option) => `'${option}'`);
  const head = quoted.slice(0, -1).join(", ");
  return `Input should be ${quoted.length > 1 ? `${head} or ${quoted.at(-1)}` : quoted[0]}`;
}

function toInt(value, loc) {
  if (typeof value === "number" && !Number.isNaN(value) && typeof value !== "boolean") {
    if (Number.isInteger(value)) return value;
    throw invalid(loc, "Input should be a valid integer, got a number with a fractional part");
  }
  if (typeof value === "boolean") return value ? 1 : 0;
  if (typeof value === "string") {
    const text = pyStrip(value);
    if (/^[+-]?\d+$/u.test(text)) return Number.parseInt(text, 10);
    throw invalid(loc, "Input should be a valid integer, unable to parse string as an integer");
  }
  throw invalid(loc, "Input should be a valid integer");
}

function intField(raw, key, { ge, le, def }) {
  if (raw[key] === undefined) {
    if (def === undefined) throw invalid(key, MISSING);
    return def;
  }
  const value = toInt(raw[key], key);
  if (ge !== undefined && value < ge) throw invalid(key, `Input should be greater than or equal to ${ge}`);
  if (le !== undefined && value > le) throw invalid(key, `Input should be less than or equal to ${le}`);
  return value;
}

const TRUE_WORDS = new Set(["1", "on", "t", "true", "y", "yes"]);
const FALSE_WORDS = new Set(["0", "off", "f", "false", "n", "no"]);

function boolField(raw, key) {
  const value = raw[key];
  if (value === undefined) return false;
  if (typeof value === "boolean") return value;
  if (value === 0 || value === 1) return value === 1;
  if (typeof value === "string") {
    const word = value.toLowerCase();
    if (TRUE_WORDS.has(word)) return true;
    if (FALSE_WORDS.has(word)) return false;
    throw invalid(key, "Input should be a valid boolean, unable to interpret input");
  }
  throw invalid(key, "Input should be a valid boolean");
}

function literalField(raw, key, options, def) {
  const value = raw[key] === undefined ? def : raw[key];
  if (value === null && def === null) return null;
  if (!options.includes(value)) throw invalid(key, literalMessage(options));
  return value;
}

function strValue(value, loc) {
  if (typeof value !== "string") throw invalid(loc, "Input should be a valid string");
  return value;
}

function listValue(value, loc) {
  if (!Array.isArray(value)) throw invalid(loc, "Input should be a valid list");
  return value;
}

function checkLength(list, loc, min, max) {
  if (min !== undefined && list.length < min) {
    throw invalid(loc, `List should have at least ${min} item${min === 1 ? "" : "s"} after validation, not ${list.length}`);
  }
  if (max !== undefined && list.length > max) {
    throw invalid(loc, `List should have at most ${max} item${max === 1 ? "" : "s"} after validation, not ${list.length}`);
  }
}

function parseWindow(raw, index, data) {
  const loc = `windows.${index}`;
  if (raw === null || typeof raw !== "object" || Array.isArray(raw)) {
    throw invalid(loc, "Input should be a valid dictionary or instance of TimeWindow");
  }
  const fields = {};
  for (const [key, parse] of [["day", parseDay], ["start", parseClock], ["end", parseClock]]) {
    if (raw[key] === undefined) throw invalid(`${loc}.${key}`, MISSING);
    try {
      fields[key] = parse(raw[key], data);
    } catch (error) {
      throw invalid(`${loc}.${key}`, error.message);
    }
  }
  const { day, start, end } = fields;
  if (mod(end - start, 1440) === 0 && !(start === 0 && end === 1440)) {
    throw invalid(loc, "Zeitfenster ohne Dauer / window has no duration");
  }
  if (start === 1440) {
    throw invalid(loc, "Beginn 24:00 → stattdessen 0:00 am Folgetag / use 0:00 next day");
  }
  const minutes = mod(end - start, 1440) || 1440;
  return { day, start, end, minutes, weekStart: day * 1440 + start };
}

function parseGames(raw) {
  if (raw.games === undefined) throw invalid("games", MISSING);
  const list = listValue(raw.games, "games");
  list.forEach((value, index) => strValue(value, `games.${index}`));
  checkLength(list, "games", 1, 5);
  const cleaned = [];
  for (const value of list) {
    const text = squash(value);
    const size = cpLen(text);
    if (size < 2 || size > 80) throw invalid("games", "Spielname 2–80 Zeichen / game name 2–80 characters");
    if (!cleaned.some((item) => casefold(item) === casefold(text))) cleaned.push(text);
  }
  return cleaned;
}

function parseRank(raw, key) {
  const value = raw[key];
  if (value === undefined || value === null) return null;
  strValue(value, key);
  if (cpLen(value) > 20) throw invalid(key, "String should have at most 20 characters");
  const text = squash(value);
  if (!text) return null;
  if (!RANK_RE.test(text) || text.includes("_")) {
    throw invalid(key, "Rang-Ziel nur mit Buchstaben, Ziffern, Leerzeichen und + / rank goal: letters, digits, spaces and + only");
  }
  return text;
}

function checkCommands(commands, data) {
  const max = data.titles.max_commands;
  if (commands.length > max) throw new Error(`Höchstens ${max} Befehle / at most ${max} commands`);
  // Python re.match mit „$“ erlaubt einen abschließenden Zeilenumbruch; nach strip() gibt es keinen.
  const pattern = new RegExp(data.titles.command_pattern);
  for (const command of commands) {
    if (!pattern.test(command)) {
      throw new Error(`Ungültiger Befehl / invalid command: ${pyRepr(command)} (Form: !name, Kleinbuchstaben, Ziffern, _)`);
    }
  }
  return [...new Set(commands)];
}

function parseCommands(raw, data) {
  if (raw.commands === undefined) return [];
  const list = listValue(raw.commands, "commands");
  list.forEach((value, index) => strValue(value, `commands.${index}`));
  try {
    return checkCommands(list.map((value) => pyStrip(value)), data);
  } catch (error) {
    throw invalid("commands", error.message);
  }
}

const MOOD_ALIASES = { chillig: "chill", entspannt: "chill", "gemütlich": "chill", ehrgeizig: "ambitious", lustig: "funny" };

function parseMood(raw) {
  let value = raw.mood === undefined ? null : raw.mood;
  if (typeof value === "string") {
    const key = casefold(pyStrip(value));
    value = (Object.hasOwn(MOOD_ALIASES, key) ? MOOD_ALIASES[key] : key) || null;
  }
  if (value === null) return null;
  if (!["chill", "ambitious", "funny"].includes(value)) {
    throw invalid("mood", literalMessage(["chill", "ambitious", "funny"]));
  }
  return value;
}

// Prüft und normalisiert eine Anfrage wie StrategyRequest in models.py. Wirft StrategistError
// mit kind "validation"; loc ist der Feldpfad wie bei pydantic (z. B. "windows.0.start").
export function parseRequest(raw, data) {
  checkData(data);
  if (raw === null || typeof raw !== "object" || Array.isArray(raw)) {
    throw invalid("", "Input should be a valid dictionary or object to extract fields from");
  }
  const games = parseGames(raw);
  if (raw.windows === undefined) throw invalid("windows", MISSING);
  const rawWindows = listValue(raw.windows, "windows");
  const windows = rawWindows.map((item, index) => parseWindow(item, index, data));
  checkLength(windows, "windows", 1, 21);
  const request = {
    games,
    windows,
    hours_per_week: intField(raw, "hours_per_week", { ge: 2, le: 60 }),
    streams_per_week: intField(raw, "streams_per_week", { ge: 1, le: 7 }),
    average_viewers: intField(raw, "average_viewers", { ge: 0, le: 1000000, def: 0 }),
    active_chatters: intField(raw, "active_chatters", { ge: 0, le: 1000000, def: 0 }),
    goal: literalField(raw, "goal", ["discovery", "community", "consistency"], "discovery"),
    experience: literalField(raw, "experience", ["beginner", "intermediate", "advanced"], "beginner"),
    language: literalField(raw, "language", ["de", "en"], "de"),
    platform: literalField(raw, "platform", ["twitch", "youtube", "kick", "tiktok", "other"], "twitch"),
    rank_goal: parseRank(raw, "rank_goal"),
    current_rank: parseRank(raw, "current_rank"),
    commands: parseCommands(raw, data),
    mood: parseMood(raw),
    first_time: boolField(raw, "first_time"),
    week_number: intField(raw, "week_number", { ge: 1, le: 520, def: 1 }),
    collab_partner: boolField(raw, "collab_partner"),
  };
  // Der Kategorie-Check läuft nie im Browser (Twitch-Secret) – Messungen gibt es hier nicht.
  if (Array.isArray(raw.measurements) && raw.measurements.length) {
    throw invalid("measurements", "Messungen werden in der Website-Version nicht unterstützt / measurements are not supported on the website");
  }
  return request;
}

// ------------------------------------------------------------------ Genres, Glücksspiel, Tags

export function detectGenre(game, data) {
  const words = ` ${normalize(game)} `;
  for (const [alias, genre] of data.genres.alias_table) {
    if (alias && words.includes(` ${alias} `)) return genre;
  }
  return null;
}

function genreLabel(genre, language, data) {
  const pair = genre && data.genres.labels[genre] ? data.genres.labels[genre] : data.genres.unknown_label;
  return t(pair, language);
}

function aliasTarget(name, data) {
  const key = normalize(name);
  const target = Object.hasOwn(data.category_aliases, key) ? data.category_aliases[key] : null;
  if (target === null || normalize(target) === key) return null;
  return target;
}

// category_check/gambling.py: is_gambling_name (Fallstrick 15 – Glücksspiel wird nie geplant).
export function isGamblingName(name, data) {
  const names = data.gambling.names;
  const target = aliasTarget(name, data);
  return names.includes(normalize(name)) || (target !== null && names.includes(normalize(target)));
}

function rejection(name, language, data) {
  return data.gambling.rejection[language].split("{name}").join(name);
}

function isValidTag(tag, data) {
  const size = cpLen(tag);
  return size > 0 && size <= data.twitch_limits.tag_max_chars && TAG_RE.test(tag);
}

function tagFromText(text, data) {
  const words = text.replaceAll("'", "").replaceAll("’", "").match(ALNUM_RUN) || [];
  const joined = words.map((word) => upperFirst(cpSlice(word, 0, 1)) + cpSlice(word, 1)).join("");
  const tag = cpSlice(joined, 0, data.twitch_limits.tag_max_chars);
  return isValidTag(tag, data) ? tag : null;
}

function cleanTags(candidates, data) {
  const result = [];
  const seen = new Set();
  for (const raw of candidates) {
    const tag = isValidTag(raw, data) ? raw : tagFromText(raw, data);
    if (tag === null || seen.has(casefold(tag))) continue;
    seen.add(casefold(tag));
    result.push(tag);
    if (result.length === data.twitch_limits.tags_max_count) break;
  }
  return result;
}

function fitTitle(title, data) {
  const max = data.twitch_limits.title_max_chars;
  const text = squash(title);
  if (cpLen(text) <= max) return text;
  let cut = cpSlice(text, 0, max - 1);
  if (cut.includes(" ")) cut = cut.slice(0, cut.lastIndexOf(" "));
  return cut.replace(/[ \-|:,]+$/u, "") + "…";
}

// ------------------------------------------------------------------ Titel (titles.py)

function daypart(minuteOfDay, data) {
  const hour = mod(floorDiv(minuteOfDay, 60), 24);
  for (const [limit, noun, nounM, english] of data.titles.dayparts) {
    if (hour < limit) return [noun, nounM, english];
  }
  return data.titles.dayparts.at(-1).slice(1);
}

function compoundWithDaypart(game, noun) {
  const name = squash(game);
  if (COMPOUND_RE.test(name)) return `${name.replaceAll(" ", "-")}-${noun}`;
  return `${noun} in ${name}`;
}

function streamMood(formatId, genre, requested, data) {
  if (requested) return requested;
  const own = data.titles.stream_titles[formatId].mood;
  if (own) return own;
  const key = genre === null ? "_general" : genre;
  return Object.hasOwn(data.titles.genre_mood, key) ? data.titles.genre_mood[key] : "chill";
}

function firstBlock(text, separator) {
  return text.split(separator)[0];
}

function buildTitles(formatId, genre, game, language, options, data) {
  const { counter, startMinute, mood, rankGoal, currentRank, rankCounter, firstTime, rotation, commands } = options;
  const titles = data.titles;
  const separator = titles.separator;
  const index = language === "de" ? 0 : 1;
  const item = titles.stream_titles[formatId];
  const current = streamMood(formatId, genre, mood, data);
  const [zeit, zeitM, time] = daypart(mod(startMinute, 1440), data);
  const fills = {};
  for (const [key, value] of Object.entries(titles.fills[formatId] || {})) fills[key] = value[index];
  const values = {
    game, game_zeit: compoundWithDaypart(game, zeit), zeit, zeit_m: zeitM, time, n: counter,
    k: rankCounter, rank: rankGoal || "", from: currentRank || "", ...fills,
  };

  const ranked = item.ranked && titles.ranked_genres.includes(genre);
  let goal;
  if (ranked && rankGoal) goal = (currentRank ? titles.rank_journey : titles.rank_goal)[index];
  else if (firstTime && item.first) goal = item.first[index];
  else goal = item.goal[index];
  const moods = titles.mood_titles[genre !== null && Object.hasOwn(titles.mood_titles, genre) ? genre : "_general"];
  const genreMood = moods[current][index];
  let moodText = genreMood;
  if (ranked && current === "ambitious") {
    moodText = (rankGoal ? titles.ranked_goal_mood : titles.ranked_mood)[index];
    // Beginnt das Ziel schon mit demselben Baustein, nimm den Stimmungs-Titel des Genres.
    if (firstBlock(fill(moodText, values), separator) === firstBlock(fill(goal, values), separator)) {
      moodText = genreMood;
    }
  }

  const suffix = commands.join(" ");
  const max = data.twitch_limits.title_max_chars;
  const result = [];
  for (const [approach, template] of [["goal", goal], ["mood", moodText], ["invite", item.invite[index]]]) {
    const text = fill(template, values);
    const fits = suffix && cpLen(text) + cpLen(separator) + cpLen(suffix) <= max;
    const extra = fits ? suffix : "";
    result.push({ text, approach, full: extra ? `${text}${separator}${extra}` : text });
  }
  const start = mod(rotation, result.length);
  return [...result.slice(start), ...result.slice(0, start)];
}

function clipTitles(formatId, language, data) {
  const index = language === "de" ? 0 : 1;
  return data.titles.clip_titles[formatId].map((pair) => pair[index]);
}

// ------------------------------------------------------------------ Planer (planner.py)

const WEEK = 7 * 1440;

function chatLevel(activeChatters) {
  if (activeChatters <= 2) return "none";
  if (activeChatters <= 7) return "low";
  return "active";
}

function clock(minuteOfWeek) {
  const minute = mod(minuteOfWeek, 1440);
  return formatClock(minute);
}

function dayOf(minuteOfWeek) {
  return floorDiv(mod(minuteOfWeek, WEEK), 1440);
}

function session(start, minutes, language, data) {
  const labels = data.input.day_labels;
  const end = start + minutes;
  let label = labels[language][dayOf(start)];
  if (dayOf(end - 1) !== dayOf(start)) {
    label += language === "de" ? ` (bis ${labels.de[dayOf(end - 1)]})` : ` (until ${labels.en[dayOf(end - 1)]})`;
  }
  return { day: dayOf(start), label, start: clock(start), end: clock(end), minutes };
}

function mergedWindows(request) {
  const spans = request.windows
    .map((w) => [w.weekStart, w.weekStart + w.minutes])
    .sort(compareTuples);
  const merged = [];
  for (const [start, end] of spans) {
    if (merged.length && start <= merged.at(-1)[1]) {
      merged.at(-1)[1] = Math.max(merged.at(-1)[1], end);
    } else {
      merged.push([start, end]);
    }
  }
  // Ein Fenster über das Wochenende hinaus (So → Mo) kann mit dem ersten verschmelzen.
  if (merged.length > 1 && merged.at(-1)[1] >= merged[0][0] + WEEK) {
    const first = merged.shift();
    merged.at(-1)[1] = Math.max(merged.at(-1)[1], first[1] + WEEK);
  }
  return merged;
}

function trimSteps(p) {
  // Reihenfolge beim Kürzen: Wochenrückblick → Clip-Zeit → Vorbereitung auf 15 min.
  const full = { prep: p.prep_minutes, clip: p.clip_minutes, review: p.review_minutes };
  return [
    full,
    { ...full, review: 15 }, { ...full, review: 0 },
    { ...full, clip: 15, review: 0 }, { ...full, clip: 0, review: 0 },
    { prep: p.min_prep_minutes, clip: 0, review: 0 },
  ];
}

function isTrimmed(extras, p) {
  return extras.prep !== p.prep_minutes || extras.clip !== p.clip_minutes || extras.review !== p.review_minutes;
}

function lengthFor(request, extras, p) {
  const count = request.streams_per_week;
  const available = request.hours_per_week * 60 - extras.review - count * (extras.prep + extras.clip);
  return Math.min(p.max_stream, floorDiv(floorDiv(Math.max(0, available), count), p.step) * p.step);
}

function streamLength(request, p) {
  for (const extras of trimSteps(p)) {
    const length = lengthFor(request, extras, p);
    if (length >= p.min_stream) return [length, extras];
  }
  const count = request.streams_per_week;
  const needed = -floorDiv(-(count * (p.min_stream + p.min_prep_minutes)), 60);
  if (request.language === "de") {
    throw planError(
      `Zu wenig Zeit: ${count} Streams mit je mindestens ${p.min_stream} Minuten plus ` +
      `${p.min_prep_minutes} Minuten Vorbereitung brauchen mindestens ${needed} Stunden pro ` +
      "Woche (Clips und Wochenrückblick sind dabei schon weggelassen). Die Stunden pro " +
      "Woche sind die gesamte Zeit inklusive Vorbereitung. Weniger Streams planen oder " +
      "mehr Stunden angeben.");
  }
  throw planError(
    `Not enough time: ${count} streams of at least ${p.min_stream} minutes plus ` +
    `${p.min_prep_minutes} minutes of preparation need at least ${needed} hours per week ` +
    "(already without clips and weekly review). Hours per week are the total time " +
    "including preparation. Plan fewer streams or more hours.");
}

function trimNote(extras, language, p) {
  if (!isTrimmed(extras, p)) return null;
  const de = language === "de";
  const parts = [];
  if (extras.review !== p.review_minutes) {
    parts.push(de
      ? (extras.review ? `Wochenrückblick auf ${extras.review} min gekürzt` : "Wochenrückblick weggelassen")
      : (extras.review ? `weekly review cut to ${extras.review} min` : "weekly review left out"));
  }
  if (extras.clip !== p.clip_minutes) {
    parts.push(de
      ? (extras.clip ? `Clip-Zeit auf ${extras.clip} min pro Stream gekürzt` : "keine feste Clip-Zeit")
      : (extras.clip ? `clip time cut to ${extras.clip} min per stream` : "no fixed clip time"));
  }
  if (extras.prep !== p.prep_minutes) {
    parts.push(de ? `Vorbereitung auf ${extras.prep} min gekürzt` : `preparation cut to ${extras.prep} min`);
  }
  if (de) {
    return "Die Zeit ist knapp: Damit jeder Stream mindestens 60 Minuten hat, wurden " +
      `Zusatzaufgaben gekürzt (${parts.join(", ")}). Die Stunden pro Woche ` +
      "zählen Vorbereitung, Clips und Rückblick mit – mit etwas mehr Zeit passt alles.";
  }
  return "Time is tight: so that every stream gets at least 60 minutes, extra tasks were " +
    `trimmed (${parts.join(", ")}). Hours per week include preparation, clips and ` +
    "the review – with a bit more time everything fits.";
}

function formatsFor(genre, data) {
  return data.formats.filter((item) => item.genre === genre);
}

function score(item, request) {
  let value = 0;
  if (item.goals.includes(request.goal)) value += 3;
  if (item.expert && request.experience === "beginner") value -= 3;
  if (item.expert && request.experience === "advanced") value += 1;
  if (item.needs_chat === "low") value += 2;
  if (item.needs_chat === "active") value += 3;
  if (item.needs_collab) value += 2;
  if (item.series.length && request.goal === "consistency") value += 1;
  return value;
}

function eligible(item, request, level, p) {
  if (p.chat_order[item.needs_chat] > p.chat_order[level]) return false;
  return request.collab_partner || !item.needs_collab;
}

function ranked(genre, request, level, data) {
  const p = data.planner;
  const order = new Map(data.formats.map((item, index) => [item.id, index]));
  const pool = formatsFor(genre, data).filter((item) => eligible(item, request, level, p) &&
    !item.week_end && (request.first_time || !item.first_time_only));
  return pool.sort((a, b) => compareTuples([-score(a, request), order.get(a.id)], [-score(b, request), order.get(b.id)]));
}

function weekCloser(genre, request, level, data) {
  for (const item of formatsFor(genre, data)) {
    if (item.week_end && eligible(item, request, level, data.planner) && item.goals.includes(request.goal)) return item;
  }
  return null;
}

function nextFormat(queue, position, firstOfGame) {
  // Formate mit Vorgeschichte nie als erster Stream eines Spiels in Woche 1 (Platz tauschen).
  const size = queue.length;
  const index = position % size;
  if (firstOfGame) {
    for (let offset = 0; offset < size; offset += 1) {
      const candidate = (index + offset) % size;
      if (!queue[candidate].needs_history) {
        [queue[index], queue[candidate]] = [queue[candidate], queue[index]];
        break;
      }
    }
  }
  return queue[index];
}

function why(item, genre, request, data) {
  const de = request.language === "de";
  const parts = [genre
    ? (de ? `passt zu ${genreLabel(genre, "de", data)}` : `fits ${genreLabel(genre, "en", data)}`)
    : (de ? "allgemeines Format, weil kein Genre erkannt wurde" : "general format because no genre was recognised")];
  parts.push(item.needs_chat === "none"
    ? (de ? "funktioniert ohne Chat" : "works without chat")
    : (de ? "nutzt deinen aktiven Chat" : "uses your active chat"));
  if (item.needs_collab) parts.push(de ? "mit deinem Mitspieler" : "with your teammate");
  if (item.goals.includes(request.goal)) {
    const goal = t(data.planner.goal_label[request.goal], request.language);
    parts.push(de ? `unterstützt dein Ziel „${goal}“` : `supports your goal '${goal}'`);
  }
  if (item.expert && request.experience === "beginner") {
    parts.push(de ? "braucht etwas Vorbereitung" : "needs some preparation");
  }
  const text = parts.join("; ");
  return `${upperFirst(cpSlice(text, 0, 1))}${cpSlice(text, 1)}.`;
}

function tags(game, genre, item, language, data) {
  const candidates = [];
  if (genre !== "just_chatting") {
    const gameTag = tagFromText(game, data);
    if (gameTag) candidates.push(gameTag);
  }
  candidates.push(language === "de" ? "Deutsch" : "English");
  if (genre) candidates.push(t(data.planner.genre_tag[genre], language));
  for (const pair of item.tags) candidates.push(t(pair, language));
  return cleanTags(candidates, data);
}

function spread(windows, count) {
  // Reihenfolge ohne Messungen: über die Woche verteilen, ein Stream pro Tag bevorzugt.
  const byDay = new Map();
  for (const window of windows) {
    const day = dayOf(window[0]);
    const current = byDay.get(day);
    if (current === undefined || window[1] - window[0] > current[1] - current[0]) byDay.set(day, window);
  }
  const days = [...byDay.values()].sort(compareTuples);
  let picks;
  if (days.length >= count) {
    const step = days.length / count;
    picks = Array.from({ length: count }, (_, i) => days[Math.trunc(i * step)]);
  } else {
    picks = [...days];
  }
  const inPicks = (w) => indexOfWindow(picks, w) >= 0;
  const rest = windows.filter((w) => !inPicks(w))
    .sort((a, b) => compareTuples([-(a[1] - a[0]), a[0]], [-(b[1] - b[0]), b[0]]));
  return [...picks, ...days.filter((w) => !inPicks(w)), ...rest];
}

function breakNote(minutes, language) {
  if (minutes < 120) return null;
  const marks = [1, 2, 3].map((i) => 90 * i).filter((mark) => mark < minutes - 20);
  const times = marks.join(", ");
  if (language === "de") {
    return `Pause einplanen: nach etwa ${times} Minuten je 5–10 Minuten (in der Streamzeit ` +
      "enthalten). Die Szene „Pause“ aus dem Layout-Baukasten passt dafür.";
  }
  return `Plan breaks: 5–10 minutes after about ${times} minutes (included in the stream ` +
    "time). The “Pause” scene from the layout builder fits this.";
}

function clipDay(day, minutes, language) {
  if (minutes) {
    return language === "de" ? `${day} (Tag nach dem Stream), ${minutes} min` : `${day} (day after the stream), ${minutes} min`;
  }
  return language === "de"
    ? `${day} (Tag nach dem Stream), nur wenn Zeit übrig ist – keine feste Clip-Zeit`
    : `${day} (day after the stream), only if you have time left – no fixed clip time`;
}

function timingReason(game, stream, request) {
  // Ohne Messungen (im Browser gibt es keinen Kategorie-Check) bleibt nur dieser Fall.
  const window = `${stream.label} ${stream.start}–${stream.end}`;
  return request.language === "de"
    ? `Uhrzeit (${window}) kommt nur aus deinem Zeitfenster – ohne Messungen weiß der Plan ` +
      `nicht, wann in ${game} am meisten los ist.`
    : `The time (${window}) only comes from your window – without measurements the plan ` +
      `doesn't know when ${game} is busiest.`;
}

function weekMinute(sessionInfo) {
  const [hours, minutes] = sessionInfo.start.split(":");
  return sessionInfo.day * 1440 + Number(hours) * 60 + Number(minutes);
}

function isRankStream(entry, genres, request, data) {
  return Boolean(request.rank_goal) && data.titles.stream_titles[entry.format_id].ranked &&
    ["shooter", "battle_royale", "moba", "sports"].includes(genres.get(entry.game));
}

function notesFor(request, level, genres, streams, extras, data) {
  const de = request.language === "de";
  const notes = [];
  const trim = trimNote(extras, request.language, data.planner);
  if (trim) notes.push(trim);
  if (level === "none") {
    notes.push(de
      ? "Weil höchstens 2 Leute aktiv chatten, enthält der Plan nur Formate, die ohne Chat " +
        "funktionieren – mit Messgrößen, die keine Chat-Reaktionen brauchen."
      : "Because at most 2 people chat actively, the plan only contains formats that work " +
        "without chat – with measurements that don't need chat reactions.");
  }
  for (const [game, genre] of genres) {
    if (genre === null) {
      notes.push(de
        ? `„${game}“: kein Genre erkannt – der Plan nutzt allgemeine Formate. Falls die ` +
          "Schreibweise nicht stimmt: die Twitch-Kategorie genau angeben."
        : `“${game}”: no genre recognised – the plan uses general formats. If the spelling ` +
          "is off, use the exact Twitch category.");
    }
  }
  // Ohne Messungen: derselbe ehrliche Hinweis wie in Python, aber ohne Kommandozeilen-Befehl.
  notes.push(t(data.planner.no_measurements_note, request.language));
  if (request.platform !== "twitch") {
    notes.push(de
      ? "Titel und Tags folgen den Twitch-Grenzen; auf anderen Plattformen gelten eigene Regeln."
      : "Titles and tags follow Twitch's limits; other platforms have their own rules.");
  }
  if (streams.some((item) => item.needs_collab)) {
    notes.push(de
      ? "Koop- und Coach-Formate nur mit Einverständnis der Mitspieler, dass sie im Stream zu " +
        "hören sind."
      : "Co-op and coach formats only with your teammates' consent to be heard on stream.");
  }
  if (new Set(streams.map((item) => item.stream.day)).size === 7) {
    notes.push(de
      ? "Der Plan hat keinen freien Tag. Ein Tag ohne Stream hilft gegen Überlastung."
      : "The plan has no day off. One day without streaming helps against burnout.");
  }
  const repeated = streams.some((item) => streams.filter((other) => other.format_id === item.format_id).length > 1);
  if (repeated) {
    notes.push(de
      ? "Manche Formate kommen mehrmals vor – Wiederholung macht den Kanal für Stammzuschauer " +
        "wiedererkennbar."
      : "Some formats appear more than once – repetition makes the channel recognisable for " +
        "regulars.");
  }
  return notes;
}

// Wochenplan wie build_plan(request, surface="web") in planner.py.
// request: rohe Eingabe (wie der API-Body von POST /api/v1/content/strategy, ohne Messungen).
export function buildPlan(rawRequest, data) {
  const request = parseRequest(rawRequest, data);
  const p = data.planner;
  const lang = request.language;
  const de = lang === "de";
  const labels = data.input.day_labels;

  // Glücksspiel wird nicht unterstützt (Fallstrick 15): kein Plan, keine Titel, keine Formate.
  const refused = request.games.filter((game) => isGamblingName(game, data));
  const games = request.games.filter((game) => !refused.includes(game));
  if (!games.length) throw planError(refused.map((game) => rejection(game, lang, data)).join(" "));
  const level = chatLevel(request.active_chatters);
  const [length, extras] = streamLength(request, p);
  const count = request.streams_per_week;

  const windows = mergedWindows(request).filter((w) => w[1] - w[0] >= p.min_stream);
  if (windows.length < count) {
    throw planError(de
      ? `Du hast ${windows.length} nutzbare(s) Zeitfenster (mindestens ${p.min_stream} Minuten), ` +
        `aber ${count} Streams geplant. Mehr Zeitfenster angeben oder weniger Streams planen.`
      : `You have ${windows.length} usable window(s) (at least ${p.min_stream} minutes) but ` +
        `planned ${count} streams. Add windows or plan fewer streams.`);
  }

  const genres = new Map(games.map((game) => [game, detectGenre(game, data)]));
  const gameInfos = games.map((game) => ({
    name: game, genre: genres.get(game), genre_label: genreLabel(genres.get(game), lang, data),
    genre_recognized: genres.get(game) !== null, category_check: null,
  }));

  // Zeitfenster wählen: ohne Messungen gleichmäßig über die Woche verteilt.
  const assignment = [];
  const free = [...windows];
  const usedDays = new Set();
  const spreadOrder = spread(windows, count);
  for (let index = 0; index < count; index += 1) {
    const game = games[index % games.length];
    let best = null;
    for (const window of free) {
      const winLen = Math.min(length, floorDiv(window[1] - window[0], p.step) * p.step);
      const position = indexOfWindow(spreadOrder, window);
      const key = [1, false, 0, usedDays.has(dayOf(window[0])) ? 1 : 0,
        position >= 0 ? position : windows.length, window[0]];
      if (best === null || compareTuples(key, best.key) < 0) best = { key, window, start: window[0], winLen };
    }
    free.splice(indexOfWindow(free, best.window), 1);
    usedDays.add(dayOf(best.window[0]));
    assignment.push({ game, start: best.start, minutes: best.winLen });
  }
  assignment.sort((a, b) => a.start - b.start);

  // Formate: pro Genre reihum aus der Rangliste, damit sich Ideen nicht wiederholen.
  const queues = new Map();
  const position = new Map();
  const streams = [];
  const spans = assignment.map((item) => [item.start, item.start + item.minutes]);
  const played = new Set();
  const prepMinutes = extras.prep;
  assignment.forEach(({ game, start, minutes }, i) => {
    const number = i + 1;
    const genre = genres.get(game);
    if (!queues.has(genre)) queues.set(genre, ranked(genre, request, level, data));
    const queue = queues.get(genre);
    const closer = number === count && count > 1 ? weekCloser(genre, request, level, data) : null;
    let item;
    if (closer !== null) {
      item = closer;
    } else {
      item = nextFormat(queue, position.get(genre) || 0, request.week_number === 1 && !played.has(game));
      position.set(genre, (position.get(genre) || 0) + 1);
    }
    played.add(game);

    const overlaps = (prepStart) => spans.filter(([a, b]) => a !== start &&
      a < prepStart + prepMinutes + p.prep_gap && prepStart < b);
    let prepStart = start - p.prep_gap - prepMinutes;
    while (overlaps(prepStart).length) {
      prepStart = Math.min(...overlaps(prepStart).map(([a]) => a)) - p.prep_gap - prepMinutes;
    }
    const prep = session(mod(prepStart, WEEK), prepMinutes, lang, data);
    const stream = session(mod(start, WEEK), minutes, lang, data);
    const clipDayLabel = labels[lang][(dayOf(start) + 1) % 7];

    streams.push({
      number, stream, game, genre_label: genreLabel(genre, lang, data),
      format_id: item.id, format_name: t(item.name, lang), needs_chat: item.needs_chat,
      needs_collab: item.needs_collab,
      title: "", title_alternatives: [], title_mood: streamMood(item.id, genre, request.mood, data),
      clip_title_ideas: clipTitles(item.id, lang, data),
      tags: tags(game, genre, item, lang, data),
      run_of_show: item.steps.map((step) => t(step, lang)),
      break_note: breakNote(minutes, lang),
      preparation: prep, prep_steps: item.prep.map((step) => t(step, lang)),
      hook: t(item.hook, lang), clip_idea: t(item.clip, lang),
      clip_day: clipDay(clipDayLabel, extras.clip, lang),
      measurement: t(item.metric, lang),
      why: why(item, genre, request, data),
      timing_reason: timingReason(game, stream, request),
    });
  });

  // Titel: Zähler laufen über die Wochen weiter; dasselbe Format nie mit gleichem Haupttitel.
  const totals = new Map();
  for (const entry of streams) totals.set(entry.format_id, (totals.get(entry.format_id) || 0) + 1);
  const rankedTotal = streams.filter((entry) => isRankStream(entry, genres, request, data)).length;
  const seen = new Map();
  const usedMain = new Map();
  let rankedSeen = 0;
  streams.forEach((entry, index) => {
    seen.set(entry.format_id, (seen.get(entry.format_id) || 0) + 1);
    const counter = (request.week_number - 1) * totals.get(entry.format_id) + seen.get(entry.format_id);
    if (isRankStream(entry, genres, request, data)) rankedSeen += 1;
    if (!usedMain.has(entry.format_id)) usedMain.set(entry.format_id, new Set());
    let options;
    for (let shift = 0; shift < 3; shift += 1) {
      options = buildTitles(entry.format_id, genres.get(entry.game), entry.game, lang, {
        counter, startMinute: weekMinute(entry.stream), mood: request.mood,
        rankGoal: request.rank_goal, currentRank: request.current_rank,
        rankCounter: (request.week_number - 1) * rankedTotal + Math.max(rankedSeen, 1),
        firstTime: request.first_time, rotation: index + shift, commands: request.commands,
      }, data);
      if (!usedMain.get(entry.format_id).has(options[0].text)) break;
    }
    usedMain.get(entry.format_id).add(options[0].text);
    const titles = options.map((option) => fitTitle(option.full, data));
    entry.title = titles[0];
    entry.title_alternatives = titles.slice(1, 3);
  });

  const lastDay = streams.at(-1).stream.day;
  const review = {
    day: labels[lang][(lastDay + 1) % 7], minutes: extras.review,
    questions: de
      ? ["Welcher Stream hatte die meisten durchschnittlichen Zuschauer – lag es eher am " +
         "Format, an der Uhrzeit oder am Spiel?",
         "Welcher Clip wurde am häufigsten angesehen?",
         "Was änderst du nächste Woche – nur eine Sache?"]
      : ["Which stream had the most average viewers – was it the format, the time or the game?",
         "Which clip got the most views?",
         "What will you change next week – just one thing?"],
  };
  const streamTotal = streams.reduce((sum, item) => sum + item.stream.minutes, 0);
  const budget = {
    weekly_minutes: request.hours_per_week * 60, stream_minutes: streamTotal,
    preparation_minutes: count * extras.prep, clip_minutes: count * extras.clip,
    review_minutes: extras.review,
    unplanned_minutes: request.hours_per_week * 60 - streamTotal -
      count * (extras.prep + extras.clip) - extras.review,
  };
  let series = null;
  for (const entry of streams) {
    const source = data.formats.find((item) => item.id === entry.format_id);
    if (source.series.length) {
      series = { format_name: entry.format_name, game: entry.game, episodes: source.series.map((step) => t(step, lang)) };
      break;
    }
  }

  const limits = data.twitch_limits;
  return {
    version: data.version, prototype: true, model_used: false,
    language: lang, platform: request.platform, chat_level: level,
    timing_source: "windows_only",
    games: gameInfos, streams, review, series, budget,
    twitch_limits: de
      ? `Titel höchstens ${limits.title_max_chars} Zeichen, höchstens ${limits.tags_max_count} Tags mit je ` +
        `höchstens ${limits.tag_max_chars} Zeichen ohne Leer- und Sonderzeichen. Quelle: ` +
        `${limits.source_url} (Stand: ${limits.source_date})`
      : `Title at most ${limits.title_max_chars} characters, at most ${limits.tags_max_count} tags of at most ` +
        `${limits.tag_max_chars} characters without spaces or special characters. Source: ` +
        `${limits.source_url} (as of ${limits.source_date})`,
    notes: [...refused.map((game) => rejection(game, lang, data)),
      ...notesFor(request, level, genres, streams, extras, data)],
    limitations: de
      ? ["Redaktionelle Regeln, kein Sprachmodell und keine Wachstumsvorhersage.",
         "Titel und Tags sind Vorschläge – vor dem Stream lesen und anpassen.",
         "Spielinhalte ändern sich mit Updates; Ideen vor dem Stream in deiner Spielversion prüfen."]
      : ["Editorial rules, no language model and no growth prediction.",
         "Titles and tags are suggestions – read and adjust them before you go live.",
         "Game content changes with updates; check ideas in your game version before streaming."],
  };
}

// Für den Paritätstest: Ergebnis oder Fehler als schlichtes Objekt (wie die Python-Fixtures).
export function runCase(rawRequest, data) {
  try {
    return { plan: buildPlan(rawRequest, data) };
  } catch (error) {
    if (error instanceof StrategistError) {
      return error.kind === "plan"
        ? { error: { type: "plan", message: error.message } }
        : { error: { type: "validation", loc: error.loc, message: error.message } };
    }
    throw error;
  }
}
