// Paritätstest-Lauf für js/strategist-core.js in Node (ohne Browser).
//
// Aufruf (aus der Repo-Wurzel):
//   node tests/web/strategist_parity.mjs
// Gibt eine JSON-Zeile aus: {"total": n, "mismatches": [{"name", "js", "python"}], "casefold": [...]}
// und endet mit Exit-Code 1, wenn ein Ergebnis abweicht. Genutzt von
// agents/tests/test_strategist_web.py; der Chromium-Test steht in test_strategist_parity.py.
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const core = await import(pathToFileURL(resolve(root, "js", "strategist-core.js")).href);
const data = JSON.parse(readFileSync(resolve(root, "data", "content-strategist.json"), "utf8"));
const fixtures = JSON.parse(readFileSync(resolve(root, "tests", "fixtures", "strategist-parity.json"), "utf8"));

export function compare(coreModule, contentData, fixtureData) {
  const mismatches = [];
  for (const item of fixtureData.cases) {
    let result;
    try {
      result = coreModule.runCase(structuredClone(item.request), contentData);
    } catch (error) {
      result = { crash: String(error && error.stack ? error.stack : error) };
    }
    // Strenger Vergleich inklusive Reihenfolge der Schlüssel.
    const js = JSON.stringify(result);
    const python = JSON.stringify(item.expected);
    if (js !== python) mismatches.push({ name: item.name, js, python });
  }
  const casefold = fixtureData.casefold
    .filter(([text, folded]) => coreModule.casefold(text) !== folded)
    .map(([text, folded]) => ({ text, js: coreModule.casefold(text), python: folded }));
  return {
    total: fixtureData.cases.length, mismatches, casefold,
    dataMatches: fixtureData.data_sha256 === contentData.sha256,
  };
}

const report = compare(core, data, fixtures);
console.log(JSON.stringify(report));
process.exitCode = report.mismatches.length || report.casefold.length || !report.dataMatches ? 1 : 0;
