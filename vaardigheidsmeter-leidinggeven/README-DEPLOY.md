# README-DEPLOY — Vaardigheidsmeter Leidinggeven v0.5

Deploy-pakket na het CINAB-testprotocol van 2026-09-03. Alles wat nodig is om de werksessie op de website te draaien.

## Inhoud

| Bestand | Plaatsing | Opmerking |
|---|---|---|
| `vaardigheidsmeter-leidinggeven.html` | webroot van de tool-host (Firebase Hosting `public/`) | hoofd-app: gratis + 360/teamanalyse, live-adapter met demo-terugval |
| `vaardigheidsmeter_join.html` | idem, naast de hoofd-app | beoordelaar-pagina; wordt geserveerd op `/join/{code}` via de rewrite |
| `cinab-tool-client.js` | idem, naast de hoofd-app | **niet in dit pakket**: neem het ongewijzigde bestand uit de context-bibliotheek/platform-pack (de app importeert het relatief: `./cinab-tool-client.js`) |
| `firebase.json` | projectroot van het Firebase-project | rewrite `/join/** → /vaardigheidsmeter_join.html`, CSP `frame-ancestors` voor de hoofd-app |
| `database.rules.json` | projectroot | app-specifieke regels: `meta`/`content`/`state` facilitator-only, `answers` push-only met validatie (name ≤120, vals LV1..LV20 0-100, `at` verplicht) |
| `TESTRAPPORT-…md` | documentatie | bevindingen B-01…B-23, testkaart, staging-stappen |

## Vóór go-live invullen

1. **`FB_CONFIG`** in *beide* HTML-bestanden (gedeeld blok `VLM SHARED: FB_CONFIG`, byte-identiek houden): `apiKey` en `appId` uit de Firebase-console van project `cinab-vaardigheidsmeter-leidinggeven` (europe-west1). Zolang de placeholders `[INVULLEN…]` staan, draait de join-pagina in demo en valt de hoofd-app bij een token terug op demo mét zichtbare melding.
2. **Fonts self-hosten** (`.woff2` Fraunces 600, Plus Jakarta Sans 400/600/700) en `@font-face` toevoegen aan het `<style id="cinab-theme">`-blok — de standaard verbiedt font-CDN's; nu wordt de fallback-stack gebruikt.
3. **Platform (WordPress)**: `template_id = vaardigheidsmeter_leidinggeven`, `_cinab_betaal_vanaf_fase = 2`, `_cinab_credits = 1`, token-TTL 12 h, `_cinab_is_vergelijkbaar = ja`; embed-url en origin-whitelist van de tool-host; betaal-return-url = tool-url (de app geeft `returnUrl` mee aan `goToPayment`).
4. **E-mail-endpoint** `POST /wp-json/cinab/v1/stuur-uitnodigingen` — body `{token, raters:[{name,email,join_url}], meta:{initiatiefnemer, organisatie, tool_naam}}` → `{sent:n}`. Zonder dit endpoint faalt "Verstuur uitnodigingen" netjes met een melding (PLATFORM-WERKBOEK §3.4, blokkerend voor de betaalde route).

## Deploy

```bash
firebase use cinab-vaardigheidsmeter-leidinggeven            # of het staging-project
firebase deploy --only database,hosting
```

Staging en productie zijn gescheiden Firebase-projecten (EU); `FB_CONFIG` per omgeving.

## Echte-koppelingstest (staging, de ontbrekende schakel van het protocol)

1. Start vanuit de detailpagina met launch-code → devtools: `POST /start-tool` 200; `sessionStorage.vlm_cinab` bevat `token`, `betaalVanafFase: 2`, `credits: 1`, `code`.
2. Kies 360 → Akkoord → `POST /sessie-afrekenen` `{betaald:true}`; F5 → app blijft live en keert terug op de vragenlijst met de antwoorden (B-02).
3. Nodig 3 collega's uit → tweede klik verstuurt → `POST /stuur-uitnodigingen` 200; RTDB toont `/sessions/{code}/content`.
4. Open de join-link op een telefoon → organisatie zichtbaar, beoordeling versturen → bij de initiatiefnemer springt de badge live op "gereageerd".
5. Bij 3 reacties: teambeeld → "Download als PDF / Printen" → printdialoog én `POST /rapport-opslaan` 200 met `data_ref`; nogmaals → `PATCH /rapport/{id}`.
6. Account met 0 credits: Akkoord → credit-shop (URL bevat `cinab_return_url`) → betaal → terugkeer `?action=resume` → vragenlijst betaald, geen tweede afschrijving.
7. Rules Playground: push naar `answers` zonder `at` → denied; lezen `answers` met een andere uid → denied.

## Demo

Zonder `?launch`/`?token` draait alles in demo (ribbon "demo"): geen platform-calls, geen Firebase-writes, geen credits, geen opslag; reacties via "Simuleer reacties". Werkt in een sandboxed 16:9 iframe (geen `alert()` meer). `?demo=1` is toegestaan en verandert niets aan dit gedrag.

## Go-live-checklist

- [ ] `FB_CONFIG` ingevuld in beide bestanden (md5 gedeeld blok gelijk: `python3 qa_static.py`)
- [ ] fonts self-hosted, `@font-face` aanwezig
- [ ] `firebase deploy --only database,hosting` op staging én productie
- [ ] WordPress-meta ingesteld; embed-url, origin-whitelist, betaal-return-url
- [ ] e-mail-endpoint gebouwd en getest (stap 3 hierboven)
- [ ] staging end-to-end (stappen 1–7) groen
- [ ] beslispunten D-1…D-4 uit het testrapport beantwoord
- [ ] testscripts (`testprotocol-2026-09-03/`) opnieuw gedraaid na elke wijziging: `qa_static.py`, `qa_scenario.py`, `qa_aspects.py`
