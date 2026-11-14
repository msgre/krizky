# Kontrola: Python styl

Cíl: Python core a všech pluginů působí jako od jednoho autora.

Pravidla jsou v `docs/guidelines/python.md`. Co z nich vynucuje ruff přes `scripts/verify` (formát, pořadí importů, zákaz `from __future__ import annotations`, `X | None` a další pravidla z `[tool.ruff.lint]`), se nehlásí.

## Postup

1. Porovnej `[tool.ruff*]` v `pyproject.toml` všech repů s core a ověř, že každé repo má `scripts/verify`.
2. Pro každý plugin projdi strukturu balíčku, `plugin.py` a hlavičky modulů.
3. Porovnej s core a s `docs/guidelines/python.md` podle pravidel níže.

## Pravidla

### Nástroje

- Repo bez `scripts/verify`, nebo s jinou konfigurací ruff než core → **recommended**.

### Struktura balíčku

- Balíček `krizky_<x>`, entry point `krizky_<x>.plugin:plugin`, v `plugin.py` třída `<Název>Plugin` a modulová instance `plugin`. Odchylka → **recommended**.
- Obsah `__init__.py` se mezi pluginy liší (prázdný, re-exporty, verze) → **nice-to-have**.

### Podle guidelines

Každá odchylka od těchto sekcí `docs/guidelines/python.md` je **recommended**:

- › Docstringy: Google styl v angličtině a modulový docstring na prvním řádku.
- › Type hints: hinty na veřejných funkcích včetně návratového typu.
- › Imports: absolutní importy, líný import jen s komentářem proč.
- › Data types: `dataclass` a `TypedDict` místo `namedtuple`.
- › Anti-patterns: `assert` v produkčním kódu, `print()`, `except Exception:` mimo top-level CLI handler.

### Click příkazy

- Pluginy registrují příkazy jinak než přes `register_commands`, nebo pod jinou strukturou skupin než core (`krizky fetch <x>`, `krizky build <x>`) → **recommended**.
- Help texty příkazů jsou v různých jazycích nebo některé chybí → **nice-to-have**.

Blocker v této kontrole nevzniká. Problémy s API řeší `api-boundaries.md`.
