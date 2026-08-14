# 2026-08-12-01 — Konfigurovatelná cesta k focal_points + JS runtime

## Motivace

Ohniska fotek (`focal_points.json`) dosud musela být na hardcoded cestě `sources/photos/focal_points.json`. Soubor je přitom ručně udržovaný a patří do repa — nikoliv do gitignore adresáře `sources/`. Uživatel proto potřebuje volitelnou konfigurovatelnou cestu (podobně jako u ostatních zdrojů).

Druhý problém byl kolegiální s pluginem `krizky-filters`: karta vygenerovaná v SSR přes makro `_picture.html` má korektní `<img style="object-position:...">`, ale po JS filtraci se karty klonují ze `<template>` a `filters.js` v handleru `data-field-photo` nastavuje jen `src`. Focal point se ztratil a fotky se centrovaly na `50% 50%`, což vede k ořezaným hlavám / špatné kompozici.

## Implementace

### krizky-photos

**Nový modul `krizky_photos/focal.py`** — vytáhli jsme normalizaci a načítání focal_points z pluginu do samostatného modulu s vlastními testy.

- `resolve_focal_points_path(photos_cfg, config_dir, sources_output) → (Path, explicit)` — priorita: config → default.
- `load_focal_points(...)` — čte + normalizuje. Vrací `dict` s klíči bez přípony. Vypisuje warningy pro legacy klíče (`"005.jpg"`) a pro duplicity po normalizaci (jen když se hodnoty liší). Zvedá `FocalPointsError` pouze pokud byla cesta explicitně nakonfigurovaná v `config.yaml` a soubor chybí / je nevalidní.
- `FocalPointsError` — vlastní výjimka.

**Kontrakt normalizace se přesunul z `PhotoContext` sem.** `context.py` dostává dict už normalizovaný, `Path(k).stem` odtud zmizel. `PhotoContext` má nyní property `focal_points` pro čtení.

**`plugin.py`:**
- Nová instance state `self._focal_points` (potřeba pro cross-hook sdílení dat mezi `prepare_jinja2_environment` a `inject_head`).
- V `prepare_jinja2_environment` se focal_points načítají přes `load_focal_points`; `FocalPointsError` se přehazuje na `click.ClickException` (build se zastaví).
- **Nový hook `inject_head`** — pokud jsou focal_points nenulové, injektuje `<script>window.krizkyPhotos={"focalPoints":{...}};</script>` do `<head>` každé stránky. Vypnutí je automatické, když jsou focal_points prázdné (žádný overhead).

**Config klíč `sources.photos.focal_points`** — volitelná cesta relativní k `config.yaml` (stejná konvence jako `transform: ./transforms/data.sh`).

### krizky-filters

**`filters.js` handler `data-field-photo`** — 2 řádky navíc:
```js
const focal = window.krizkyPhotos?.focalPoints?.[paddedId];
if (focal) el.style.objectPosition = focal;
```
Optional chaining znamená, že filters nadále funguje samostatně bez photos pluginu.

### Testy

- Nový `test_focal.py` (14 testů) — `resolve_focal_points_path`, `load_focal_points` (default vs. explicit, missing, invalid JSON, non-dict), `_normalize` (extension stripping, variant suffixes, warnings).
- Nový `test_plugin.py` (5 testů) — `inject_head` bez focal_points, s focal_points, `prepare_jinja2_environment` s configurovanou cestou, propagace `ClickException` při chybějícím explicit path.
- V `test_photo_context.py` odstraněn `test_focal_point_key_with_extension` (funkčnost se přesunula do `test_focal.py`).

## Změněné/vytvořené soubory

**Vytvořeno:**
- `_plugins/krizky-photos/krizky_photos/focal.py`
- `_plugins/krizky-photos/tests/test_focal.py`
- `_plugins/krizky-photos/tests/test_plugin.py`
- `work/2026-08-12-01-focal-points-configurable-and-js.md`

**Změněno:**
- `_plugins/krizky-photos/krizky_photos/context.py` — normalizace odstraněna, nová property `focal_points`.
- `_plugins/krizky-photos/krizky_photos/plugin.py` — nový `inject_head`, `_focal_points` state, delegace na `focal.load_focal_points`.
- `_plugins/krizky-photos/README.md` — sekce "Ohniska fotek" rozšířena o config klíč a JS runtime.
- `_plugins/krizky-photos/tests/test_photo_context.py` — odstraněn 1 test (přesunutý do `test_focal.py`).
- `_plugins/krizky-filters/krizky_filters/assets/krizky-filters/filters.js` — aplikace `objectPosition` v `data-field-photo` handleru.
- `_plugins/krizky-filters/docs/card-template.md` — zmíněna spolupráce s krizky-photos.

## Výsledky testů

```
_plugins/krizky-photos/tests/   60 passed
_plugins/krizky-filters/tests/  45 passed
krizky/tests/                   88 passed
```

## Technické poznámky

- **Signatura `inject_head(page_cfg, config)`** neobsahuje `config_dir`, takže focal_points nelze načíst až tam. Proto se load provádí v `prepare_jinja2_environment` (kde `config_dir` je) a výsledek se cache-uje na instanci pluginu.
- **Cross-plugin coupling** filters ↔ photos je *runtime-only* přes `window.krizkyPhotos`. Filters plugin nemá žádnou Python závislost na krizky-photos.
- **Velikost inline JSON** — pro aktuální dataset s ~1500 klíči je payload ~40 kB (gzip ~10 kB). Injektuje se do každé stránky, kde je `sources.photos` a existují focal_points. Pokud by to začalo vadit, snadný přechod na variantu B (statický `/krizky-photos/focal_points.json` + async fetch v JS).
- **Backward compat**: šablony bez `_picture.html` a stránky bez filters nadále fungují beze změny. Legacy focal_points s příponou (`"005.jpg"`) fungují, jen s warningem při načítání.
