#!/usr/bin/env python3
"""Converteert de vier TTF's naar de woff2-bestandsnamen die de fasebestanden verwachten."""
import sys, pathlib
from fontTools.ttLib import TTFont
NAMES = {
    'fraunces-semibold': 'fraunces-600.woff2',
    'plusjakartasans-regular': 'plus-jakarta-sans-400.woff2',
    'plusjakartasans-semibold': 'plus-jakarta-sans-600.woff2',
    'plusjakartasans-bold': 'plus-jakarta-sans-700.woff2',
}
for src in sys.argv[1:]:
    key = pathlib.Path(src).stem.lower().replace('_', '-').replace(' ', '')
    out = next((v for k, v in NAMES.items() if k in key), None)
    if not out:
        print('overgeslagen (onbekende naam):', src); continue
    f = TTFont(src); f.flavor = 'woff2'; f.save(out); print('geschreven:', out)
