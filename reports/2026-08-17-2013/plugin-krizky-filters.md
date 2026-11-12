# krizky-filters — revize konzistence

Datum: 2026-08-17 20:13
Reviewer: Claude Code (review-consistency skill)

## Souhrn

- 1 blocker
- 6 recommended
- 3 nice-to-have

Nejdůležitější zjištění: Config klíče `pagination_window`/`pagination_boundary` (Python snake_case) se v JS objevují jako `window`/`boundary` — přejmenované + zkrácené → blocker. Třída se jmenuje `FilterPlugin` (singular) zatímco package/directory jsou `krizky-filters` (plural). Chybí `from __future__ import annotations` (jediný outlier). Chybí logger, chybí `PLAN.md`. Duplikát template registrace, `_copy_assets` (viz consolidation proposal).

## Zjištění

### JavaScript style / Python↔JS naming

#### [blocker] Config klíče `pagination_window` → `window` a `pagination_boundary` → `boundary` — přejmenované, ne jen camelCase

**Kde:** `_plugins/krizky-filters/krizky_filters/plugin.py:84-85` (Python straně), `_plugins/krizky-filters/krizky_filters/assets/krizky-filters/filters.js:37-38` (JS straně)

**Co:** Python čte `site_cfg.get("pagination_window", 2)` a `site_cfg.get("pagination_boundary", 1)`, ale do JS configu pošle jako klíče `"window"` a `"boundary"`. JS pak čte `config.window` a `config.boundary`.

**Proč vadí:** Kolize s built-in JS `window` (globální objekt) — matoucí čtení kódu. Uživatel, který vidí `config.window`, si nespojí s Python `pagination_window`. Není to čistě transformace snake_case → camelCase (jako u ostatních klíčů), ale přejmenování. Označuji jako blocker, protože je to reálný footgun (kolize s `window` globálem) a udělá se to jednorázově.

**Doporučení:** Přejmenovat v JS na `paginationWindow` a `paginationBoundary` (konzistentní kebab-to-camel jako ostatní klíče v tom samém configu — `jsonUrl`, `basePath`, `pageSize`). Python straně změnit hodnotu klíče v `_build_filter_config()`:
```python
"paginationWindow": site_cfg.get("pagination_window", 2),
"paginationBoundary": site_cfg.get("pagination_boundary", 1),
```
JS straně:
```javascript
const paginationWindow = config.paginationWindow ?? 2;
const paginationBoundary = config.paginationBoundary ?? 1;
```

### Python style

#### [recommended] Chybí `from __future__ import annotations` (jediný plugin bez toho)

**Kde:** `_plugins/krizky-filters/krizky_filters/plugin.py:1-15` (header)

**Co:** Photos, json, map, share plugin.py — všechny mají `from __future__ import annotations`. Filters ne.

**Proč vadí:** Nekonzistence napříč ekosystémem. Bez importu jsou type hinty vyhodnocované eagerly, což znamená potenciální problém s forward references.

**Doporučení:** Přidat na první řádek za docstring:
```python
"""krizky-filters plugin — in-browser filtering via progressive enhancement."""

from __future__ import annotations
```

#### [recommended] Třída `FilterPlugin` (singular) vs. package `krizky_filters` (plural)

**Kde:** `_plugins/krizky-filters/krizky_filters/plugin.py:92`, package `krizky_filters`

**Co:** Ostatní pluginy jsou konzistentní: `PhotosPlugin`/`krizky_photos`, `MapPlugin`/`krizky_map`, `SharePlugin`/`krizky_share`, `JsonExportPlugin`/`krizky_json`. Filters má nesoulad — třída singular, package plural.

**Proč vadí:** Malý drobný nesoulad, ale při skenu ekosystému rušivý. Ostatní pluginy mají class name ~ package name.

**Doporučení:** Přejmenovat `FilterPlugin` → `FiltersPlugin`. Je to plugin-internal třída (uživatel vidí jen `plugin` instanci), takže migrace je jednoduchá. Zvážit i entry-point label:
```toml
[project.entry-points."krizky"]
filters = "krizky_filters.plugin:plugin"  # už teď plural
```

#### [recommended] Chybí logger

**Kde:** `_plugins/krizky-filters/krizky_filters/plugin.py` (celý)

**Co:** Photos, map, share mají `_log = logging.getLogger(__name__)`. Filters a json nemají.

**Proč vadí:** Když se něco nepovede tiše (např. dimension config je špatný), uživatel nemá stopu.

**Doporučení:** Přidat modul-level `_log = logging.getLogger(__name__)`. Použít při warning nebo debug o filter configu.

### Hraniční API

#### [recommended] Cross-plugin coupling: čte `sources.photos.base_url`

**Kde:** `_plugins/krizky-filters/krizky_filters/plugin.py:76`

**Co:** Filters čte `config.get("sources", {}).get("photos", {}).get("base_url", "")` — stejný pattern jako map. Sahá do configu jiného pluginu bez formálního API.

**Proč vadí:** Viz `plugin-krizky-map.md` — analogický problém.

**Doporučení:** Stejné řešení jako pro map: (a) photos vystavuje helper, (b) filters dostává `photos_base_url` v vlastním configu, nebo (c) zavést sdílený context v core. Preferuji (b).

### Dokumentace

#### [recommended] Chybí `PLAN.md` (jediný plugin bez něj)

**Kde:** projekt kořen

**Co:** Photos, map, share, json mají `PLAN.md`. Filters nemá.

**Proč vadí:** Filters je jeden z nejsložitějších pluginů (extensive JS + JSON gen + facet counting). Bez PLAN.md je architekturní přehled roztroušen v README + `docs/` + TODO.md.

**Doporučení:** Přidat stručný `PLAN.md` (~50 řádků) s architekturní roadmapou: proč in-browser vs SSR, jak funguje AND-OR logika, kde jsou hlavní extension points.

#### [recommended] Chybí `CLAUDE.md`

**Kde:** projekt kořen

**Co:** Konzistentně chybí napříč pluginy.

**Doporučení:** Přidat minimální `CLAUDE.md`.

### Konfigurace

#### [recommended] Config klíče `pagination_window`/`pagination_boundary` v `site.*` (globální), ne v `filters:` per-page

**Kde:** `_plugins/krizky-filters/krizky_filters/plugin.py:84-85`, čte z `config["site"]`

**Co:** Filters je jinak per-page plugin — všechna config je v `pages.<X>.filters:`. Ale pagination_window/boundary čte ze site-level (`site.pagination_window`). To je nesoulad — jak globální kontrola pagination shrinkage, kterou dělá filters plugin, patří do plugin-owned prostoru.

**Proč vadí:** Uživatel, který hledá "co filters dělá", najde `filters:` na page, ale nezjistí, že plugin čte i `site.pagination_window`. Kdyby site.pagination_window existovala jako obecná pagination_window (kterou používá i core paginátor), byl by to sdílený config — ale v core `krizky/site.py` je paginační logic asi jinde a tyhle klíče se nepoužívají globálně.

**Doporučení:** Přesunout do `pages.<X>.filters.pagination_window` a `pages.<X>.filters.pagination_boundary`, nebo pokud jde o skutečně globální (napříč všemi filter stránkami sdílenou) hodnotu, dát pod `site.filters.pagination_window`. Preferuji per-page — konzistentní se zbytkem plugin scope.

### Duplikace (viz consolidation proposal)

#### [recommended] Template registrace, `_copy_assets` — patterny sdílené s map a share

**Kde:** `_plugins/krizky-filters/krizky_filters/plugin.py:99-112, 174-182`

**Co:** Viz `plugin-krizky-map.md` a `proposals/consolidation-to-core.md`.

**Poznámka:** Filters používá `shutil.rmtree` + `shutil.copytree` pro celé assets tree, zatímco map/share používají per-file `shutil.copy2`. Filters je "agresivnější" — smaže cokoli, co v cílovém dir zbylo. Diverging sémantika.

### JavaScript style

#### [nice-to-have] `filters.js` má hardcoded CZ pagination text

**Kde:** `_plugins/krizky-filters/krizky_filters/assets/krizky-filters/filters.js:597, 601, 613`

**Co:** "předchozí", "další", "Stránkování" napevno.

**Doporučení:** Konzistentní s map/share (všechny mají hardcoded CZ). Řešit až se udělá i18n.

### Testy

#### [nice-to-have] 650 LOC testů — heavy fixture use přes `@pytest.fixture`

**Kde:** `_plugins/krizky-filters/tests/test_filter_plugin.py`

**Co:** Jediný test file, ale s bohatými pytest fixtures (`conn`, `conn_tags`, `minimal_config`). Ostatní pluginy nevyužívají `@pytest.fixture` tak výrazně.

**Proč vadí:** Neni to špatně, ale je to unikátní styl. Nový přispěvatel, který se učí na test_plugin.py z jiného pluginu, se pak zde ztratí.

**Doporučení:** Volitelné. Zvážit rozdělení do víc souborů (`test_config.py`, `test_dimensions.py`, `test_json_gen.py`) — konzistentní s krizky-map (3 soubory).

### Dokumentace (drobnost)

#### [nice-to-have] `docs/` obsahuje víc souborů, což je unikátní pattern

**Kde:** `_plugins/krizky-filters/docs/` (4 soubory: configuration.md, widgets.md, javascript.md, card-template.md)

**Co:** Jediný plugin s vlastním `docs/`. Ostatní mají všechno v README.

**Proč vadí:** Nekonzistence, ale zde je opodstatnitelné — filters je nejsložitější plugin.

**Doporučení:** Držet. Do config-style-guide (v `proposals/`) uvést pravidlo "docs/ subfolder jen když README překročí ~300 řádků nebo když plugin má fyzicky odlišné tématické okruhy".
