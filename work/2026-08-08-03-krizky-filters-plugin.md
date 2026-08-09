# 2026-08-08-03 — krizky-filters plugin

## Co bylo implementováno

### Core změny (`krizky`)

**Dva nové hookspecy** v `krizky/hooks.py`:
- `inject_head(page_cfg, config) -> str | None` — HTML pro vložení do `<head>`
- `inject_body_end(page_cfg, config) -> str | None` — HTML pro vložení před `</body>`

Hooky jsou volány jednou per page config entry (ne per vygenerovaný HTML soubor). Výsledky všech implementací se concatenuji.

**`krizky/pages/base.py`** — `RenderContext` rozšířen o:
```python
head_injections: str = ""
body_end_injections: str = ""
```

**`krizky/site.py`** (`_generate()`) — před každým `process_page()` se zavolají nové hooky a výsledky se předají do `RenderContext`.

**Tři page procesory** (`simple.py`, `category.py`, `detail.py`) — předávají `head_injections` a `body_end_injections` jako template proměnné do Jinja2 kontextu.

Template autoři přidají do base layoutu:
```html
{{ head_injections | safe }}   {# v <head> #}
{{ body_end_injections | safe }}  {# před </body> #}
```

### Nový plugin `_plugins/krizky-filters/`

Plugin implementuje in-browser filtrování jako **progressive enhancement**:
- No-JS vrstva: pill-tlačítka zůstávají jako `<a href>` na statické category pages
- JS vrstva: interceptuje kliky, načte filter JSON, filtruje v prohlížeči, re-renderuje přes `<template>` klonování

**Config:**
```yaml
pages:
  vsechna_mista:
    card_template: _karta.html     # partial pro JS klonování
    filters:
      fields: [slug, nazev, ...]   # pole pro filter JSON (rezervovaný klíč)
      typ: {label: Typ, type: select, fallback_url: "/typy/{slug}.html"}
      stitky: {label: Štítek, type: multiselect, many: true}
```

**Filtrovací logika:** AND uvnitř dimenze i AND mezi dimenzemi.
- `many: false`: max 1 aktivní hodnota (select UI) → AND trivially satisfied
- `many: true`: record musí obsahovat VŠECHNY vybrané hodnoty

**Plugin hooky:**
- `prepare_jinja2_environment` — přidá plugin templates do Jinja2 loaderu
- `extra_template_vars` — vrátí `page_filters` dict (distinct hodnoty per dimenze per stránka, keyed by page_name)
- `inject_head` — CSS link tag pro stránky s `filters:`
- `inject_body_end` — filter config JSON + JS script tag
- `after_page_written` — generuje `output/jsons/{stem}-filter.json`, kopíruje assets

**Šablony (overrideable):**
- `_filter_widget.html` — dispatcher iterující dimenze
- `_filter_widget_select.html` — widget pro `type: select`
- `_filter_widget_multiselect.html` — widget pro `type: multiselect`
- Nový typ = nový soubor `_filter_widget_{type}.html` (bez změny kódu)
- `_filter_card_template.html` — wrappuje card partial do `<template id="card-template">`

**JS** (`filters.js`) — vanilla ES2020:
- Parsuje filter config z `#filter-config` scriptu
- Fetchuje filter JSON
- Čte/zapisuje stav do URL query params (`?typ=kriz&stitky=baroko,hrbitov`)
- Klik na pill: `preventDefault`, toggle state, `history.pushState`, re-filter+render
- `popstate`: back/forward tlačítka prohlížeče fungují
- Klonuje `<template id="card-template">`, plní `data-field` atributy

**Assets URL:** `/krizky-filters/filters.{js,css}` (plugin kopíruje přímo do `output_dir/krizky-filters/`, nezávisle na user's assets config)

## Soubory vytvořeny/změněny

### Změněno (core)
- `krizky/hooks.py` — 2 nové hookspecy
- `krizky/pages/base.py` — 2 nová pole v RenderContext
- `krizky/site.py` — volání nových hooků v `_generate()`
- `krizky/pages/simple.py` — předání injections do extra_ctx
- `krizky/pages/category.py` — totéž
- `krizky/pages/detail.py` — totéž

### Vytvořeno (plugin)
- `_plugins/krizky-filters/pyproject.toml`
- `_plugins/krizky-filters/krizky_filters/__init__.py`
- `_plugins/krizky-filters/krizky_filters/plugin.py`
- `_plugins/krizky-filters/krizky_filters/values.py`
- `_plugins/krizky-filters/krizky_filters/json_gen.py`
- `_plugins/krizky-filters/krizky_filters/templates/_filter_widget.html`
- `_plugins/krizky-filters/krizky_filters/templates/_filter_widget_select.html`
- `_plugins/krizky-filters/krizky_filters/templates/_filter_widget_multiselect.html`
- `_plugins/krizky-filters/krizky_filters/templates/_filter_card_template.html`
- `_plugins/krizky-filters/krizky_filters/assets/krizky-filters/filters.js`
- `_plugins/krizky-filters/krizky_filters/assets/krizky-filters/filters.css`
- `_plugins/krizky-filters/tests/test_filter_plugin.py` (25 testů)

## Výsledky testů

- Core suite: **88 passed** (beze změny)
- Plugin suite: **25 passed**

## Technické poznámky

- `fetch_distinct_categories` / `fetch_distinct_tags` třídí alfabeticky (pořadí pills nerespektuje site `order_by`)
- Plugin assets URL je hardcoded `/krizky-filters/` — nezávislé na `assets_url` v config (nevhodné pro CDN)
- AND uvnitř dimenze pro `many: false` s více hodnotami vrátí 0 výsledků (pole nemůže mít 2 hodnoty)
- Stránkování s aktivním JS filtrem: vždy začíná od str. 1; statické `/mista-2.html` se ignoruje
