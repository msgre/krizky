# 2026-08-08-01 — Plugin systém

## Co bylo implementováno

Zavedení rozšiřitelného plugin systému postaveného na knihovně **pluggy** (stejná jako pytest/datasette). Cíl: oddělit core funkcionalitu (generování statického webu) od specifičtějších funkcí, které mohou být pro různé projekty zbytečné.

---

## Nové soubory

### `krizky/hooks.py`

Definice 6 hookspeců (= veřejné API plugin systému):

| Hook | Sémantika | Kde se volá |
|---|---|---|
| `prepare_jinja2_environment(env, config)` | přidat filtry/globály do Jinja2 env | `site.py`, po vytvoření env |
| `extra_template_vars(config, config_dir, conn)` | vrátit dict pro merge do base_ctx | `site.py`, před renderingem |
| `register_commands(cli)` | přidat Click příkazy | `cli.py`, při startu modulu |
| `register_page_processor(page_cfg)` | vrátit PageProcessor nebo None (firstresult) | `pages/__init__.py` |
| `after_page_written(page_cfg, html_path, output_dir, records, config)` | post-write akce | každý page procesor |
| `after_sources_fetched(config, config_dir, sources_output)` | post-fetch akce | `fetch.py` |

Exportuje také `hookimpl` marker pro použití v pluginech.

### `krizky/plugin_manager.py`

Funkce `get_plugin_manager(config_dir=None) -> pluggy.PluginManager`.

Discovery pořadí (nejvyšší priorita první):
1. Lokální `plugins/` adresář vedle `config.yaml` — každý `*.py` musí mít `plugin` objekt s `@hookimpl` metodami
2. Nainstalované balíčky přes `[project.entry-points."krizky"]` v pyproject.toml
3. Built-in pluginy (vždy registrovány)

### `krizky/builtin_plugins.py`

`JsonExportPlugin` — `@hookimpl after_page_written` — přesunutá logika JSON exportu z page procesorů. Volá stávající funkce z `json_export.py`.

---

## Upravené soubory

### `krizky/pages/base.py`

`RenderContext` rozšířen o dvě optional pole:
- `pm: Any = None` — pluggy.PluginManager instance
- `config: dict = field(default_factory=dict)` — celý krizky config dict

Obě pole mají default, takže stávající testy nebylo potřeba měnit.

### `krizky/site.py`

- `build_site(config, config_dir, pm=None)` — přidán volitelný parametr; pokud None, vytvoří se přes `get_plugin_manager(config_dir)`
- Po vytvoření Jinja2 env: `pm.hook.prepare_jinja2_environment(env, config)`
- Po sestavení `base_ctx`: merge výsledků `pm.hook.extra_template_vars(...)`
- `pm` a `config` předány do `RenderContext`

### `krizky/pages/__init__.py`

`process_page()` nejprve zkusí pluginy (`pm.hook.register_page_processor(page_cfg)`), pak teprve core fallback (detail/category/simple). Pluginy tak mohou přidat nové typy stránek nebo přepsat stávající.

### `krizky/pages/simple.py`, `detail.py`, `category.py`

- Odstraněny přímé `if json_cfg is not None: write_json_*` bloky
- Nahrazeny `pm.hook.after_page_written(...)` voláním
- `json_export.py` zůstává beze změny (volá ho JsonExportPlugin)

Sémantika `after_page_written`:
- simple: fired 1× s `html_path=page_cfg["path"]`, `records`=vše
- category: fired 1× per kategorie s rendered path + filtered records
- detail: fired 1× per záznam s rendered path + `records=[record]`

### `krizky/fetch.py`

- `fetch_sources(..., pm=None)` — přidán volitelný parametr
- Na konci funkce: `pm.hook.after_sources_fetched(...)` pokud pm není None

### `krizky/cli.py`

- `fetch sources` příkaz: vytvoří pm s config_dir, předá do `_fetch_sources`
- Konec modulu: `get_plugin_manager().hook.register_commands(cli=cli)` pro entry-point pluginy (lokální `plugins/` není dostupný v tento moment — config_dir není znám)

### `pyproject.toml`

Přidána závislost `pluggy>=1.0`.

---

## Nové soubory v repozitáři

- `PLAN_PLUGIN.md` — implementační plán plugin systému (architektonická dokumentace)
- `docs/plugins.md` — uživatelská dokumentace plugin API

---

## Testy

138 testů, 138 prošlo. Žádný stávající test nebylo potřeba upravit — RenderContext má nová pole s defaulty, build_site má pm jako optional parametr.

---

## Architektonická rozhodnutí z diskuze

- **Google Sheets/Docs zůstávají v core** — jsou primárním use-case krizky; abstrakce DataSource by přinesla jen složitost
- **JSON export**: architektonicky refaktorován do JsonExportPlugin (stávající `json_cfg` bloky v page procesorech odstraněny), ale zůstává bundlovaný jako built-in plugin — diskutovalo se, zda ho přesunout do samostatného balíčku v souladu s principem "core ví jen o HTML"
- **Fotky**: beze změny v core — přesun do `krizky-photos` sibling package je plánován jako samostatný krok
- **`contribute_assets` hook**: identifikován jako budoucí potřeba pro pluginy, které přinášejí vlastní CSS/JS; zatím neimplementován
- **Config extension hook**: není potřeba — `page_cfg` je volný dict, pluginy čtou vlastní klíče přes `.get()` bez jakékoliv úpravy core; striktní validace by si ho vyžádala teprve v budoucnu
