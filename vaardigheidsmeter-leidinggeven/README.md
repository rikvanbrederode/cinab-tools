# Vaardigheidsmeter Leidinggeven

| | |
|---|---|
| Firebase-project | `vaardigheidsmeter-leidin-f82f7` (`europe-west1`) |
| Staging en productie | zelfde project; de aliassen in `.firebaserc` wijzen allebei hierheen |
| Regels deployt | Rik, vanuit deze map |
| Anonymous sign-in | aan (ingeschakeld bij inrichting) |
| Tool-client | `public/cinab-tool-client.js`, versie in de header (1.1.0 bevat de sessionCode-ondersteuning voor F2-21, herstart van meerdaagse sessies) |

## Deployen

```powershell
cd C:\Users\rikva\Projecten\cinab-tools\vaardigheidsmeter-leidinggeven
firebase deploy --only hosting,database
```

Alleen hosting als de regels niet wijzigen: `firebase deploy --only hosting`.

Komt er later een apart productieproject, volg dan het stappenplan in de Visiekaart-README en werk de aliassen bij.
