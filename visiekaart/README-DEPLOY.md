# README-DEPLOY — Visiekaart (werksessie) · pakket 2026-09-03

Dit pakket bevat de zeven bladen na het CINAB-testprotocol (bevindingen B-01 t/m B-27, zie
`TESTRAPPORT-VISIEKAART-2026-09-03.md`), de bijgewerkte AI-proxy-template en de lokale fontlaag.

## 1. Plaatsing

Zet alles in **één map** op de tool-host (bijvoorbeeld `/tools/visiekaart/`):

```text
visiekaart_fase0.html … visiekaart_fase5.html, visiekaart_rapport.html
cinab-tool-client.js              (ongewijzigde module-client, zelfde map — wordt relatief geïmporteerd)
fonts/fonts.css                   (+ de vier woff2-bestanden, zie §3)
```

De deelnemerslink is nu `…/visiekaart_fase0.html?join=<code>` (B-01). Er is **geen** hosting-rewrite
meer nodig. Wil je toch een korte link (`/join/<code>`), maak dan een **302-redirect** naar
`visiekaart_fase0.html?join=$1` — nooit een interne rewrite die de URL op `/join/…` laat staan,
want dan breken de relatieve fase-navigaties op het deelnemer-apparaat.

## 2. AI-proxy

* Bestand: `cinab-ai-proxy_template.php` → plaats als **`/vk-ai-proxy.php` op de site-root** van de
  tool-host (de bladen roepen `VK_AI_ENDPOINT = '/vk-ai-proxy.php'` aan). Staat de tool onder een
  ander pad of domein, pas dan `VK_AI_ENDPOINT` in de vier AI-bladen (fase 1, 2, 3, 5) aan — het staat
  in het gedeelde AI-helper-blok; wijzig het in alle vier tegelijk.
* Invullen: `ANTHROPIC_API_KEY` (server-omgeving), `ANTHROPIC_MODEL`, `$ALLOWED_ORIGINS`,
  `CINAB_VALIDATE_URL` (productie-URL), `CINAB_REQUIRE_TOKEN = true` in productie.
* Nieuw in deze versie: taak **`roadmap`** (B-23). Zonder die taak kreeg fase 5 altijd 422.
* Tokenpad (B-24): het platform-token uit `startCinabSession()` staat nu op `window.__VK_TOKEN` en
  gaat mee in `{token}` én header `X-CINAB-Token`.
* Zonder token (staging zonder platform): zet in een klein inline script vóór de bladen
  `window.__VK_AI_OPEN = true` — anders doet de tool in productie-modus **geen** AI-call en meldt
  hij eerlijk "AI niet bereikbaar — voorlopige lokale clustering". In demo-modus (localhost/LAN)
  wordt nooit gecalld.

## 3. Fonts (B-13)

Geen Google-Fonts-CDN meer (AVG, standaard). Plaats in `fonts/`:

```text
DMSans-Variable.woff2   DMSans-Italic.woff2   DMSerifDisplay-Regular.woff2   DMSerifDisplay-Italic.woff2
```

(`fonts/fonts.css` verwijst ernaar met `font-display: swap`.) Ontbreken ze, dan vallen de bladen terug
op de systeemstack; er wordt nooit iets extern geladen.

## 4. Firebase RTDB (cross-device) — B-20

`VK_FB_PROD` staat in het gedeelde glue-blok van alle zeven bladen nog op `null`. Op elke host die
niet als staging wordt herkend (`localhost`, `127.*`, `192.168.*`, `*.local`, `*.web.app`,
`*.firebaseapp.com`, `staging.*`) is er dan **geen** live-verbinding: deelnemers op een eigen
apparaat kunnen niet meedoen. De tool toont dat nu als één duidelijke melding (facilitator én
deelnemer) en draait in dezelfde browser gewoon door. Vul `VK_FB_PROD` in (zelfde vorm als
`VK_FB_STAGING`) in **alle zeven bladen** en houd het blok byte-identiek (`qa_static.py` bewaakt dat).
Zet `database.rules.json` op het productieproject.

## 5. Echte-AI-test op staging (de ontbrekende schakel)

```bash
# cluster
curl -s -X POST https://<tool-host>/vk-ai-proxy.php \
  -H 'Content-Type: application/json' -H 'Origin: https://<tool-host>' \
  -d '{"task":"cluster","lang":"nl","token":"<sessietoken of leeg op staging>","data":{"items":["Bewoners voelen zich eenzaam","Digitale systemen sluiten niet aan","Familie wordt te weinig betrokken"],"question":"Welk vraagstuk maakt dit plan nodig?","context":"Fase 1 van de Visiekaart"}}'
# verwacht: {"task":"cluster","text":"{\"clusters\":[{\"label\":\"…\",\"members\":[0,2]},…]}"}  (members dekken 0..n-1 exact één keer)

# roadmap
curl -s -X POST https://<tool-host>/vk-ai-proxy.php \
  -H 'Content-Type: application/json' -H 'Origin: https://<tool-host>' \
  -d '{"task":"roadmap","lang":"nl","token":"","data":{"stip":"Omdat …","themes":[{"name":"Klantgerichtheid","score":4.2}],"acties":[{"text":"Interview tien bewoners","themeName":"Klantgerichtheid"}],"versnellers":["Eigenaarschap"],"remmers":["ICT"],"sessie":{"urgentie":1.2,"periodes":20}}}'
# verwacht: {"task":"roadmap","text":"{\"actions\":[{\"text\":\"Interview tien bewoners\",\"priorityScore\":85,\"justif\":\"…\",\"owner\":\"…\"}]}"}
```

Bewijs in de UI: op het clusterscherm staat "AI-resultaat: geclusterd door AI …" (element
`#t-aiNote` / `.vk-ai-note[data-ai-source="ai"]`); bij een fout staat er "AI niet bereikbaar — …".
Kwaliteit (protocol stap 4.5): clusters dekken alle items exact één keer, labels kort en dekkend,
adviezen concreet en in de juiste taal; de tool strip't fences en verwerpt ongeldige JSON.

## 6. Demo-modus

Demo is host-gebaseerd (`isProductionMode()`): op localhost/LAN draait de tool met voorbeelddata en
zonder AI-call; op elke andere host is hij live. `?demo=1` bestaat niet (standaard §7 — beslispunt
B-21). De knoppen `data-env="dev-only"` (reset, terug) zijn op productie verborgen.

## 7. Go-live-checklist

- [ ] Zeven bladen + `cinab-tool-client.js` + `fonts/` in één map; `python3 qa_static.py` groen (blokken md5-identiek)
- [ ] `/vk-ai-proxy.php` geplaatst en ingevuld; curl-test §5 geeft geldige JSON voor `cluster` én `roadmap`
- [ ] `CINAB_REQUIRE_TOKEN = true`; start via het platform zet `window.__VK_TOKEN` (console) en de AI-melding zegt "AI-resultaat"
- [ ] `VK_FB_PROD` ingevuld in alle zeven bladen; cross-device-bewijs: telefoon volgt F0 → F5, roster en tellers live
- [ ] Deelnemerslink/QR wijst naar `visiekaart_fase0.html?join=<code>` op de juiste host
- [ ] Betaalpoort op fase 5 en `saveReport` → `rapport_url` op staging doorlopen
- [ ] Beslispunten B-21 (adviesborden.nl-vermeldingen, `?demo=1`) en B-12-restpunten (knopkleuren) besloten
- [ ] Regressie na elke wijziging: `python3 qa_scenario.py && python3 qa_teams.py && python3 qa_aspects.py && python3 qa_static.py && node qa_tparity.js`
