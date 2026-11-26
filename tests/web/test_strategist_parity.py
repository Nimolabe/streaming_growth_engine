"""Parität Python ↔ JavaScript für den Content Strategist – im echten Chromium.

``js/strategist-core.js`` läuft in einem Web Worker (dort gibt es kein DOM: der Test beweist
damit auch, dass der Kern ohne DOM auskommt) mit den Eingaben aus
``tests/fixtures/strategist-parity.json`` und muss exakt die Ergebnisse liefern, die Python
erzeugt hat (``agents/tests/strategist_parity.py``). Das Netzwerk wird mitgeschnitten: Der Kern
selbst lädt nichts nach.
"""

from __future__ import annotations

import json

from conftest import ROOT, new_context

WORKER = """
const base = self.location.origin;
const core = await import(base + "/js/strategist-core.js");
const [data, fixtures] = await Promise.all([
  fetch(base + "/data/content-strategist.json").then((r) => r.json()),
  fetch(base + "/tests/fixtures/strategist-parity.json").then((r) => r.json()),
]);
const mismatches = [];
for (const item of fixtures.cases) {
  let result;
  try { result = core.runCase(structuredClone(item.request), data); }
  catch (error) { result = { crash: String(error && error.stack || error) }; }
  const js = JSON.stringify(result);
  const python = JSON.stringify(item.expected);
  if (js !== python) mismatches.push({ name: item.name, js, python });
}
const casefold = fixtures.casefold.filter(([text, folded]) => core.casefold(text) !== folded);
self.postMessage({ total: fixtures.cases.length, mismatches, casefold,
                   dataMatches: fixtures.data_sha256 === data.sha256,
                   hasDocument: typeof document !== "undefined" });
"""


def test_strategist_core_matches_python_in_chromium(browser, base_url):
    context = new_context(browser, base_url)
    page = context.new_page()
    requests: list[str] = []
    page.on("request", lambda request: requests.append(request.url))
    page.goto(f"{base_url}/data/content-strategist.json")
    report = page.evaluate(
        """(source) => new Promise((resolve, reject) => {
            const url = URL.createObjectURL(new Blob([source], { type: "text/javascript" }));
            const worker = new Worker(url, { type: "module" });
            worker.onmessage = (event) => resolve(event.data);
            worker.onerror = (event) => reject(new Error(event.message || "Worker-Fehler"));
        })""",
        WORKER,
    )
    context.close()
    assert report["dataMatches"], "Fixtures passen nicht zum Export (Fixtures neu erzeugen)"
    assert not report["hasDocument"]
    assert report["casefold"] == []
    assert report["mismatches"] == [], report["mismatches"][:1]
    assert report["total"] >= 60
    loaded = {url.split("?")[0].removeprefix(base_url) for url in requests if url.startswith(base_url)}
    assert loaded <= {"/data/content-strategist.json", "/js/strategist-core.js",
                      "/tests/fixtures/strategist-parity.json", "/favicon.ico"}
    assert all(url.startswith((base_url, "blob:")) for url in requests)


def test_strategist_core_has_no_dom_network_or_randomness():
    source = (ROOT / "js" / "strategist-core.js").read_text(encoding="utf-8")
    for forbidden in ("document.", "window.", "fetch(", "XMLHttpRequest", "Math.random",
                      "Date.now", "new Date", "localStorage", "import("):
        assert forbidden not in source, forbidden


def test_export_and_fixtures_belong_together():
    data = json.loads((ROOT / "data" / "content-strategist.json").read_text(encoding="utf-8"))
    fixtures = json.loads((ROOT / "tests" / "fixtures" / "strategist-parity.json")
                          .read_text(encoding="utf-8"))
    assert fixtures["data_sha256"] == data["sha256"]
