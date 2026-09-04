# Visiekaart

| | |
|---|---|
| Firebase-project | `visiekaart`, database in `europe-west1`; staging en productie gebruiken hetzelfde project |
| Subdomein | `visiekaart.cinab.nl`, live, CNAME naar `visiekaart.web.app` |
| Regels deployt | Rik, vanuit deze map |
| Anonymous sign-in | aan op staging; bij het productieproject direct aanzetten (Authentication, Sign-in method) |
| Deelnemerslink | `visiekaart_fase0.html?join=<code>`; `/join/<code>` blijft werken via een 302-redirect |
| Tool-client | `public/cinab-tool-client.js`, versie in de header |
| Bladen | versie 13 (pakket 3 september 2026, na het testprotocol van de tooldeveloper) |

## Varianten via `?doel=`

Eén app, meerdere producten in de etalage. Elke `cinab_tool`-post krijgt een eigen embed-URL:

| Variant | Embed-URL |
|---|---|
| Visiekaart | `…/visiekaart_fase0.html?doel=strategisch` |
| Jaarplankaart | `…/visiekaart_fase0.html?doel=jaarplan` |
| Projectkaart | `…/visiekaart_fase0.html?doel=project` |
| Vrije variant | `…/visiekaart_fase0.html?doel=anders` |

De tool accepteert ook `?sessietype=` en kent aliassen (`visiekaart`, `strategie`, `strategic`,
`jaarplankaart`, `annualplan`, `projectkaart`, `overig`, `other`). Een onbekende waarde doet niets.
Bij een herstart via `?action=` wint de opgeslagen sessie-state boven de parameter, bij een verse
start wint de parameter. De keuze blijft in de tool wijzigbaar; dit is voorinvulling, geen slot.

## Wat de variant precies verandert

Getest op 3 september 2026: `?doel=` vinkt in fase 0 het sessietype aan en roept `toggleCard()`
aan, waarmee de kaartstijl, de naam en het voorbeeld meteen meelopen. De facilitator ziet dus
geen openstaande vraag meer maar een ingevulde keuze, die hij kan wijzigen.

Wat er per variant wisselt, in alle zeven bladen:

1. De naam in paginatitels, koppen en het rapport.
2. Het voorbeeld in het naamveld van de sessie.
3. Het woord achter `{type}` in lopende tekst: strategisch plan, jaarplan of project.
4. Het zinsframe van de stip op de horizon in fase 1. Dit is het inhoudelijke verschil:

| Slot | strategisch | jaarplan | project |
|---|---|---|---|
| 2 | richten wij ons op | richten wij ons dit jaar op | starten wij dit project voor |
| 4 | Wij willen bereiken dat | Aan het eind van dit jaar hebben wij bereikt dat | Bij oplevering hebben wij bereikt dat |
| 5 | Daarom ligt onze focus de komende periode op | Daarom ligt onze focus dit jaar op | Daarom ligt onze focus voor dit project op |

Slot 1 en 3 zijn bewust identiek, en slot 4 houdt overal de constructie "dat plus bijzin" aan,
zodat de AI-voorstelgenerator en bestaande antwoordpatronen blijven werken.

Het type stuurt daarnaast de tijdsplanning en prioritering in de roadmap van fase 5.

Niet variantafhankelijk: de opmaak, de kleuren, het rapportsjabloon, en de aanvullende context
in fase 0 (tijdshorizon, schaalniveau, urgentie, budget). Die vult de facilitator zelf.

## Meerdere sessies, één tool: wat gelijk moet blijven

Elke variant is een eigen `cinab_tool`-post, dus een eigen product in de etalage met een eigen
naam, pagina en teksten. De motor is dezelfde en `template_id` blijft `visiekaart`, dus het
rapport is voor alle varianten gelijk.

Deze velden moeten in alle posts dezelfde waarde houden. Wijzig je er één, werk de andere
meteen bij:

| Veld | Waarom |
|---|---|
| `_cinab_credits` | dezelfde sessie mag niet op de ene pagina meer kosten dan op de andere |
| `_cinab_duur` | zelfde sessie, zelfde duur |
| `_cinab_origin` | `https://visiekaart.cinab.nl`, voor alle varianten |
| `_cinab_betaal_vanaf_fase` | de poort ligt op dezelfde plek in de flow |
| `_cinab_token_geldig_uren` | idem |
| `_cinab_deel_geldig` | idem |
| `_cinab_render_url_pattern` | idem |
| Rapport-template | idem, want `template_id` is gelijk |

Alleen de Start-URL verschilt, in de `?doel=`. En de etalageteksten natuurlijk.

De variant `anders` krijgt bewust geen eigen post: die heeft geen eigen situatie en geen eigen
zinsframe en valt terug op het strategische. Hij blijft binnen de tool bestaan als keuze voor
de facilitator.

## Deployen

```powershell
cd C:\Users\rikva\Projecten\cinab-tools\visiekaart
git status
firebase use staging
firebase deploy --only hosting,database
```

Alleen hosting als de regels niet wijzigen: `firebase deploy --only hosting`.
Geen deploy zonder commit; de commitmessage is de changelog-regel.

## AI loopt sinds s87 via het platform

`VK_AI_ENDPOINT` stond op `/vk-ai-proxy.php`, relatief aan de tool-host. Die host is Firebase
Hosting en draait geen PHP, dus die call kwam nergens aan. Op 3 september is vastgesteld dat er
ook nergens anders een `vk-ai-proxy.php` draaide, niet op `cinab.nl` en niet op `staging2.cinab.nl`.
De AI in deze tool heeft dus nooit gewerkt; tot versie 13 meldde fase 1 wel altijd dat AI had
geclusterd. Sinds versie 13 zegt de tool eerlijk "AI niet bereikbaar, voorlopige lokale
clustering" en werkt de rest gewoon.

Sinds s87 is er wel een werkend endpoint, en niet als los PHP-bestand maar in de plugin:
`POST https://cinab.nl/wp-json/cinab/v1/ai`. De vier AI-bladen (fase 1, 2, 3 en 5) leiden die host
af uit de platformcontext van de sessie, dus er valt aan tool-zijde niets meer om te zetten tussen
staging en productie.

Wat er nog moet gebeuren om AI hier daadwerkelijk aan te zetten, gebeurt allemaal op het platform:

1. `CINAB_AI_KEY` en `CINAB_AI_MODEL` in `wp-config.php`. Dit moet een CINAB-sleutel zijn, niet die
   van de tooldeveloper.
2. Bij de sessie in WordPress het blok **AI**: vinkje aan, takenset `visiekaart`, plafond per sessie.
3. Controleren op `/beheer/ai/` of de aanroepen binnenkomen en hoeveel er op terugval eindigen.

De taken die deze tool mag aanroepen zijn `cluster` (fase 1, 2 en 3) en `roadmap` (fase 5). De
prompts staan server-side in de plugin, onder `includes/ai/taken-visiekaart.php`.

## Wijzigingen van CINAB in de aanlevering van de tooldeveloper

Bij een volgende set moeten deze opnieuw, anders komen ze er zo weer uit.

1. `visiekaart_fase0.html`: de QR-generator laadt uit `vendor/qrcode.min.js` in plaats van uit
   `cdnjs.cloudflare.com`. Zelfde bibliotheek, zelfde versie 1.0.0.
2. `firebase.json`: de rewrite naar `visiekaart_join.html` is vervangen door een 302-redirect naar
   `visiekaart_fase0.html?join=:code`, conform B-01 en het advies in zijn eigen README-DEPLOY.

## Open punten

1. Drie of vier `cinab_tool`-posts aanmaken met de embed-URL's uit de varianttabel hierboven.
2. Vóór productie: `data-cinab-api` op de html-tag van `visiekaart_rapport.html` zetten. Nu
   staat er alleen `<html lang="nl">` en valt de rapportpagina terug op `staging2.cinab.nl`.
   Op staging klopt dat toevallig, op productie zoekt hij het rapport dan op de verkeerde host
   en toont een deellink niets. Het wordt `<html lang="nl" data-cinab-api="https://cinab.nl">`.
   Nadeel: er is één gedeployde kopie, dus daarna kun je de deellink niet meer op staging testen.
   Voorstel aan de tooldeveloper: laat de pagina de host ook uit een queryparameter accepteren,
   dan bedient één deploy beide omgevingen.
3. Beslissen wat er met de vermeldingen van adviesborden.nl in het rapport gebeurt.
4. `?demo=1` ontbreekt, terwijl risicobeheersing dat wel heeft.
5. 42 visuele metingen uit het testrapport staan nog open, vooral knopkleuren en tabellen die
   binnen een kader scrollen.

## Over het Firebase-project

Op 3 september 2026 nagekeken in de console: de database van het project `visiekaart` staat in
`europe-west1`. In deze README stond eerder dat het project in de VS draaide en daarom alleen
staging kon zijn. Dat klopte niet. De EU-eis uit HS-11 is dus al voldaan en er is geen apart
productieproject nodig; `VK_FB_PROD` wijst nu naar hetzelfde project als `VK_FB_STAGING`,
net als bij de vaardigheidsmeter en risicobeheersing.

Gevolg: staging en productie delen één database. Wil je ze later echt scheiden, maak dan een
tweede project aan in `europe-west1` en vervang alleen het `VK_FB_PROD`-blok. Dat blok staat in
alle zeven bladen en moet daar byte-identiek blijven.
