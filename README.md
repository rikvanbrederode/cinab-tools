# cinab-tools

Bron van waarheid voor de CINAB-tools op Firebase. Wat hier staat, is wat er draait; er wordt uitsluitend vanuit deze mappen gedeployd.

## De ene regel die alles draagt

**Geen `firebase deploy` zonder commit.** De commitmessage is meteen de ene regel changelog die naar de tooldeveloper gaat als de wijziging het contract raakt. Levert de tooldeveloper een nieuwe set bestanden aan, commit die dan onder zijn versienummer, bijvoorbeeld: `Erik v11.2: variantlaag doel=jaarplan/project`.

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
