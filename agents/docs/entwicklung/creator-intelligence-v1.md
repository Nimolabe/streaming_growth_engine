# Creator Intelligence V1 — Offline prototype

The first Creator Intelligence Agent is a *conservative analytics assistant*:
it takes weekly numbers entered or exported by a creator, validates their
structure, compares a recent and an earlier period, and suggests a small set of
testable next steps. **It does not learn from live channel accounts, use
language models or forecast results.** It cannot diagnose causal reasons from
aggregate counts.

## Development branch

`feature/creator-intelligence-v1-offline` is based on the existing offline
Content Strategist V3 branch. It retains all V1/V2/V3 content endpoints.
The website is *not* connected. No changes have been merged to `main`.

## Input

`POST /api/v1/growth/analysis`

Required fields: `weekly_hours_available` and `weeks` (4–26 consecutive
weekly records, in chronological order, seven days apart). Optional fields:
`platform`, `channel_category`, `primary_goal`.

Each weekly record requires `week_start` and `stream_minutes`; it can also
include `average_viewers`, `unique_viewers`, `returning_viewers`,
`follows`, `clips_published`, and `clip_views`.

Use `null` when a number is not available. **Zero is a genuine observation,
not a missing value.** Do not combine unique-viewer definitions from different
analytics platforms. Clip views should come from comparable publication windows
when possible. If a week has no streaming minutes, leave its average viewer
field null. Input is held only for processing in this API; this prototype
does not store it in a database.

The first and second halves are compared using weekly rates for counts.
Stream-minute-weighted averages are used for viewers. A change of more than
five percent is categorized as up/down, not as statistically significant.
When a denominator is zero, the percent change is omitted, rather than
inventing infinity. Missing observations suppress invalid comparisons.

## Local setup (PowerShell)

Open an extracted ZIP of the branch, then run this block to find the real
project root (the folder containing `pyproject.toml`):

```powershell
$project = Get-ChildItem "$HOME\Downloads" -Recurse -File -Filter pyproject.toml |
    Where-Object { $_.FullName -like "*creator-intelligence-v1-offline*" } |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $project) { throw "Creator Intelligence ZIP not found under Downloads." }
Set-Location $project.DirectoryName
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check streaming_agents tests
.\.venv\Scripts\python.exe -m uvicorn streaming_agents.api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/api/v1/docs` and try
`POST /api/v1/growth/analysis` with
[`examples/creator_intelligence_v1_request.json`](../../examples/creator_intelligence_v1_request.json).

## What this V1 diagnoses

- Recent stream time above available weekly hours: capacity warning.
- A clear directional change in stream-minute-weighted viewers: monitoring
  suggestion (not a causal claim).
- A discovery goal with no recently published clips: simple clip experiment.
- Rising unique viewers with falling returning viewers: investigate return habit.
- Rising reach with declining follows: review conversion messaging.
- Clip-reach decline: review comparable short-form content.
- Otherwise: keep a consistent baseline and collect more data.

Diagnostics include concrete evidence fields, uncertainty, recommended next
action and a suggested verification check. Priority rules are editorial, not
machine learning or a probability of future success.

## Limits and production readiness

This is a **testable offline prototype**, not a production-ready SaaS.
Before real users: authentication, access control, data minimization, consent,
security review, storage strategy, tests for real platform exports, more
fine-grained stream-level baselines and well-calibrated evaluations are needed.
Automated causal analysis and statistically robust forecasts are explicitly
out of scope. We will build the separate Clip Intelligence Agent next, not in
this branch.

As of creation, source-level review was performed; **do not label this branch
fully tested until the local pytest and Ruff commands pass**.

## Erweiterte Qualitätsprüfung

Die [synthetischen Abnahmeszenarien](creator-intelligence-acceptance-tests.md)
prüfen kleine und etablierte Kanäle, stabile Kennzahlen, Rückkehrer-Rückgänge,
Zeitüberlastung und fehlende Daten. Ihre Python-Tests werden von der bestehenden
GitHub-Actions-Pipeline ausgeführt. Ein erfolgreiches CI-Ergebnis ist **kein**
Nachweis der tatsächlichen Wirksamkeit der empfohlenen Wachstumsmaßnahmen.
