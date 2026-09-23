# README-DEPLOY — Vaardigheidsmeter Leidinggeven v0.7

> **Aangepast aan de CINAB-kant op 23 september 2026.** Drie dingen wijken af van wat hieronder
> staat, en die wijken bewust af:
>
> 1. **Geen `vaardigheidsmeter-ai-proxy.php`.** De tool-host is Firebase Hosting en die is statisch,
>    dus een PHP-bestand naast de app wordt nooit uitgevoerd. De AI loopt sinds s87 via het platform:
>    `POST {apiBase}/wp-json/cinab/v1/ai`, met dezelfde body `{token, task, lang, data}` en hetzelfde
>    antwoord `{task, text}`. De app is daarop omgezet; `apiBase` komt uit `?cinab` bij de start, dus
>    staging en productie regelen zichzelf. Punt 6 hieronder vervalt daarmee.
> 2. **De fontregel staat er weer in.** `<link rel="stylesheet" href="fonts/fonts.css">` direct na de
>    charset, in beide bestanden. De woff2-bestanden staan in `public/fonts/`. Punt 2 hieronder is
>    daarmee afgehandeld.
> 3. **`FB_CONFIG` wees naar een project dat niet bestaat.** In het geleverde pakket stonden
>    `authDomain`, `databaseURL` en `projectId` op `cinab-vaardigheidsmeter-leidinggeven`, met
>    `apiKey` en `appId` op `[INVULLEN]`. `firebase projects:list` kent maar drie projecten, en voor
>    deze tool is dat `vaardigheidsmeter-leidin-f82f7`, precies zoals `.firebaserc` al zei. Het hele
>    blok is vervangen door de uitvoer van `firebase apps:sdkconfig WEB --project
>    vaardigheidsmeter-leidin-f82f7`, in beide bestanden identiek. RTDB staat in europe-west1.
>    Gevolg voor de geschiedenis: met dat oude blok had het verzamelen van 360-reacties ook met
>    ingevulde sleutels nooit gewerkt.
>
> Nog open aan de platformkant: de takenset voor de taak `beschouwing` bestaat nog niet
> (`includes/ai/` heeft alleen visiekaart en risicobeheersing). Zonder die set weigert het endpoint de
> taak en valt het rapport terug op de lokale beschouwing.
>
> Let op bij deployen: het commando onder "Deploy" hieronder noemt
> `cinab-vaardigheidsmeter-leidinggeven`. Dat project bestaat niet. Gebruik
> `firebase use vaardigheidsmeter-leidin-f82f7`, of laat `firebase use` weg, want `.firebaserc` wijst
> daar al naartoe.

Deploy-pakket na het CINAB-testprotocol van 2026-09-03. Alles wat nodig is om de werksessie op de website te draaien.

## Inhoud

| Bestand | Plaatsing | Opmerking |
|---|---|---|
| `vaardigheidsmeter-leidinggeven.html` | webroot van de tool-host (Firebase Hosting `public/`) | hoofd-app: gratis + 360/teamanalyse, live-adapter met demo-terugval |
| `vaardigheidsmeter_join.html` | idem, naast de hoofd-app | beoordelaar-pagina; wordt geserveerd op `/join/{code}` via de rewrite |
| `cinab-tool-client.js` | idem, naast de hoofd-app | **niet in dit pakket**: neem het ongewijzigde bestand uit de context-bibliotheek/platform-pack (de app importeert het relatief: `./cinab-tool-client.js`) |
| `firebase.json` | projectroot van het Firebase-project | rewrite `/join/** → /vaardigheidsmeter_join.html`, CSP `frame-ancestors` voor de hoofd-app |
| `database.rules.json` | projectroot | app-specifieke regels: `meta`/`content`/`state` facilitator-only, `answers` push-only met validatie (name ≤120, vals LV1..LV20 0-100, `at` verplicht) |
| `vaardigheidsmeter-ai-proxy.php` | tool-host, naast de hoofd-app (same-origin) | **AI-verrijking van het rapport (betaalde 360).** Server-side proxy: browser stuurt alleen een PII-vrij datapakket + taak `beschouwing`; prompt/model/`max_tokens` server-side; token als poort; strikte JSON terug. De app roept `location.origin + '/vaardigheidsmeter-ai-proxy.php'` aan en valt bij elke fout terug op de lokale beschouwing. |
| `TESTRAPPORT-…md` | documentatie | bevindingen B-01…B-23, testkaart, staging-stappen |

## Vóór go-live invullen

1. **`FB_CONFIG`** in *beide* HTML-bestanden (gedeeld blok `VLM SHARED: FB_CONFIG`, byte-identiek houden): `apiKey` en `appId` uit de Firebase-console van project `cinab-vaardigheidsmeter-leidinggeven` (europe-west1). Zolang de placeholders `[INVULLEN…]` staan, draait de join-pagina in demo en valt de hoofd-app bij een token terug op demo mét zichtbare melding.
2. **Fonts self-hosten** (`.woff2` Fraunces 600, Plus Jakarta Sans 400/600/700) en `@font-face` toevoegen aan het `<style id="cinab-theme">`-blok — de standaard verbiedt font-CDN's; nu wordt de fallback-stack gebruikt.
3. **Platform (WordPress)**: `template_id = vaardigheidsmeter_leidinggeven`, `_cinab_betaal_vanaf_fase = 2`, `_cinab_credits = 1`, token-TTL 12 h, `_cinab_is_vergelijkbaar = ja`; embed-url en origin-whitelist van de tool-host; betaal-return-url = tool-url (de app geeft `returnUrl` mee aan `goToPayment`).
4. **E-mail-endpoint** `POST /wp-json/cinab/v1/stuur-uitnodigingen` — body `{token, raters:[{name,email,join_url}], meta:{initiatiefnemer, organisatie, tool_naam}}` → `{sent:n}`. Zonder dit endpoint faalt "Verstuur uitnodigingen" netjes met een melding (PLATFORM-WERKBOEK §3.4, blokkerend voor de betaalde route).
5. **Taal (NL/EN)** — de werksessie is volledig tweetalig: NL/EN-knop rechtsboven in zowel de hoofd-app als de join-pagina. De taalkeuze wordt onthouden (localStorage) en overleeft refresh en resume; `?lang=nl|en` werkt als voorinvulling. De join-pagina volgt de **sessietaal** uit `/sessions/{code}/content.lang`, tenzij de beoordelaar zelf een taal koos. De AI-proxy krijgt de actieve taal mee, dus de verdiepende analyse komt terug in dezelfde taal. Het gedeelde `MODEL`-blok (domeinen, 20 competenties, 40 stellingen in beide talen) moet **byte-identiek** blijven in beide HTML's — controleer met `python3 qa/qa_lang.py`.
6. **AI-proxy** `vaardigheidsmeter-ai-proxy.php` (alleen voor de betaalde 360): zet het bestand op de tool-host naast de hoofd-app. Vul in: `ANTHROPIC_MODEL` (gelicentieerd model), `$ALLOWED_ORIGINS` (productie- + staging-subdomein), en de sleutel via env-var `ANTHROPIC_API_KEY` of `../cinab-secrets.php` boven de webroot — **nooit in het bestand**. In productie: `CINAB_REQUIRE_TOKEN = true` en `CINAB_VALIDATE_URL = https://cinab.nl/wp-json/cinab/v1/validate-token`. Zonder proxy of bij een fout toont het rapport gewoon de lokale (regelgebaseerde) beschouwing — de app blijft werken.

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
8. **Taal:** wissel halverwege de vragenlijst naar EN — stellingen, knoppen en voortgang schakelen om, ingevulde antwoorden blijven staan. Open daarna een join-link: die opent in de sessietaal. Loop één keer de hele sessie in het Engels door, inclusief rapport en afdrukweergave (protocol stap 6d).
9. **AI-verrijking** (betaalde 360, ≥3 reacties): op het resultaatscherm verschijnt kort "Verdiepende analyse wordt opgesteld…", daarna de AI-beschouwing met per advies een `Onderbouwing:`-regel. Devtools: `POST /vaardigheidsmeter-ai-proxy.php` 200 met `{text}`. Test de terugval: proxy tijdelijk uit → de lokale (regelgebaseerde) beschouwing blijft staan, geen vastloper. Op staging kun je de AI ook los bekijken met `?aitest=1` (proxy met `CINAB_REQUIRE_TOKEN=false`).

## Demo en live

**Live/demo hangt alleen aan de platformsessie.** Komt de tool binnen met een geldig launch-token, dan is de sessie live en verdwijnt de demo-ribbon — óók als Firebase/RTDB niet beschikbaar is. De RTDB is apart (`sync`) en alleen nodig om 360-reacties te verzamelen: valt die weg, dan blijft de eigen vragenlijst en het resultaat gewoon werken, toont de app `#sync-err`, en weigert `sendInvites` expliciet (geen "verstuurd"-melding terwijl er niets kan binnenkomen). Staan `FB_CONFIG.apiKey`/`appId` nog op `[INVULLEN]`, dan is dat precies het geval.

Zonder `?launch`/`?token` draait alles in demo (ribbon "demo"): geen platform-calls, geen Firebase-writes, geen credits, geen opslag; reacties via "Simuleer reacties". Werkt in een sandboxed 16:9 iframe (geen `alert()` meer). `?demo=1` is toegestaan en verandert niets aan dit gedrag.

## Go-live-checklist

- [ ] `FB_CONFIG` ingevuld in beide bestanden (md5 gedeeld blok gelijk: `python3 qa_static.py`)
- [ ] fonts self-hosted, `@font-face` aanwezig
- [ ] `firebase deploy --only database,hosting` op staging én productie
- [ ] WordPress-meta ingesteld; embed-url, origin-whitelist, betaal-return-url
- [ ] e-mail-endpoint gebouwd en getest (stap 3 hierboven)
- [ ] taalcontrole groen: `python3 qa/qa_lang.py` (pariteit) en `python3 qa/qa_besch.py` (beschouwing NL+EN)
- [ ] volledige doorloop in het Engels gedaan (protocol stap 6d)
- [ ] AI-proxy geplaatst; `ANTHROPIC_MODEL` + `$ALLOWED_ORIGINS` + sleutel ingevuld; productie `CINAB_REQUIRE_TOKEN=true` + productie-validate-url; terugval getest (stap 8)
- [ ] staging end-to-end (stappen 1–7) groen
- [ ] beslispunten D-1…D-4 uit het testrapport beantwoord
- [ ] testscripts (`testprotocol-2026-09-03/`) opnieuw gedraaid na elke wijziging: `qa_static.py`, `qa_scenario.py`, `qa_aspects.py`
