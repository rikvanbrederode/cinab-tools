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

## 2. AI-proxy: server-side instellen (checklist §9)

In `risicobeheersing-ai-proxy.php`:
1. `ANTHROPIC_MODEL` invullen (gelicentieerd model) — **[INVULLEN]**.
2. Sleutel **nooit** in het bestand: env-var `ANTHROPIC_API_KEY`, of `../cinab-secrets.php` boven de webroot
   met `<?php return ['anthropic_key' => 'sk-ant-…'];`.
3. Productie-schakelaars (het bestand staat op staging-defaults):
   - `CINAB_REQUIRE_TOKEN = true`
   - `CINAB_VALIDATE_URL = 'https://cinab.nl/wp-json/cinab/v1/validate-token'`
4. Vereist: PHP met cURL; schrijfrechten op `/tmp/cinab_ai_rate` (rate-limiting).

**Echte AI-test op staging** (met `CINAB_REQUIRE_TOKEN = false` tijdelijk):
```bash
curl -s -X POST https://staging.risicobeheersing.cinab.nl/risicobeheersing-ai-proxy.php \
  -H 'Content-Type: application/json' -H 'Origin: https://staging.risicobeheersing.cinab.nl' \
  -d '{"task":"cluster","lang":"nl","data":{"maxClusters":3,"items":[{"idx":0,"text":"Onduidelijke overdracht bij dienstwissel"},{"idx":1,"text":"Verouderd medicatiesysteem"},{"idx":2,"text":"Geen dubbele controle"}]}}'
```
Verwacht: `{"task":"cluster","text":"{\"clusters\":[…]}"}`. Daarna in de tool: fase 1 → "Clusteren met AI" →
de banner meldt **"AI heeft de inzendingen in n clusters geordend"**. Meldt hij "AI niet bereikbaar", dan
is de proxy/sleutel/origin niet goed — de tool verhult dat nooit meer als AI-resultaat.

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
