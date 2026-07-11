# 2026-07-11-01 — Site generation (Fáze 3 + rozšíření)

## Co bylo implementováno

### Nové soubory

| Soubor | Popis |
|---|---|
| `krizky/site.py` | Orchestrace buildu: `build_site()`, `_generate()`, `_copy_assets()`, `_load_inline_css()`, `_load_docs()` |
| `krizky/db.py` | DB vrstva: `fetch_records()`, `fetch_table()`, `fetch_distinct_categories()`, `fetch_distinct_tags()`, `fetch_by_category()`, `fetch_by_tag()`, `parse_row()` (JSON auto-parse) |
| `krizky/render.py` | Renderovací utility: `render_config_str()`, `page_path()`, `render_paginated()` |
| `krizky/pages/__init__.py` | Dispatcher `process_page()` dle typu stránky |
| `krizky/pages/base.py` | `RenderContext` dataclass, `resolve_page_site()` |
| `krizky/pages/simple.py` | Prostá stránka (s volitelným query) |
| `krizky/pages/detail.py` | Detail stránka — jedna HTML per záznam |
| `krizky/pages/category.py` | Category stránka — jedna HTML per unikátní hodnotu kategorie (vč. `many: true` pro JSON listy) |
| `tests/test_site.py` | 33 testů pro site generation |
| `tests/test_db.py` | Testy DB vrstvy |

### Upravené soubory

| Soubor | Co se změnilo |
|---|---|
| `krizky/cli.py` | `krizky build site` plně implementován; šablona configu aktualizována |
| `krizky/config.py` | `validate_config()` rozšířena o povinné `site.title` |
| `README.md` | Aktualizována sekce `site`, kontext šablon, interpolace |
| `tests/test_config.py` | Testy aktualizovány pro nové validace |

## Klíčové rozhodnutí a konvence

### Kontext šablon — namespace

Proměnné jsou organizovány do tří namespace místo plochého top-level:

- `site.*` — konfigurační hodnoty (`title`, `description`, `language`, formátovací řetězce)
- `build.*` — build-time hodnoty (`last_update`, `assets_url`, `inline_css`)
- `pagination.*` — stránkování (`page`, `total_pages`, `has_prev`, `has_next`, `prev_url`, `next_url`, `paginated`)

Top-level zůstávají: `tables`, `docs`, `filtered`, `record`, `category`.

### Interpolace v config hodnotách

Původní `<col>` notace nahrazena Jinja2 syntaxí. `path`, `title`, `language` v page configu jsou Jinja2 šablony:

```yaml
path: "/{{ record.slug }}.html"
title: "{{ record.nazev }} — Web"
path: "/{{ category.slug }}.html"
title: "{{ tables.typy[record.typ_slug].nazev }}"  # cross-table
```

Renderování probíhá přes `render_config_str()` v odděleném `jinja2.Environment(autoescape=False)`.

### Page-level override `title` a `language`

Na úrovni pages lze přetížit `site.title` a `site.language`. Přetížená hodnota je Jinja2 šablona s přístupem k `record`, `tables`, `category`. Implementováno v `resolve_page_site()`.

### `inline_css`

Obsah `<assets>/css/style.css` se čte při buildu a předává do šablon jako `build.inline_css` — pro performance inlining CSS bez externího requestu.

## Výsledky testů

```
46 passed in 0.17s
```

`tests/test_site.py` (33 testů) + `tests/test_config.py` (13 testů) + ostatní.
