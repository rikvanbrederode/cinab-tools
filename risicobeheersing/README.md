# Risicobeheersing

| | |
|---|---|
| Firebase-project | nog aanmaken, daarna project-ID invullen in `.firebaserc` |
| Regio | `europe-west1` (ligt onherroepelijk vast bij aanmaken, HS-11) |
| Regels deployt | Rik, vanuit deze map |
| Anonymous sign-in | direct aanzetten bij het aanmaken (Authentication, Sign-in method, Anonymous) |
| Subdomein | nog te bepalen; conventie is `[instrument]-[onderwerp].cinab.nl`, zie `SUBDOMAIN-NAMING.md` |
| Tool-client | `public/cinab-tool-client.js`, versie in de header |
| AI-proxy | `server/risicobeheersing-ai-proxy.php`, draait op SiteGround, niet op Firebase Hosting |
| Fasen | 0 tot en met 5, plus rapport (poortindex rapport = 6) |
| Datacontract | `template_id` risicobeheersing, `schema_version` 1.0, zes zone-dimensies |

## Mapindeling

```
risicobeheersing/
  .firebaserc          projectaliassen (default, staging, production)
  firebase.json        hosting-config en verwijzing naar de regels
  database.rules.json  RTDB-securityregels
  public/              alles wat naar Firebase Hosting gaat
  server/              PHP-proxy, hoort op SiteGround, nooit in public
  fonts/               bouwscript voor de vier woff2-bestanden
  qa/                  testscripts van de tooldeveloper
```

Alleen `public/` wordt gedeployd. De zeven HTML-bestanden importeren
`./cinab-tool-client.js` als module, dus die staat daar naast en niet in de root.

## Deployen

```powershell
cd C:\Users\rikva\Projecten\cinab-tools\risicobeheersing
git status
firebase use staging
firebase deploy --only hosting,database
```

Alleen hosting als de regels niet wijzigen: `firebase deploy --only hosting`. Geen deploy
zonder commit; de commitmessage is de changelog-regel.

## Open punten voor livegang

1. Subdomein kiezen volgens de conventie en het DNS-record aanmaken.
2. Firebase-project aanmaken in `europe-west1`, anonymous sign-in aan, project-ID in `.firebaserc`.
3. Waar draait de AI-proxy en op welke origin. De tool staat op Firebase Hosting en kan
   zelf geen PHP draaien, dus de proxy komt op SiteGround en de app praat cross-origin.
4. `ANTHROPIC_MODEL`, de sleutel als omgevingsvariabele, `CINAB_REQUIRE_TOKEN = true` en de
   productie-validate-url. De sleutel is van CINAB, niet van de tooldeveloper.
5. Meta-velden in WordPress: credits, betaal-vanaf-fase, token-TTL, deellink-TTL en
   `_cinab_render_url_pattern`. Zie het toolpaspoort.
6. Renderroute voor het gedeelde rapport. `risicobeheersing_rapport.html` is nu de laatste
   fase van de sessie en leest geen opgeslagen rapport terug via `rapport-data/{rapport_id}`.
   Zolang dat er niet is, kan een deellink geen rapport tonen.
7. Vier woff2-bestanden plaatsen, anders draait de tool met vervangende letters.
8. Bewaartermijn persoonsgegevens vastleggen en het moment waarop de sessie-state wordt gewist.
