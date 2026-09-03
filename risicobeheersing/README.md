# Risicobeheersing

| | |
|---|---|
| Firebase-project | `risicobeheersing-e174f` (Spark-plan, aangemaakt 3 september 2026); hosting op `risicobeheersing-e174f.web.app` |
| Regio | `europe-west1` (vastgelegd bij aanmaken RTDB, 3 september 2026, HS-11) |
| Database-URL | `https://risicobeheersing-e174f-default-rtdb.europe-west1.firebasedatabase.app` |
| Regels deployt | Rik, vanuit deze map |
| Anonymous sign-in | aan sinds 3 september 2026, met auto clean-up na 30 dagen |
| Subdomein | `risicobeheersing.cinab.nl` (besluit 3 september 2026; uitzondering op het patroon, varianten lopen via `?doel=`) |
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

## Firebase web-config

Voor `RB_FB_STAGING` en `RB_FB_PROD` in het glue-blok van de tool. Eén project voor beide,
dus beide constanten krijgen deze waarden. De `apiKey` is publiek van opzet en hoort in de
browser; de beveiliging zit in `database.rules.json`, niet in deze sleutel.

```js
{
  apiKey: "AIzaSyB5fpBg_jmPT1pacDjuX_rZ7LA_DdWi5wQ",
  authDomain: "risicobeheersing-e174f.firebaseapp.com",
  databaseURL: "https://risicobeheersing-e174f-default-rtdb.europe-west1.firebasedatabase.app",
  projectId: "risicobeheersing-e174f",
  storageBucket: "risicobeheersing-e174f.firebasestorage.app",
  messagingSenderId: "254623665118",
  appId: "1:254623665118:web:79607b597daf0deb3eab4f"
}
```

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

1. DNS aanmaken voor `risicobeheersing.cinab.nl`: CNAME naar het Firebase-project, plus het A-record voor `www.`.
2. Realtime Database aanmaken in `europe-west1` en anonymous sign-in aanzetten. Project en `.firebaserc` zijn klaar.
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
