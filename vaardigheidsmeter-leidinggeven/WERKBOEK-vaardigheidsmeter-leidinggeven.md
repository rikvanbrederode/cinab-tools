# WERKBOEK — Vaardigheidsmeter Leidinggeven

Bouwlog van de app. Bij elke iteratie komt er een versieregel bij. Geef dit bestand samen met de nieuwste app-versie en het PLATFORM-WERKBOEK door bij elke ronde.

---

## Versiehistorie

| Versie | Datum | Wat is gebeurd / gewijzigd |
|---|---|---|
| v0.1 | 2026-06-18 | Verplichte eerste stap: `APP-START` ingevuld. Werkboek + platform-werkboek opgezet. Codeblok 1: standalone gratis variant — CINAB-thema ingebed, keuzescherm (perspectief + variant), volledige vragenlijst (20×2, 5-punts + n.v.t.), scoreberekening 0-100, resultaatscherm met domeinkaarten + ▲-profiel + onderbouwing. |
| v0.2 | 2026-06-18 | **Codeblok 2 + 3 + 4 + 5 (demo):** volledige 360-/teamanalyse-flow toegevoegd. Nieuw: betaalpoort-popups (per perspectief, Akkoord/Annuleren), **platform-adapter** met demo-fallback (betaling, e-mail, reacties, opslaan gesimuleerd), uitnodigscherm (collega's toevoegen), verzamelscherm (status + demo-simulatie van reacties), 360-resultaat met volledige dumbbell (▲ + ● + spreiding + verschil-lijn), sorteren (model / grootste verschil), klikbare gap-duiding (perspectief-afhankelijk), anonimiteits- en drempellogica (≥3, alles-of-niets opt-in), en rapportacties (printen via print-stylesheet, `saveReport`-stub, vergelijk-stub). Blok 2 meegenomen: teaser-preview op het gratis resultaat + volledige visual. Gratis variant kan niet printen (print-blokkade). |
| v0.3 | 2026-06-18 | **Beschouwing-module (regelgebaseerd, rijk):** in het rapport (scherm + PDF) een geschreven beschouwing in zes secties — beeld in het kort, sterke punten, ontwikkelpunten, samenhang & patronen, advies, vervolg. Vervangt de enkele eindopmerking door een data-gedreven analyse die signalen combineert: niveau per domein, benoemde leiderschapspatronen (sturend / uitvoerder / mensgericht / vernieuwer / evenwichtig), samenhang bínnen blokken (uitschieters + A/B-divergentie per competentie) en tússen blokken, en (betaald) zelfbeeld vs teambeeld (systematische over-/onderschatting, blinde vlekken, onderschatte krachten, consensus vs verdeeldheid, plus de combinatie blinde vlekken + lage feedback-score). Niet-repetitief: seeded RNG (stabiel per profiel) met brede formuleringspools en anti-herhaling binnen één rapport; 20 competentie-specifieke ontwikkeltips. In 360 zijn sterke/ontwikkelpunten op het teambeeld gebaseerd (niet het zelfbeeld). Werkt in gratis (zelfbeeld) en betaald (teambeeld). Syntaxcheck + functietest met twee profielen uitgevoerd. |
| v0.4 | 2026-06-21 | **Live-koppeling (op verzoek platformontwikkelaar):** de `Platform`-adapter is van demo-stubs naar **live** gebracht — `cinab-tool-client.js` (launch→token, `getSaldo`/`settleSession`/`goToPayment`, `saveReport`, `notify*`) + Firebase RTDB (anonieme auth, sessie-aanmaak met 6-tekens code, `content` publiceren, `onValue` op `answers`). Module-bridge + `FB_CONFIG` (project `cinab-vaardigheidsmeter-leidinggeven`, europe-west1) toegevoegd; `sessionStorage`-persistentie + `?action=resume` na betaling. **Beoordelaar-invulpagina `vaardigheidsmeter_join.html` gebouwd** (identiteitspoort + dezelfde 40 stellingen, byte-identieke DOMAINS, push naar `answers`, refresh-overleving, demo-modus). **App-specifieke `database.rules.json`** geleverd die exact op de schrijfacties aansluit. Demo-fallback overal intact. Open afstempunten voor het platform vastgelegd in PLATFORM-WERKBOEK §8 (n.v.t.-validate, entry-URL, gratis→betaald-token, relaunch-code, launch-params). JS-syntax beide bestanden OK; DOMAINS-diff identiek. |
| v0.6 | 2026-09-15 | **Echte AI-verrijking van het rapport (alleen betaalde 360).** Server-side proxy `vaardigheidsmeter-ai-proxy.php` (afgeleid van het CINAB-template): de browser stuurt alléén een PII-vrij datapakket + taaktype `beschouwing`; de prompt, het model en `max_tokens` staan server-side; token als poort; strikte JSON terug. **Model server-side ingebakken** (4 domeinen × 20 competenties, schaal 0-100, 360 = zelf-anderovereenstemming: gap = blinde vlek/onderschatte kracht, spreiding = (on)eensgezindheid) → "continu zicht op het model". **Grounding:** de AI mag uitsluitend de meegeleverde getallen/bevindingen gebruiken, geen verzonnen scores/competenties/personen, géén externe bronnen; elke uitspraak noemt het onderliggende getal, en elk advies krijgt een `grond`-onderbouwing. **Lokaal blijft leidend:** de regelgebaseerde beschouwing wordt eerst gerenderd en is de terugval bij elke fout (geen token, demo, netwerk, 502, onparsebare JSON, timeout). AI-tekst wordt geëscaped vóór render (§16). Datapakket bevat geen namen/e-mail (AVG). AI-analyse gaat mee in het opgeslagen rapport (`data.beschouwing_ai`). Test: PII-check, tolerante parse en XSS-escape geverifieerd; JS-syntax OK. Nog invullen vóór go-live: `ANTHROPIC_MODEL`, `$ALLOWED_ORIGINS` (staging-subdomein) en de sleutel (env/config) in de proxy; `CINAB_REQUIRE_TOKEN=true` + productie-validate-url in productie. |
| v0.7 | 2026-09-16 | **Taalwissel NL/EN + demo-fout opgelost.** (1) *Demo-fout:* `live=true` werd pas ná de Firebase-login gezet, waardoor een mislukte RTDB-init (o.a. door de `[INVULLEN]`-placeholders) de héle app naar demo trok, óók met geldig token. Platformsessie (`live`) en RTDB (`sync`) zijn nu ontkoppeld; zonder RTDB blijft de sessie live en meldt de app eerlijk dat uitnodigen niet kan (`sendInvites` weigert i.p.v. stil te falen). Nieuwe melding `#sync-err`. (2) *Taal:* gedeeld `MODEL`-blok met domeinen, 20 competenties en 40 stellingen in NL én EN (md5-identiek in hoofd-app en join); `DOMAINS`/`COMPS` worden eruit afgeleid via `rebuildModel()`. NL/EN-knop in de header van beide bestanden; `T()`-helper met `{placeholder}`-substitutie; alle statische teksten via `data-i18n`/`-html`/`-ph`/`-aria`; alle runtime-meldingen vertaald. Volledige beschouwing (banden, 5 archetypen, 6 secties, 20 facetten, 20 ontwikkeltips) verhuisd naar taalpakket `BETXT`. AI-proxy krijgt `LANG` mee i.p.v. hardgecodeerd `nl`. Taal onthouden (localStorage + sessie), `?lang=` ondersteund, join-pagina volgt de sessietaal tenzij de beoordelaar zelf koos. Join-pagina kreeg `quizBuilt`-guard + `restoreAnswers()` (voorkwam gestapelde listeners bij hertekenen). Dode code (`BE`, `syncBE`) verwijderd. **Getest:** pariteit 226 sleutels in 4 sets zonder ontbrekende/lege/gelijke waarden; beschouwing in NL+EN × 360+zelf zonder taallekken of placeholders; taalwissel behoudt antwoorden heen en terug; md5 van alle drie gedeelde blokken gelijk; `node --check` beide bestanden. Testscripts in `qa/`. |

---

## Huidige stand (v0.2)

**Werkt nu — gratis variant (standalone, niets opgeslagen):**
- Keuze invalshoek + variant; vragenlijst; resultaat met domeinkaarten + ▲-profiel + onderbouwing.
- Wegklikbare teaser-preview met collega-voorbeeld (● + spreiding) op het gratis resultaat.
- Geen download/print (print-stylesheet blokkeert dit in de gratis variant).

**Werkt nu — betaalde variant in DEMO-modus (geen echte betaling/verzending/opslag):**
- Betaalpoort-popup per perspectief (360-meting / teamanalyse) met credit-melding, Akkoord/Annuleren.
- Eigen vragenlijst → uitnodigen (collega's toevoegen) → verzamelen (status + "Simuleer reacties") → 360-resultaat.
- 360-resultaat: domeinkaarten (eigen + team), volledige dumbbell met ● en spreiding, sorteren, gap-duiding, drempel (<3 = eigen beeld + melding), anonimiteit (anoniem tenzij unanieme opt-in), printen via de browser.

**Platform-afhankelijk (zit achter de adapter, nu gesimuleerd) — zie PLATFORM-WERKBOEK:**
- `Platform.init / ensureAccountAndCredits / settle / sendInvites / subscribeResponses / saveReport`.
- Live e-mailverzending (Route 1), Firebase RTDB-sync, account/credits, terugkeer na dagen, vergelijken.

**Nog te doen:**
- Codeblok 6: opsplitsen in CINAB-fasebestanden (fase 0–3 + rapport + join) met gedeelde glue-blokken; `firebase.json` + `database.rules.json` per app; live-adapter koppelen aan `cinab-tool-client.js` + Firebase.
- Detail-polish: per-beoordelaar individuele antwoorden tonen wanneer namen zijn vrijgegeven (nu aggregaat + statusmelding); vergelijken-met-vorige visueel uitwerken zodra account-historie beschikbaar is.

---

## Architectuur- en ontwerpbesluiten (referentie)

- **Platform-adapter** isoleert alle platform-/Firebase-afhankelijkheden in één object met een vast contract. Demo-implementatie werkt standalone; live-implementatie wordt door de platformontwikkelaar ingevuld. Zo blijft de app testbaar zonder platform.
- **Demo vs live:** `Platform.init()` detecteert `?launch`/`?token`. Geen token → demo (ribbon "demo", gesimuleerde calls). Token → live-pad (nog in te vullen). Conform de standaard (demo = geen platform-POSTs/opslag).
- **Twee invalshoeken** sturen alle teksten (`TEKST`) en de betekenis van ▲/●; statements zijn perspectief-neutraal.
- **Scorecontract:** 4 domeinscores (0-100) in `scores`; eigen + team-aggregaten opaak in `data` (zie `buildWrapper()`).
- **Anonimiteit/drempel:** teambeeld vanaf 3 reacties; namen alleen bij unanieme opt-in (alles-of-niets); anders aggregaat + spreiding.
- **Printen:** alleen betaalde variant (`body.can-print`); print-stylesheet verbergt UI-chrome en toont profiel + onderbouwing.
- **Huisstijl:** `cinab-theme.css` ingebed (productie: linken); fonts via fallback (productie: woff2 self-host); officieel logo ongewijzigd.

---

## Testlog

| Versie | Test | Resultaat |
|---|---|---|
| v0.2 | Gratis: keuze → vragenlijst → resultaat + teaser, beide perspectieven | open `vaardigheidsmeter-leidinggeven.html` |
| v0.2 | Betaald (demo): popup → eigen vragenlijst → uitnodigen → "Simuleer reacties" → 360-resultaat | volledige flow zichtbaar; ribbon "demo" zichtbaar |
| v0.2 | Drempel <3 reacties → eigen beeld + melding; ≥3 → teambeeld | ingebouwd |
| v0.2 | Sorteren / gap-duiding / printen (alleen betaald) | te verifiëren in browser |
| v0.2 | Bekende minor: vergelijken en per-beoordelaar-namenweergave nog stub/aggregaat | gepland (zie "nog te doen") |
