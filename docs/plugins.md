# Plugin systém

krizky podporuje rozšíření přes plugin systém postavený na [pluggy](https://pluggy.readthedocs.io/). Pluginy mohou přidávat nové typy stránek, Jinja2 filtry a globální proměnné, CLI příkazy, post-write akce (např. JSON export, generování search indexu) nebo reagovat na dokončení fetche.

---

## Jak napsat plugin

Plugin je Python objekt (instance třídy nebo modul) s metodami dekorovanými `@hookimpl`.

```python
from krizky.hooks import hookimpl

class MyPlugin:
    @hookimpl
    def prepare_jinja2_environment(self, env, config):
        env.globals["my_helper"] = lambda x: x.upper()

    @hookimpl
    def after_page_written(self, page_cfg, html_path, output_dir, records, config):
        # např. aktualizovat search index
        pass

plugin = MyPlugin()
```

Modul-level proměnná `plugin` je povinná pro lokální pluginy (discovery přes `plugins/` adresář). Pro instalovatelné balíčky viz sekci níže.

---

## Jak plugin zaregistrovat

### Lokální plugin (bez publishování)

Vlož soubor do adresáře `plugins/` vedle `config.yaml`:

```
my-project/
├── config.yaml
├── plugins/
│   └── search_index.py   ← plugin = SearchIndexPlugin()
└── templates/
```

Lokální pluginy mají **vyšší prioritu** než nainstalované balíčky.

### Instalovatelný balíček

Přidej do `pyproject.toml` svého balíčku:

```toml
[project.entry-points."krizky"]
myplugin = "myplugin:plugin"
```

Kde `myplugin:plugin` je `<modul>:<atribut>`. Po `pip install` se plugin automaticky načte.

---

## Dostupné hooky

### `prepare_jinja2_environment(env, config)`

Voláno jednou před renderingem, po registraci core filtrů (`md`, `mdtext`, `strftime`). Vhodné pro přidání vlastních filtrů nebo globálních proměnných.

```python
@hookimpl
def prepare_jinja2_environment(self, env, config):
    env.filters["muj_filter"] = lambda v: v.strip()
    env.globals["my_callable"] = MyCallable(config)
```

### `extra_template_vars(config, config_dir, conn) → dict | None`

Voláno jednou před renderingem. Vrátí dict, který se přidá do kontextu všech šablon. Více pluginů — dicts se mergují (poslední registrovaný vyhraje při kolizi klíčů).

```python
@hookimpl
def extra_template_vars(self, config, config_dir, conn):
    return {"my_data": load_something(conn)}
```

### `register_commands(cli)`

Voláno při startu CLI (importu modulu). Slouží pro přidání nových Click příkazů. Dostupné **jen pro nainstalované balíčky** — lokální `plugins/` není v tento moment načten (config_dir není znám).

```python
@hookimpl
def register_commands(self, cli):
    @cli.command("my-command")
    @click.pass_context
    def my_command(ctx):
        """Popis příkazu."""
        click.echo("Hello from plugin!")
```

### `register_page_processor(page_cfg) → PageProcessor | None`

Firstresult hook — první plugin, který vrátí nenulovou hodnotu, vyhraje. Core procesory (detail, category, simple) jsou fallback.

```python
@hookimpl
def register_page_processor(self, page_cfg):
    if page_cfg.get("feed"):
        return self._render_feed
    return None

def _render_feed(self, page_cfg, template, ctx):
    # vlastní logika renderování
    pass
```

### `after_page_written(page_cfg, html_path, output_dir, records, config)`

Voláno po zápisu každé logické stránky. Všechny implementace jsou zavolány.

**Sémantika dle typu stránky:**
- **simple**: fired 1× po renderování všech stránek (vč. paginace); `html_path` = base path z configu (např. `/mista.html`), `records` = všechny záznamy
- **category**: fired 1× per kategorie; `html_path` = rendered path (např. `/priroda.html`), `records` = filtrované záznamy kategorie
- **detail**: fired 1× per záznam; `html_path` = rendered path (např. `/kamen-u-lesa.html`), `records` = `[record]`

```python
@hookimpl
def after_page_written(self, page_cfg, html_path, output_dir, records, config):
    csv_cfg = page_cfg.get("csv")
    if csv_cfg is None:
        return
    # zapsat CSV sidecar soubor
    import csv
    from pathlib import PurePosixPath
    out = output_dir / "exports" / PurePosixPath(html_path.lstrip("/")).with_suffix(".csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        if records:
            w = csv.DictWriter(f, fieldnames=records[0].keys())
            w.writeheader()
            w.writerows(records)
```

### `after_sources_fetched(config, config_dir, sources_output)`

Voláno na konci `krizky fetch sources` po dokončení všech fetchů a transformací. Vhodné pro post-processing dat, validaci nebo warmup cache.

```python
@hookimpl
def after_sources_fetched(self, config, config_dir, sources_output):
    db_path = sources_output / config["sources"]["database"]
    # např. vybudovat search index z čerstvé DB
```

---

## Rozšíření config.yaml

Vlastní klíče v `page_cfg` jsou automaticky podporovány — krizky předává celý dict stránky do hooků bez validace neznámých klíčů. Plugin může definovat libovolné klíče:

```yaml
pages:
  export:
    path: /vsechna-mista.html
    template: mista.html
    csv:               # vlastní klíč JSON/CSV pluginu
      fields: [slug, nazev, latitude, longitude]
    json:              # klíč JsonExportPlugin
      fields: [slug, nazev, latitude, longitude]
      pretty: true
```

---

## Built-in pluginy

### `JsonExportPlugin`

Vždy registrován. Generuje JSON sidecar soubory pro stránky s klíčem `json:` v page configu.

Výstup: `<output>/jsons/<stejné jméno jako HTML>.json`

```yaml
pages:
  vsechna_mista:
    path: /mista.html
    template: mista.html
    json:
      fields: [slug, nazev, latitude, longitude]
      exclude: [interni_pole]
      pretty: true
```

---

## Příklad: plugin pro sitemap.xml

```python
# plugins/sitemap.py
from pathlib import Path
from krizky.hooks import hookimpl


class SitemapPlugin:
    def __init__(self):
        self._urls = []

    @hookimpl
    def after_page_written(self, page_cfg, html_path, output_dir, records, config):
        base_url = config.get("site", {}).get("base_url", "").rstrip("/")
        self._urls.append(f"{base_url}{html_path}")

    @hookimpl
    def after_sources_fetched(self, config, config_dir, sources_output):
        # reset při každém novém fetchi
        self._urls = []


plugin = SitemapPlugin()
```
