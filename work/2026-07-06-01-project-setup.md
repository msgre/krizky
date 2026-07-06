# Phase 1 — Projekt + Config

**Date:** 2026-07-06  
**Status:** DONE

## What was implemented

### Files created

| File | Description |
|------|-------------|
| `pyproject.toml` | Project metadata, dependencies, entry point (`krizky = "krizky.cli:cli"`), hatchling build backend, Python >=3.12 |
| `krizky/__init__.py` | Empty package marker |
| `krizky/config.py` | `ConfigError`, `load_config()`, `validate_config()`, recursive ENV substitution |
| `krizky/cli.py` | Click CLI: `cli` group with `--config`, `validate` (fully functional), `init`, `fetch sources`, `fetch photos`, `build`, `build site`, `build photos` |
| `tests/__init__.py` | Empty package marker |
| `tests/test_config.py` | 11 tests covering all specified cases + edge cases |

### Key implementation notes

- `_substitute_env()` is fully recursive — handles nested dicts, lists, and scalar strings.
- `load_dotenv(override=False)` is called in `load_config()` so existing env vars take precedence.
- `validate_config()` checks: `sources`/`site` presence, exactly-one `main: true`, transform path existence, docs `transform`+`output` presence.
- `krizky init` generates `config.yaml` (comprehensive example with comments), `.env.example`, and creates `templates/`, `assets/`, `transforms/` directories; asks for confirmation if target dir is non-empty.

## Test results

```
11 passed in 0.12s
```

All 6 required tests plus 5 additional edge-case tests pass.
