# Vaardigheidsmeter Leidinggeven

| | |
|---|---|
| Firebase-project | `vaardigheidsmeter-leidin-f82f7`, database in `europe-west1` |
| Staging en productie | zelfde project; de aliassen in `.firebaserc` wijzen allebei hierheen |
| Subdomein | `vaardigheidsmeter-leidinggeven.cinab.nl`, live, CNAME naar `vaardigheidsmeter-leidin-f82f7.web.app` |
| Regels deployt | Rik, vanuit deze map |
| Anonymous sign-in | aan |
| Deelnemerslink | `/join/<code>` via de hosting-rewrite naar `vaardigheidsmeter_join.html` |
| Tool-client | `public/cinab-tool-client.js`, versie in de header |
| Bladen | versie 0.5 (pakket 3 september 2026, na het testprotocol van de tooldeveloper) |
| Taal | alleen Nederlands; Engels ontbreekt (beslispunt D-1) |

## Deployen

```powershell
cd C:\Users\rikva\Projecten\cinab-tools\vaardigheidsmeter-leidinggeven
git status
firebase deploy --only hosting,database
```

Alleen hosting als de regels niet wijzigen: `firebase deploy --only hosting`.
Geen deploy zonder commit; de commitmessage is de changelog-regel.

## Wijzigingen van CINAB in de aanlevering van de tooldeveloper

Bij een volgende set moeten deze opnieuw, anders komen ze er zo weer uit.

1. **F2-21 hersteld, en dit is de belangrijkste.** In v0.5 stond bij een verse start
   `code=genCode();`. Dat is teruggezet naar `code = client.sessionCode || genCode();`.
   Het platform bewaart de `session_code` bij het token en hervat een lopende sessie via
   `POST /cinab/v1/herstart-sessie` met precies die code, en start de tool opnieuw met
   `?session=<code>`. Verzint de tool zijn eigen code, dan wijst die herstart naar een sessie
   die in Firebase nooit onder die naam is aangemaakt en belandt de facilitator in een lege
   sessie. Gebouwd en op staging bewezen in sessie 35 en 36.
2. **Zelfgehoste fonts toegevoegd.** De CDN-verwijzing is in v0.5 terecht verdwenen, maar er
   kwam niets voor in de plaats, dus de tool draaide op systeemletters. Nu staat er
   `public/fonts/fonts.css` met vier woff2-bestanden, en een `<link>` in de head van beide
   bladen. Dezelfde vier bestanden als bij risicobeheersing.
3. **CSP in `firebase.json`.** De aanlevering dekte alleen het toolblad en miste het kale
   `cinab.nl`. Beide bladen worden in een iframe geladen, dus beide staan er nu in.

## Databaseregels

Versie 2.0.0, overgenomen uit de aanlevering v0.5 en strakker dan de vorige set: de ongebruikte
tak `raters` is eruit en een vangnet `$other` weigert alles wat niet expliciet is toegestaan.
Vooraf nagelopen welke paden de app echt gebruikt: `meta`, `content`, `state` en `answers`.
De beoordelaars staan niet in de database; die lijst gaat rechtstreeks naar het platform.

## Uitnodigingen

Het endpoint bestaat en draait op staging:

```
POST /wp-json/cinab/v1/stuur-uitnodigingen
  token   string  verplicht
  raters  array   verplicht
  meta    object  optioneel
```

Sinds plugin 1.11.0. Tokenvalidatie zit in de handler en is non-consuming. Eén uitnodigingsronde
per sessietoken, maximaal 50 beoordelaars. Het platform slaat de e-mailadressen niet op: die
worden alleen gebruikt om te versturen en leven verder in de RTDB van de tool, met de
bewaartermijn van de tool.

In het testrapport staat dit endpoint als ontbrekend en als blokker voor de betaalde route.
Dat klopt niet; het stond alleen niet in het werkboek dat de tooldeveloper had.

## Open punten

1. Volledige testronde op staging: starten via de etalage, betaalpoort, uitnodigingen versturen,
   drie beoordelaars op eigen apparaat, rapport opslaan en openen, en het hervatten van een
   lopende sessie vanuit `/account/`.
2. D-1: de app is alleen Nederlands. De standaard vraagt ook Engels; dat is ongeveer 120 strings
   plus de beschouwingszinnen. Beslissing van Rik.
3. D-2: er is geen ingevuld APP-START. De tooldeveloper heeft de waarden uit de code afgeleid en
   in zijn testkaart gezet; die moeten bevestigd worden. Het ontbreken hiervan is de directe
   oorzaak van punt 1 hierboven onder "wijzigingen van CINAB".
