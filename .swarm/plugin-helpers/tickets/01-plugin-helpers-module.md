---
id: "01"
slug: plugin-helpers-module
title: Modul krizky/plugin_helpers.py s pomocnými funkcemi pro pluginy
status: pending
depends_on: []
files:
  - krizky/plugin_helpers.py
  - tests/test_plugin_helpers.py
attempts: 0
pr: ""
---

## Cíl
Pluginy map, share, filters a photos si dnes samy registrují šablony do Jinja2, kopírují assety do výstupu a převádějí cesty z configu na absolutní. Nový modul `krizky/plugin_helpers.py` nabídne tři veřejné funkce, které tyhle opakované části nahradí: `register_plugin_templates`, `replace_tree` a `resolve_path`. Specifikace `.swarm/plugin-helpers/spec.md`, část 2. Dokumentaci funkcí v `docs/plugins.md` dopíše tiket 02, tady jen kód, docstringy a testy.

## Akceptační kritéria
- Nový soubor `krizky/plugin_helpers.py` s modulovým docstringem a třemi veřejnými funkcemi. Každá má docstring (co dělá, argumenty, návratová hodnota) a typové anotace.
- `register_plugin_templates(env, templates_dir)`:
  - pokud `env.loader` je `jinja2.ChoiceLoader`, vloží `jinja2.FileSystemLoader(templates_dir)` do `env.loader.loaders` na index 1 (hned za první loader = šablony projektu, před ostatní = vestavěné šablony core),
  - opakované volání se stejnou cestou loader nepřidá znovu (porovnání cest přes `FileSystemLoader.searchpath`, normalizuj `str`/`Path`),
  - pokud `env.loader` není `ChoiceLoader` (nebo je `None`), nic neudělá a nevyhodí výjimku,
  - přijímá `str` i `Path`.
- `replace_tree(source, target)`: když `target` existuje, celý ho smaže (`shutil.rmtree`), chybějící nadřazené adresáře vytvoří a zkopíruje `source` do `target` (`shutil.copytree`). Přijímá `str` i `Path`.
- `resolve_path(path, config_dir)`: `None` nebo `""` vrátí `None`; relativní cestu vyhodnotí vůči `config_dir` a vrátí `.resolve()`; absolutní cestu vrátí jako `Path(path).resolve()`. Přijímá `str` i `Path`. Návratový typ `Path | None`.
- Žádný jiný kód core se nemění (core helpery sám nepoužívá, viz „Mimo rozsah“ ve specifikaci).
- `scripts/verify` projde.

## Testy
Napiš je nejdřív, v novém `tests/test_plugin_helpers.py`:
- `register_plugin_templates`:
  - prostředí s `ChoiceLoader([FileSystemLoader(projekt), FileSystemLoader(vestavene)])` (adresáře v `tmp_path`); po volání jsou `searchpath` loaderů v pořadí projekt, plugin, vestavěné,
  - šablona stejného jména ve všech třech adresářích: `env.get_template` vrátí verzi projektu; šablona jen v pluginu a ve vestavěných vrátí verzi pluginu,
  - dvojí volání se stejnou cestou (jednou jako `str`, jednou jako `Path`) přidá loader jen jednou,
  - `Environment(loader=FileSystemLoader(...))` i `Environment()` bez loaderu zůstanou beze změny (loader je stejný objekt).
- `replace_tree`: zkopíruje soubory i podadresáře; soubor, který byl v `target` a není v `source`, po volání neexistuje; funguje, když `target` ani jeho rodič neexistují.
- `resolve_path`: `None` a `""` → `None`; relativní `str` i `Path` → `(config_dir / path).resolve()`; absolutní `str` i `Path` → stejná cesta po `.resolve()` (nezávisle na `config_dir`).

## Poznámky
- Pravidla v `docs/guidelines/python.md`: `from __future__ import annotations` je zakázaný (ruff TID251), anotace piš moderně (`str | Path`).
- Vzor dnešního kódu: `prepare_jinja2_environment` v `/Users/msgre/projects/muzeum/krizky-filters/krizky_filters/plugin.py` (a obdobně v krizky-map, krizky-share); kopírování assetů projektu v `_copy_assets` v `krizky/site.py`. Tyto soubory neměň, jen se inspiruj.
- Pozor na `resolve()` na macOS (`/tmp` → `/private/tmp`): v testech porovnávej s `.resolve()` očekávané cesty.

## Otázky
