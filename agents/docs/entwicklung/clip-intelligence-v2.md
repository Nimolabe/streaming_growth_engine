# Clip Intelligence V2 — Multisignal-Sichtung ohne Sprachmodell

**Status:** experimenteller Offline-Prototyp auf
`feature/clip-intelligence-v2-multisignal`. V1 bleibt unverändert erreichbar.

## Was gegenüber V1 neu ist

- **Audio:** Kurze, deutliche Lautstärke-Aktivität gegenüber dem Medianpegel.
- **Video:** Auffällige visuelle Änderungen anhand zweier stark verkleinerter
  Graustufenframes pro Sekunde; etwa harte Szenenwechsel oder starke
  Bildänderungen.
- **Kombination:** Zeitlich eng zusammenliegende Audio- und Videohinweise
  werden als gemeinsamer Sichtungsvorschlag markiert.
- **Ohne Audiospur:** Video-only-Clips dürfen analysiert werden.
- **Schutzmaßnahmen:** Datei- und Zeitbegrenzung, feste Pixelauflösung,
  kontrollierte FFmpeg-Protokolle, nicht persistente Uploads und keine
  automatischen Veröffentlichungen.
- **Kompatibilität:** Der alte V1-Endpunkt existiert weiterhin.

## API

`POST /api/v1/clips/scan`

Multipart-Feld `file`: eigene WAV-, MP4-, MOV-, MKV- oder WEBM-Aufnahme.
Optionale Query `max_candidates`: 1–10, Standard 5.

Demo: höchstens 100 MB und 15 Minuten. FFmpeg/FFprobe sind nur für
Videodateien notwendig, nicht für unkomprimierte 16-Bit-PCM-WAVs.
Nur lokal auf `127.0.0.1` betreiben; das Demo-Backend hat keine
Authentifizierung und darf nicht öffentlich erreichbar sein.

Antworten enthalten Zeitstempel, `evidence` (`audio_peak`,
`visual_change` oder beides), relative `activity_score`,
Sichtungshinweise und Grenzen der Interpretation.

## Was V2 ausdrücklich **nicht** kann

- Keine Bedeutungserkennung für ein Valorant-Clutch, einen lustigen Dialog
  oder eine wichtige Entscheidung.
- Keine Gesichtsausdruck-, Emotions-, Transkriptions- oder Chat-Erkennung.
- Keine Vorhersage über Likes, Reichweite oder Viralität.
- Ein visueller Wechsel kann eine Overlay-Einblendung oder ein Menü sein.
- Musik und laute Effekte können Audio-Kandidaten erzeugen.
- Ereignisse zwischen den zwei Videoframes pro Sekunde können übersehen werden.
- Eine stille, unveränderte Szene kann inhaltlich der beste Clip sein.

Das System produziert **Review-Kandidaten**, nicht veröffentlichungsfertige Clips.
Nur Inhalte verwenden, für die Veröffentlichungserlaubnis besteht.

## Qualitätsprüfungen

`tests/test_clip_intelligence_v2.py` beinhaltet reproduzierbare synthetische
Audiosignale sowie FFmpeg-generierte Videos mit und ohne Tonspur.
Tests überprüfen:

- Erkennung harter Farbwechsel und Vermeidung falscher Wechsel bei statischem Bild,
- echte Video-Dekodierung, Grenzwerte und API-Uploads,
- explizite Audio-/Video-Hinweise und Kombinationslogik,
- chronologische Zeitstempel, Kapazitätsgrenzen und menschliche Sichtung,
- Kompatibilität mit dem ursprünglichen V1-Endpunkt.

Eine vollständig grüne Pipeline ist **nur** eine technische Prüfung;
für die Bewertung, wie viele wirklich interessante Momente gefunden werden,
benötigen wir später einen freiwilligen, ausreichend vielfältigen Korpus
mit manuell markierten Highlight-Zeitpunkten und unabhängigen Reviewern.

## Kosten

Verwendet keinerlei bezahlte Modell- oder Analyse-API. GitHub Actions
verwendet das Kontingent des GitHub-Kontos, das nicht unbegrenzt ist.

## Kontrollierter synthetischer Benchmark

`tests/test_clip_intelligence_v2_benchmark.py` misst getrennt:
- Trefferrate (**Recall**) bei einem absichtlich eingefügten harten Schwarz-Weiß-Szenenwechsel.
- Präzision der gefundenen Szenenwechsel gegenüber dem bekannten Zeitpunkt.
- Fehlalarme in einem gleichbleibenden Video ohne Szenenwechsel.

Diese selbst erzeugten Fälle sind ein **Technik-Sanity-Check**, kein repräsentativer
Gameplay-Datensatz und keine gemessene Quote gefundener interessanter Clips.
Bei echten Stream-Aufnahmen können Menüs, Zooms, Motion Effects und ruhige
Highlights ganz andere Ergebnisse liefern. Für eine externe Qualitätsfreigabe
sind freiwillig bereitgestellte Aufnahmen samt unabhängigen menschlichen
Highlight-Markierungen notwendig.

## Menschlich annotierter Qualitätsvergleich

Mit `POST /api/v1/clips/evaluate` werden die vorgeschlagenen
Ereigniszeitpunkte gegen zuvor **unabhängig markierte** Highlights verglichen.
Die Anfrage enthält die Aufnahmedauer, Zeitpunkte der Vorschläge, Zeitpunkte
der menschlichen Highlights und ein Toleranzfenster von standardmäßig 5 Sekunden.
Die Funktion meldet Treffer, falsch-positive und verpasste Zeitpunkte,
sowie **Precision**, **Recall** und **F1**. Jede Markierung darf maximal
mit einem Vorschlag verbunden werden; die Zuordnung maximiert zuerst die
Trefferzahl und minimiert danach die Zeitabweichung.

Wenn keine Vorschläge vorhanden sind, ist Precision nicht definiert;
wenn keine menschlichen Markierungen vorhanden sind, ist Recall nicht
definiert. Für beide Fälle wird kein fiktives 100%-Ergebnis ausgegeben.
Dies misst **Zeitnähe**, nicht ob ein fertiger Clip gut geschnitten oder
unterhaltsam ist. Untereinander unabhängige menschliche Reviewer und
verschiedene Stream-Arten sind für eine belastbare externe Bewertung nötig.

Beispiel:

```json
{
  "duration_seconds": 120,
  "suggested_event_seconds": [10, 30, 80],
  "human_highlight_seconds": [11, 31, 60],
  "tolerance_seconds": 3
}
```

Erwartet: zwei Treffer, ein Fehlalarm und ein übersehener Highlight-Zeitpunkt.
Die Auswertung benötigt keinerlei Video-Upload und speichert keine Daten.

## CI-Zuverlässigkeit und Kostenkontrolle

Der Standard-Pull-Request-Workflow führt die schnellen Offline-Prüfungen
ohne vorherige Paketinstallation aus. FFmpeg-abhängige Videotests werden
dann übersprungen, wenn FFmpeg auf dem Runner nicht vorhanden ist; das
muss im CI-Log sichtbar bleiben. Für den vollständigen Video-Integrationstest
kann der Workflow auf dem Entwicklungsbranch **manuell** mit dem Feld
`enable_video_tests=true` gestartet werden. Die optionale Installation
ist auf zwei Minuten begrenzt, damit temporäre Paketserverprobleme nicht
den ganzen Testlauf blockieren. Ein grüner Lauf mit übersprungenen
Videotests ist ausdrücklich kein Nachweis für funktionierende
Videodekodierung auf diesem Runner.
