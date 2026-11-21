# Social-Logos für den Facecam-Rahmen

Der Layout-Baukasten kann im schlichten Facecam-Rahmen Logos vor den Social-Namen zeigen
(Option „Logos anzeigen“). Die Logos werden **nicht** mitgeliefert. Sie kommen ausschließlich
aus den offiziellen Dateien der Plattformen, die ihr selbst hier ablegt.

## Dateien

Genau diese Namen, als SVG oder PNG. Das Overlay sucht zuerst `<name>.svg`, dann
`<name>.png`:

| Datei | Plattform |
| --- | --- |
| `twitch.svg` / `twitch.png` | Twitch |
| `youtube.svg` / `youtube.png` | YouTube |
| `instagram.svg` / `instagram.png` | Instagram |
| `tiktok.svg` / `tiktok.png` | TikTok |
| `x.svg` / `x.png` | X |

### Anforderungen an die Dateien

- **Transparenter Hintergrund.** JPEG geht nicht, ebenso wenig ein PNG mit weißem oder
  farbigem Hintergrund.
- **Nur das Zeichen, ohne Kachel.** Das Overlay färbt das Logo einfarbig ein und übernimmt
  dabei nur die Form der deckenden Pixel. Eine App-Kachel (z. B. das lila Twitch-Quadrat oder
  das rote YouTube-Rechteck) würde zu einem einfarbigen Klotz, das eigentliche Zeichen wäre
  nicht mehr zu sehen. Die Markenseiten bieten dafür eigene Fassungen an, z. B. das
  Twitch-„Glitch“-Logo, das YouTube-Icon, das Instagram-Glyph, das TikTok-Notensymbol ohne
  Schriftzug und das X-Logo.
- **SVG ohne Skripte, ohne Event-Attribute (`onload` usw.) und ohne externe Verweise.**

## Woher

Nur von den offiziellen Marken- bzw. Presseseiten der Plattformen. Sucht dort nach
„Brand“, „Brand assets“, „Press“ oder „Markenrichtlinien“ (z. B. die Brand-Seiten von Twitch,
YouTube, Instagram/Meta, TikTok und X). Nicht aus Icon-Sammlungen oder von Drittseiten
übernehmen.

## Regeln

- **Unverändert lassen:** Form und Proportionen nicht ändern, nichts hinzufügen oder
  wegschneiden. Das Overlay färbt das Logo nur einfarbig ein (Weiß oder Akzentfarbe, je nach
  Stil). Ob eine einfarbige Darstellung erlaubt ist, steht in den Richtlinien der jeweiligen
  Plattform. Wenn nicht, die Datei hier nicht ablegen.
- **Nur als Verweis auf den eigenen Kanal** nutzen, nicht als Werbung und nicht so, dass es
  nach einer Partnerschaft mit der Plattform aussieht.
- Es gelten die jeweiligen **Markenrichtlinien** der Plattformen. Die Rechte an den Logos
  liegen bei den Plattformen. Sie stehen nicht unter der Lizenz dieses Repos.

## Herkunft der abgelegten Dateien

| Datei | Quelle | heruntergeladen am |
| --- | --- | --- |
| – | – | – |

Noch keine Datei abgelegt. Die am 21.11.2026 gelieferten Dateien (Instagram PNG, TikTok
JPEG, Twitch PNG, YouTube PNG) erfüllten die Anforderungen nicht: keine Transparenz, App-Kachel
bzw. weißer Hintergrund. X fehlte. Sie wurden deshalb nicht übernommen.

## Verhalten

- Fehlt eine Datei oder lädt sie nicht, zeigt das Overlay für diese Plattform automatisch
  den Text (z. B. „Twitch /name“). Es gibt keinen Fehler und keinen leeren Platz.
- Ohne die Option „Logos anzeigen“ werden die Dateien gar nicht geladen.
