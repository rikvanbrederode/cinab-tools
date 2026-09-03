# Fonts voor risicobeheersing.cinab.nl (standaard §5: self-hosted .woff2, geen font-CDN)

De fasebestanden verwachten exact deze vier bestanden in **`public/fonts/`**, dus naast de
HTML-bestanden in de map die naar Firebase Hosting gaat. Deze map hier bevat alleen het
bouwscript en de bronbestanden; die worden niet gedeployd.

| Bestand | Familie | Gewicht |
|---|---|---|
| `fraunces-600.woff2` | Fraunces | 600 |
| `plus-jakarta-sans-400.woff2` | Plus Jakarta Sans | 400 |
| `plus-jakarta-sans-600.woff2` | Plus Jakarta Sans | 600 |
| `plus-jakarta-sans-700.woff2` | Plus Jakarta Sans | 700 |

Zolang ze ontbreken vallen de fasebestanden automatisch terug op de fallback-stacks
(Georgia / system-ui) — de app blijft werken, alleen de typografie is dan niet de huisstijl.

## Bron (beide SIL Open Font License)
- Fraunces: https://github.com/undercasetype/Fraunces (map `fonts/`) of Google Fonts "Fraunces"
- Plus Jakarta Sans: https://github.com/tokotype/PlusJakartaSans (map `fonts/webfonts/`) of Google Fonts

Download de statische TTF's (Fraunces SemiBold; Plus Jakarta Sans Regular, SemiBold, Bold) en
converteer met het script hiernaast:

```bash
pip install fonttools brotli
python3 maak-woff2.py Fraunces-SemiBold.ttf PlusJakartaSans-Regular.ttf PlusJakartaSans-SemiBold.ttf PlusJakartaSans-Bold.ttf
```

Het script schrijft de vier bestanden met de juiste namen naar deze map.

## Stand per 3 september 2026

De vier woff2-bestanden staan in `public/fonts/`, gemaakt uit de statische TTF's uit de
Google Fonts-download: Fraunces 72pt SemiBold, en Plus Jakarta Sans Regular, SemiBold en Bold.
Elk bestand is ongeveer 30 kB.

De zips en TTF's blijven lokaal en staan in `.gitignore`; alleen de woff2 gaat mee in de repo.

## Als het converteren niet lukt op je eigen machine

Op Windows ARM64 bestaat er geen kant-en-klare wheel voor `brotli`, dus `pip install brotli`
probeert te compileren en vraagt om de Microsoft C++ build tools. Installeer die niet voor
vier bestanden. Zet de zips in deze map en laat de conversie elders doen; het resultaat is
hetzelfde, want `fontTools` met `flavor = 'woff2'` is de hele bewerking.
