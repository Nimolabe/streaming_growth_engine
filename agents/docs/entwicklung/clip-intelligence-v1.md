# Clip Intelligence V1 — kostenfreier lokaler Audio-Scanner

**Ziel:** Eine vom Creator bereitgestellte Aufnahme nach auffälligen
Audio-Abschnitten durchsuchen und sinnvolle Zeitstempel zur **manuellen
Sichtung** liefern. Das ist **kein** semantischer AI-Videocutter und
keine Prognose für TikTok-/Shorts-Erfolg.

## Funktionsumfang

- Reine Python-Analyse für unkomprimierte 16-Bit-PCM-WAV-Dateien (Mono/Stereo).
- Mit installiertem [FFmpeg](https://ffmpeg.org/) und FFprobe auch lokale
  `.mp4`, `.mov`, `.mkv` und `.webm`-Aufnahmen.
- Akustische Aktivitätsspitzen gegenüber dem Median-Geräuschpegel finden.
- Sehr kurze Impulse und nahe Duplikate aussortieren.
- Bis zu zehn Clips mit Start-, Ende- und Peak-Zeitstempel vorschlagen.
- Optional lokale Review-MP4-Schnitte per FFmpeg exportieren.
- Keine Accounts, API-Schlüssel, Netzwerkanfragen oder KI-Sprachmodelle.
- Alles bleibt lokal; der Test-Endpunkt löscht Upload-Dateien nach Verarbeitung.

## Wie wir richtig interpretieren

**audio_activity_score** ist lediglich ein heuristischer relativer
Lautstärke-Aktivitätswert, keine Wahrscheinlichkeit für Reichweite,
Humor, Spannung oder Viralität.

Ein ruhiger Valorant-Clutch kann übersehen werden; Musik, Hintergrundgeräusche
oder Geschrei können zu Fehlvorschlägen führen. Gute Momente müssen
anschließend von einer Person angesehen werden. Das Tool transkribiert
keine Sprache, erkennt keine Spielsituationen und behauptet nicht,
einen Clip automatisch als attraktiv beurteilen zu können.

## Im Browser ausprobieren

Der lokale FastAPI-Endpunkt heißt:

`POST /api/v1/clips/scan`

In `http://127.0.0.1:8000/api/v1/docs` kannst du eine eigene Aufnahme
hochladen. Demo-Limits: maximal **100 MB**, maximal **15 Minuten**;
maximal 10 Clip-Vorschläge.

FFmpeg und FFprobe müssen auf dem ausführenden Rechner installiert sein,
wenn du Videodateien hochlädst. WAV-Dateien benötigen sie nicht.
Dieses Demo-Backend hat **keine Authentifizierung**, daher **nur lokal**
auf `127.0.0.1` betreiben und nicht öffentlich freigeben.

## Längere Videos direkt lokal bearbeiten

Der CLI-Modus unterstützt Dateien bis zu **1 GB** und bis zu **einer Stunde**
mit Standardeinstellungen (konfigurierbare Analyse bis 2 Stunden).
Keine Daten werden an einen Server übertragen.

```powershell
python -m streaming_agents.clip_cli --input "C:\Videos\mein_stream.mp4" --json "C:\Videos\clip_kandidaten.json"
```

Optional mit lokal gerenderten Review-Ausschnitten:

```powershell
python -m streaming_agents.clip_cli --input "C:\Videos\mein_stream.mp4" --extract-dir "C:\Videos\review_clips"
```

Bestehende Zielclips oder JSON-Dateien werden **nicht überschrieben**.

## Kostenfreie GitHub-Tests

Der CI-Workflow führt Audio-Unit-Tests mit synthetischen Wellenformen aus
und prüft den WAV-Upload-Endpunkt, Fehlermeldungen und den CLI-Export.
Wenn FFmpeg auf dem GitHub-Runner installiert ist, wird zusätzlich ein
kleines lokales MP4 synthetisch erzeugt und über den realen Decoder geprüft.

Ein GitHub-Actions-Lauf belastet das enthaltene kostenlose Minuten-Kontingent
und kann bei Überschreitung Kosten verursachen. Der Workflow ist nicht
unbegrenzt kostenlos.

## Wie es weitergeht

Für die tatsächliche Qualität von Clip-Erkennung benötigen wir später
zusätzlich Kontextsignale (beispielsweise Spielereignisse, Sprache,
Schnittwechsel oder Creator-Markierungen), einen kuratierten,
eingewilligten Bewertungsdatensatz und Blindtests.
Die gegenwärtige V1 kann nur **Audio-Auffälligkeiten** finden, keine
erfolgreichen Clips vorhersagen.

Die Website, das Repository `main`, Creator Intelligence V1/V2 und
Content Strategist V1/V2/V3 bleiben unverändert. Änderungen liegen
auf `feature/clip-intelligence-v1-offline`.
