# TESTRAPPORT — Vaardigheidsmeter Leidinggeven (CINAB-TESTPROTOCOL)

```text
Werksessie:            Vaardigheidsmeter Leidinggeven — v0.4.1 getest, opgeleverd als v0.5
Datum:                 2026-09-03
Testkaart:             2 bestanden (hoofd-app met 5 schermen + beoordelaar-join), 2 rollen + rapportlezer,
                       sessionStorage-contract vlm_cinab + RTDB /sessions/{code}, geen AI-taken, NL-only
Teams:                 T1 Netjes · T2 Slordig · T3 Extreem · T5 Ongeduldig · T6 Mobiel · LIVE-keten (stub)
                       (T4 Engelstalig: n.v.t. — app is NL-only, zie beslispunt D-1)
Resultaat per stap:    1 ✓ (45 checks)  2 ✓ (46)  3 ✓ (78)  4 n.v.t. (geen AI; eerlijkheid ✓)
                       5 ✓ (249, 4 viewports × 13 schermen)  6 n.v.t. (NL-only)  7 ✓ (34 LIVE-checks)
                       8 ✓ (XSS, console, 30 beoordelaars, init-fout)  9 ✓ (print, wrapper-schema, data_ref)
Bevindingen:           23 (B-01…B-23): 2 hoog, 9 midden, 12 laag — alle opgelost en hertest
Regressierun:          statisch 45/45 · scenario 124/124 · visueel 249/249 — 0 uncaught exceptions
Niet testbaar hier:    echte platform-calls, echte Firebase (rules/cross-device), Mollie, e-mailverzending,
                       self-hosted fonts — zie §6 met staging-stap per punt
Opgeleverd:            deploy-2026-09-03/ (html ×2, firebase.json, database.rules.json, README-DEPLOY)
                       testprotocol-2026-09-03/ (qa_static.py, qa_scenario.py, qa_aspects.py, fb-stub.js,
                       patch_v05.py, shots/) · WERKBOEK v0.5 · PLATFORM-WERKBOEK bijgewerkt
```

---

## 1. Testkaart (stap 0)

| Onderdeel | Vastgesteld |
|---|---|
| Bestanden | `vaardigheidsmeter-leidinggeven.html` (hoofd-app, 90 kB, één bestand), `vaardigheidsmeter_join.html` (beoordelaar), nevenbestanden uit de context-bibliotheek: `cinab-tool-client.js`, `_wrapper.schema.json`, `firebase.json`/`database.rules.json` (sjablonen). Geen AI-proxy (geen AI). |
| Fasen en schermen | Hoofd-app: `screen-start` (invalshoek + variant) → `screen-quiz` (20×2 stellingen) → gratis: `screen-result`; betaald: betaalpoort-popup → `screen-quiz` → `screen-invite` → `screen-wait` → `screen-result`. Join: `screen-intro` → `screen-quiz` → `screen-done`. Geen `publishStage`/deelnemer-stages: de beoordelaar-flow is asynchroon (dagen), niet facilitator-gestuurd. |
| Rollen | Initiatiefnemer (leidinggevende óf medewerker; twee invalshoeken sturen alle teksten), beoordelaar (eigen apparaat via `/join/{code}`), rapportlezer (print/PDF; platform-rapport via wrapper). |
| Datacontract | `sessionStorage.vlm_cinab` = `{apiBase, token, code, betaalVanafFase, credits, settled, rapportId, rapportUrl, persp, variant, answers, raters, screen}` — schrijver hoofd-app (live), lezer hoofd-app (refresh/resume). `localStorage.vlm_joined_{code}` = "1" (join, dubbel-insturen-guard). RTDB `/sessions/{code}/meta {createdAt, facilitatorUid, lang, tool}`, `content {tool_naam, organisatie, initiatiefnemer, subject, persp, lang, createdAt}` (hoofd-app schrijft, join leest), `answers/{pushId} {name, email?, naamZichtbaar, vals{LV1..LV20: 0-100}, at}` (join pusht, hoofd-app luistert). Afgeleid (nooit opgeslagen): compPct, domainSelf/Team, teamAgg, beschouwing. |
| Invoervelden | Hoofd-app: 40 radiogroepen (1-5) + 20 n.v.t.-checkboxes; `r-name` (verplicht, ≤120), `r-email` (verplicht, formaat, ≤200, uniek). Join: `f-name` (verplicht, ≤120), `f-email` (optioneel, formaat, ≤200), `f-consent`; 40 radiogroepen + 20 n.v.t. Weergave van namen/e-mails via `esc()`. |
| AI-taken | Geen. De "Beschouwing" is een regelgebaseerde engine (seeded RNG) en meldt dat expliciet ("Automatisch opgesteld uit de gegeven antwoorden"). Eerlijkheidseis: voldaan — nergens wordt een AI-resultaat gesuggereerd. |
| Popups/dialogen | Betaalpoort-modal (`#overlay`, Akkoord/Annuleren); teaser-overlay (gratis); onderbouwing-paneel (toggle); inline meldingen `#invite-msg`, `#result-msg`, `#live-err`; join-banners demo/err. Twee-staps: "Verstuur uitnodigingen" (na fix). |
| Vertaling | Geen T-dicts; UI uitsluitend NL. `TEKST[persp]` stuurt perspectief-varianten. |
| Expressielaag | Fase-accenten per scherm (teal/blauw/groen/geel/zwart) via inline `--fase-accent`, fasepill, accentstreep, Fraunces-watermerk (`.page-glyph`, verborgen < 900 px), 6px kaartrand + coin-stip (E2). Geen ladder/wachtschermen (geen live-facilitatie). F5/F6 afwezig. |
| Platform | `Platform`-adapter (init/ensureAccountAndCredits/settle/sendInvites/subscribeResponses/saveReport/notify*). Bootstrap via `startCinabSession()`; restore (na fix) via `createCinabClient()` uit sessionStorage. Betaalpoort fase 2 (popup vóór de vragenlijst), 1 credit. Demo = geen token (ribbon "demo"); `?demo=1` werkt impliciet. |
| Bekende zwakke plekken (werkboek) | v0.4.1: opstartvolgorde module-bridge (opgelost met `libReady`). Open platformpunten §8 PLATFORM-WERKBOEK: e-mail-endpoint, terugkeer na dagen, vergelijken. Werkboek "Huidige stand" liep achter (v0.2 terwijl v0.4.1 bestond). Geen ingevuld APP-START in de map; `database.rules.json` uit v0.4 ontbrak in de map. |

Bewuste afwijking van de standaard (gedocumenteerd, niet "gefixt"): de join-pagina bevat de volledige vragenlijst in plaats van alleen een identiteitspoort (§11A). Reden: beoordelaars vullen asynchroon over dagen in zonder facilitator en zonder stage-sturing; één bron van waarheid is geborgd door het byte-identieke gedeelde blok `DOMAINS` (md5-geverifieerd).

## 2. Virtuele testteams (stap 3)

| Team | Casus | Deelnemers | Profiel / wat is gedaan |
|---|---|---|---|
| T1 Netjes | Gemeente Westerkwartier — teamleider Sanne wil weten of haar "sturende" stijl klopt | Sanne + Bram, Fatima, Joost, Lieke, Pieter | Gratis zelftest (1× n.v.t.) → teaser → 360 in demo: popup, uitnodigen, verwijderen, terug/vooruit, simulatie, 360-resultaat, sorteren, duiding, wrapper, print, opnieuw. 46 checks. |
| T2 Slordig | Bouwbedrijf Van Dijk — medewerker start teamanalyse van uitvoerder Henk | Karin, Mo, Els | Wisselvallige keuzes, dubbelklik Akkoord, directe handler-aanroep zonder 20/20, n.v.t. na antwoorden, lege/spaties/fout e-mail, dubbel adres (case-insensitief), drievoudige klik verstuur, <3 reacties. |
| T3 Extreem | Ziekenhuis Sint Anna — afdelingshoofd met 30 beoordelaars | 30 raters incl. `<img onerror>`, `<script>`, emoji/CJK, 800 tekens, quotes | XSS-injectie via naam (nooit uitgevoerd), overloop van lange namen, prestaties (30 toevoegen < 8 s, 360-render < 2 s), wrapper geldig met 30 deelnemers. |
| T5 Ongeduldig | Startup Loopr — founder refresht alles | — | Refresh in gratis (schone start, verwacht), `?demo=1`, join zonder code (demo-banner), beginnen zonder naam, alles n.v.t., browser terug/vooruit. |
| T6 Mobiel | Zorgcentrum De Linde — teamleider op 1024 px, beoordelaars op 380 px | 4 collega's | Hele flow op 380/768/1024 (+ join op 380/1280): niets buiten de viewport, tikdoelen ≥ 40 px, layout profielrijen. |
| LIVE-keten | Provincie Utrecht — Sanne live via platform (gestubd) | Anke (opt-in), `<b>Bas</b>`, Chris (zonder e-mail) | `?launch` → token → sessionStorage; popup zonder demo-tekst; settle 1×; refresh midden in de vragenlijst (blijft live, antwoorden terug); invites 500 → melding + retry; invites OK (token in body, join-url zonder token, content in RTDB); 3 beoordelaars op eigen "apparaat" (aparte browsercontext) via `/join/{code}`; live binnenkomst bij de initiatiefnemer; refresh op verzamelscherm; 360 anoniem; wrapper met `data_ref`; 2× printen = 1× opslaan + patch; 402 → shop met `cinab_return_url` → `?action=resume` zonder token → settle opnieuw → vragenlijst; init-fout met token → zichtbare melding. |

## 3. Bevindingenregister

| Nr | Ernst | Fase | Bevinding (reproductie) | Oorzaak | Fix | Hertest |
|---|---|---|---|---|---|---|
| B-01 | hoog | vragenlijst | Na teaser → 360, en bij resume/refresh, toont de vragenlijst lege radio's terwijl de teller 20/20 zegt en de knop actief is | `buildQuiz()` bouwt de DOM opnieuw, `state.answers` blijft; DOM volgde de state niet | `restoreAnswers()` na elke (her)opbouw | T1, LIVE ✓ |
| B-02 | hoog | platform | Refresh in live-modus (token is uit de URL gewist) én terugkeer na betaling (`?action=resume` zonder token) vielen terug op demo: sessie kwijt, betaalflow kapot | `Platform.init()` keek alleen naar URL-params; geen restore uit sessionStorage (standaard §9 bootstrap/restore) | restore via `createCinabClient()` uit `vlm_cinab`; scherm/raters gepersisteerd; refresh keert terug op vragenlijst/uitnodigen/verzamelen; `settled`-vlag voorkomt onnodige settle-call; `betaalVanafFase/credits` worden bij restore nooit met null overschreven | LIVE ✓ |
| B-03 | midden | betaalpoort | Popup sluit niet met Escape/backdrop; bij een settle-fout (niet-402) bleef Akkoord disabled zonder melding (unhandled rejection) | geen keydown/backdrop-handlers; geen try/catch | Escape/backdrop sluiten; try/catch met inline foutmelding; dubbelklik-guard; `pageshow`-reset (§11B) | T1, T2 ✓ |
| B-04 | midden | uitnodigen/resultaat | Validatie- en foutmeldingen via `alert()`: in de sandboxed demo-iframe (§7) worden alerts stil geblokkeerd → gebruiker ziet geen melding | `alert()` | inline `.msg`-banners (`#invite-msg`, `#result-msg`) met `role=alert/status` | T2, static ✓ |
| B-05 | laag | resultaat | Knop "vergelijken" toonde een interne verwijzing ("zie PLATFORM-WERKBOEK §3.3") aan eindgebruikers | placeholder-tekst | gebruikerstekst, demo/live-variant | T1 ✓ |
| B-06 | midden | uitnodigen | "Verstuur uitnodigingen" (onomkeerbaar: mails) ging op één klik | geen twee-staps (§11B) | bewapenen (`aria-pressed`, tekst wijzigt) → tweede klik verstuurt; `disarm` bij lijstwijziging en `pageshow` | T1, T2, T3 ✓ |
| B-07 | laag | uitnodigen | Dubbel e-mailadres (ook met andere hoofdletters) toegestaan; geen maxlength; e-mailregex te ruim | ontbrak | uniek-check case-insensitief, `maxlength` 120/200, strakkere regex | T2 ✓ |
| B-08 | midden | verzamelen | Status "gereageerd" matchte alleen op exact e-mailadres; beoordelaar zonder e-mail (optioneel op join) of met andere hoofdletters bleef op "wacht" | strikte vergelijking | match op e-mail (case-insensitief) óf naam | LIVE ✓ (3/3 badges) |
| B-09 | midden | rapport | Elke klik op "PDF/Printen" riep `saveReport` aan → tweede keer 409 (token single-use); `notifyCompleted` vóór `window.print` kan de parent laten doorschakelen vóór de printdialoog | geen opslag-vlag; volgorde | eerst printen; `rapportId` in sessiecontext; tweede keer `patchReport`; melding in `#result-msg` | LIVE ✓ (1 save bij 2 prints) |
| B-10 | midden | rapport | Wrapper zonder `data_ref` (nodig voor terugkeer/render/audit, standaard §12) en zonder perspectief/variant in `meta` | ontbrak | `data_ref {store:"firebase-rtdb", path:"/sessions/{code}"}` in live; `meta.perspectief/variant` | LIVE ✓, schema ✓ |
| B-11 | midden | platform | Token aanwezig maar live-init mislukt (SDK/config/netwerk) → stille demo-terugval; gebruiker denkt dat zijn 360 loopt | catch zonder UI | `#live-err`-banner ("koppeling niet gelukt — oefenversie") | LIVE init-fout ✓ |
| B-12 | laag | resultaat | Vanuit het 360-resultaat kon je niet terug naar het verzamelscherm (nieuwe reacties niet zichtbaar zonder "Opnieuw") | ontbrak | knop "Terug naar reacties" | T1 ✓ |
| B-13 | laag | huisstijl | Losse hex (`#fff`, `#FFF6E5`, `#FBEBEA`, `#7a5a12`), gradient in join-sticky-balk, logo-SVG met hernoemde klassen | afwijking §4/§5 | tokens, solide off-white + lijn, officiële klassen | static ✓ |
| B-14 | midden | a11y (join) | Gekozen schaalwaarde wit op teal (`#2A9791`) = 3,9:1 < 4,5:1 (tokenadvies teal = donkere tekst) | kleurkeuze | geselecteerd = inkt-achtergrond + off-white tekst (gelijk aan hoofd-app) | aspects ✓ |
| B-15 | laag | HTML | `<p>` binnen `<button>` (ongeldig contentmodel) | markup | `<span>` met `display:block` | static tagbalans ✓ |
| B-16 | midden | vragenlijst | Directe aanroep van de handler zonder 20/20 (of zonder reacties) ging door naar de volgende stap | voorwaarde alleen via `disabled` | guards in `btn-start`, `btn-result`, `btn-to-result` | T2 ✓ |
| B-17 | laag | uitnodigen | Naam van 800 tekens brak uit het kader | geen `overflow-wrap` | `overflow-wrap:anywhere` | T3 ✓ |
| B-18 | midden | a11y | Tikdoelen < 44 px: sorteerschakelaar (35), profielrijen (34), n.v.t.-rijen | ontbrak | `min-height:var(--touch-target)` | T6 ✓ |
| B-19 | laag | a11y | Watermerk-glyph zonder `aria-hidden` (screenreader leest "?", "✓") | ontbrak | `aria-hidden="true"` | aspects ✓ |
| B-20 | laag | a11y (join) | Verplicht-sterretje in coral op wit = 3,4:1 | kleur | "(verplicht)" in grijs als tekst | aspects ✓ |
| B-21 | midden | mobiel | Op 380 px overlapten de as-labels ("in ontwikkeling / voldoende / zeer vaardig") en waren de rails ~80 px | drie-koloms grid | ≤ 640 px: label boven, rail volle breedte, waarde rechts | T6, screenshot ✓ |
| B-22 | laag | uitnodigen | Badge "uitgenodigd" vóórdat er iets verstuurd is | tekst | "toegevoegd" tot versturen | ✓ |
| B-23 | laag | join | Alles op n.v.t. → lege `vals` → RTDB-rules weigeren de push → technische foutmelding | geen guard | begrijpelijke melding, knop weer actief | T5 ✓ |

Documentatiebevindingen (geen code): werkboek "Huidige stand" liep achter op de versiehistorie (opgelost in v0.5); `database.rules.json` en `firebase.json` per app ontbraken in de map (nu in het deploy-pakket); geen ingevuld `APP-START` in de map (D-2).

## 4. Stap 4 — AI-eerlijkheid

De app bevat geen AI-taken en geen proxy-aanroepen; de beschouwing is een regelgebaseerde engine en labelt zichzelf als "Automatisch opgesteld uit de gegeven antwoorden" (T1-check). Er is dus geen keten om met een stub-proxy te bewijzen. Mocht AI later worden toegevoegd (bijv. verfijning van de beschouwing), dan gelden de vier stub-modi en de herkomstmelding uit het protocol; de lokale engine is dan de terugval.

## 5. Stap 5/6 — visueel en vertaling

249 metingen over 13 schermen × 4 viewports (1280/1024/768/380): geen overloop, geen horizontale scroll, geen tekst < 4,5:1 (decoratief watermerk uitgesloten), geen placeholders/NaN, watermerk verborgen < 900 px, reduced-motion gerespecteerd, toetsenbordfocus zichtbaar, print-CSS (betaald: chrome weg, onderbouwing zichtbaar; gratis: geblokkeerd met melding).

Kwalitatieve blik: de resultaatpagina is rustig en leesbaar; de dumbbell-visual met domeinkleuren draagt het verhaal. Twee kanttekeningen: (1) in de sandbox rendert de fallback-serif (geen Fraunces/Plus Jakarta) — live moeten de `.woff2`-fonts self-hosted staan, anders oogt het generiek; (2) de "Beschouwing"-kaart is tekstzwaar; een korte samenvatting in drie kaarten boven de secties (sterkste domein / grootste blinde vlek / eerste stap) zou de scan-baarheid verbeteren — als optie genoteerd, niet doorgevoerd.

Vertaling: de app is NL-only (geen T-dicts). Stap 6 en team T4 zijn daarmee n.v.t.; zie beslispunt D-1.

## 6. Niet testbaar in deze omgeving — staging-stap

| Wat | Waarom niet hier | Staging-bewijs |
|---|---|---|
| Echte platform-calls (`start-tool`, `saldo`, `sessie-afrekenen`, `rapport-opslaan`, `PATCH /rapport/{id}`) | gestubd via Playwright-routes | Start vanuit de WordPress-detailpagina met launch-code; controleer in devtools: `POST /start-tool` 200 → `sessionStorage.vlm_cinab.token` gevuld; Akkoord → `POST /sessie-afrekenen` `{betaald:true}`; printen → `POST /rapport-opslaan` 200 met `data_ref`; tweede print → `PATCH /rapport/{id}` 200. |
| `POST /wp-json/cinab/v1/stuur-uitnodigingen` | endpoint bestaat nog niet (PLATFORM-WERKBOEK §3.4, beslissing nodig) | Zodra gebouwd: verstuur naar 3 testadressen; controleer body `{token, raters[{name,email,join_url}], meta}` en dat de mail de `join_url` `https://<host>/join/{code}` bevat. |
| Firebase RTDB + `database.rules.json` (write-denies, cross-device) | stub in plaats van SDK; geen emulator | `firebase deploy --only database,hosting` op staging; open `/join/{code}` op een telefoon (andere netwerkverbinding): content zichtbaar, push slaagt, initiatiefnemer ziet badge "gereageerd" live; test met de Rules Playground: schrijven naar `answers` zonder `at` of met `vals.LV21` → denied; lezen van `answers` als niet-facilitator → denied. |
| Mollie/402-terugkeer | redirect gestubd | Account met 0 credits: Akkoord → shop; betaal (testmodus) → terugkeer `?action=resume` → vragenlijst in betaald zonder tweede afschrijving. |
| Terugkeer na dagen met vers token (§3.7a) | platformbeslissing open | Na beslissing: relaunch met `?session={code}` + nieuwe launch; controleer dat `meta.facilitatorUid` de nieuwe anonieme uid accepteert (rules) of dat het platform de uid-koppeling regelt. |
| Fonts self-hosted | geen `.woff2` in de map | Op staging: Network-tab toont `fraunces*.woff2`/`plus-jakarta*.woff2` 200; computed `font-family` van `h1` = Fraunces. |
| Demo in 16:9 sandboxed iframe | geen WordPress | Embed op de detailpagina; hele gratis flow + betaald-in-demo doorlopen zonder alert-pop-ups (nu inline) en zonder netwerkcalls (Network-tab leeg behalve statics). |

## 7. Beslispunten voor de eigenaar (geen gok gedaan)

- **D-1 Taal**: NL-only laten (huidige keuze) of EN toevoegen conform de standaard (T-dicts, `data-t`)? Bij EN: ± 120 strings + beschouwing-pools (± 90 zinnen) — substantieel.
- **D-2 APP-START**: het ingevulde app-startblad staat niet in de map; `template_id`, betaalfase 2, 1 credit, TTL 12 h, dimensies + kleuren zijn uit de code afgeleid en in de testkaart vastgelegd — graag bevestigen/vastleggen.
- **D-3 `?org=`/`?initiator=`/`?subject=`** als launch-hints: nu voorinvulling zonder handmatig alternatief (organisatie komt alleen uit de URL in de wrapper). Optie: invoerveld "organisatie" op het startscherm (§17.4).
- **D-4 Samenvattingskaarten** boven de beschouwing (zie §5) — cosmetische optie.

## 8. Exit-criteria

Alle B-hoog/B-midden opgelost en hertest ✓ · nul uncaught exceptions ✓ · gedeelde blokken (`DOMAINS`, `FB_CONFIG`, `LIBREADY`) md5-identiek ✓ · AI-eerlijkheid: n.v.t. (geen AI; lokale engine correct gelabeld) ✓ · geen overloop op 4 viewports ✓ · T-pariteit: n.v.t. (NL-only, D-1) · refresh-overleving en beoordelaar-sync bewezen op de stub-keten ✓ (echte RTDB: staging) · wrapper schema-geldig ✓ · deploy-pakket compleet ✓.
