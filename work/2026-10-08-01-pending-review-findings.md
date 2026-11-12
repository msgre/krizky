# 2026-10-08-01 — Pending: zbývající findings z review

Stav session při odložení. Session rozpracovaná od 2026-08-17.

## Co bylo uděláno

1. **Skill `review-consistency`** vytvořen v `.claude/skills/review-consistency/` (zdroj v `skills/`).
   - Multi-check sken core + 5 pluginů, generuje reporty do `reports/`.

2. **Skill `implement-review`** vytvořen v `.claude/skills/implement-review/` (zdroj v `skills/`).
   - Načítá report, implementuje findings s verifikačními gates (ruff + pytest + eslint), commituje per finding bez pushe.

3. **Review report** vygenerován: `reports/2026-08-17-2013/`
   - 46 findings celkem: **2 blocker**, 29 recommended, 15 nice-to-have.
   - Per-project reporty + `summary.md` + 3 proposals (consolidation, hook-changes, config-style-guide).

4. **Blockers implementovány (2/2):**
   - **krizky-filters** `b3af0a2` — JS config klíče `window`→`paginationWindow`, `boundary`→`paginationBoundary`.
   - **krizky-photos** `bba6905` — odstraněn `click.ClickException` reraise z `prepare_jinja2_environment` (hook teď bublá `FocalPointsError`).

5. Nainstalovány nástroje: `ruff 0.16.3` (přes pip), Node.js 22.11.0 (stažen tarball), ESLint 9.39.5, Prettier 3.9.6 (přes npm). Všechny v `~/.local/bin/`.

## Co zbývá

**Nic není v nekonzistentním stavu** — všechny změny jsou committed, repa jsou clean. Zbývají nerealizované findings z reportu.

### Zbývající findings (44)

Viz `reports/2026-08-17-2013/summary.md` — rozložení:

| Projekt | Recommended | Nice-to-have |
|---|---|---|
| krizky (core) | 5 | 3 |
| krizky-photos | 4 (–1 blocker vyřešen) | 2 |
| krizky-json | 3 | 2 |
| krizky-map | 6 | 3 |
| krizky-share | 5 | 2 |
| krizky-filters | 6 (–1 blocker vyřešen) | 3 |

### Priorizace pro next session

Dle `summary.md` sekce "Top priority":

1. **Konsolidace do core** (3 strong kandidáti; největší impact):
   - `_copy_assets` idempotent helper nebo nový hook `copy_plugin_assets` (map + share + filters replikují ~60 LOC).
   - `register_plugin_templates` helper (map + share + filters replikují ~30 LOC).
   - `resolve_path(config_dir)` helper (photos + map).
   - Jsou **cross-repo** → nejdřív core commit, pak každý plugin.
2. **Cross-plugin coupling:** map + filters čtou `sources.photos.base_url`.
3. **Naming/code hygiena:** `FilterPlugin` → `FiltersPlugin`, `FetchError` kolize core↔photos, chybějící loggery v json + filters.
4. **Docs debt:** přidat `CLAUDE.md` do pluginů, `PLAN.md` do filters, aktualizovat core `PLAN.md`.

### Spotted-not-fixed (ne v reportu, zazanamenáno z předchozí session)

- `_plugins/krizky-filters/krizky_filters/plugin.py:25` — ruff `UP028` doporučuje `yield from`. Nice-to-have.
- **Core CLI postrádá top-level plugin-exception wrapper.** Po blocker fixu v krizky-photos uživatel teď dostane raw `FocalPointsError` traceback místo pretty Click erroru. Doporučuji přidat jako nový finding do `core.md` (severity: recommended). Core by měl v CLI obalit volání plugin hooků a přepakovat unhandled exceptions.

### Policy decisions během minulé session

- **`from __future__ import annotations`** se v novém kódu nepíše (Python 3.12+); existující usage se neodstraňuje proaktivně. Zapsáno v `.claude/skills/implement-review/guidelines/python.md`.
- Finding "filters chybí `from __future__`" **zamítnut** per tato policy.

## Environmentální poznámky pro pokračování

- `uv` není v sandbox PATH → používat `ruff` přímo, `python -m pytest` místo `uv run pytest`. Skill guideline v `python.md` mluví jen o `uv run` — fallback je ověřený.
- Git identita v plugin repech není nastavená → inline `git -c user.name=... -c user.email=... commit` (safety protocol: žádná trvalá změna gitconfigu).
- `.eslintrc` / `.prettierrc` configy chybí v pluginech → JS verifikace jen `node --check`. Přidání configů je samostatný finding (viz `guidelines/javascript.md`).

## Jak pokračovat v další session

### Doporučený prompt pro další session

```
Jsme uprostřed implementace findings z reports/2026-08-17-2013/.
Blockers jsou hotové (commits b3af0a2 ve filters, bba6905 v photos).

Přečti stav v work/2026-10-08-01-pending-review-findings.md a pokračuj
podle skillu .claude/skills/implement-review/. Začni s nejvyšší prioritou
podle summary.md — konsolidace do core (copy_plugin_assets +
register_plugin_templates). Je to cross-repo change: nejdřív commit v core,
pak po jednom v krizky-map, krizky-share, krizky-filters.

Před každým commitem ověř (ruff + pytest + node --check) a drž se policy
z guidelines/ (zejména: žádné from __future__ v novém kódu, 1:1 Py↔JS naming).
Nepushuj.
```

### Alternativní směry (pokud nechceš cross-repo rovnou)

- `/implement-review recommended krizky-filters` — zbývajících 6 recommended v jednom pluginu.
- `/implement-review hooks` — jen hook changes (přidat `copy_plugin_assets`, dokumentovat reserved hooky).
- `/implement-review docs` — docs debt (CLAUDE.md do pluginů, filters/PLAN.md, core/PLAN.md).

## Soubory a kontext

- Report: `reports/2026-08-17-2013/`
- Implementation log (append-only paper trail): `reports/2026-08-17-2013/implementation-log.md`
- Skill zdroje: `skills/review-consistency/`, `skills/implement-review/`
- Skill runtime: `.claude/skills/review-consistency/`, `.claude/skills/implement-review/`
