# Check: Python style

Cíl: kód napříč všemi pluginy + core vypadá, jako by ho psal jeden člověk.

## Kontext

Používá se Python ≥3.12, balíčkování přes uv, `pyproject.toml` s hatchling. Plugin entry point je typicky `plugin.py` s třídou `<Name>Plugin` a instancí `plugin`.

Pravidla jsou v `docs/guidelines/python.md`. Ruff se stejnou konfigurací ve všech repech hlídá přes `scripts/verify` formátování, pořadí importů, zákaz `from __future__ import annotations` (TID251), `X | None` místo `Optional[X]` a další. To nehlas, jen rozdíl v `[tool.ruff*]` mezi repy.

## Postup

1. Přečti core (`krizky/*.py`) — to je precedent.
2. Pro každý plugin porovnej níže uvedené aspekty s core.
3. Zaznamenej odchylky.

## Checklist

### Package & module layout
- [ ] Plugin package má jméno `krizky_<x>` (snake_case, ne `krizky-x`). Konzistentní?
- [ ] Entry point je `krizky_x.plugin:plugin` s modulovým `plugin = <Name>Plugin()`? Nebo někdo exportuje třídu vs instanci?
- [ ] Rozdělení do modulů: kdy plugin má víc než `plugin.py` (kdy vydělit do `build.py`, `context.py`, atd.)? Konzistentní princip nebo ad-hoc?
- [ ] `__init__.py` obsah — prázdný, re-exporty, nebo verze?

### Imports
- [ ] Absolute vs relative imports — jednotný styl?
- [ ] Import `hookimpl` — vždy `from krizky.hooks import hookimpl`, nebo někdo import přes `pluggy` přímo?
- [ ] Lazy imports uvnitř metod (viz `PhotosPlugin.prepare_jinja2_environment` importuje `PhotoContext` uvnitř) — kdy ano, kdy ne? Konzistentní kritérium?

### Typing
- [ ] Používají všechny moduly type hints na veřejném API?
- [ ] Return type `-> None` na `void` funkcích — konzistentně vyžadován?
- [ ] `TYPE_CHECKING` použití — kdo, proč?

### Naming
- [ ] Třídy: `<Feature>Plugin` (např. `PhotosPlugin`, `JsonExportPlugin`)? Konzistentní suffix?
- [ ] Custom exception třídy: `<Name>Error` (viz `FocalPointsError`)? Všude?
- [ ] Private funkce/proměnné: `_foo` prefix — konzistentně?
- [ ] Konstanty: `UPPER_SNAKE_CASE` — dodržené?
- [ ] Boolean funkce: `is_x`, `has_x`, `can_x` — konzistentní?

### Docstrings
- [ ] Styl: Google-style (`Args:`, `Returns:`, `Raises:` — jako v `krizky/hooks.py`) je precedent. Používají to všechny pluginy?
- [ ] Modul-level docstring — přítomný, jednotný formát ("krizky-X plugin — <one-liner>")?
- [ ] Třída/funkce bez docstringu tam, kde je smysl — flag jako recommended.
- [ ] Docstring v jazyce — český vs anglický, konzistentní?

### CLI / Click
- [ ] Které pluginy přidávají Click commands? Přes `register_commands` hook — všechny stejný pattern?
- [ ] `@click.command`, `@click.group` — struktura konzistentní? (`fetch photos`, `build photos` — používají všichni sub-command style pod globálními groups?)
- [ ] Help texty: jazyk, formát, přítomnost?
- [ ] Chybové výstupy: `click.ClickException` vs vlastní exception + traceback?

### Dataclasses / plain classes / dicts
- [ ] Kdy se používá `@dataclass`, kdy plain class, kdy prostě dict pro strukturovaná data? Konzistentní kritérium?
- [ ] Photo dict, config dict — je někde formalizovaný (dataclass/TypedDict), nebo všude jen `dict`?

### Hlavička modulu
- [ ] Header každého modulu (docstring, imports, `_log`) — konzistentní pořadí?
- [ ] Šebang, encoding pragma — nemá tu nikdo být (Python 3), pokud ano → nice-to-have.

### Chybějící / zapomenuté konvence
- [ ] `assert` v produkčním kódu (má být jen v testech nebo za `if __debug__`) — někdo?
- [ ] `print()` místo loggeru — někdo?
- [ ] Má každé repo `scripts/verify` a stejné sekce `[tool.ruff*]` v `pyproject.toml`?

## Reporting

Většina zjištění bude `recommended`. Označ `blocker` jen když inconsistence blokuje spolehlivé používání API (např. jeden plugin importuje z `krizky.render._internal` — to je API break risk).
