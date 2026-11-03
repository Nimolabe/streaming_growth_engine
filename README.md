# Streaming Growth Engine

Eine Website für **neue Streamer**: Guides, Tools und Community, um schneller zu wachsen.

## Struktur

```
index.html      → Startseite
setups.html     → Setups: Budget-Planer, Streamer-Setups, Hardware-Katalog
css/style.css   → Design (Farben oben unter :root anpassen)
js/main.js      → Menü, Scroll-Animationen
js/auth.js      → Anmeldung (Firebase Authentication)
js/setups.js    → Logik der Setups-Seite
js/setups-data.js → Produkte, Kategorien und Streamer-Setups (hier neue Daten eintragen)
js/firebase-config.js → Firebase-Zugangsdaten (hier eintragen)
database.rules.json   → Sicherheitsregeln der Realtime Database
assets/         → Bilder, Logos, Icons
```

## Lokal ansehen

Wegen der Anmeldung (JavaScript-Module) die Seite über einen kleinen lokalen Server öffnen:

```bash
python3 -m http.server 8000
```

Dann http://localhost:8000 aufrufen.

## Anmeldung einrichten (Firebase)

1. In der Firebase-Konsole: **Authentication → Los gehts**
2. Unter **Anmeldemethode** aktivieren: **E-Mail/Passwort** und **Google**
3. Unter **Projekteinstellungen → Allgemein → Deine Apps** eine **Web-App** hinzufügen
4. Die angezeigte `firebaseConfig` in `js/firebase-config.js` eintragen
5. Sobald die Seite online ist: Domain unter **Authentication → Einstellungen → Autorisierte Domains** eintragen (`localhost` ist schon freigegeben)

## Datenbank-Regeln

Die Sicherheitsregeln stehen in `database.rules.json`. Bei Änderungen den Inhalt in der
Firebase-Konsole unter **Realtime Database → Regeln** einfügen und **Veröffentlichen** klicken.

- `users/<uid>`: private Daten, nur der Nutzer selbst darf lesen und schreiben
- `users/<uid>/favorites`: gespeicherte Lieblings-Setups (Setups-Seite)
- `profiles/<uid>`: öffentliche Profile, alle Eingeloggten dürfen lesen, nur der Besitzer schreiben

## Zusammenarbeiten

1. Neuen Branch anlegen: `git checkout -b feature/mein-feature`
2. Änderungen committen und pushen
3. Pull Request auf GitHub öffnen, der andere schaut drüber, dann mergen

## Ideen / Roadmap

- [ ] Guides-Seite mit echten Inhalten
- [ ] Tool-Sammlung
- [x] Anmeldung (E-Mail + Google)
- [x] Setups: Budget-Planer, Streamer-Setups, Hardware-Katalog, Favoriten
- [ ] Echte Streamer-Setups mit Quellen eintragen
- [ ] Kaufen-Links / aktuelle Preise
- [ ] Community-Link (z. B. Discord)
- [ ] Eigenes Logo
- [ ] Veröffentlichen über GitHub Pages
