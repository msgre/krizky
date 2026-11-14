# Kontrola: JavaScript

Cíl: JS všech pluginů působí jako od jednoho autora a sedí na svou Python stranu.

JS je vždy doplněk Python pluginu: nativní JS bez build kroku, typicky v `krizky_<x>/assets/`. Pravidla jsou v `docs/guidelines/javascript.md` a `cross-language.md`. Co vynucuje ESLint nebo Prettier přes `scripts/verify`, se nehlásí.

## Postup

1. `find ../krizky-* -name "*.js" -not -path "*/node_modules/*" -not -path "*/.venv/*"`
2. Porovnej `eslint.config.mjs` a `.prettierrc.json` mezi pluginy.
3. U každého souboru přečti hlavičku, bootstrap a místa, kde čte config a data-atributy.
4. Ke každému data-atributu a klíči configu najdi protějšek v šablonách a Pythonu pluginu.

## Pravidla

### Nástroje

- Plugin s JS bez ESLint nebo Prettier, nebo s jinou konfigurací než ostatní → **recommended**.

### Podle guidelines

Odchylka od těchto sekcí `docs/guidelines/javascript.md` je **recommended**:

- › Modul-level struktura: IIFE s `'use strict'` a tichý návrat, když chybí kořenový element.
- › DOM APIs: `querySelector`, `dataset`, `addEventListener`.
- › Error handling: `try/catch` kolem `JSON.parse` vložených dat, `console.warn` pro chybný config.
- › Naming a › Data attributes: prefix `data-<plugin>-*`, `UPPER_SNAKE` pro modulové konstanty.

### Vazba Python ↔ JS

- Klíč configu pro JS není 1:1 `camelCase` podoba Python klíče (zkrácení, přejmenování) → **recommended**. Pokud koliduje s globálem prohlížeče (`window`), **blocker**.
- Data-atribut, který JS čte, šablona negeneruje, nebo opačně → **blocker**.
- Dva pluginy používají stejný data-atribut → **blocker** (kolize v HTML webu).
- Globální objekt na `window` bez předpony `krizky` → **recommended**.
- Pluginy předávají config do JS různými cestami (`<script type="application/json">` × globál z `inject_head`) bez zjevného důvodu → **nice-to-have**, popiš obě varianty.

### Progresivní vylepšení

- Plugin bez fallbacku, když API prohlížeče (Web Share, Clipboard) chybí → **recommended**.
