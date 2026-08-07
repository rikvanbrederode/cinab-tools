# Visiekaart

| | |
|---|---|
| Firebase-project (staging) | `visiekaart` (regio VS; historisch, blijft staging) |
| Firebase-project (productie) | nog aanmaken in `europe-west1`; daarna project-ID invullen in `.firebaserc` onder `production` |
| Regels deployt | Rik, vanuit deze map |
| Anonymous sign-in | aan op staging; bij het productieproject direct aanzetten (Authentication, Sign-in method) |
| Hosting-rewrites | `/join/**` naar `visiekaart_join.html` |
| Tool-client | `public/cinab-tool-client.js`, versie in de header |

## Deployen

```powershell
cd C:\Users\rikva\Projecten\cinab-tools\visiekaart
firebase use staging
firebase deploy --only hosting,database
```

Alleen hosting als de regels niet wijzigen: `firebase deploy --only hosting`.

## Productieproject aanmaken (nog te doen)

1. Nieuw Firebase-project aanmaken, database-regio `europe-west1` (ligt daarna onherroepelijk vast).
2. Anonymous sign-in aanzetten (Authentication, Sign-in method, Anonymous).
3. Project-ID invullen in `.firebaserc` onder `production`.
4. `firebase use production` en deployen.
5. Project-ID en regio noteren in het toolpaspoort voor de tooldeveloper.
