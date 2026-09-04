# cinab-tools

Bron van waarheid voor de CINAB-tools op Firebase. Wat hier staat, is wat er draait; er wordt uitsluitend vanuit deze mappen gedeployd.

## De ene regel die alles draagt

**Geen `firebase deploy` zonder commit.** De commitmessage is meteen de ene regel changelog die naar de tooldeveloper gaat als de wijziging het contract raakt. Levert de tooldeveloper een nieuwe set bestanden aan, commit die dan onder zijn versienummer, bijvoorbeeld: `Erik v11.2: variantlaag doel=jaarplan/project`.

## Het werkboek voor tool-bouwers

`WERKBOEK-TOOLBOUWERS.md` in deze repo is de bindende beschrijving van het datacontract, de koppeling, de betaalpoort, deelname op een eigen apparaat en de renderroute van het rapport. Dat is het document waar een externe bouwer op werkt, en het is meteen het antwoord op de vraag welke versie de actuele is: die van deze repo.

Het is een afgeleide van het interne `CINAB-Werkboek-Tool-Bouwen-en-Koppelen.md` in `cinab-platform/docs`, zonder de commerciële punten en zonder de hardening van het platform zelf. Wijzigt het interne werkboek, dan wordt deze uitgave opnieuw afgeleid en meegecommit, met hetzelfde versienummer. Andersom werkt niet: wijzigingen beginnen altijd in het interne document.

De scheiding tussen de twee repo's is meteen de toegangsregel. Wat in `cinab-tools` staat mag een tool-bouwer zien, wat in `cinab-platform` staat niet.

## Structuur

Per tool een map met dezelfde opbouw:

```
<tool>/
  .firebaserc          projectaliassen (default, staging, production)
  firebase.json        hosting-config en verwijzing naar de regels
  database.rules.json  RTDB-securityregels
  public/              de bestanden die naar Firebase Hosting gaan
  README.md            project-ID, regio, status en deploy-commando's
```

## Versienummers

Drie bestanden dragen een versieregel: `public/cinab-tool-client.js` (header bovenaan), `database.rules.json` en `firebase.json` (commentaarregel bovenaan). Bij elke wijziging: nummer ophogen, datum bijwerken. Raakt de wijziging het datacontract (endpoint, statuscode, TTL, rapport-wrapper), stuur dan het nieuwe bestand met een regel uitleg naar de tooldeveloper.

Let op: `.firebaserc` is strikte JSON, daar kan geen commentaar in. Versie-informatie hoort dus niet in dat bestand.

## Deployen

Vanuit de map van de tool, in de LocalWP-loze gewone terminal (PowerShell):

```powershell
cd C:\Users\rikva\Projecten\cinab-tools\<tool>
git status
firebase use staging
firebase deploy --only hosting,database
```

Gebruik `--only hosting` als de regels niet wijzigen. `firebase use production` schakelt naar het productieproject; dat werkt pas als de production-alias in `.firebaserc` een echt project-ID heeft. Bij een verlopen login eerst `firebase login --reauth`.

## Vaste afspraken

Eén Firebase-project per tool, regio `europe-west1` (HS-11: de regio ligt onherroepelijk vast bij aanmaken, dus EU-residency regel je aan het begin). Anonymous sign-in aanzetten in de console hoort bij het aanmaken van elk project (Authentication, Sign-in method, Anonymous). Sleutels en omgevingsbestanden horen niet in deze repo; de gitignore vangt de bekende gevallen af, maar blijf er zelf op letten.
