# CINAB — Werkboek voor tool-bouwers

**Uitgave 3.6 · 4 september 2026**
Alles wat je nodig hebt om een CINAB-tool te bouwen en te koppelen aan het platform: het
datacontract, de koppeling, de betaalpoort, deelname op een eigen apparaat, het rapport en de
testen die de tool moet doorstaan voordat hij live gaat.

Deze uitgave is afgeleid van het interne werkboek van CINAB en loopt daarmee mee in versienummer.
Bij twijfel of tegenspraak is dat interne document leidend. Weggelaten zijn drie paragrafen die
niet over het bouwen van een tool gaan: de commerciële open punten (5.7) en de hardening en
auditpunten van het WordPress-platform zelf (7.5 en 7.6). De nummering is verder ongewijzigd, zodat
een verwijzing over en weer klopt; daarom ontbreken die nummers hieronder.

> **Regel of voorbeeld — lees dit eerst.**
> Bindend is alleen wat op een afvinkregel staat. Codeblokken en bestandsnamen zijn illustratie:
> ze laten zien hoe iets eruit kán zien, niet welke bestanden een tool moet hebben. Een levering
> bevat dus geen voorbeeldbestanden, en geen configuratie die verwijst naar een bestand dat niet
> in de levering zit. Wie hier een sjabloon van maakt, bouwt de vorige tool na in plaats van deze.

> **Wijzigingen v3.5 → v3.6** (4 september 2026 — AI rechtgezet na s87)
> - **§7.3 herschreven en §7.3a nieuw.** De AI-proxy stond voorgeschreven op de tool-host. Statische
>   hosting draait geen PHP, dus die aanroep kwam nergens aan: AI heeft in geen enkele tool ooit
>   gewerkt. AI loopt nu via het platform, `POST /wp-json/cinab/v1/ai`, met de sleutel, het model en
>   het plafond aan platformzijde. Een tool levert geen proxy en geen sleutel meer.
> - **Token in de body, geen eigen header.** De CORS-whitelist staat alleen `Content-Type` toe;
>   `X-CINAB-Token` liet de preflight stranden.
> - **Eerlijkheidsregels als afvinkregels.** AI is een overlay en nooit een afhankelijkheid, één
>   herkomstbron per taak met vier standen, geen animatie of banner die vooruitloopt op het antwoord,
>   ongeldige JSON is een terugval, en de herkomst gaat mee in de export.
> - **Appendix A, B en C aangevuld** met het endpoint, de plaats van de sleutel en de drie
>   meta-velden `_cinab_ai_aan`, `_cinab_ai_set` en `_cinab_ai_plafond`.
> - **Valkuilen 22 en 23** toegevoegd.

> **Wat er in 3.5 is veranderd (4 september 2026).** Deelname op een eigen apparaat is herzien na
> de bouw bij risicobeheersing: geen apart joinblad en geen hosting-rewrite meer, maar het
> fasebestand zelf met `?join=<code>`, met de link afgeleid uit `location.origin`. Nieuw als harde
> eis: `meta` met de facilitator-uid bestaat vóórdat er verkeer is, de deelnemer komt niet langs de
> betaalpoort, en de deelnemerslijst wordt bijgehouden zolang de sessie loopt (§7.4a). De
> renderroute van het rapport staat nu als tooleis in hoofdstuk 6. `session_code` van het platform
> is bindend voor de tool (§3.4). En hoofdstuk 2 toont voortaan de statische opzet die er werkelijk
> staat, met de waarschuwing dat statische hosting geen PHP draait.

---

## 0. Twee niveaus — en waarom we hier op B beginnen

| | **Niveau A — MVP / koppeling bewijzen** | **Niveau B — Productie / echte klantdata** |
|---|---|---|
| Token | korte TTL, single-use bij opslaan | per tool 1–72u (`_cinab_token_geldig_uren`); zo kort als de sessie toelaat |
| Auth (browser-POST) | sessietoken is de auth (route 2) | idem; token blijft primair |
| Token uit URL | direct uit de start-URL | via **launch-code → token-uitwisseling** |
| Sessie-state | mag in geheugen | **persistent server-side** (Redis/RTDB); nodig voor pay-resume én hervatten na "stop na fase X" |
| Secrets | geen credential in de bundle | AI-sleutel op het platform, nooit in de tool; RTDB dicht; EU-hosting |
| Publiek rapport | basis | meta-sanitisatie + strikte output-escaping verplicht |

> **Voor deze tool:** we testen mét echte klantdata, dus we starten direct op Niveau B. Alles in
> hoofdstuk 7 (beveiliging + AVG) moet af zijn vóór de eerste echte deelnemer.

---

## 1. EERST: het datacontract vastleggen (doe dit vóór je een regel bouwt)

Bindend; bepaalt het rapport-template. Wijzigen achteraf kost schema-versionering. Leg het per tool
vast in de tool-docs (invulblad: appendix E).

### 1.1 De interne schaal is van de tool, niet van het platform
- [ ] De volledige interne representatie (categorieën, sliders, ruwe scores) leeft in het opake
      `data`-veld. WordPress valideert dit **niet** (ADR 0004). Elke tool mag hier anders zijn.
- [ ] Visiekaart-voorbeeld: per stelling `kracht`/`neutraal`/`aandachtspunt` (`k`/`n`/`a`) plus
      sessie-instellingen (urgentie, budget, horizon) horen in `data`.

### 1.2 De dunne `scores`-laag (voor het rapport-template, niet voor cross-tool)
- [ ] `scores` bevat per dimensie een integer 0–100. **Let op:** dit is sinds v3 géén universele
      vergelijkeenheid meer (we doen geen cross-tool vergelijk). Het voedt het rapport-template en
      kan binnen dezelfde tool over de tijd worden vergeleken (hoofdstuk 4).
- [ ] Dimensienamen: alleen kleine letters + underscores, geen spaties/speciale tekens.
- [ ] Werkt de tool intern op een andere schaal: leg de **afbeelding naar `scores`** vast en bevries
      die. Voor Visiekaart's categorische scoring kies je een vaste mapping, bv.
      `aandachtspunt→0, neutraal→50, kracht→100`. Welke getallen je kiest is aan jou; ze moeten
      **stabiel** blijven over de tijd (zie 4.4).

### 1.3 De dunne wrapper (platformlaag — ADR 0004)
WordPress valideert **alleen** deze laag, licht. `data` blijft opaak.

```json
{
  "template_id": "visiekaart",
  "schema_version": "1.0",
  "scores": { "dimensie_a": 78, "dimensie_b": 52 },
  "meta": {
    "organisatie": "Naam bedrijf",
    "datum": "2026-06-03",
    "deelnemers": 8,
    "sector": "zorg"
  },
  "data": { "...volledige tool-payload, opaak..." },
  "parent_rapport_id": null
}
```

- [ ] `template_id` gekozen (kiest het render-template; oude rapporten houden hun eigen template).
- [ ] Vergelijken ondersteunen? → `_cinab_is_vergelijkbaar = true` (hoofdstuk 4). Voor Visiekaart: **false**.
- [ ] `parent_rapport_id` zit al als nullable veld in de wrapper — geen schema-ophoging nodig om
      vergelijken later aan te zetten. Bij een eenmalige sessie blijft het `null`.
- [ ] Wijzigingen aan de wrapper zelf → `schema_version` ophogen.

---

## 2. De tool zelf — architectuur

Aparte routes voor **starten** en **renderen**. Onze tools zijn statische bladen op Firebase
Hosting; de opzet hieronder is de vorm die er werkelijk staat, geen sjabloon om na te bouwen.

```
public/
  [tool]_fase0.html … [tool]_fase5.html   # de facilitator start op fase 0; deelnemers komen
                                          # binnen op het fasebestand met ?join=<code>
  [tool]_rapport.html                     # twee standen: direct na de laatste fase (lokaal),
                                          # en render vanaf het platform (?rapport_id=)
  cinab-tool-client.js                    # ongewijzigd overnemen, niet forken
  fonts/  vendor/                         # zelf gehost, geen externe CDN
firebase.json  database.rules.json  .firebaserc
```

> **Statische hosting draait geen PHP.** Een AI-proxy, of welk server-side stuk dan ook, kan dus
> niet op de tool-host staan; een pad als `/[tool]-ai-proxy.php` bestaat daar nooit. Zo'n proxy
> AI loopt daarom via het platform: `POST /wp-json/cinab/v1/ai` (§7.3a). De tool bouwt zelf geen
> proxy en heeft geen sleutel nodig.

- [ ] Tool leest het **token** (bij voorkeur via launch-code-uitwisseling, 3.4) en eventueel
      `parent_rapport_id` / `action=resume` uit de start-URL.
- [ ] **Alles wat de sessie moet overleven staat server-side, niet alleen in `localStorage`.**
      Nodig voor pay-resume én voor hervatten na "stop na fase X". `localStorage` overleeft de
      sprong naar Mollie/WP en terug niet betrouwbaar en is niet device-overschrijdend, dus het
      mag hooguit de werkkopie op het apparaat van de facilitator zijn. De gedeelde waarheid
      staat in de RTDB-sessie, de sessiecode bij het platformtoken (§3.4).
- [ ] **Multi-file opzet (fase-per-html):** draag bij elke fase-overgang (elke wisseling van
      html-bestand) het **token** en de **persistente sessie-identiteit** mee. Niet de betaalstatus —
      die leeft server-side (hoofdstuk 5).
- [ ] **Preview-modus:** bij `?preview=1` géén rapport opslaan, alleen `console.log` van de scores.
- [ ] Verplicht element: `<div id="cinab-status"></div>` — feedback en redirect lopen hierlangs.
- [ ] Tool start **full-screen** (ADR 0005); iframe alleen voor het **rapport** (render-route).
- [ ] Tijden: opslaan in **UTC**, "nu" in code uitrekenen (UTC), nooit tegen MySQL `NOW()`.
- [ ] **Geen credentials in de browser-bundle.** Sessietoken mag; AI-/API-sleutel (Anthropic) niet
      → het AI-endpoint van het platform (§7.3a).
- [ ] Bij afronden: **`session/clear`** — de tool houdt daarna **geen data** meer (stateless-at-rest).

---

## 3. De koppeling — route 2 (browser-POST met token-auth)

| Bestand | Waar | Status |
|---|---|---|
| `cinab-tool-client.js` | in de tool-app | **kern** — token lezen, wrapper POSTen, feedback, auto-redirect; helpers voor leesendpoint (h4) en afreken-endpoint (h5) |
| `cinab-callback.php` | op een PHP-host | **optioneel** — alleen voor tools met een eigen backend |
| `cinab-api-key-addon.php` (`X-CINAB-Key`) | in de WP-plugin | **optioneel** — tweede factor voor backend-tools |

### 3.1 Minimale integratie
- [ ] `<script src="/cinab-tool-client.js"></script>` toegevoegd.
- [ ] Bij start: token inwisselen/lezen → `cinab.init()`.
- [ ] Na de laatste stap: `cinab.submit(wrapper)` → POST naar `/wp-json/cinab/v1/rapport-opslaan`.
- [ ] Client-side input-validatie vóór de POST.
- [ ] Niet aanpassen: ingebouwde redirect, foutafhandeling, automatische `duur_minuten`.

### 3.2 Het opslaan-endpoint
`POST /wp-json/cinab/v1/rapport-opslaan` — body = `token` + wrapper. Auth = token.
Antwoord: `{ "rapport_id": "...", "rapport_url": "..." }`. Verlopen/2e gebruik → 409.

### 3.3 cinab-callback.php — alleen bij een eigen backend
- [ ] Niet nodig voor statische tools. Skip als je geen backend hebt.

### 3.4 Launch-code → token-uitwisseling (verplicht op B)
- [ ] Start-URL bevat een kortlevende **launch-code** (2 min, single-use) i.p.v. het token.
- [ ] Tool wisselt de launch-code meteen in via het **platform-endpoint**
      `POST /cinab/v1/start-tool` en ontvangt `{ token, betaal_vanaf_fase, credits, session_code }` —
      het poort-fasenummer en de credit-prijs komen dus uit déze response (§5.1).
- [ ] **`session_code` is bindend.** De tool gebruikt die code als sessiecode en verzint er geen
      eigen. Het platform bewaart hem bij het token en hervat een meerdaagse sessie via
      `POST /cinab/v1/herstart-sessie`, waarna de tool opnieuw start met `?session=<code>`.
      Verzint de tool zijn eigen code, dan wijst die herstart naar een sessie die in de RTDB nooit
      onder die naam is aangemaakt en komt de facilitator in een lege sessie terecht. Ontbreekt
      `session_code` (demo, lokaal draaien), dan pas een eigen code als terugval.
- [ ] Resultaat: het token staat **niet** in URL/historie/analytics.

### 3.5 validate-token: non-consuming
- [ ] Token-validatie verbruikt het token **niet** (anders breekt refresh/hervat/pay-resume).
      Single-use geldt pas bij `rapport-opslaan` (2e save → 409).

---

## 4. Vergelijken met de vorige meting (zelfde tool, over de tijd)

**Scope-besluit (v3):** geen cross-tool vergelijk. Alleen resultaat van **dezelfde tool** op datum X
vs. datum Y — een verschilscore tussen een eerdere en latere afname.

### 4.1 Aan/uit per tool
- [ ] `_cinab_is_vergelijkbaar` (true/false) bepaalt of vergelijken kan. **Visiekaart = false**
      (altijd een eenmalige sessie zonder vergelijk).
- [ ] Staat de vlag uit, dan: nieuwe sessie → opslaan met `parent_rapport_id = null` → state wissen.
      Geen vergelijkcode nodig in de tool.

### 4.2 Eigenaar en selectie — geen keuze voor de gebruiker
- [ ] **Eigenaar = de persoon van het gebruikersaccount** (niet de organisatie).
- [ ] Er wordt **altijd** vergeleken met de **laatste** eigen definitieve meting voor dit
      `template_id`. De gebruiker kiest niets.
- [ ] Resolve "de laatste" **één keer bij de start** en **pin** het concrete `parent_rapport_id`
      (voorkomt dat een tussentijds nieuw rapport "de laatste" verschuift).
- [ ] Gevolg, bewust geaccepteerd: vergelijken is **persoonsgebonden**. Een vervolgmeting door een
      ánder teamlid ketent niet aan de vorige.

### 4.3 De runtime-flow (alleen als de vlag aan staat)
1. Bij de start kan de gebruiker aangeven of hij/zij de vorige meting wil meenemen.
2. Zo ja: tool haalt de vorige data op via het **leesendpoint** (4.5), account-gescoped.
3. Gebruiker doorloopt de tool; de tool berekent en **rendert de delta zelf** (Optie 1).
4. Bij genereren: opslaan **mét** `parent_rapport_id` → versie-keten (`versie`, `parent_rapport_id`,
   `status`).
5. Daarna `session/clear` — tool houdt geen data.

> Omdat de **tool** de vergelijking doet, hoeft het platform jouw schaal niet te begrijpen.

### 4.4 Stabiliteitsregel (bindend voor vergelijk-tools)
- [ ] **Dimensienamen** (`scores`-sleutels) blijven identiek tussen afnames; anders is een
      per-dimensie delta betekenisloos.
- [ ] De **numerieke mapping** van de interne schaal naar `scores` blijft stabiel.
- [ ] Wijzig je dimensies of mapping → `schema_version` ophogen; oud en nieuw zijn op die punten niet
      meer vergelijkbaar (de tool detecteert de versie en degradeert netjes of mapt oud→nieuw).

### 4.5 Het leesendpoint (nieuw — enige nieuwe bouwsteen voor vergelijken)
- [ ] `GET /cinab/v1/rapport-data/laatste?template_id=...` — **token-auth**, **non-consuming**,
      rate-limited. Geeft de opgeslagen wrapper (incl. opaak `data`) van het **laatste eigen**
      definitieve rapport voor dit template terug.
- [ ] **Account-scoping is ingebouwd:** het endpoint accepteert géén willekeurig `parent_rapport_id`
      van buitenaf, maar zoekt zelf "mijn laatste voor dit template" op basis van token/account.
      Daarmee valt het IDOR-risico vrijwel weg — je kunt alleen je eigen data ophalen.
- [ ] Antwoord bevat het concrete `rapport_id` dat als `parent_rapport_id` wordt teruggeschreven.
- [ ] **Nooit via de publieke `/rapport/{uuid}`** data trekken — dat is de publieke, ge-escapete
      renderpagina, geen databron.

### 4.6 Voorbereid zijn zonder nu te bouwen
- [ ] Datamodel is al forward-compatible: `_cinab_is_vergelijkbaar` + nullable `parent_rapport_id` +
      versionering bestaan al. **Het leesendpoint (4.5) bestaat nog níét aan platform-kant** en
      staat ook nog niet in het platform-eisendocument; implementatie mag uitgesteld tot de
      **eerste** vergelijk-tool, maar leg het **contract** (vorm, auth, scoping) nu wél vast —
      óók in het platform-eisendocument.

---

## 5. De betaalmuur — gefaseerd afrekenen (credits)

**Leidend besluit:** géén credit-precheck bij start. Per tool instelbaar **vanaf welke fase** er
betaald moet worden. Default = de rapport-/genereerfase (= gedrag v2).

### 5.1 Configuratie
- [ ] `_cinab_betaal_vanaf_fase` per tool. **Leeg veld = gratis tool** (ADR 0007). De tool
      ontvangt het nummer via de `start-tool`-response; een ontbrekend nummer bij een
      betaalde tool behandel je als tool-default, een te hoog nummer als "laatste fase".
      Voorbeeld Visiekaart: `5` (betalen bij de overgang naar fase 5).
- [ ] `_cinab_credits` per tool (kosten per sessie; komt eveneens mee in de `start-tool`-response).

### 5.2 De poort (op de start van de betaalde fase)
Volgorde bij het binnengaan van de betaal-fase:
1. **Advisory saldo-check** (`POST /cinab/v1/saldo` met `{ token }` in de body — zo blijft het
   token uit URL/historie/logs, ADR 0006). Het endpoint accepteert ook `GET`, maar dat is voor
   ingelogde portaal-gebruikers; tools doen **POST**. Deze check bepaalt **alleen** welke knop
   verschijnt:
   - Voldoende → toon "Wil je verder? (X credits worden afgeschreven)".
   - Onvoldoende → toon "Onvoldoende credits — kopen?".
2. Bij bevestigen "verder" of na kopen: **atomische, idempotente aftrek** (5.3).

> De advisory check is UX. De **bindende** stap is de atomische aftrek. Daalt het saldo tussen check
> en aftrek (race), dan faalt de aftrek met **402** en val je vanzelf in de koop-tak.

### 5.3 Afreken-endpoint (nieuw)
- [ ] `POST /cinab/v1/sessie-afrekenen` — **token-auth**. Trekt `_cinab_credits` af met
      `UPDATE ... WHERE saldo >= nodig` (atomisch, voorkomt TOCTOU) en zet **`betaald = true`** op de
      sessie/het token.
- [ ] **Idempotent:** is er al betaald, dan no-op (geen dubbele afschrijving bij refresh/retry/pay-resume).
- [ ] Onvoldoende saldo → **HTTP 402** met `payment_url` (`/credits?return_token=...`) +
      `session_blijft_geldig_tot`.

### 5.4 De drie uitkomsten van de poort
- **Voldoende + verder** → afschrijven → door naar de betaalde fase.
- **Onvoldoende + kopen** → pay-resume (5.5) → terug → afschrijven → door.
- **Niet verder / niet kopen** → **stopt na de vorige fase**. Niets afgeschreven. De sessie-state
  blijft persistent, dus de gebruiker kan **binnen de token-geldigheid** terugkomen, alsnog kopen
  en doorgaan zonder de gratis fases over te doen. (Weeg dit mee bij de token-TTL-keuze, §7.1.)

### 5.5 Pay-resume flow (ongewijzigd t.o.v. v2, hergebruikt voor de poort)
1. Tool krijgt 402.
2. Sessie-state staat persistent.
3. Redirect naar `payment_url` met **`window.top.location`** (niet `window.location`).
4. Mollie betaling.
5. WC Thank-You-pagina **polt** `/wp-json/cinab/v1/credits-applied/{order_id}`.
6. Terug: `…/start?token=…&action=resume`.
7. Tool ziet `action=resume` → validate → state laden → **automatische retry** van
   `sessie-afrekenen` (idempotent) → door.

### 5.6 Server-side afdwingen (cruciaal door de multi-file opzet)
- [ ] De `betaald`-vlag leeft **server-side** op de sessie.
- [ ] De endpoints van de **betaalde fases** (fase ≥ poort) **en** `rapport-opslaan` controleren
      `betaald = true`, anders **402**. De client-check is alleen UX en mag niet de poort zijn.
- [ ] **Geef niets gratis weg:** de html van fase ≥ poort toont zijn inhoud pas nadat `betaald = true`
      server-side bevestigd is. Fases ervóór zijn de gratis preview.

---

## 6. Rapport wegschrijven, opslaan en renderen

Strategie: **blob + index**. Rapport = één JSON-blob; zoekbare velden apart in een index.

- [ ] Wrapper opslaan met `template_id` (+ `data` opaak, + `parent_rapport_id`).
- [ ] **UUID** deellink 22 tekens (`wp_generate_password(22,false,false)`, ~131 bits).
- [ ] Index-rij: trim tot universeel + `sector`.
- [ ] Versionering: `versie`, `parent_rapport_id`, `status` (definitief/gearchiveerd/
      pending_deletion — er is bewust géén concept-status, LC-1/LC-2).
- [ ] Multi-step: `PATCH /rapport/{id}` (mits dezelfde gebruiker).
- [ ] **Render via iframe** naar de render-modus van de tool: `_cinab_render_url_pattern`, bij
      statische hosting een renderpagina met query-parameter:
      `https://[naam].cinab.nl/[tool]_rapport.html?rapport_id={rapport_id}`. De renderpagina haalt
      de opgeslagen wrapper op via `GET /cinab/v1/rapport-data/{rapport_id}` en tekent dááruit,
      niet uit de live sessie. Bij vergelijk-tools rendert dezelfde route de delta-weergave.

#### De renderroute is een tooleis, geen platformextraatje

Zonder deze route werkt het rapport alleen op het apparaat van de facilitator, en alleen zolang hij
zijn browser niet opschoont. Iedereen die het rapport later of ergens anders opent, ziet niets.

- [ ] **Eén stand erbij, niet een tweede pagina.** Hetzelfde rapportblad heeft twee bronnen: direct
      na de laatste fase de lokale gegevens, en met `?rapport_id=` in de URL de opgeslagen snapshot
      van het platform. Laat alle leesfuncties van het rapport langs één punt lopen, dan verandert
      er verder niets aan de opbouw.
- [ ] **In render-modus slaat de pagina niets op** en plaatst zij **geen demovulling**. Anders
      overschrijft een demo het opgeslagen rapport of wordt hetzelfde rapport twee keer bewaard.
- [ ] **Alles wat het rapport toont zit in de export.** Wat niet in de opgeslagen payload staat,
      bestaat niet meer zodra het rapport wordt teruggehaald. Loop de bijlagen na: die vergeet je
      het snelst, en ze zijn juist op het eigen apparaat wél zichtbaar, dus de fout valt niet op.
- [ ] **De API-host wordt afgeleid**, bij voorkeur uit de platformpagina die het rapport toont,
      met alleen `cinab.nl` als toegestane host. Dan werkt staging en productie zonder omzetten.
      Een expliciet attribuut op de pagina mag daarvan winnen, als noodgreep per omgeving.
- [ ] De renderpagina zet **`frame-ancestors`** (`'self' https://staging2.cinab.nl https://*.cinab.nl`)
      zodat het platform haar mag inframen (spiegelt de platform-CSP `frame-src`).
- [ ] `report-page.php` doet **template-dispatch** op `template_id`.
- [ ] **Strikte output-escaping** op de publieke weergave (zie 7.1).
- [ ] Deellink-TTL via `_cinab_deel_geldig_dagen` (default 30).
- [ ] Getest: verschijnt onder "Mijn rapporten" én `/rapport/{uuid}` werkt zonder login.

---

## 7. Beveiliging van de data — B-niveau (af vóór de eerste echte deelnemer)

Onder route 2 is `/rapport-opslaan` een open bearer-endpoint: bezit van het token = autorisatie.
CORS beschermt dat **niet**. De bescherming komt uit de maatregelen hieronder.

### 7.1 Door-tokenhouder-bepaalde inhoud op publieke rapporten
- [ ] **Strikte output-escaping** in `report-page.php` op alle door de tool aangeleverde inhoud.
- [ ] **`meta`-sanitisatie** (organisatienaam, deelnemers) aan WP-zijde bij opslaan.
- [ ] **Launch-code → token-uitwisseling** (3.4) zodat tokens niet uit URL's lekken.
- [ ] **Token-TTL minimaliseren — maar weeg de poort mee.** Visiekaart's 8u is lang voor een
      bearer; kies zo kort als de sessie toelaat (`_cinab_token_geldig_uren`, 1–72), maar bedenk:
      de `betaald`-vlag, pay-resume én "later terugkomen en alsnog betalen" (§5.4) leven allemaal
      op het token. De TTL moet dus de sessie **inclusief een betaal-onderbreking** dekken.

### 7.2 Endpoint-harding (route-2 randvoorwaarden)
- [ ] **Rate-limiting** op `rapport-opslaan`, `sessie-afrekenen` en `rapport-data/laatste`,
      **per IP én per token**.
- [ ] **Payload-limiet** 1 MB → 413.
- [ ] **Origin/Referer-check** als defense-in-depth.
- [ ] **CORS-whitelist per tool-origin** (legitieme browser-calls toestaan, niet als beveiliging).

### 7.3 Token & credential
- [ ] **Token = capability** (single-use, kortlevend) — mag in de browser.
- [ ] **Credential** (AI-/API-sleutel) — **nooit** in de bundle, en ook niet in een eigen proxy van
      de tool. AI loopt via het platform: `POST /wp-json/cinab/v1/ai`. De sleutel, het model en het
      plafond staan aan platformzijde. Een tool levert geen proxybestand mee en heeft geen eigen
      sleutel nodig.

#### 7.3a AI in de tool (bindend voor elke tool die AI gebruikt)

Tot september 2026 stond hier dat de proxy op de tool-host hoorde. Dat kon niet werken: statische
hosting draait geen PHP, dus een pad als `/[tool]-ai-proxy.php` bestond daar nooit. Elke aanroep
kwam nergens aan en de tools vielen stil terug op hun eigen berekening, in één geval terwijl het
scherm meldde dat AI had geclusterd. Sinds s87 is AI een endpoint van het platform.

**De aanroep**

- [ ] **`POST /wp-json/cinab/v1/ai`, met een absolute URL.** De host wordt afgeleid uit de
      platformcontext van de sessie, met alleen `cinab.nl` als toegestane host; een expliciet
      attribuut op de pagina mag daarvan winnen. Zo werken staging en productie zonder omzetten.
      Geen host betekent geen aanroep, en dus de eerlijke terugval.
- [ ] **Body `{ token, task, lang, data }`. Het token gaat in de body, nooit als eigen header.**
      De CORS-whitelist van het platform staat alleen `Content-Type` toe; een eigen header laat de
      preflight stranden en de aanroep komt niet aan.
- [ ] Er zit **geen tool-veld** in de body. Het platform leidt de tool af uit het token, zodat een
      taak van een andere tool niet aan te roepen is.
- [ ] Antwoord `{ task, text }`. Elke niet-200 betekent voor de tool hetzelfde: terugvallen op de
      eigen berekening en dat eerlijk melden.
- [ ] **De origin waar de tool draait staat in `_cinab_origin` van die sessie.** Test je vanaf een
      ander adres dan het productiesubdomein, bijvoorbeeld de `web.app`-URL op staging, zet dan op
      díé omgeving `_cinab_origin` op dat adres. Anders blokkeert de browser de aanroep voordat er
      iets bij het platform aankomt, en zie je alleen de terugval zonder reden.

**Wat de tool nooit doet**

- [ ] Geen eigen proxybestand, geen sleutel, geen modelkeuze en geen prompt in de bundle. De prompt
      wordt server-side opgebouwd; anders is de tool een prompt-as-a-service voor wie het token heeft.
- [ ] **Taken lever je aan als specificatie, niet als code:** naam, invoercontract, prompttekst,
      uitvoercontract en een plafond per aanroep. Het platform bouwt de taak in.

**Eerlijk zijn over wat er is gebeurd**

- [ ] **AI is een overlay, nooit een afhankelijkheid.** Elke fase loopt volledig door zonder AI. Een
      fase die wacht op een antwoord dat niet komt, loopt vast bij de eerste deelnemer met een
      slechte verbinding.
- [ ] **Eén herkomstbron per AI-taak, zichtbaar in het scherm**, met vier standen: bezig, AI, lokaal
      en demo. Een lokale uitkomst wordt nooit als AI-resultaat gepresenteerd.
- [ ] Dat geldt ook voor wat eromheen staat. **Een animatie of banner die vooruitloopt op het
      antwoord is dezelfde fout in een andere vorm.** Een voortgangslijst op een vaste timer die
      afloopt voordat er antwoord is, en een melding "alle adviezen verfijnd" na één geslaagde van
      de achttien, zijn allebei onwaar.
- [ ] **Een AI-resultaat telt alleen bij een geldig contract.** Ongeldige of lege JSON is een
      terugval, geen resultaat.
- [ ] **Geen AI-aanroep zonder platformtoken, en niet in demo.**
- [ ] **De herkomst per taak gaat mee in de export van het rapport.** Zonder dat is een half
      AI-rapport achteraf niet te onderscheiden van een heel AI-rapport.

### 7.4 Tool-store / RTDB
- [ ] **Regels dicht vóór de eerste echte sessie:** anonieme aanmelding aan, en de sessie gescoped
      per code. Open regels zijn alleen goed genoeg voor testdata. Bij de drie tools die nu draaien
      staat dit aan; een nieuwe tool begint hier, niet later.
- [ ] **Regels opnieuw deployen na elke wijziging** (`firebase deploy --only database`). Een
      regelwijziging die niet gedeployd is, geeft geen foutmelding, alleen stilte.

#### 7.4a Deelnemen op een eigen apparaat (bindend voor elke tool met deelnemers)

Deelnemers doen mee op hun eigen telefoon of laptop. De facilitator ziet wie er is en wat er
binnenkomt. Onderstaande regels zijn niet vrijblijvend: elke tool die deelnemers kent, doet het zo.
Ze komen uit de visiekaart (s22) en zijn in s86 bijgesteld op wat er bij risicobeheersing misging.

**Het entreepunt**

- [ ] **Geen apart joinblad en geen hosting-rewrite.** De deelnemer komt binnen op het fasebestand
      waar hij moet meedoen, met `?join=<code>` erachter. Zo blijft de relatieve navigatie tussen
      de fasebladen werken en is er niets nodig van de hosting. Een apart `[tool]_join.html` met
      een rewrite op `/join/**` was de oude aanpak en vervalt.
- [ ] **De join-URL wordt afgeleid van `location.origin`.** Nooit een domein in de code. Twee tools
      stonden op een verzonnen domein (`visiekaart.app`, `risicobeheersing.app`) en de uitnodiging
      deed daardoor niets. Alleen als de pagina van schijf wordt geopend mag een vaste terugval
      gelden.
- [ ] Bestaat er al een `/join/`-link in omloop, vang die dan af met een **redirect** naar het
      fasebestand met `?join=`, niet met een rewrite naar een apart bestand.

**De sessiecode**

- [ ] **Eén code, één plek.** Dezelfde code staat in de link, in de QR, in wat de facilitator
      schrijft en in wat hij leest. Komt de code van het platform, dan is dat `session_code` (§3.4).
- [ ] **De code overleeft een herlaad** van het scherm waarop hij getoond wordt. Een code die bij
      elke verversing opnieuw gegenereerd wordt, betekent dat de facilitator na één keer F5 naar
      een lege sessie kijkt terwijl zijn deelnemers onder de oude code zitten.
- [ ] Wordt de code pas laat vastgelegd, bijvoorbeeld bij het starten van de sessie, let dan op dat
      elke luisteraar op het startscherm de code gebruikt die dáár getoond wordt, en niet de code
      uit een opslag die op dat moment nog leeg is.

**Eerst `meta`, dan pas verkeer**

- [ ] De facilitator legt **`sessions/<code>/meta`** aan met zijn eigen uid, in een transactie die
      alleen schrijft als `meta` nog niet bestaat, en doet dat in **elke** fase. Zonder die meta
      weigeren de regels zowel het schrijven van de stage als het lezen van de deelnemersinzendingen.
- [ ] Die weigering is **stil**. Firebase geeft geen zichtbare fout als er geen foutcallback hangt.
      Symptoom: alles lijkt te werken, er komt alleen nooit iets binnen. Zie ook valkuil 10 en 19.

**Wat waarheen wordt geschreven**

- [ ] Deelnemer schrijft **append-only**: zijn aanmelding naar `sessions/<code>/participants`
      (naam verplicht, e-mail optioneel) en zijn inzendingen naar `sessions/<code>/phaseN/answers`.
      Alleen de facilitator leest die paden.
- [ ] Elk pad dat gebruikt wordt staat **expliciet** in `database.rules.json`. Een ontbrekend pad
      levert dezelfde stille weigering op.
- [ ] Vangnetregels krijgen lengtegrenzen. Een regel die alleen controleert of er een veld `at` in
      zit, laat willekeurig grote objecten toe.

```json
"sessions": {
  "$code": {
    "meta": {
      ".read":  "auth != null",
      ".write": "auth != null && (!data.exists() || data.child('facilitatorUid').val() === auth.uid)",
      ".validate": "newData.hasChildren(['createdAt','facilitatorUid']) && newData.child('facilitatorUid').val() === auth.uid"
    },
    "participants": {
      ".read": "auth != null && root.child('sessions').child($code).child('meta/facilitatorUid').val() === auth.uid",
      "$pushId": {
        ".write": "auth != null && !data.exists()",
        ".validate": "newData.hasChildren(['name','at']) && newData.child('name').isString() && newData.child('name').val().length <= 120 && (!newData.hasChild('email') || (newData.child('email').isString() && newData.child('email').val().length <= 254))"
      }
    }
  }
}
```

Dit blok is illustratie van de vorm, geen bestand om over te nemen. De paden en veldnamen van jouw
tool horen erin te staan, met dezelfde drie eigenschappen: append-only schrijven, lezen alleen door
de facilitator, en lengtegrenzen op alles wat een deelnemer stuurt.

**Tijdens de sessie**

- [ ] **De deelnemer komt niet langs de betaalpoort.** Die hoort bij de facilitator, niet bij
      iedereen die meedoet.
- [ ] **De deelnemerslijst wordt bijgehouden zolang de sessie loopt**, niet één keer weggeschreven
      bij de start. Anders telt niemand mee die later binnenkomt en staat `meta.deelnemers` in het
      rapport op nul.
- [ ] **De context reist mee.** Wat de deelnemer nodig heeft om de vraag te begrijpen, dus de
      stellingen, het onderwerp en de sessiegegevens, gaat mee met de fase die de facilitator
      publiceert. Anders ziet hij wel de juiste fase, maar niet waar het over gaat.
- [ ] Schakelt de facilitator naar een volgende fase, dan **navigeert het deelnemerapparaat mee**,
      met de join-parameter erbij.
- [ ] **Geen `window.alert` en geen `window.confirm`.** Ze blokkeren de pagina, tonen de domeinnaam
      van de tool, zijn niet te stijlen en zijn stil in een sandboxed iframe. Gebruik het eigen
      meldvenster van de tool.

**AVG**

- [ ] **E-mailadres is optioneel** en blijft tool-zijdige sessiedata, niet in de platform-wrapper
      (§7.7). Eigen bewaartermijn vastleggen; wissen bij `session/clear`.
- [ ] **Naam verplicht**, met een lengtegrens; e-mail, indien aanwezig, eveneens begrensd.

**Bewijs**

- [ ] Pas na een **echte test met twee apparaten** is de deelname bewezen: deelnemer meldt zich aan
      op apparaat B, facilitator ziet hem live verschijnen op apparaat A, de inzending komt binnen,
      en bij het wisselen van fase gaat apparaat B mee. Zie §8.

### 7.7 AVG / data-residency (verplicht — er komt persoonsdata in)
- [ ] **EU-regio binnen Firebase:** nieuw **productieproject** met RTDB in **`europe-west1`**
      (de RTDB-regio ligt vast bij aanmaken en kan niet verhuizen). Het huidige project
      `visiekaart` wordt de staging-omgeving. Geen verhuizing weg van Firebase nodig.
- [ ] **Persoonsdata gesplitst.** In de **platform-wrapper** (`meta`): alleen deelnemersnámen,
      facilitator en organisatienaam — **geen e-mailadressen** (de verloopmail bij naderend
      token-verloop verstuurt WordPress zelf via het gebruikersaccount). Heeft de **join-flow**
      e-mail nodig, dan is dat tool-zijdige sessiedata in RTDB: eigen bewaartermijn vastleggen
      en wissen bij `session/clear` (stateless-at-rest).
- [ ] Per tool: welke persoonsdata, bewaartermijn (soft-delete 30d?), toestemming. Hard-delete
      cron werkt.
- [ ] Bij vergelijken: documenteer dat de "laatste meting" persoonsgebonden is (account), wie wat mag
      inzien, en de bewaartermijn van vorige metingen.

---

## 8. Testen

### Op de tool-host
- [ ] `cinab-tool-client.js` ingesloten; launch-code → token werkt; preview-modus (`?preview=1`).
- [ ] Voltooiing → wrapper wordt rechtstreeks ge-POST; daarna `session/clear`.
- [ ] **Deelname met twee apparaten (§7.4a):** facilitator start de sessie op apparaat A en laat
      dat scherm staan; deelnemer opent de join-URL op apparaat B, vult zijn naam in en ziet de
      juiste vraag; de naam verschijnt **live** in de wachtkamer op A; de inzending komt binnen bij
      A; de facilitator schakelt door en B gaat mee. Werkt dit niet, loop dan in deze volgorde na:
      (1) bestaat `sessions/<code>/meta` met de uid van de facilitator, (2) gebruiken beide kanten
      dezelfde code, (3) staan alle gebruikte paden in de RTDB-regels, (4) zijn die regels opnieuw
      gedeployd (`firebase deploy --only database`). Niets zien zonder foutmelding is bijna altijd
      een stille weigering, niet een bug in de tool.
- [ ] **AI (§7.3a):** een taak in een echte sessie geeft een AI-resultaat, met de herkomstmelding
      erbij. Zet daarna `_cinab_ai_aan` uit en herhaal: de tool loopt gewoon door, de melding zegt
      lokaal, en nergens op het scherm staat of beweegt iets dat AI suggereert. Controleer ook het
      opgeslagen rapport: de herkomst per taak staat erin.
- [ ] **Herlaad het startscherm** nadat de uitnodiging is gedeeld: de code moet dezelfde blijven.
- [ ] **Aantal deelnemers:** iemand die pas ná de start binnenkomt telt mee in het rapport.
- [ ] **Rapport terughalen:** open het opgeslagen rapport vanuit de werkruimte, in een **andere**
      browser dan die van de facilitator. Alles wat de facilitator zag hoort er te staan,
      bijlagen incluis, en er mag geen tweede rapport bijkomen.

### Koppeling
- [ ] `rapport-opslaan` via de **browserconsole** → testrapport in dashboard. (Curl/PowerShell
      wordt op de staging-API geblokkeerd door SiteGround's botbescherming.) Verlopen/2e
      token → 409.
- [ ] **XSS-test**: `meta.organisatie` met `<script>` → ge-escaped renderen, niet uitvoeren.

### Vergelijken (alleen bij vlag aan; voor Visiekaart: testen dat het uit staat)
- [ ] `rapport-data/laatste` geeft alleen het **eigen** laatste rapport (probeer een vreemd account
      → mag niets teruggeven).
- [ ] "Laatste" wordt bij start gepind; een tussentijds nieuw rapport verschuift de keten niet.
- [ ] Schema-mismatch (oud rapport, nieuwere dimensies) → nette degradatie.

### Betaalpoort
- [ ] Poort op `_cinab_betaal_vanaf_fase`; gratis fases ervóór tonen geen betaalde inhoud.
- [ ] Voldoende → verder → atomische aftrek → door. Race: saldo tussentijds weg → 402 → koop-tak.
- [ ] Onvoldoende → kopen → Mollie (test-mode) → terug → idempotente retry → door.
- [ ] Niet kopen → stopt; later terugkomen → state hervat, alsnog betalen, door.
- [ ] Server-side gate: betaalde fase direct opvragen zonder `betaald=true` → 402.

### Integratie
- [ ] Pay-resume end-to-end; rate-limit getriggerd → nette afhandeling; multi-user, mobiel,
      netwerk-weg, trage webhook.

---

## 9. Deploy & go-live checklist

**Datacontract** — wrapper + dimensienamen + scores-mapping vastgelegd; render-template op `template_id`.

**Koppeling (route 2)** — `cinab-tool-client.js` POST met token; launch-code-uitwisseling;
validate non-consuming; `rapport-opslaan` getest.

**Vergelijken** — vlag per tool gezet (Visiekaart: false); leescontract vastgelegd; (indien aan)
leesendpoint account-gescoped + stabiliteitsregel.

**Betaalmuur** — geen precheck; `_cinab_betaal_vanaf_fase` gezet; advisory check + atomische,
idempotente aftrek; `betaald`-vlag + server-side gate op betaalde fases; pay-resume end-to-end;
Mollie live.

**Deelname op een eigen apparaat (§7.4a)** — entreepunt op het fasebestand met `?join=`, link uit
`location.origin`; één sessiecode die een herlaad overleeft; `meta` vóór het eerste verkeer; alle
gebruikte paden in de regels met lengtegrenzen; deelnemer niet langs de betaalpoort;
deelnemerslijst bijgehouden tijdens de sessie; getest met twee echte apparaten.

**Rapport terughalen (§6)** — renderroute op `?rapport_id=`; `_cinab_render_url_pattern` ingevuld;
in render-modus niets opslaan en geen demovulling; alles wat het rapport toont zit in de export;
getest in een andere browser dan die van de facilitator.

**AI (§7.3a)** — absolute URL naar `/wp-json/cinab/v1/ai`, token in de body, geen eigen headers;
`_cinab_origin` klopt met de origin waar de tool werkelijk draait; `_cinab_ai_aan`, `_cinab_ai_set`
en `_cinab_ai_plafond` gezet; elke fase loopt door zonder AI; herkomstmelding in vier standen en de
herkomst mee in de export.

**Levering compleet** — geen voorbeeldbestanden; elk pad in `firebase.json` en in de bladen bestaat
echt; fonts en bibliotheken zelf gehost, geen externe CDN.

**Beveiliging (B-niveau af, tool-zijde)** — geen credentials in de bundle, AI-sleutel achter een
server-side proxy; RTDB-regels dicht en gedeployd; korte token-TTL; `frame-ancestors` op de
renderpagina; `_cinab_origin` op het eigen subdomein; AVG-plan per tool (§7.7).

**Deploy** — nooit rechtstreeks op de host bewerken. Git, commit, dan deployen. Geen
`firebase deploy` zonder commit; de commitmessage is de changelog-regel.

---

## 10. Veelgemaakte valkuilen

1. **CORS verwarren met beveiliging.** Bescherming komt uit escaping, sanitisatie, rate-limiting,
   korte token-TTL — niet uit CORS.
2. **Token vs. credential door elkaar.** Token mag in de browser; een AI-sleutel nooit.
3. **Token in URL/historie.** Gebruik launch-code-uitwisseling.
4. **Geen output-escaping op `/rapport/{uuid}`.**
5. **Iframe-redirect** in de pay-flow: `window.top.location`, niet `window.location`.
6. **`NOW()`-bug:** reken "nu" in PHP/UTC uit.
7. **validate-token verbruikt het token** → refresh/hervat/pay-resume breekt. Non-consuming maken.
8. **Schema te streng aan WP-kant** (ADR 0004 — alleen de wrapper licht valideren; `data` opaak).
9. **CSP breekt iframes** — eerst op staging testen.
10. **Open RTDB-regels** vergeten dicht te zetten vóór echte klantdata. En het omgekeerde: een
    **ontbrekend pad in de regels** geeft géén foutmelding — writes worden stilletjes geweigerd.
    Symptoom: de schrijvende kant ziet geen fout, de lezende kant ziet niets. Altijd de
    RTDB-regels deployen ná elke wijziging (`firebase deploy --only database`) en cross-device
    end-to-end testen.
11. **(v3) Precheck als poort.** "Saldo voldoende?" is advisory; de bindende stap is de **atomische,
    idempotente** aftrek. Nooit checken-en-later-aftrekken.
12. **(v3) Betaalde inhoud tonen vóór `betaald=true`.** Dan geef je de deliverable gratis weg.
13. **(v3) Client-side gate vertrouwen.** De fase-poort moet **server-side** worden afgedwongen.
14. **(v3) Leesendpoint dat een willekeurig `rapport_id` accepteert.** Account-scopen, anders IDOR.
15. **(v3) Dimensies/mapping wijzigen bij een vergelijk-tool** zonder `schema_version`-ophoging →
    delta wordt onzin.
16. **(v3) Vergelijken per organisatie verwachten** terwijl de eigenaar het **account** is.
17. **(v3.5) Een voorbeeld als specificatie lezen.** De codeblokken en bestandsnamen in dit werkboek
    laten zien hoe iets eruit kán zien. Bindend is alleen wat op een afvinkregel staat. Een tool
    naar het voorbeeld van de vorige tool bouwen levert bestanden op die niemand nodig heeft, en
    een configuratie die naar bestanden wijst die er niet zijn.
18. **(v3.5) Configuratie die verwijst naar iets wat niet bestaat.** Een rewrite naar een joinblad
    dat niet is meegeleverd, een proxy-pad op een host zonder PHP, een lettertype dat nergens staat.
    Controleer bij elke levering dat elk pad in `firebase.json` en in de bladen ook echt bestaat.
19. **(v3.5) `meta` ontbreekt bij de start van een sessie.** Dezelfde stille weigering als valkuil
    10, maar dan een niveau hoger: zonder `meta/facilitatorUid` mag de facilitator zijn eigen
    sessie niet lezen of beschrijven. Leg meta aan vóór het eerste verkeer, in elke fase.
20. **(v3.5) Een neutrale terugvalwaarde in `scores`.** Een dimensie zonder meting invullen met een
    middenwaarde is niet te onderscheiden van een echte uitslag en telt in de werkruimte mee alsof
    er gemeten is. Laat zo'n dimensie weg uit `scores` in plaats van hem te vullen.
21. **(v3.5) Een eigen sessiecode verzinnen** terwijl het platform er een meegeeft. De herstart van
    een meerdaagse sessie wijst dan naar een sessie die niet bestaat (§3.4).
22. **(v3.6) Een server-side stuk op een statische host zetten.** De AI-proxy stond hier jarenlang
    voorgeschreven op de tool-host. Firebase Hosting draait geen PHP, dus die aanroep kwam nooit
    ergens aan. Symptoom: alles werkt, AI doet alleen nooit iets, en in het ergste geval meldt het
    scherm wel dat AI het gedaan heeft.
23. **(v3.6) Een eigen header meesturen naar het platform.** De CORS-whitelist staat alleen
    `Content-Type` toe. Een header als `X-CINAB-Token` laat de preflight stranden en de aanroep
    komt niet aan. Het token hoort in de body.

---

## Appendix A — Endpoints (REST-contract, route 2)

| Endpoint | Methode | Auth | Doel |
|---|---|---|---|
| `/cinab/v1/start-tool` | POST | **launch-code** | wisselt launch-code in voor token, zonder credit-precheck; response `{ token, betaal_vanaf_fase, credits, session_code }`. **`session_code` is de sessiecode van de tool** (§3.4) |
| `/cinab/v1/herstart-sessie` | POST | **token** | hervat een lopende, meerdaagse sessie; geeft de bewaarde `session_code` terug waarmee de tool opnieuw start (`?session=<code>`) |
| `/cinab/v1/stuur-uitnodigingen` | POST | **token** (non-consuming) | verstuurt uitnodigingen aan beoordelaars; body `{ token, raters, meta? }`; één ronde per sessietoken, maximaal 50 adressen. Het platform **bewaart de adressen niet**, ze blijven tool-zijdige sessiedata (§7.7) |
| `/cinab/v1/validate-token` | POST | token | token checken, **non-consuming** |
| `/cinab/v1/ai` | POST | **token** (non-consuming) | AI-taak uitvoeren; body `{ token, task, lang, data }`, antwoord `{ task, text }`. De prompt wordt **server-side** opgebouwd en de tool volgt uit het token, dus er zit geen tool-veld in de body. Token in de **body**, geen eigen header. 403 als AI uit staat of de taak niet bij deze tool hoort, 429 bij het sessieplafond, 502 als het model niet antwoordt, 503 als het platform geen sleutel of model heeft (§7.3a) |
| `/cinab/v1/saldo` | GET · **POST** | **token** (vanuit de tool) | saldo tonen (advisory check op de poort). **Tools: POST met `{ token }` in de body** (token niet in URL/historie/logs, ADR 0006). GET is voor ingelogde portaal-gebruikers |
| `/cinab/v1/sessie-afrekenen` | POST | **token** | atomisch + idempotent afschrijven; zet `betaald`; 402 bij te weinig |
| `/cinab/v1/rapport-data/laatste` | GET | **token** | *(vergelijken — contract-only, nog niet gebouwd)* laatste eigen rapport voor `template_id`; account-gescoped; non-consuming |
| `/cinab/v1/rapport-data/{rapport_id}` | GET | publiek (TTL) | *(render — gebouwd s22)* opgeslagen wrapper voor de render-route van de tool: `template_id`, `schema_version`, `meta`, `scores`, `data` (opaak), `aangemaakt`. Tekent uit de **opgeslagen** data (stateless-at-rest), niet de live sessie. Zelfde toegangspoort als `/rapport/{uuid}`; telt de view-teller niet op; CORS via `_cinab_origin` |
| `/cinab/v1/rapport-opslaan` | POST | **token** | wrapper opslaan; controleert `betaald`; 402 bij te weinig credits |
| `/cinab/v1/rapport/{id}` | **PATCH** | token | multi-step bijwerken (mits dezelfde gebruiker). **Let op: PATCH-only** — er bestaat **geen** `GET /rapport/{id}`; voor render-data gebruik je `GET /rapport-data/{rapport_id}` (hierboven) |
| `/cinab/v1/credits-applied/{order_id}` | GET | — | Thank-You polling |
| `/rapport/{uuid}` | GET | publiek (TTL) | rapport-renderpagina (strikt ge-escaped) |

Statuscodes: 200 · 401 auth · 402 te weinig credits / niet betaald (+`payment_url`) · 409 token
verlopen, ongeldig of al gebruikt (**was 419** — WordPress laat onbekende statuscodes stilletjes
vallen) · 413 payload te groot · 422 validatiefout · 429 rate-limited.

> Status: het volledige contract hierboven (m.u.v. `rapport-data/laatste`) is gebouwd én
> end-to-end bewezen op staging2.cinab.nl (plugin 1.5.1), inclusief de Mollie-betaalflow met
> 402-lus en `action=resume`.

## Appendix B — Omgevingsvariabelen

**Statische tool (route 2, regel):** geen server-side secrets. Token komt uit de launch-URL.
**Nooit in de browser-bundle:** AI-sleutels (Anthropic). AI loopt via `POST /wp-json/cinab/v1/ai`;
sleutel, model en plafond staan aan platformzijde (§7.3a).
**Alleen backend-tools (optioneel):** `CINAB_WP_URL`, `CINAB_API_KEY`, `CINAB_SIGNING_SECRET`.

## Appendix C — WordPress meta-velden per tool

| Veld | Waarde |
|---|---|
| `_cinab_credits` | _____ |
| `_cinab_duur` (min) | _____ |
| `_cinab_embed_url` | _____ |
| `_cinab_origin` (CORS) | `https://[naam].cinab.nl` — het eigen subdomein, niet het `web.app`-adres van Firebase (leeg = CORS-blokkade) |
| `_cinab_is_vergelijkbaar` | true/false |
| `_cinab_betaal_vanaf_fase` | _____ (leeg = gratis tool, ADR 0007) |
| `_cinab_vraagt_deelnemers` | true/false (anders 422) |
| `_cinab_deel_geldig_dagen` | 30 |
| `_cinab_render_url_pattern` | `https://[naam].cinab.nl/[tool]_rapport.html?rapport_id={rapport_id}` (statische hosting; leeg = geen renderroute, en dan toont het platform het rapport niet) |
| `_cinab_token_geldig_uren` | 1–72 — zo kort als de sessie toelaat |
| `_cinab_ai_aan` | true/false — AI toestaan voor deze sessie. **Standaard uit** |
| `_cinab_ai_set` | takenset, bijvoorbeeld `visiekaart` of `risicobeheersing` (leeg = geen taken) |
| `_cinab_ai_plafond` | maximaal aantal geslaagde AI-aanroepen per sessie (leeg = 40, 0 = geen plafond) |
| `_cinab_rapport_schema` | optioneel (alleen tool-zijdige validatie) |

Subdomein: `[naam].cinab.nl`. Zie `SUBDOMAIN-NAMING.md` voor de naamgeving en de DNS-stappen; het
subdomein benoemt de app, niet het product.

> **Let op:** `_cinab_is_vergelijkbaar` en `_cinab_vraagt_deelnemers` staan wel in het
> eisendocument maar bestaan **niet** in het beheerscherm. Reken er niet op bij het bouwen.

## Appendix D — Stand van zaken per tool

Dit was een visiekaart-dossier. Dat werkte averechts: het werd overgenomen als sjabloon, inclusief
de join-aanpak die inmiddels vervalt. Wat tool-specifiek is hoort in het **toolpaspoort** van die
tool, niet hier. Deze appendix houdt alleen bij waar elke tool staat.

| Tool | Firebase-project (regio) | Host | Deelname eigen apparaat | Renderroute rapport |
|---|---|---|---|---|
| Visiekaart (ook Jaarplankaart en Projectkaart, via `?doel=`) | `visiekaart` (europe-west1) | visiekaart.cinab.nl | ja, `/join/:code` redirect naar fase 0 met `?join=` | ja |
| Vaardigheidsmeter Leidinggeven | `vaardigheidsmeter-leidin-f82f7` (europe-west1) | vaardigheidsmeter-leidinggeven.cinab.nl | ja | ja |
| Risicobeheersing | `risicobeheersing-e174f` (europe-west1) | risicobeheersing.cinab.nl | ja, fase 1 met `?join=` (gebouwd s86) | ja (gebouwd s86) |

Bij alle drie staat anonieme aanmelding aan en worden de databaseregels meegedeployd.

## Appendix E — Datacontract-invulblad (kopieer per tool)
```
Tool:                 __________________
template_id:          __________________
schema_version:       1.0
Dimensies (scores):   __________________ (kleine letters, underscores, 0-100)
Mapping interne schaal → scores: __________________ (bevriezen!)
Vergelijkbaar?:       ja / nee  → _cinab_is_vergelijkbaar; eigenaar = ACCOUNT; altijd laatste
Betaal vanaf fase:    ____ (leeg = gratis tool, ADR 0007)   Credits/sessie: ____
Token-TTL (uur):      ____ (kort)   Deellink-TTL (dgn): 30
Backend?:             ja / nee
Persoonsdata:         __________________   Bewaartermijn: __________________
Credentials server-side?: ja  (AI-sleutel mag NIET in de bundle)
AI gebruiken?:        ja / nee  -> _cinab_ai_aan; takenset: __________  plafond/sessie: ____
  Taken:              __________________ (naam, invoer, prompttekst, uitvoer, max_tokens)
  Terugval per taak:  __________________ (wat de tool doet zonder AI)
  Herkomst in export? ja

Deelnemers op eigen apparaat?: ja / nee
  Entreepunt:         [tool]_faseN.html?join=<code>, link uit location.origin
  Sessiecode:         van het platform (session_code) / eigen, alleen als terugval
  RTDB-paden:         meta, participants, phaseN/answers, ...
  Meta vóór verkeer:  ja
  Deelnemer langs de betaalpoort?: nee
Renderroute rapport:  [tool]_rapport.html?rapport_id={rapport_id}
  Alles in de export? __________________ (bijlagen nagelopen)
```

---
*Referenties: ADR 0004 (datacontract), ADR 0005 (full-screen start), ADR 0006 (transport:
browser-POST met token-auth), ADR 0007 (betaalpoort per tool-fase). Deze uitgave is afgeleid van
het interne CINAB-werkboek versie 3.5; bij tegenspraak is dat document leidend. Vragen of een
wijzigingsvoorstel: leg ze voor aan CINAB voordat je ervan afwijkt in je bron.*
