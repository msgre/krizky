# Implementation log

Log implementací nálezů z tohoto reportu. Připisuje se append-only.

---

## Session 2026-08-20 07:30

Reviewer: Claude Code (implement-review skill)
Invocation: `/implement-review` — implicitní filter `blocker`

### Environment setup

- Ruff 0.16.3 nainstalován přes `pip install ruff --user --break-system-packages` (v tomto sandboxu není `uv` v PATH).
- Node.js 22.11.0 stažen a rozbalen do `~/.local/opt/`, symlinked do `~/.local/bin/`.
- ESLint 9.39.5 a Prettier 3.9.6 nainstalované globálně přes `npm install -g eslint prettier`.

### Freshness check

- `git log --since='2026-08-17 20:13'` pro dotčené soubory (`plugin.py` a `filters.js` u obou pluginů): **0 commits** — report je aktuální, safe pokračovat.

### Findings addressed

- ✓ **[blocker] Config klíče pagination_window → window a pagination_boundary → boundary** (krizky-filters)
  - Commit: `b3af0a2`
  - Files: `krizky_filters/plugin.py`, `krizky_filters/assets/krizky-filters/filters.js`
  - Verified: ruff (existující UP028 nesouvisí — viz "Spotted, not fixed"), pytest 45/45 OK, node --check OK
  - Notes: user-facing YAML klíče `site.pagination_window` a `site.pagination_boundary` se **nemění**; jen interní Python→JS transport.

- ✓ **[blocker] click.ClickException vyhazován z hooku, který nemusí běžet v Click kontextu** (krizky-photos)
  - Commit: `bba6905`
  - Files: `krizky_photos/plugin.py`, `tests/test_plugin.py`
  - Verified: ruff OK (po `--fix` doplnění isort — bezpečný cosmetic reorder), pytest 60/60 OK
  - Notes:
    - Test `test_prepare_jinja2_environment_missing_explicit_focal_points_raises` aktualizován — nyní očekává `FocalPointsError` místo `click.ClickException`.
    - Import `FocalPointsError` odstraněn z `plugin.py` (unused po odstranění except bloku).
    - Import `click` zůstává (používá se v `register_commands` hooku, který legitimně CLI hook je).
    - **UX regression:** dřív uživatel viděl pretty Click error rendering, teď dostane raw Python traceback. Trade-off za správnost API surface — viz "New findings spotted" níže.

### Skipped

_none_

### Failed

_none_

### Spotted, not fixed

- `_plugins/krizky-filters/krizky_filters/plugin.py:25` — ruff `UP028`: `for key, val in ...items(): yield key, val` → doporučeno `yield from`. Nesouvisí s implementovaným findingem. Doporučuji založit jako **nice-to-have** finding do příštího review.

### New findings spotted (návrh na doplnění reportu)

Během implementace vyplynul jeden strukturální problém, který skill nemohl řešit sám:

- **[recommended] Core `krizky/site.py` (nebo `cli.py`) nemá top-level wrapper pro plugin exceptions.** Když plugin v build hooku vyhodí vlastní exception (nově např. `FocalPointsError` po předchozím fixu), uživatel v CLI dostane raw traceback místo vlídné chybové hlášky. Ideálně by core CLI měl obalit volání plugin hooků `try/except Exception` a přepakovat jako `click.ClickException` (nebo obdobný CLI-agnostic reporter). To by umožnilo pluginům vyhazovat vlastní exceptions bez UX regresí. Doporučuji nový finding do `core.md` sekce "Error handling a logging" (severity: recommended).

### Environmental notes

- Sandbox neměl `uv`, `node`, `npm`, ani `xz`. Prebuilt Node.js `.tar.gz` variant fungovala.
- Nebyly nalezené `.eslintrc` ani `.prettierrc` configy v pluginech — skill jich nepoužil pro tuto sekci, jen `node --check` na syntax. Přidání linter configů je samostatný finding (viz `guidelines/javascript.md` sekce ESLint + Prettier config).
- Git identita v repech nebyla nastavená — použit inline `git -c user.name=... -c user.email=... commit` (bez trvalé změny gitconfigu, per skill safety protocol).

### Zamítnutá zjištění (policy)

- **[recommended] krizky-filters chybí `from __future__ import annotations`** — zamítnuto na základě nové policy v `guidelines/python.md`: na Python 3.12+ tento import není potřeba (ruff `FA102` ho bude flagovat jako zbytečný). Existující usage v ostatních pluginech se nemá proaktivně odstraňovat.
