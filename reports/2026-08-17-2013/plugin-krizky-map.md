# krizky-map — revize konzistence

Datum: 2026-08-17 20:13
Reviewer: Claude Code (review-consistency skill)

## Souhrn

- 0 blocker
- 6 recommended
- 3 nice-to-have

Nejdůležitější zjištění: `map.js` používá `var` a old-style function declarations, zatímco filters.js a share.js jsou ES6. `_copy_assets`, template registrace a config path resolution se opakují napříč map/share/filters (viz consolidation proposals). CSS design tokeny (`--surface`, `--hairline`, ...) coupling na projekt Valašské nebe — dokumentované, ale slabý bod. Přímý import `sources.photos.base_url` v `prepare_jinja2_environment` = cross-plugin coupling (soft).

## Zjištění

### Hraniční API

#### [recommended] Cross-plugin coupling: čte `sources.photos.base_url` z configu

**Kde:** `_plugins/krizky-map/krizky_map/plugin.py:143-144`

**Co:** Map plugin čte `config.get("sources", {}).get("photos", {}).get("base_url", "")`, tj. sahá do configu jiného pluginu (krizky-photos). Předává to do `photos_base_url` v `map_config` pro JS side panel (thumbnail composition).

**Proč vadí:** Nekonzistence: photos plugin vlastní `sources.photos.*` prostor, map do něj sahá bez formálního API. Kdyby photos přejmenoval `base_url` nebo zavedl novou hierarchii, map se rozbije.

**Doporučení:** Formalizovat: buď (a) photos vystavuje public helper (`from krizky_photos import get_photos_base_url(config)`) — map ho volá; (b) tuhle informaci dostává map jako parametr konfigurace `map.thumbnail_base_url`, nezávisle na photos; (c) zavést v core sdílený context, do kterého pluginy publikují data (nový hook `provide_shared_context`). Preferuji (b) — nejjednodušší a nejméně coupled.

### JavaScript style

#### [recommended] `map.js` používá `var` a old-style `function` declarations

**Kde:** `_plugins/krizky-map/krizky_map/assets/krizky-map/map.js` (429 řádků, celý soubor)

**Co:** `map.js` používá `var` skoro všude a preferuje `function name() {}` deklarace pro callbacks. `filters.js` (780 LOC) i `share.js` (89 LOC) jsou modern ES6 (`const`/`let`, arrow functions).

**Proč vadí:** Kód nevypadá "jako od jednoho autora". Rozdíl je viditelný na první pohled.

**Doporučení:** Postupný refactor `var` → `const`/`let` (relativně mechanická změna). Arrow functions pro krátké callbacks. Není potřeba dělat naráz — flag jako "žádosti PR reviewera při dalších editacích tohoto souboru".

### Python style

#### [recommended] Chybí `CLAUDE.md`

**Kde:** projekt kořen

**Co:** Konzistentně chybí napříč všemi 5 pluginy. Uvedeno per plugin, řešení jednotné (viz `proposals/config-style-guide.md` sekce dokumentace).

**Doporučení:** Přidat minimální `CLAUDE.md` s pokyny pro Claude: struktura kódu (`geojson.py`, `plugin.py`), jak testovat, konvence pro tile presety.

### Duplikace (viz consolidation proposal)

#### [recommended] Template registrace přes `ChoiceLoader` — duplikát v map/share/filters

**Kde:** `_plugins/krizky-map/krizky_map/plugin.py:131-140`

**Co:** ~10 řádků kódu pro vložení `FileSystemLoader` na správnou pozici. Stejný pattern v share (`plugin.py:68-78`) a filters (`plugin.py:99-112`).

**Doporučení:** Extrahovat do `krizky.plugin_helpers.register_plugin_templates(env, path)`. Viz `proposals/consolidation-to-core.md`.

#### [recommended] `_copy_assets` s per-instance guardem — duplikát v map/share/filters

**Kde:** `_plugins/krizky-map/krizky_map/plugin.py:333-359`

**Co:** Pattern `self._assets_copied: set[str]` + kopírování `plugin/assets/plugin-name/*` do `output/plugin-name/`. Map + share používají per-file `shutil.copy2`; filters používá `shutil.copytree`+`rmtree`. Různé sémantiky pro obsolete soubory (filters je maže, map/share ne).

**Doporučení:** Extrahovat + sjednotit sémantiku. Viz `proposals/consolidation-to-core.md` a `proposals/hook-changes.md` (varianta s novým hookem).

#### [recommended] `_resolve_source_path` — duplikát ve photos

**Kde:** `_plugins/krizky-map/krizky_map/plugin.py:361-368`

**Co:** Resolve relativní cesty vůči `config_dir`. Analogická funkce v `krizky-photos/focal.py`.

**Doporučení:** Konsolidovat do `krizky.config.resolve_path(path, config_dir)`.

### Konfigurace

#### [recommended] Config je částečně v `site.map`, částečně v per-page `map:` — dokumentovat pravidlo

**Kde:** `README.md:26-133` (site.map) + `README.md:113-132` (per-page map:)

**Co:** Site-level klíč (`site.map.tile`, `site.map.markers`, ...) drží defaulty a globální nastavení; per-page `map: true` nebo `map: {fields, lat_field, ...}` opt-in a page-specific override. Není to špatně, ale dokumentace pravidla "co patří kam" chybí — musí se odvodit z README příkladů.

**Proč vadí:** Nový uživatel neví, kdy má věc přidat na site-level a kdy na page-level. Analogický vzorec je v filters (per-page only) a photos (site-level jen v `sources.photos`).

**Doporučení:** Do config-style-guide (v `proposals/`) uvést pravidlo: **site-level = globální defaulty, per-page = opt-in flag a override**.

### Naming a data

#### [nice-to-have] Config: `fit_padding: [top, right, bottom, left]` — CSS shorthand order

**Kde:** `_plugins/krizky-map/README.md:97-102`, `plugin.py:214`

**Co:** Pole 4 čísel v CSS shorthand pořadí. README to vysvětluje jasně; kód taky. Konzistentní.

**Doporučení:** Držet. Zmiňuji jen protože je to zajímavé design decision — jinde v ekosystému se pole 4 čísel nepoužívá.

### Testy

#### [nice-to-have] Testy jsou dobře rozdělené (`test_plugin.py`, `test_macros.py`, `test_geojson.py`)

**Kde:** `_plugins/krizky-map/tests/`

**Co:** 768 LOC / 3 soubory. Dobrá struktura — hook implementace, template makra, GeoJSON logic testovány samostatně.

**Doporučení:** Použít jako model pro ostatní pluginy s víc modulech.

### Assety

#### [nice-to-have] Hardcoded Czech UI text v `map.js`

**Kde:** `_plugins/krizky-map/krizky_map/assets/krizky-map/map.js:248, 284, 329`

**Co:** Texty "Otevřít detail", "Vaše poloha" jsou v JS napevno. Nemají cestu k lokalizaci.

**Proč vadí:** Ekosystém je čs. produkt → OK; ale pro budoucí i18n potřeba. Konzistentní se share.js a filters.js (všechny mají hardcoded CZ texty).

**Doporučení:** Volitelné teď. Až se udělá i18n mechanism (např. plugin dostane překlady přes config), sjednotit napříč pluginy.
