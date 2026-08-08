# Plugin systém pro krizky — implementační plán

## Přehled

Zavedení plugin systému postaveného na **pluggy** (stejná knihovna jako pytest/datasette). Cílem je oddělit core funkcionalitu (static site generation) od specifické funkcionality (foto pipeline, JSON export) tak, aby krizky mohl přijímat příspěvky od komunity aniž by se core rozrůstal.

## Architektura

```
krizky/
├── hooks.py            # KrizkySpec — definice 6 hookspeců
├── plugin_manager.py   # get_plugin_manager() — discovery + registrace
├── builtin_plugins.py  # JsonExportPlugin (vždy dostupný, bez extra deps)
└── ...
```

### Šest hooků

| Hook | Soubor | Sémantika |
|---|---|---|
| `prepare_jinja2_environment(env, config)` | `site.py` | all; přidat filtry/globály do Jinja2 env |
| `extra_template_vars(config, config_dir, conn)` | `site.py` | all; vrátí dict pro merge do base_ctx |
| `register_commands(cli)` | `cli.py` | all; přidat Click příkazy (jen entry-point pluginy) |
| `register_page_processor(page_cfg)` | `pages/__init__.py` | firstresult; nový typ stránky |
| `after_page_written(page_cfg, html_path, output_dir, records, config)` | page procesory | all; post-write akce (JSON, search index…) |
| `after_sources_fetched(config, config_dir, sources_output)` | `fetch.py` | all; post-fetch akce |

### Plugin discovery (pořadí priority)

1. Lokální `plugins/` adresář vedle `config.yaml` — per-projekt, bez publishování
2. Nainstalované balíčky přes `[project.entry-points."krizky"]`
3. Built-in pluginy (vždy registrovány)

### Built-in pluginy

- **JsonExportPlugin** — přesunutá logika z page procesorů; aktivuje se přítomností `json:` v page config

## Dělící čára: core vs. plugin

### Zůstává v core

- config, db, query, render, markdown, pages (simple/detail/category), site orchestrátor
- Google Sheets + Docs fetching (primární use-case krizky)
- Základní CLI příkazy: validate, init, fetch sources, build site

### Stávající funkcionalita přesunutá na plugin (tento plán)

- JSON export → `JsonExportPlugin` v `builtin_plugins.py` (vždy k dispozici, jen jinak strukturováno)

### Plánované pluginy do budoucna (mimo scope tohoto plánu)

- `krizky-photos` — celý foto pipeline (GDrive → Pillow → CF R2), sibling package

## Implementační kroky

### Krok 1.1 — Infrastruktura (zero behavior change)

- [ ] `uv add pluggy`
- [ ] Vytvořit `krizky/hooks.py` — `KrizkySpec` se 6 hookspecs, `hookimpl` marker
- [ ] Vytvořit `krizky/plugin_manager.py` — `get_plugin_manager(config_dir=None)`
- [ ] Vytvořit `krizky/builtin_plugins.py` — `JsonExportPlugin`

### Krok 1.2 — Rozšíření RenderContext

- [ ] `krizky/pages/base.py`: přidat `pm: pluggy.PluginManager | None = None` a `config: dict = field(default_factory=dict)`

### Krok 1.3 — Thread pm + wire hook calls

- [ ] `krizky/site.py`: `build_site(config, config_dir, pm=None)` — vytvoří pm pokud None; wire `prepare_jinja2_environment` + `extra_template_vars`; předá `pm` a `config` do `RenderContext`
- [ ] `krizky/pages/__init__.py`: wire `register_page_processor` (plugins first, pak core fallback)
- [ ] `krizky/pages/simple.py`: wire `after_page_written`, odstranit `json_cfg` blok
- [ ] `krizky/pages/detail.py`: wire `after_page_written`, odstranit `json_cfg` blok
- [ ] `krizky/pages/category.py`: wire `after_page_written`, odstranit `json_cfg` blok
- [ ] `krizky/fetch.py`: `fetch_sources(..., pm=None)` — wire `after_sources_fetched`
- [ ] `krizky/cli.py`: create pm s config_dir v subpříkazech; wire `register_commands` na module level

## Signatura after_page_written

```
page_cfg     — page config dict z config.yaml
html_path    — logická HTML cesta jako string (např. "/mista.html"); pro JSON path výpočet
output_dir   — Path výstupního adresáře
records      — list[dict] záznamů na této logické stránce
config       — celý krizky config dict
```

**Simple pages**: hook fired 1× s `html_path=page_cfg["path"]`, `records`=vše  
**Category pages**: hook fired 1× per kategorie s rendered path + filtered records  
**Detail pages**: hook fired 1× per záznam s rendered path + `records=[record]`

## Jak psát plugin

```python
# plugins/myplugin.py  (lokální) nebo nainstalovaný balíček

from krizky.hooks import hookimpl

class MyPlugin:
    @hookimpl
    def prepare_jinja2_environment(self, env, config):
        env.globals["my_helper"] = lambda x: x.upper()

    @hookimpl
    def after_page_written(self, page_cfg, html_path, output_dir, records, config):
        # např. generovat search index
        pass

plugin = MyPlugin()
```

Pro nainstalovaný balíček přidat do `pyproject.toml`:
```toml
[project.entry-points."krizky"]
myplugin = "myplugin:plugin"
```

## Testování

```bash
uv run pytest                    # všechny testy musí projít
uv run pytest tests/test_site.py # site generation
uv run pytest tests/test_json_export.py  # JSON export přes plugin
```

JSON export testy by měly projít bez změny — JsonExportPlugin produkuje identický výstup jako původní json_cfg bloky.
