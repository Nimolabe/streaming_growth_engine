# Testbilder für den Logo-Upload

Nur für die Browser-Tests (`test_layout_icons.py`). Es sind einfache geometrische Formen,
**keine** Logos.

| Datei | Zweck |
| --- | --- |
| `kreis-transparent.png` | Kreis auf transparentem Grund: Der Alphakanal ist die Form |
| `dreieck-ohne-transparenz.png` | schwarzes Dreieck auf Weiß: Die dunklen Pixel sind die Form |
| `leer.png` | komplett transparent: wird abgelehnt (fast leer) |
| `vollflaechig.png` | komplett schwarz: wird abgelehnt (fast vollflächig) |
| `quadrat.webp` | WebP mit Transparenz |
| `raute-mit-script.svg` | SVG mit `<script>` und `onload`: Beides darf nicht ausgeführt werden |
