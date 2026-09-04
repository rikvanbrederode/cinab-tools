# README-DEPLOY — Risicobeheersing® op risicobeheersing.cinab.nl (v0.11, 2026-09-02)

Alles wat nodig is om de werksessie op de website te laten draaien, in de volgorde waarin je het plaatst.

## 1. Bestanden op het tool-subdomein (webroot)

| Bestand | Rol |
|---|---|
| `risicobeheersing_fase0.html` … `risicobeheersing_fase5.html`, `risicobeheersing_rapport.html` | De zeven fasebestanden (standalone, geen build) |
| `cinab-tool-client.js` | Ongewijzigde platformclient; wordt als ES-module geïmporteerd door alle zeven bestanden — moet **naast** de HTML staan |
| `risicobeheersing-ai-proxy.php` | Server-side AI-proxy (fase 1 clusteren, fase 4 verfijnen) — zelfde origin als de tool |
| `fonts/` (4× `.woff2`) | Huisstijlfonts; zie `fonts/README-FONTS.md` + `fonts/maak-woff2.py` |

Embed-url voor het platform (`_cinab_embed_url`): `https://risicobeheersing.cinab.nl/risicobeheersing_fase0.html`
Origin (`_cinab_origin`): `https://risicobeheersing.cinab.nl`

## 2. AI: het endpoint staat op het platform

De proxy hoort **niet** op de tool-host. Firebase Hosting is statisch en draait geen PHP, dus het
oude pad `/risicobeheersing-ai-proxy.php` bestond daar nooit: elke aanroep kwam nergens aan en de
tool viel stil terug op de lokale berekening.

Sinds s87 loopt AI via het platform:

* Endpoint: **`POST https://cinab.nl/wp-json/cinab/v1/ai`**. Fase 1 en fase 4 leiden die host zelf
  af uit de platformcontext van de sessie (`sessionStorage.rb_cinab`); alleen `cinab.nl` wordt
  geaccepteerd, een expliciete `<html data-cinab-api="...">` wint.
* Verzoek `{ token, task, lang, data }`, token in de body en niet als header. Antwoord
  `{ task, text }`, ongewijzigd.
* Taken voor deze tool: `cluster` (fase 1) en `verfijn_advies` (fase 4). De prompts staan
  server-side in de plugin, onder `includes/ai/taken-risicobeheersing.php`.
* Aan tool-zijde valt er niets in te vullen. Sleutel, model, origins, tokenvalidatie,
  rate-limiting en het plafond per sessie staan in de plugin.

**Aanzetten** gebeurt op het platform: `CINAB_AI_KEY` en `CINAB_AI_MODEL` in `wp-config.php`, en
bij de sessie het blok **AI** met takenset `risicobeheersing`. Staat het vinkje uit, dan geeft het
endpoint 403 en draait de tool lokaal.

**Controle na aanzetten.** In de tool: fase 1 → "Clusteren met AI" → de banner meldt dat AI de
inzendingen heeft geordend. Meldt hij "AI niet bereikbaar", dan is er iets mis met de sleutel, het
model of het vinkje; de tool verhult dat nooit als AI-resultaat. Op het platform:
`/beheer/ai/` toont de aanroepen en hoeveel er op terugval eindigden.

`server/risicobeheersing-ai-proxy.php` blijft in de repo als bron van de prompttekst. Het bestand
wordt niet meer gedeployd.

## 3. Demo op de website

Zonder launch-code draait de tool zelfstandig (geen platform, geen opslag). Voor een échte demo met
voorbeelddata en simulatieknoppen: open `…/risicobeheersing_fase0.html?demo=1`. De demo-vlag blijft
de hele doorloop actief (sessionStorage), doet **geen** AI-call, geen betaling, geen platform-opslag.

## 4. Platform (WordPress meta-velden, Appendix C) — nog te bevestigen

`_cinab_credits`, `_cinab_betaal_vanaf_fase`, `_cinab_token_geldig_uren`, `_cinab_deel_geldig_dagen`,
`_cinab_render_url_pattern`: zie `APP-START_risicobeheersing.md` §2 — de tool leest betaalfase en credits
runtime uit `start-tool` en dwingt de poort af (fase 0–5 = 0–5, rapport = 6).

## 5. Live meerschermen (deelnemers op eigen telefoon) — volgende stap

Nu: facilitator-modus met deelnemer-view in dezelfde browser (bewezen werkend, incl. tabblad-sync).
Cross-device vereist het RB-Firebaseproject (europe-west1): config invullen in het gedeelde blok
(`RB_FB_STAGING` / `RB_FB_PROD`), `firebase.json` + `database.rules.json` deployen en
`risicobeheersing_join.html` bouwen (standaard §11A). Beide configbestanden staan klaar in dit pakket.

## 6. Go-live-controle (kort)

- [ ] Fonts geplaatst (4× woff2) — anders fallback-typografie.
- [ ] Proxy: model + sleutel + `CINAB_REQUIRE_TOKEN=true` + productie-validate-url.
- [ ] `cinab-tool-client.js` naast de HTML; console toont geen 404 op de module.
- [ ] Launch-flow: fase 0 met `?launch=…` → sessiecontext gevuld (`sessionStorage.rb_cinab`).
- [ ] Betaalpoort op staging end-to-end (402 → Mollie → `?action=resume`).
- [ ] Rapport: `saveReport` → rapport-url → `notifyCompleted`.
