# 2026-08-08-02 — Extrakce krizky-json a krizky-photos do samostatných pluginů

## Co bylo implementováno

Fotky a JSON export byly extrahovány z krizky core do samostatných instalovatelných balíčků uložených v `/workspace/_plugins/` (určeno k publikování jako separátní GitHub repozitáře).

---

## Nové balíčky

### `_plugins/krizky-json/`

Plugin pro generování JSON sidecar souborů vedle HTML stránek.

| Soubor | Obsah |
|---|---|
| `PLAN.md` | architektonický plán extrakce |
| `pyproject.toml` | závisí pouze na `krizky>=0.1`, entry point `krizky_json.plugin:plugin` |
| `krizky_json/plugin.py` | `JsonExportPlugin` s `@hookimpl after_page_written` + inlinovaná JSON logika |
| `tests/test_json_plugin.py` | přesunuté testy z `krizky/tests/test_json_export.py` |

### `_plugins/krizky-photos/`

Plugin pro celou foto pipeline: GDrive → resize/convert → Cloudflare R2.

| Soubor | Obsah |
|---|---|
| `PLAN.md` | architektonický plán včetně popisu všech změn v core |
| `pyproject.toml` | závislosti: Pillow, boto3, google-api-python-client, krizky>=0.1 |
| `krizky_photos/build.py` | přejmenovaný `krizky/build_photos.py` (beze změny logiky) |
| `krizky_photos/context.py` | přejmenovaný `krizky/photo_context.py` (beze změny) |
| `krizky_photos/fetch.py` | `fetch_gdrive_metadata` + `_parse_photo_row_number` přesunuté z `krizky/fetch.py` |
| `krizky_photos/plugin.py` | `PhotosPlugin` s `@hookimpl prepare_jinja2_environment` (registruje `PhotoContext`) a `@hookimpl register_commands` (přidá `fetch photos`, `build photos` do CLI) |
| `tests/` | přesunuté testy z `krizky/tests/test_build_photos.py` a `test_photo_context.py` |

---

## Změny v krizky core

### `krizky/hooks.py`
Přidán parametr `config_dir` do `prepare_jinja2_environment` hookspec. Zpětně kompatibilní změna — pluginy, které `config_dir` nepotřebují, ho nemusí deklarovat.

### `krizky/site.py`
- Odstraněn `from krizky.photo_context import PhotoContext` a celý blok setup PhotoContext v `_generate()`
- Aktualizováno volání `pm.hook.prepare_jinja2_environment(env, config, config_dir=config_dir)`
- Přidán no-op fallback po hook callu:
  ```python
  if "photos" not in jinja_env.globals:
      jinja_env.globals["photos"] = _noop_photos   # vrací has_photos=False
      jinja_env.globals["photo_contexts"] = {}
  ```
  Zajišťuje, že šablony používající `photos()` nespadnou pokud krizky-photos není nainstalovaný.

### `krizky/fetch.py`
Odstraněny funkce `fetch_gdrive_metadata` a `_parse_photo_row_number` (přesunuty do `krizky_photos/fetch.py`).

### `krizky/cli.py`
Odstraněny příkazy `fetch photos` a `build photos` (přesunuty do `krizky_photos/plugin.py` přes `register_commands` hook).

### `krizky/builtin_plugins.py`
Odstraněn `JsonExportPlugin` (přesunut do `krizky-json`). Soubor zůstává jako prázdný placeholder.

### `krizky/plugin_manager.py`
Odstraněna registrace `JsonExportPlugin` z `get_plugin_manager()`.

### Smazané soubory
- `krizky/json_export.py` → přesunuto do `krizky_json/plugin.py`
- `krizky/build_photos.py` → přesunuto do `krizky_photos/build.py`
- `krizky/photo_context.py` → přesunuto do `krizky_photos/context.py`
- `tests/test_json_export.py` → přesunuto do `_plugins/krizky-json/tests/`
- `tests/test_build_photos.py` → přesunuto do `_plugins/krizky-photos/tests/`
- `tests/test_photo_context.py` → přesunuto do `_plugins/krizky-photos/tests/`

### `pyproject.toml`
Odstraněna `photos` extras sekce (nahrazena komentářem `# photos = ["krizky-photos"]`).

---

## Testy

88 testů, 88 prošlo (ze 138 původních; 50 testů přesunuto do plugin balíčků).

---

## Architektonická poznámka: zpětná kompatibilita šablon

Šablony používající `photos(record.row_number)` nebo `photo_contexts` zůstávají funkční:
- **S krizky-photos**: `PhotoContext` registrován přes `prepare_jinja2_environment` hook → plná funkcionalita
- **Bez krizky-photos**: no-op fallback v `site.py` → `photos()` vrací `has_photos=False`, stránka se vyrenderuje bez fotek
