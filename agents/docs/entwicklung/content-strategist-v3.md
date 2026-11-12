# Content Strategist V3 — Offline-Empfehlungen

**Arbeitsstand:** eigenständiger, kostenfreier Backend-Prototyp. Noch keine
Website-Integration, keine produktive Nutzerverwaltung, keine Live-Trends und
keine KI-Modellaufrufe.

## Was V3 gegenüber V2 verbessert

- Echte Profilfelder für durchschnittliche Zuschauer und aktive Chatteilnehmer
  statt nur "kleiner Kanal".
- Wenn weniger als drei Chatteilnehmer angegeben werden, werden Formate
  ausgespart, die eine aktive Live-Abstimmung oder einen Coach brauchen.
- Wo ein Entscheidungsformat auch ohne Live-Chat sinnvoll ist, wird der Ablauf
  ausdrücklich ohne Abstimmung geschrieben.
- Konkrete evergreen Spielsituationen für Valorant, Minecraft und Fortnite.
  Beispiele sind keine Behauptung über die jeweils aktuelle Meta.
- Kuratierte Formate werden nach Spiel, Stil, Ziel, Zeitbudget und
  Realisierbarkeit bewertet und in der Auswahl diversifiziert.
- Drei aufeinander aufbauende Episoden für das beste Format.
- Wöchentliche Aufwandsaufteilung mit einer nachvollziehbaren 65/15/15/5-Regel
  (Stream/Vorbereitung/Schnitt/Rückblick). Diese Verteilung ist ein anpassbarer
  Planungsvorschlag, kein universelles Optimum.
- Die früheren Demo-Schnittstellen (V1-Vorlagen, V2) wurden bei der
  Bereinigung entfernt; V2 bleibt intern als Grundlage von V3 erhalten.

## Lokal auf Windows testen

Lade den Branch `feature/content-strategist-v3-offline` als ZIP herunter.
Entpacke ihn und öffne PowerShell **in dem Unterordner, in dem
`pyproject.toml` liegt**.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check streaming_agents tests
.\.venv\Scripts\python.exe -m uvicorn streaming_agents.api:app --host 127.0.0.1 --port 8000
```

In `http://127.0.0.1:8000/api/v1/docs` den Endpunkt
**POST /api/v1/content/strategy** öffnen:

```json
{
  "platform": "twitch",
  "game": "Valorant",
  "audience": "Deutschsprachige Gaming-Zuschauer",
  "language": "de",
  "experience": "intermediate",
  "style": "interactive",
  "goal": "discovery",
  "average_viewers": 2,
  "active_chatters": 0,
  "hours_per_week": 12,
  "streams_per_week": 3,
  "ideas_requested": 5,
  "exclude_format_ids": []
}
```

Achtung: `platform` wird in V3 kleingeschrieben (`"twitch"`),
`average_viewers` meint **gleichzeitige durchschnittliche Zuschauer**;
`active_chatters` ist die ungefähre Zahl regelmäßiger aktiver Chatteilnehmer,
nicht die Anzahl aller Chatnachrichten.

## Qualität und Grenzen

- Die `fit_score`-Zahl ist eine **redaktionelle Priorisierung**, keine
  Wahrscheinlichkeit oder prognostizierte Viewzahl.
- Die Quellen stützen übergreifende Content-Prinzipien, nicht den Erfolg
  jeder konkreten Idee.
- Es gibt keine automatisierte Bewertung von realen Zuschauerreaktionen,
  da noch keine vom Nutzer freigegebenen Analytics integriert wurden.
- Unterstützte spezifische Szenarien: Valorant, Minecraft, Fortnite.
  Andere Spiele bekommen passende Genre- oder Allgemeinformate;
  sie werden nicht als vollständig erforschte Spiele ausgegeben.
- Ein Experiment sollte mehrere vergleichbare Streams berücksichtigen.
  Bei sehr wenigen Zuschauern sind Kennzahlen stark schwankend; qualitative
  Rückmeldungen und praktische Umsetzbarkeit bleiben wichtig.
- Live-Daten, kostenpflichtige API-Keys und Cloud-/KI-Provider werden von V3
  nicht verwendet. Die früher optional angelegte OpenAI-Provider-Datei bleibt
  für V3 **unbenutzt**.

## Quellen für Methoden, nicht für Erfolgsgarantien

- Twitch Creator Camp: https://www.twitch.tv/creatorcamp/de-de/
- Twitch Stream Summary: https://help.twitch.tv/s/article/stream-summary
- Valorant-Agentenrollen: https://playvalorant.com/en-us/agents/
- YouTube Shorts Discovery: https://support.google.com/youtube/answer/11914225?hl=en

## Produktionsfreigabe

Bevor ein öffentlicher Dienst daraus wird, müssen echte
Nutzertests, redaktionelle Quellenprüfung, Sicherheitsmaßnahmen,
Authentifizierung, Limits sowie Wartungs- und Datenschutzregeln folgen.
V3 ist zur **lokalen Qualitätsprüfung** bereit, nicht als fertig
abgesicherter SaaS-Dienst.
