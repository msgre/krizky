# Kandidáti na konsolidaci do core

Odvozeno z revize 2026-08-17. Kandidáty seřazené podle "efektu na řádek konsolidovaného kódu" (LOC ušetřených × počet pluginů).

Doporučené umístění v core: nový modul `krizky/plugin_helpers.py` pro věci, které pluginy volají; `krizky/testing.py` pro test utility.

---

## 1. `_copy_assets` — copy-once idempotent asset copy do output

**Vzorec:** plugin zkopíruje své `assets/<plugin-name>/*` do `<output>/<plugin-name>/` právě jednou za build. Guard přes `self._assets_copied: set[str]` klíčovaný `str(output_dir)`.

**Síla vzoru:** **strong** — 3 pluginy, ~15-25 řádků každý, celkem ~60 LOC.

**Výskyty:**
- `_plugins/krizky-map/krizky_map/plugin.py:333-359` — per-file `shutil.copy2` v cyklu + copy mask/overlays.
- `_plugins/krizky-share/krizky_share/plugin.py:151-161` — per-file `shutil.copy2` v cyklu.
- `_plugins/krizky-filters/krizky_filters/plugin.py:174-182` — `shutil.rmtree` + `shutil.copytree` (celý strom).

**Rozdíly:** filters agresivně smaže cílový dir (odstraněné plugin soubory se propíší); map/share ne (obsolete soubory zůstanou). Sjednotit na jednu sémantiku — preferuji **rmtree+copytree** (deterministic, žádné duchy).

**Návrh API v core:**
```python
# krizky/plugin_helpers.py
class AssetCopier:
    """Copy plugin assets into output/<plugin_slug>/ once per build."""

    def __init__(self, plugin_slug: str, source_dir: Path) -> None:
        self._slug = plugin_slug
        self._source = source_dir  # <plugin>/assets/<plugin-slug>
        self._done: set[str] = set()

    def copy_once(self, output_dir: Path) -> None:
        key = str(output_dir)
        if key in self._done:
            return
        dst = output_dir / self._slug
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(self._source, dst)
        self._done.add(key)
```

Použití v pluginu:
```python
class MapPlugin:
    def __init__(self):
        self._copier = AssetCopier("krizky-map", _PLUGIN_ASSETS / "krizky-map")

    @hookimpl
    def after_page_written(self, ..., output_dir, ...):
        self._copier.copy_once(output_dir)
```

**Alternativa (silnější):** místo helperu zavést nový hook `copy_plugin_assets(output_dir)`, který core zavolá jednou za build a idempotency řeší framework. Viz `proposals/hook-changes.md`.

**Riziko:** map plugin má custom logiku pro mask + overlays (`_copy_assets` v map dělá víc než jen kopírování assets/). Refactor musí ponechat map schopnost přidat vlastní kopírování na vrchol.

---

## 2. Template registrace přes `ChoiceLoader` — vložit plugin templates do Jinja2

**Vzorec:** plugin vloží `FileSystemLoader(_PLUGIN_TEMPLATES)` do `env.loader.loaders` na správnou pozici (za projekt templates, před built-in). Kontrola, jestli už není zaregistrovaný (idempotence).

**Síla vzoru:** **strong** — 3 pluginy, ~10 řádků každý, celkem ~30 LOC.

**Výskyty:**
- `_plugins/krizky-map/krizky_map/plugin.py:131-140`
- `_plugins/krizky-share/krizky_share/plugin.py:68-78`
- `_plugins/krizky-filters/krizky_filters/plugin.py:99-112`

**Návrh API v core:**
```python
# krizky/plugin_helpers.py
def register_plugin_templates(env, path: Path) -> None:
    """Insert a plugin's templates/ directory into the Jinja2 ChoiceLoader chain.

    Position: after project templates (first loader), before built-in krizky
    templates. Idempotent — safe to call multiple times per env.
    """
    if not isinstance(env.loader, ChoiceLoader):
        return
    loaders = env.loader.loaders
    if any(isinstance(l, FileSystemLoader) and str(path) in l.searchpath for l in loaders):
        return
    env.loader.loaders = [loaders[0], FileSystemLoader(str(path))] + loaders[1:]
```

Použití:
```python
@hookimpl
def prepare_jinja2_environment(self, env, config, config_dir):
    register_plugin_templates(env, _PLUGIN_TEMPLATES)
    # ...zbytek plugin setup
```

**Riziko:** null. Sémanticky totožné napříč všemi 3 pluginy, refactor je 1:1.

---

## 3. Config path resolution vůči `config_dir`

**Vzorec:** vyresolvovat cestu ze configu vůči adresáři configu — pokud je absolutní, ponechat; jinak relativně ke `config_dir`.

**Síla vzoru:** **medium** — 2 pluginy, ~7 řádků, ale koncept je základní.

**Výskyty:**
- `_plugins/krizky-map/krizky_map/plugin.py:361-368` (`_resolve_source_path`)
- `_plugins/krizky-photos/krizky_photos/focal.py` (analogická logika uvnitř `load_focal_points`)

**Návrh API v core:**
```python
# krizky/config.py — přidat k existujícím helperům
def resolve_path(path: str | Path | None, config_dir: Path) -> Path | None:
    """Resolve a config-relative path.

    - None → None
    - absolute path → returned unchanged
    - relative path → resolved against config_dir
    """
    if path is None:
        return None
    p = Path(path)
    return p if p.is_absolute() else (config_dir / p).resolve()
```

Použití:
```python
mask_polygon = resolve_path(mask.get("polygon"), self._config_dir)
```

**Riziko:** minimální. Zvážit, jestli přítomné volání v map (které vrací i `Path("relativní")` pokud `config_dir is None`) potřebuje speciální fallback — pravděpodobně ne, ale ověřit.

---

## 4. Test helper `_make_db()` — SQLite fixture pro testy

**Vzorec:** vytvořit SQLite databázi s tabulkou pro test data.

**Síla vzoru:** **medium** — 2 místa (core + json), ale bude použit dalšími pluginy (map, filters by z toho těžily).

**Výskyty:**
- `tests/test_site.py::_make_db` (core, viz test file)
- `_plugins/krizky-json/tests/test_json_plugin.py::_make_db` (téměř identická kopie)

**Návrh API v core:**
```python
# krizky/testing.py — new module, public helpers for plugin tests
import sqlite3
from pathlib import Path


def make_db(db_path: Path, records: list[dict], table: str = "data") -> None:
    """Create a SQLite database with the given records for tests."""
    cols = list(records[0].keys())
    conn = sqlite3.connect(str(db_path))
    col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
    conn.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({col_defs})')
    conn.executemany(
        f'INSERT INTO "{table}" ({", ".join(f"""\"{c}\"""" for c in cols)}) '
        f"VALUES ({', '.join('?' for _ in cols)})",
        [tuple(r[c] for c in cols) for r in records],
    )
    conn.commit()
    conn.close()


def minimal_config(**overrides) -> dict:
    """Return a minimal valid krizky config dict for tests."""
    base = {
        "sources": {"output": "./sources", "database": "data.db", "tables": {}},
        "site": {"title": "Test", "output": "./docs", "templates": "./templates", "pages": {}},
    }
    # deep merge overrides — implementation elided
    return {**base, **overrides}
```

Použití v plugin testu:
```python
from krizky.testing import make_db, minimal_config


def test_something(tmp_path):
    db = tmp_path / "data.db"
    make_db(db, [{"slug": "a", "nazev": "A"}])
    ...
```

**Riziko:** `krizky.testing` je "public" jen pro testy — kdyby ho někdo importoval do produkčního kódu, znamená to, že v runtime kódu chce něco, co patří jinam. Vyřešit doc-string warning ("This module is for tests only.").

---

## 5. `inject_head` returning `<link rel="stylesheet">` a `inject_body_end` returning `<script defer>`

**Vzorec:** plugin vrátí HTML tag odkazující na svůj CSS/JS asset.

**Síla vzoru:** **weak-medium** — 3 pluginy, ~2 řádky každý. Konsolidace nemusí ušetřit LOC, ale sjednotí konvenci.

**Výskyty:**
- `_plugins/krizky-map/krizky_map/plugin.py:252` (`<link>`), `plugin.py:273` (`<script>`)
- `_plugins/krizky-share/krizky_share/plugin.py:123` (`<link>`), `plugin.py:139` (`<script>`)
- `_plugins/krizky-filters/krizky_filters/plugin.py:152` (`<link>`), `plugin.py:163` (`<script>`)

**Návrh API v core:**
```python
# krizky/plugin_helpers.py
def plugin_stylesheet(plugin_slug: str, filename: str = None) -> str:
    """Return <link> tag for /<plugin_slug>/<filename>. Default filename = <plugin_slug>.css."""
    fname = filename or f"{plugin_slug}.css"
    return f'<link rel="stylesheet" href="/{plugin_slug}/{fname}">'


def plugin_script(plugin_slug: str, filename: str = None) -> str:
    """Return <script src=... defer> tag for /<plugin_slug>/<filename>. Default: <plugin_slug>.js."""
    fname = filename or f"{plugin_slug}.js"
    return f'<script src="/{plugin_slug}/{fname}" defer></script>'
```

**Riziko:** velmi drobná úspora. Zvážit, jestli není spíš dokumentační konvence ("plugin assets končí v `/<plugin-slug>/`") než volatelný helper. Pokud helper, tak trivial — ale někdo se ptá "kde je magie" a najde jednořádkovku. Preferuji dokumentaci + helper, ale s nižší prioritou.

---

## 6. `_PLUGIN_DIR = Path(__file__).parent` a odvozené konstanty

**Vzorec:** `_PLUGIN_DIR`, `_PLUGIN_TEMPLATES`, `_PLUGIN_ASSETS` na topu `plugin.py`.

**Síla vzoru:** **weak** — 3 pluginy, 3 řádky každý. Kód je krátký a self-explanatory. Konsolidace by přidala import bez úspory.

**Doporučení:** **NEKONSOLIDOVAT.** Jen dokumentovat konvenci v config-style-guide.

---

## Souhrn

| # | Kandidát | Síla | LOC ušetřené |
|---|---|---|---|
| 1 | `_copy_assets` idempotency | strong | ~40-50 |
| 2 | `register_plugin_templates` | strong | ~20-25 |
| 3 | `resolve_path(config_dir)` | medium | ~10-15 |
| 4 | `krizky.testing.make_db()` | medium | ~20 (+prevence dupl.) |
| 5 | `plugin_stylesheet`/`_script` helper | weak-medium | ~5 |
| 6 | `_PLUGIN_DIR` konstanty | weak | 0 (nedělat) |

**Doporučené pořadí implementace:** 1 → 2 → 3 → 4 → 5 (přeskočit 6).

Body 1 + 2 dají největší efekt — cca 65-75 řádků úspory + 3 pluginy budou jednodušší k reviewu. Body 3-5 jsou nice-to-have po základní konsolidaci.
