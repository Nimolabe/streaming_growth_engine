# Streaming Growth Engine

Eine Website für **neue Streamer**: Guides, Tools und Community, um schneller zu wachsen.

## Struktur

```
index.html      → Startseite
setups.html     → Setups: Budget-Planer, Streamer-Setups, Hardware-Katalog
community.html  → Community: Profile suchen, neue Streamer entdecken
profil.html     → Profilseite (eigenes Profil bearbeiten, fremde Profile ansehen, folgen)
css/style.css   → Design (Farben oben unter :root anpassen)
js/main.js      → Menü, Einblendungen auf Unterseiten
js/motion.js    → Animationen der Startseite (GSAP, Lenis in js/vendor/)
js/social.js    → Nutzernamen, Profile, Suche, Folgen (wird von auth.js geladen)
js/community.js → Logik der Community-Seite
js/profil.js    → Logik der Profilseite
css/social.css  → Design für Community, Profile und Nutzernamen-Feld
js/auth.js      → Anmeldung (Firebase Authentication)
js/setups.js    → Logik der Setups-Seite
js/setups-data.js → Produkte, Kategorien und Streamer-Setups (hier neue Daten eintragen)
js/firebase-config.js → Firebase-Zugangsdaten (hier eintragen)
database.rules.json   → Sicherheitsregeln der Realtime Database
assets/         → Bilder, Logos, Icons
agents/         → KI-Agenten (Python-Backend, lokaler Prototyp) → siehe agents/README.md
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
- `usernames/<name>`: reserviert Nutzernamen (klein geschrieben) → uid. Jeder Name nur einmal, nur der Besitzer kann ihn freigeben
- `profiles/<uid>`: öffentliche Profile (Name, Nutzername, Bio, Plattform, Kanal-Link, Lieblingsspiele). Für alle lesbar, damit Profil-Links und Suche ohne Anmeldung funktionieren; nur der Besitzer schreibt. Indizes für die Suche: `usernameLower`, `nameLower`, `createdAt`
- `following/<uid>/<ziel>` und `followers/<ziel>/<uid>`: wer wem folgt, nur der Folgende selbst darf schreiben

**Wichtig:** Nach jeder Änderung an `database.rules.json` die Regeln in der Firebase-Konsole veröffentlichen, sonst funktionieren Profile und Suche nicht.

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
- [x] Profile mit eigenem Nutzernamen, Profilsuche, Folgen
- [ ] Community-Link (z. B. Discord)
- [ ] Eigenes Logo
- [ ] Veröffentlichen über GitHub Pages
- [x] KI-Agenten zusammengeführt (Content Strategist, Growth Analyst, Clip Hunter als Prototypen)
- [ ] KI-Agenten in die Plattform einbinden (Beta-Bereich, Backend mit Anmeldung)
