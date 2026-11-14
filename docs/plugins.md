# Plugin systém

krizky podporuje rozšíření přes plugin systém postavený na [pluggy](https://pluggy.readthedocs.io/). Pluginy mohou přidávat Jinja2 filtry a globální proměnné, CLI příkazy a post-write akce (např. JSON export, generování search indexu).

---

## Jak napsat plugin

Plugin je Python objekt (instance třídy nebo modul) s metodami dekorovanými `@hookimpl`.

```python
from krizky.hooks import hookimpl


class MyPlugin:
    @hookimpl
    def prepare_jinja2_environment(self, env, config, config_dir):
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

### `prepare_jinja2_environment(env, config, config_dir)`

Voláno jednou před renderingem, po registraci core filtrů (`md`, `mdtext`, `strftime`). Vhodné pro přidání vlastních filtrů nebo globálních proměnných.

```python
@hookimpl
def prepare_jinja2_environment(self, env, config, config_dir):
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

### `copy_plugin_assets(output_dir, config, config_dir)`

Voláno **právě jednou za build**: po zkopírování assetů projektu (`site.assets`) a před vykreslením první stránky, tedy před prvním `after_page_written`. Plugin si proto nemusí hlídat, aby assety kopíroval jen jednou. Všechny implementace jsou zavolány, návratová hodnota se ignoruje.

- `output_dir`: absolutní cesta k výstupu webu,
- `config`: celý config,
- `config_dir`: adresář s `config.yaml`.

Assety pluginu patří do `output_dir/<jméno-pluginu>/`.

```python
from pathlib import Path

from krizky.hooks import hookimpl
from krizky.plugin_helpers import replace_tree


class MyPlugin:
    @hookimpl
    def copy_plugin_assets(self, output_dir, config, config_dir):
        replace_tree(Path(__file__).parent / "assets", output_dir / "myplugin")
```

Hook existuje od krizky 0.2.0. Starší core neznámý hookimpl tiše ignoruje, plugin proto má vyžadovat `krizky>=0.2`.

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

Assety kopíruj v `copy_plugin_assets`, ne v `after_page_written`. V `after_page_written` zůstávají jen soubory generované per stránka (CSV, sitemap a podobně).

---

## Pomocné funkce pro pluginy

Modul `krizky.plugin_helpers` obsahuje funkce, které pluginy jinak opakují.

### `register_plugin_templates(env, templates_dir)`

Vloží `FileSystemLoader(templates_dir)` do `ChoiceLoader` prostředí `env` hned za první loader (šablony projektu) a před vestavěné šablony core. Šablony projektu tak přebijí šablony pluginu a ty přebijí vestavěné. Opakované volání se stejnou cestou loader nepřidá znovu. Když `env.loader` není `ChoiceLoader`, funkce nic neudělá. Přijímá `str` i `Path`.

### `replace_tree(source, target)`

Zkopíruje adresář `source` do `target`. Když `target` existuje, nejdřív ho celý smaže, takže ve výstupu nezůstanou soubory, které plugin už nemá. Chybějící nadřazené adresáře `target` vytvoří.

### `resolve_path(path, config_dir) → Path | None`

Převede cestu z configu na absolutní `Path`. `None` nebo prázdný řetězec vrátí `None`. Relativní cestu vyhodnotí vůči `config_dir`, absolutní nechá na místě. Výsledek je vždy `.resolve()`. Přijímá `str` i `Path`.

### Příklad

```python
from pathlib import Path

from krizky.hooks import hookimpl
from krizky.plugin_helpers import register_plugin_templates, replace_tree, resolve_path

PLUGIN_DIR = Path(__file__).parent


class MyPlugin:
    @hookimpl
    def prepare_jinja2_environment(self, env, config, config_dir):
        register_plugin_templates(env, PLUGIN_DIR / "templates")

    @hookimpl
    def copy_plugin_assets(self, output_dir, config, config_dir):
        # volitelná cesta z configu, relativní k config.yaml
        custom = resolve_path(config.get("myplugin", {}).get("assets"), config_dir)
        replace_tree(custom or PLUGIN_DIR / "assets", output_dir / "myplugin")
```

### Konvence

- Assety pluginu patří do `output_dir/<jméno-pluginu>/`.
- Šablony pluginu leží v jeho adresáři `templates/`.

---

## Chyby v pluginech

Plugin smí v build hoocích vyhazovat vlastní výjimky (ne `click.ClickException`). `krizky build site` je nezobrazí jako syrový traceback, ale jedním červeným řádkem se jménem pluginu (nejvyšší balíček nebo modul, u lokálního pluginu jméno souboru bez `.py`):

```
Building site...
ERROR: krizky_photos: FocalPointsError: Neplatný focal point u fotky 007
Run with -v / --verbose to see the full traceback.
```

Celý traceback ukáže `krizky build site -v`. Výjimka vzniklá mimo kód pluginu se vypíše bez jména pluginu (`ERROR: RuntimeError: ...`). Příkaz skončí s exit kódem 1.

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


plugin = SitemapPlugin()
```
