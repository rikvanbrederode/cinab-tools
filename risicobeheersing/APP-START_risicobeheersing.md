# APP-START — Risicobeheersing® (ingevuld, sessies v0.8–v0.11 — bijgewerkt 2026-09-02)

Ingevuld conform `APP-START-IN-TE-VULLEN.md`. Alles met `[INVULLEN]` of `[TE BESLISSEN]` is een open punt; deze raken geld, tokens, persoonsgegevens of livegang en zijn bewust **niet** gegokt.

## 1. Basis

```text
App-naam:                         Risicobeheersing®
template_id:                      risicobeheersing            (besluit D2, 2026-06-12)
Korte omschrijving:               Gefaciliteerde COSO ERM-risicosessie met 6×6 kans-impactmatrix,
                                  coin-mechaniek (geel/rood/blauw) en zes diagonale zones.
Aantal fasen/bestanden:           fase 0..5 + rapport (poortindex rapport = 6)
Productie-subdomein:              risicobeheersing.cinab.nl
Staging-subdomein:                staging.risicobeheersing.cinab.nl
Demo beschikbaar:                 ja (zonder launch-code; VK_LIVE=false op localhost/file/LAN)
Talen:                            beide (nl/en)
```

## 2. Betaalpoort en credits

```text
_cinab_betaal_vanaf_fase:          [TE BESLISSEN — komt runtime uit start-tool; de poort (RB_CINAB.gate)
                                    dwingt af wat het platform meldt, incl. 0 en leeg=gratis]
Gratis preview-fasen:              [TE BESLISSEN]
_cinab_credits per sessie:         [TE BESLISSEN — komt runtime uit start-tool]
Token-TTL in uren, 1-72:           [TE BESLISSEN, advies 8-12]
Deellink-TTL in dagen:             30
```

Bevestigd door CINAB: **nee** (open punt)

## 3. Vergelijken

```text
_cinab_is_vergelijkbaar:           nee (v1)
Vergelijken met:                   n.v.t.
parent_rapport_id standaard:       null
```

## 4. Dimensies en scorecontract (besluit D1 = optie B, 2026-06-12)

Zes dimensies = **aandeel risico's per zone** (op basis van de bevestigde groepsscores /
beheersprioriteit `rb_matrix_result`; terugval: afleiding uit `rb_group_scores` via `RB_CELL_ADVICE`).

| Dimensie-label | Contractnaam | Vaste kleur-token | HEX | Interne schaal | Mapping naar 0-100 |
|---|---|---|---|---|---|
| Aanvaardbaar | zone_aanvaardbaar | tool.primary.green | #BDD24D | aantal risico's in zone | round(aantal/totaal×100) |
| Laag | zone_laag | tool.secondary.secondary10 | #C5D93D | idem | idem |
| Beperkt | zone_beperkt | tool.primary.yellow | #FCC429 | idem | idem |
| Midden | zone_midden | tool.secondary.secondary11 | #FAA833 | idem | idem |
| Hoog | zone_hoog | tool.secondary.secondary12 | #F05736 | idem | idem |
| Urgent | zone_urgent | tool.primary.red | #E8423F | idem | idem |

Regels: contractnamen en mapping zijn bevroren; geen risico's = alle scores 0; afronding kan
maken dat de som ≠ 100 (toegestaan). Wijziging ⇒ `schema_version` verhogen.

Displaylabels (v0.10, besluit Airk 2026-06-18): de zone met sleutel `aanvaardbaar` toont in de
UI als **"Veilig"** (NL) / **"Safe"** (EN); lange vormen "Veilig risico" / "Safe risk".
Datasleutels (`aanvaardbaar`, `zone_aanvaardbaar`, `--zone-aanvaardbaar`) zijn ONGEWIJZIGD
(standaard §11: UI-labels mogen wijzigen, datasleutels niet zonder migratie).

## 5. Rapport-wrapper

```json
{
  "template_id": "risicobeheersing",
  "schema_version": "1.0",
  "scores": { "zone_aanvaardbaar": 0, "zone_laag": 0, "zone_beperkt": 0, "zone_midden": 0, "zone_hoog": 0, "zone_urgent": 0 },
  "meta": { "organisatie": "", "datum": "YYYY-MM-DD", "deelnemers": 0, "sector": "", "facilitator": "" },
  "data": { "export": { } },
  "parent_rapport_id": null
}
```

Welke volledige data gaat in `data`?

```text
data.export = { rb_session (deelnemers GEANONIMISEERD tot alleen naam, e-mail gestript),
rb_session_started, rb_consequence, rb_risks, rb_individual_scores, rb_central_scores,
rb_group_scores, rb_matrix_result, rb_measures }. Ruim onder 1 MB.
```

Welke data blijft alleen tool-zijdig via `data_ref`?

```text
Nog geen data_ref: het RB-Firebaseproject bestaat nog niet. Zodra RTDB live is wordt
data_ref = { store:"firebase-rtdb", path:"/sessions/{sessionId}" } toegevoegd en kan
data.export afslanken. [TE BESLISSEN bij Firebase-livegang]
```

## 6. Sessie, deelnemers en persoonsgegevens

```text
Join-flow:                         facilitator publiceert; deelnemer joint (nu nog zelfde-browser-
                                   simulatie; cross-device join via ?join={code} is gepland werk)
Deelnemersdata:                    naam (verplicht), e-mail (optioneel, alleen lokaal)
E-mail in platform-wrapper:        nee — collectExport stript e-mailadressen actief
Bewaartermijn persoonsgegevens:    [TE BESLISSEN, advies 30 dagen]
State-opslag:                      nu localStorage; Firebase RTDB voorbereid (rbFb, config [INVULLEN])
State wissen na afronden:          rbFb.sessionClear aanwezig; aanroep-moment [TE BESLISSEN]
```

## 7. Firebase / hosting

```text
Firebase staging-project:           [INVULLEN — RB_FB_STAGING in het gedeelde glue-blok]
Firebase staging RTDB-regio:        europe-west1
Firebase productie-project:         [INVULLEN — RB_FB_PROD in het gedeelde glue-blok]
Firebase productie RTDB-regio:      europe-west1
Hosting productie:                  [TE BESLISSEN]
Hosting staging:                    [TE BESLISSEN]
```

## 8. AI

```text
AI in app:                          ja
AI-taken:                           cluster (fase 1), verfijn_advies (fase 4)
AI-fasen:                           1 en 4
Model server-side:                  [INVULLEN in risicobeheersing-ai-proxy.php]
Proxybestand:                       risicobeheersing-ai-proxy.php (opgebouwd uit
                                    cinab-ai-proxy_template.php, sessie v0.8)
Sleutelopslag:                      env-var ANTHROPIC_API_KEY of ../cinab-secrets.php (boven webroot)
```

Productie-schakelaars vóór go-live: `CINAB_REQUIRE_TOKEN = true` en
`CINAB_VALIDATE_URL = https://cinab.nl/wp-json/cinab/v1/validate-token`.

## 9. Demo/testmodus

```text
Demo-data aanwezig:                 ja (rapport seed't demo-data)
Demo zonder launch-code:            ja — expliciete demo via ?demo=1 (sessionStorage rb_demo): seed + simulatieknoppen, geen AI-call/platform/opslag (v0.11)
Demo zonder opslag:                 ja (geen platform-POSTs; rbFb no-op zonder config)
Demo zonder AI-call:                ja (vkCallAI reject in demo-modus; UI meldt eerlijk 'Demo: AI staat uit')
Demo zonder betaling:               ja (gate draait alleen met client + betaalVanafFase)
```

## 10. Go-live beslissingen

- [ ] Credits per sessie bevestigd.
- [ ] Betaalmuurfase bevestigd.
- [ ] Token-TTL bevestigd.
- [ ] Persoonsdata en bewaartermijn bevestigd.
- [ ] Productie-Firebaseproject bevestigd.
- [ ] Platform heeft productie-embed-url.
- [ ] Platform heeft staging-embed-url.
- [ ] Platform heeft CORS/origin-whitelist.
- [ ] Platform heeft betaal-return-url.
- [ ] Fonts als .woff2 op het subdomein geplaatst (./fonts/, 4 bestanden).
- [ ] `cinab-tool-client.js` naast de fasebestanden gedeployed.
- [ ] `risicobeheersing_join.html` gebouwd (dunne identiteitspoort, standaard §11A) en
      `firebase.json`-rewrite `/join/** → /risicobeheersing_join.html` gedeployed.
- [ ] `database.rules.json` (pack-versie) gedeployed op het RB-Firebaseproject.
- [ ] End-to-end stagingtest gedaan.
- [ ] End-to-end productietest gedaan vóór eerste echte klant.

## 11. App-specifieke afwijkingen van CINAB-APP-STANDAARD.md

| Afwijking | Reden | Goedgekeurd door | Datum |
|---|---|---|---|
| Bestaande rgba-light-tints (--orange-light, --green-light, …) blijven | Historisch UI-ontwerp; D5=A: normalisatie binnen bestaande layout | Airk | 2026-06-12 |
| --orange-hover #D8901E en --green-d #7B8E1E (eigen tinten) blijven | idem | Airk | 2026-06-12 |
| Logo-styling: bestaand "RB SHARED LOGO STYLES"-blok ongewijzigd | SVG-code zelf niet aangeraakt (regel: logo-SVG nooit wijzigen); herstyling buiten scope v0.8 | Airk | 2026-06-12 |
| Dual-view is nog zelfde-browser (facView-simulatie) | Cross-device join (?join={code} + RTDB) is gepland vervolgw erk; rbFb-laag staat klaar | Airk | 2026-06-12 |
