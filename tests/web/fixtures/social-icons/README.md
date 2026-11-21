# Test-Icons

Nur für die Browser-Tests (`test_layouts.py`). Es sind einfache geometrische Formen (Kreis,
Quadrat, Dreieck), **keine** Logos. `tiktok.png` prüft den Rückfall von `.svg` auf `.png`. Die Tests leiten Anfragen an `assets/social-icons/` hierher um.
Für `instagram` und `x` liegt absichtlich keine Datei hier. Damit wird der
Rückfall auf Text geprüft.
