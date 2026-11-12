# Guidelines: Python

Cílový Python: **3.12+** (dle `requires-python` v pyproject.toml). Balíčkování: **uv**. Formatter/linter: **ruff**. Test framework: **pytest**.

Load this file when a finding touches Python code.

## Ruff — canonical config

Každý projekt (core + pluginy) má mít v `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py312"
line-length = 100
extend-exclude = [".venv", "__pycache__", ".pytest_cache", "tests/fixtures"]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes
    "W",    # pycodestyle warnings
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade — modernize idioms for the target version
    "B",    # bugbear — likely bugs
    "A",    # builtins — shadowing built-in names
    "C4",   # comprehensions
    "SIM",  # simplify
    "PT",   # pytest style
    "RUF",  # ruff-specific
    "FA",   # future-annotations — enforce direction (see below)
]
ignore = [
    "E501",  # line-too-long — line-length above already governs
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
```

**Skill enforcement:** před každým commitem, kde je změněný `*.py` soubor:
1. `uv run ruff check --fix <changed_files>` — auto-fix triviality.
2. Pokud ruff hlásí neopravitelné → skill zastaví, vypíše errors, nemíří dál.
3. `uv run ruff format <changed_files>` — sjednotit formát.
4. Znovu ověřit `uv run ruff check <changed_files>` (bez `--fix`) — musí projít clean.

Pokud projekt nemá ruff config v pyproject → skill NEmění config, ale spustí ruff s výše uvedeným ekvivalentem přes CLI (`uv run ruff check --select=... --target-version=py312 ...`). Přidat ruff config je samostatný finding.

## Python idioms — canonical patterns

### Type hints

- Public API má typové hinty na parametrech + return type.
- `X | None` (PEP 604, nativně od 3.10) — **preferuj před** `Optional[X]`.
- Generic syntax: pro nové kód `def f[T](x: T) -> T` (PEP 695, od 3.12). Pro starší patterny `TypeVar` OK.
- `list[X]`, `dict[str, int]` — nativní, žádný `from typing import List, Dict`.

### `from __future__ import annotations`

**NEPOUŽÍVAT** v novém kódu (Python 3.12+ to nepotřebuje; ruff `FA102` bude flagovat). Existující usage v pluginech neodstraňovat proaktivně — smaže se jako side-effect příštího dotyku souboru.

### Docstringy

Google-style — matching core `krizky/hooks.py`:

```python
def register_plugin_templates(env, path: Path) -> None:
    """Insert a plugin's templates/ directory into the Jinja2 ChoiceLoader chain.

    Position: after project templates (first loader), before built-in krizky
    templates. Idempotent — safe to call multiple times per env.

    Args:
        env: jinja2.Environment instance with a ChoiceLoader.
        path: Path to the plugin's templates/ directory.

    Raises:
        ValueError: If env.loader is not a ChoiceLoader.
    """
```

Rules:
- 1 věta shrnutí na prvním řádku.
- Prázdný řádek, pak detaily.
- `Args:`, `Returns:`, `Raises:` sekce podle relevance.
- Angličtina.
- Modul-level docstring: 1 věta popisu modulu na prvním řádku (`"""krizky-photos plugin — photo pipeline."""`).

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
class PhotosError(Exception):
    """Base class for krizky-photos errors."""

class FocalPointsError(PhotosError):
    """Focal points file is malformed or missing."""

class PhotoFetchError(PhotosError):
    """Failed to fetch photo metadata from Google Drive."""
```

- Base class per plugin, aby uživatel mohl chytat `except PhotosError:`.
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
- Import je pomalý a funkce se často nevolá (photos delays google-api-client import).
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
- Shared helpers (SQLite make_db apod.) — importovat z `krizky.testing` po jeho vzniku (viz consolidation proposal #4).
- `pytest.fixture(scope="session"|"module"|"function")` — default `function` (isolate).
- `pytest.mark.parametrize` pro data-driven testy — preferuj před smyčkami v testu.
- Naming: `test_<what>_<condition>()` — např. `test_load_focal_points_missing_file_warns`.
- `tmp_path` fixture pro dočasné soubory (nikoli `tempfile.mkdtemp` manuálně).
- **Nemockovat** interní kód. Mock jen external boundaries (síť, filesystem občas, Google API).

### Test coverage

- Nové public API → alespoň 1 happy path test + 1 error path test.
- Refactor (přesun kódu bez změny chování) → existující testy musí projít; ne přidávat testy jen kvůli metricám.
- Rename → grep testů na staré jméno, aktualizovat.

## Package management (uv)

Přidat závislost:
```bash
uv add <package>
```

Přidat dev závislost:
```bash
uv add --dev <package>
```

Odstranit:
```bash
uv remove <package>
```

**Pravidlo balíčků:** viz `guidelines/javascript.md` sekce "Package selection" — Python i JS balíčky mají identická kritéria (age, maintenance, license, popularity).

## Před commitem

Pro každý změněný `*.py` soubor:
1. `uv run ruff check --fix <file>` — pass.
2. `uv run ruff format <file>` — apply.
3. `uv run ruff check <file>` — clean (bez `--fix`).
4. `uv run pytest tests/<related>` — pass.

Pokud (4) padne → skill NEcommituje. Vrátí staging area (`git restore --staged <files>` + `git checkout <files>` pouze pokud user explicitně souhlasil s revertem; jinak jen `git restore --staged` a nechá files v pracovní kopii, aby uživatel viděl, co skill navrhoval).
