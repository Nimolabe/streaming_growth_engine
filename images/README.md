# Bilder der Website

Alle Fotos der Startseite (`index.html`) liegen hier selbst gehostet als WebP (Qualität 78).
Die Website lädt keine Bilder von fremden Servern mehr. Damit wird auch keine IP-Adresse
an Unsplash übertragen.

Zu jedem Bild gibt es zwei Größen: die große Datei und eine Variante mit 600 px Breite
(`-600.webp`). Der Browser wählt über `srcset`/`sizes` selbst.

## Lizenz

Alle Fotos stammen von [Unsplash](https://unsplash.com) und stehen unter der
[Unsplash-Lizenz](https://unsplash.com/license): Sie dürfen kostenlos genutzt, verändert und
auch kommerziell verwendet werden, ohne Nachfrage und ohne Pflicht zur Namensnennung.
Nicht erlaubt ist, die Fotos unverändert zu verkaufen oder einen konkurrierenden Bilderdienst
damit aufzubauen.

Neue Bilder nur mit bekannter Herkunft und passender Lizenz hinzufügen und hier eintragen.
Keine Marken-Logos (siehe `CLAUDE.md`, Abschnitt 10).

## Herkunft

Die Fotos wurden bisher direkt von `images.unsplash.com` eingebunden. Die Foto-ID steht in der
damaligen Adresse `https://images.unsplash.com/photo-<ID>`.

| Datei (groß / 600 px) | Unsplash-Foto-ID | Verwendung | Fotograf |
| --- | --- | --- | --- |
| `hero-gaming-stuhl.webp` (1400×933) / `-600` | `1542751371-adc38448a05e` | Hero oben | nicht ermittelbar |
| `karte-neon-arbeitsplatz.webp` (900×506) / `-600` | `1616588589676-62b3bd4ff6d2` | Loadout-Karte | nicht ermittelbar |
| `karte-multi-monitor-setup.webp` (900×600) / `-600` | `1775410631936-7de96322df0b` | Loadout-Karte | nicht ermittelbar |
| `karte-audio-mischpult.webp` (900×600) / `-600` | `1619190324856-af3f6eb55601` | Loadout-Karte | nicht ermittelbar |
| `karte-kopfhoerer-computer.webp` (900×1350) / `-600` | `1610041321420-a596dd14ebc9` | Loadout-Karte | nicht ermittelbar |
| `karte-smartphone-filmen.webp` (1200×800) / `-600` | `1505695044222-61d7ff153f23` | Loadout-Karte (breit) | nicht ermittelbar |
| `showcase-mikrofon-monitor.webp` (1800×1201) / `-600` | `1598550480917-1c485268676e` | Showcase-Bereich | nicht ermittelbar |

**Fotograf „nicht ermittelbar“:** Die Bilddateien enthalten keine Metadaten (kein EXIF/XMP),
und die Unsplash-Seiten selbst waren beim Anlegen für automatische Abrufe gesperrt.
Mit der Foto-ID lässt sich das Foto über die Unsplash-Suche bzw. die Unsplash-API
(`GET /photos/<ID>`) wiederfinden; dort stehen Fotograf und Fotoseite. Eine Namensnennung
ist nach der Unsplash-Lizenz nicht verpflichtend, aber erwünscht und kann hier nachgetragen
werden.
