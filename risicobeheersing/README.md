# Risicobeheersing

| | |
|---|---|
| Firebase-project | `risicobeheersing-e174f` (Spark-plan, aangemaakt 3 september 2026); hosting op `risicobeheersing-e174f.web.app` |
| Regio | `europe-west1` (vastgelegd bij aanmaken RTDB, 3 september 2026, HS-11) |
| Database-URL | `https://risicobeheersing-e174f-default-rtdb.europe-west1.firebasedatabase.app` |
| Regels deployt | Rik, vanuit deze map |
| Anonymous sign-in | aan sinds 3 september 2026, met auto clean-up na 30 dagen |
| Subdomein | `risicobeheersing.cinab.nl`, live sinds 3 september 2026 (uitzondering op het patroon, varianten lopen via `?doel=`) |
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

Klaar: subdomein en DNS, Firebase-project met anonymous sign-in, de vier huisstijlfonts,
de QR-generator self-hosted, en de sessie als concept op staging.

1. Meta-velden in WordPress omzetten van de `.web.app`-url naar
   `https://risicobeheersing.cinab.nl` voor zowel `_cinab_embed_url` als `_cinab_origin`.
   Die twee moeten altijd naar dezelfde plek wijzen, anders blokkeert CORS elke API-call.
2. Credits, betaal-vanaf-fase, token-TTL en de bewaartermijn voor persoonsgegevens vaststellen.
   Let op: de tool telt vanaf nul, fase 0 tot en met 5 en het rapport is 6.
3. AI-proxy: waar hij draait (SiteGround, niet Firebase), het model, de sleutel als
   omgevingsvariabele, `CINAB_REQUIRE_TOKEN = true` en de productie-validate-url. De sleutel
   is van CINAB, niet van de tooldeveloper.
4. Renderroute voor het gedeelde rapport. `risicobeheersing_rapport.html` is nu de laatste
   fase van de sessie en leest geen opgeslagen rapport terug via `rapport-data/{rapport_id}`.
   Zolang dat er niet is blijft `_cinab_render_url_pattern` leeg en rendert het platform zelf.
5. `risicobeheersing_join.html` bouwen, daarna de rewrite `/join/**` terugzetten in
   `firebase.json`.
6. De vangnetregel `$phase/$collection/$pushId` in `database.rules.json` begrenzen voordat
   deelnemers op eigen apparaat meedoen. Nu controleert hij alleen of er een veld `at` in zit.
7. Volledige testronde: starten via de etalage, launch-code inwisselen, betaalpoort,
   rapport opslaan en openen.

## Wijzigingen van CINAB in de aanlevering van de tooldeveloper

Twee dingen zijn hier aangepast na oplevering. Bij een volgende set van de tooldeveloper
moeten ze opnieuw, anders komen ze er zo weer uit.

1. `risicobeheersing_fase0.html` regel 7: de QR-generator laadt uit `vendor/qrcode.min.js`
   in plaats van uit `cdnjs.cloudflare.com`. Zelfde bibliotheek, zelfde versie 1.0.0.
2. De vier woff2-bestanden staan in `public/fonts/`, niet in de map `fonts/` in de toolroot.
   Die map bevat alleen het bouwscript en wordt niet gedeployd.
