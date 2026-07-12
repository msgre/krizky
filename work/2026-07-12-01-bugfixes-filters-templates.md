# 2026-07-12-01 — Opravy chyb, filtry, šablony

## Co bylo změněno

### Opravy chyb v `krizky/db.py`

- **SQLite TRIM neodstraňuje `\n`** — původní `TRIM()` bez druhého argumentu odstraňuje jen mezery (U+0020). Nahrazeno `TRIM(x, char(9)||char(10)||char(11)||char(12)||char(13)||char(32))` + Python-side `.strip()` ve všech čtyřech funkcích: `fetch_distinct_categories`, `fetch_distinct_tags`, `fetch_by_category`, `fetch_by_tag`.

- **`json_extract` s dot-path syntaxí selže pro klíče s tečkou** — hodnoty jako `"1. světová válka"` nebo `"1. polovina 20. století"` obsahují tečku, kterou SQLite interpretuje jako oddělovač vnořeného objektu v JSON path (`$.1. světová válka` → broken). SQLite bracket notace `$["key"]` není dostupná v SQLite < 3.38. Řešení: slug se teď vyhledává v Pythonu přes `json.loads` + `dict.get` místo `json_extract`.

### Nové Jinja2 filtry v `krizky/site.py`

- **`strftime`** — formátuje datum/čas; automaticky parsuje ISO string (`"2026-05-02"`) i Python `date`/`datetime` objekt. Používá se jako `{{ place.vytvoreno | strftime(site.date_format) }}`.

### Šablony (`temp/templates/`)

- **`_macros.html`** — nový sdílený soubor maker; sloučeny `karta` + `free_tag` (přesunuty z `karta.html`) a `breadcrumbs`. Soubor `karta.html` smazán, importy ve čtyřech šablonách aktualizovány.

- **`_category_list.html`** — nová základní šablona pro výpis kategorie (dědí z `base.html`). Obsahuje veškerou logiku mřížky, mapy, paginace. Definuje bloky `category_label` a `category_intro`. Breadcrumbs používají `self.category_label()` pro přístup k bloku child šablony.

- **`kategorie.html`, `stitek.html`, `obdobi.html`** — zredukovány na 7 řádků; dědí z `_category_list.html`, přepisují jen `category_label` a `category_intro`.

- **`render.py`** — `pagination.paginated` se teď nastavuje na `True` jen pokud `total_pages > 1` (oprava: dříve bylo vždy `True` při zapnuté paginaci).

## Výsledky testů

```
65 passed in 0.30s
```
