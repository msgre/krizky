# Guidelines: Python

Cílový Python: **3.12+** (dle `requires-python` v pyproject.toml). Balíčkování: **uv**. Formatter/linter: **ruff**. Test framework: **pytest**.

## Ruff

Kanonická konfigurace je `[tool.ruff*]` v `pyproject.toml` core. Pluginy ji mají shodnou a `scripts/verify` ji v každém repu vynucuje (`ruff check`, `ruff format --check`). Rozdíl v konfiguraci mezi repy je chyba, ne lokální výjimka.

## Python idioms — canonical patterns

### Type hints

- Public API má typové hinty na parametrech + return type.
- `X | None` (PEP 604, nativně od 3.10) — **preferuj před** `Optional[X]`.
- Generic syntax: pro nové kód `def f[T](x: T) -> T` (PEP 695, od 3.12). Pro starší patterny `TypeVar` OK.
- `list[X]`, `dict[str, int]` — nativní, žádný `from typing import List, Dict`.

### `from __future__ import annotations`

Zakázaný. Python 3.12+ ho nepotřebuje a ruff ho blokuje pravidlem TID251.

### Docstringy

Google-style, jako v core (`krizky/hooks.py`, `krizky/plugin_helpers.py`):

```python
def register_plugin_templates(env: jinja2.Environment, templates_dir: str | Path) -> None:
    """Insert a plugin's templates directory into the Jinja2 ChoiceLoader chain.

    The loader is placed right after the first loader (project templates) and
    before the built-in krizky templates. Calling it repeatedly with the same
    path adds the loader only once. If ``env.loader`` is not a ChoiceLoader,
    nothing happens.

    Args:
        env: Jinja2 environment.
        templates_dir: Path to the plugin's templates directory.
    """
```

Rules:
- 1 věta shrnutí na prvním řádku.
- Prázdný řádek, pak detaily.
- `Args:`, `Returns:`, `Raises:` sekce podle relevance.
- Angličtina.
- Modul-level docstring: 1 věta popisu modulu na prvním řádku (`"""Photo pipeline for krizky."""`).

### Logging

```python
import logging

_log = logging.getLogger(__name__)

# Lazy formatting for logging — %s, ne f-string
_log.warning("Missing photo metadata: %s", cf_meta_path)
_log.info("Processed %d photos in %.2fs", count, elapsed)

# f-string pro user-facing text (click.echo, click.ClickException message)
click.echo(f"Processed {count} photos.")
```

Konvence:
- Modul-level `_log = logging.getLogger(__name__)`. **Ne** `logger`, **ne** `log`. Prefixované `_log` = internal.
- Lazy `%s` formatting v `_log.<level>()` calls — logging modul deferoval formátování, když je level filtrován.
- f-string jen v user-facing textech.
- `_log.warning()`, `_log.info()` — použij podle sémantiky (`warning` = recoverable problem, `info` = business event).
- **Neloguj** `_log.error()` + `raise` současně — buď jedno, nebo druhé.

### Exceptions

- Custom exceptions: `<Feature>Error`, dědí z společné base pro daný plugin.

```python
class FooError(Exception):
    """Base class for krizky-foo errors."""


class FooConfigError(FooError):
    """Invalid krizky-foo configuration."""
```

- Base class per plugin, aby uživatel mohl chytat `except FooError:`.
- Přepakování cizí exception: `raise MyError("kontext") from original_exc`.
- **Ne** re-raise bez transformace — jen `raise` (zachová traceback).
- V hooku (mimo CLI kontext) **ne** `click.ClickException` — použij plugin-specific exception. CLI handler ji chytí a přepakuje.

### I/O

```python
from pathlib import Path

# Vždy pathlib, ne os.path
config_dir = Path(__file__).parent

# Context manager pro otevřené soubory
data = json.loads(path.read_text(encoding="utf-8"))
path.write_text(json.dumps(data, indent=2), encoding="utf-8")

# SQLite s kontext managerem
import sqlite3

with sqlite3.connect(str(db_path)) as conn:
    cur = conn.execute("SELECT ...", (param,))
    rows = cur.fetchall()
```

### Data types

- `@dataclass(frozen=True)` pro nemutovatelné strukturované data (např. `Photo`, `Dimension`).
- `@dataclass` bez `frozen` pro mutovatelné.
- Plain `dict` OK pro flexibilní/uživatelské data (config sekce).
- `TypedDict` když chceš typové hinty pro dict s pevnými klíči, ale nechceš class overhead.
- **Ne** `namedtuple` — legacy.

### Imports

Pořadí (ruff `I` isort):
1. `stdlib`
2. Prázdný řádek
3. `third-party`
4. Prázdný řádek
5. `local` (`from krizky.hooks import ...`, `from krizky_photos.build import ...`)

Absolute imports vždy (`from krizky_photos.build import ...`), ne relative (`from .build import ...`).

Lazy import (uvnitř funkce) použij **pouze** když:
- Import je pomalý a funkce se často nevolá (např. klient Google API).
- Vyhýbáš se circular import.
- V obou případech přidej 1 řádkový komentář, PROČ.

### Anti-patterns v Pythonu

- `assert` v produkčním kódu (funguje jen pokud není `-O`).
- `print()` — použij `_log` nebo `click.echo`.
- Mutable default arg (`def f(x=[])`).
- `except:` nebo `except Exception:` bez specifického typu (výjimka: absolute top-level CLI handler).
- Manipulace s `sys.path` (patch přes proper imports).
- `os.system()`, `os.popen()` — použij `subprocess.run(..., check=True)`.

## Pytest — canonical style

- Function-based (`def test_x(...)`) — matching majority of ekosystém. **Ne** `class TestX`.
- Fixtures v `conftest.py` (root nebo per-directory) pro sdílené setup. Ne redefinovat per-file.
- `pytest.fixture(scope="session"|"module"|"function")` — default `function` (isolate).
- `pytest.mark.parametrize` pro data-driven testy — preferuj před smyčkami v testu.
- Naming: `test_<what>_<condition>()` — např. `test_load_focal_points_missing_file_warns`.
- `tmp_path` fixture pro dočasné soubory (nikoli `tempfile.mkdtemp` manuálně).
- **Nemockovat** interní kód. Mock jen external boundaries (síť, filesystem občas, Google API).

### Test coverage

- Nové public API → alespoň 1 happy path test + 1 error path test.
- Refactor (přesun kódu bez změny chování) → existující testy musí projít; ne přidávat testy jen kvůli metricám.
- Rename → grep testů na staré jméno, aktualizovat.

## Závislosti

Kritéria pro výběr balíčku jsou společná pro Python i JS: `javascript.md` › Package selection.

## Před commitem

`scripts/verify` musí skončit s exit 0.
