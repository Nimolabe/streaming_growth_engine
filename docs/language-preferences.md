# Länder- und Sprachwahl (erste Version)

## Verhalten
- Im Registrierungsformular gibt es eine Länderauswahl und eine separate Sprachwahl.
- Beim ersten Besuch wird die Browsersprache verwendet, sofern Deutsch oder Englisch; andere Browser-Sprachen werden vorläufig auf Englisch abgebildet.
- Nach Auswahl eines Landes wird eine Standardsprache vorgeschlagen. Aktuell unterstützt die **vollständige UI-Übersetzung nur Deutsch und Englisch**. Für Länder mit anderen Landessprachen wird bis zu einer richtigen Übersetzung Englisch als Fallback verwendet.
- Eine bewusst ausgewählte Sprache hat immer Vorrang vor einer späteren Änderung des Landes.
- Die Sprache ist in der Navigation jederzeit umschaltbar. Die Angaben bleiben lokal im Browser via localStorage gespeichert.
- Keine Geolokalisierung oder IP-Abfrage.

## Technische Umsetzung
- `js/i18n.js`: Sprache, Land, Übersetzungswörterbuch, Sprachumschalter und landesspezifische Empfehlung.
- `index.html` und `setups.html`: Einbindung des Skripts.
- `css/style.css`: Formularelemente für die Auswahl.

## Einschränkungen / weitere Schritte
- Der dynamisch generierte Setup-Finder (`js/setups.js`) enthält noch Texte, die für weitere Sprachen mit Übersetzungsschlüsseln internationalisiert werden müssen.
- Die Sprache und das Land sind bislang nur lokal gespeichert; für Synchronisierung auf verschiedenen Geräten müssen diese nach Einwilligung als Profilpräferenz gespeichert werden.
- Für Frankreich, Spanien, Italien, Polen etc. müssen die jeweiligen UI-Übersetzungen ergänzt und geprüft werden, bevor sie auswählbar werden.
- Browser-Tests für Modal, Mobile-Navigation, Registrierung und Setup-Finder stehen noch aus.
- Firebase-Meldung `auth/unauthorized-domain` ist unabhängig von dieser Änderung: Die Hosting-Domain `nimolabe.github.io` muss unter Firebase Authentication > Einstellungen > Autorisierte Domains hinzugefügt werden, bevor der Login auf GitHub Pages funktionieren kann.
