# Fonts voor risicobeheersing.cinab.nl (standaard §5: self-hosted .woff2, geen font-CDN)

De fasebestanden verwachten exact deze vier bestanden in de map `./fonts/` naast de HTML-bestanden:

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
