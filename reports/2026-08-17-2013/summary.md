# Souhrn revize konzistence — krizky ekosystém

Datum: 2026-08-17 20:13
Rozsah: full sweep (žádný focus projekt)

Projekty v revizi:
- `krizky` (core) — viz [core.md](core.md)
- `krizky-photos` — viz [plugin-krizky-photos.md](plugin-krizky-photos.md)
- `krizky-json` — viz [plugin-krizky-json.md](plugin-krizky-json.md)
- `krizky-map` — viz [plugin-krizky-map.md](plugin-krizky-map.md)
- `krizky-share` — viz [plugin-krizky-share.md](plugin-krizky-share.md)
- `krizky-filters` — viz [plugin-krizky-filters.md](plugin-krizky-filters.md)

Proposals:
- [Kandidáti na konsolidaci do core](proposals/consolidation-to-core.md)
- [Návrhy na změny plugin API](proposals/hook-changes.md)
- [Config style guide (návrh)](proposals/config-style-guide.md)

---

## Top priority

Sestupně dle dopadu:

1. **Konsolidovat `_copy_assets` pattern do core (nebo nový hook `copy_plugin_assets`).** 3 pluginy replikují ~60 LOC + diverging sémantika (filters agresivně maže, ostatní ne). → [consolidation #1](proposals/consolidation-to-core.md#1-_copy_assets--copy-once-idempotent-asset-copy-do-output) + [hook proposal](proposals/hook-changes.md#přidat-hook-copy_plugin_assets).

2. **Konsolidovat `register_plugin_templates` do core.** 3 pluginy replikují ~30 LOC identické manipulace s ChoiceLoaderem. → [consolidation #2](proposals/consolidation-to-core.md#2-template-registrace-přes-choiceloader--vložit-plugin-templates-do-jinja2).

3. **Blocker: `krizky-filters` přejmenovává `pagination_window` → `window` v JS.** Kolize s built-in `window` globálem. → [plugin-krizky-filters.md](plugin-krizky-filters.md#blocker-config-klíče-pagination_window--window-a-pagination_boundary--boundary--přejmenované-ne-jen-camelcase).

4. **Blocker: `krizky-photos` vyhazuje `click.ClickException` z `prepare_jinja2_environment` hooku** (build hook, ne CLI hook). → [plugin-krizky-photos.md](plugin-krizky-photos.md#blocker-clickclickexception-vyhazován-z-hooku-který-nemusí-běžet-v-click-kontextu).

5. **Cross-plugin coupling:** map + filters čtou `sources.photos.base_url` přímo z configu. Fragile. → [config-style-guide sekce Cross-plugin data reference](proposals/config-style-guide.md#cross-plugin-data-reference).

6. **Naming rozjezd:** třída `FilterPlugin` (singular) vs package `krizky_filters` (plural). Ostatní pluginy konzistentní. → [plugin-krizky-filters.md](plugin-krizky-filters.md).

7. **Kolize jmen exceptions:** `FetchError` v core i v `krizky-photos`. → [core.md](core.md#recommended-kolize-jmen-fetcherror-je-v-core-i-v-krizky-photos).

8. **Dva plugin (json, filters) postrádají logger.** → per-plugin reporty.

9. **Nevyužité hookspecs:** `register_page_processor` a `after_sources_fetched` — 0 implementací. Rozhodnout: reserved nebo remove. → [hook proposal](proposals/hook-changes.md#odstranit--dokumentovat-jako-reserved-register_page_processor).

10. **Docs debt:** žádný plugin nemá `CLAUDE.md`; `krizky-filters` nemá `PLAN.md`; core `PLAN.md` je zastaralý.

---

## Vzorce napříč projekty

### Duplicitní logika assetů (map + share + filters)

**Kde:** viz per-plugin reporty pro odkazy na řádky.

**Popis:** Tři pluginy s vlastními JS/CSS assety implementují stejnou logiku (registrace templates, kopírování do output, idempotence) třikrát, s drobnými odchylkami.

**Návrh:** konsolidovat do `krizky/plugin_helpers.py` (helper) a/nebo nového hooku `copy_plugin_assets`.

**Detail:** [consolidation #1 + #2](proposals/consolidation-to-core.md), [hook proposal](proposals/hook-changes.md#přidat-hook-copy_plugin_assets).

### Cross-plugin coupling na photos config

**Kde:** `krizky-map/plugin.py:143-144`, `krizky-filters/plugin.py:76`.

**Popis:** Dva pluginy sahají do `sources.photos.base_url` konfigurace bez formálního API. Kdyby photos přejmenoval, obě rozbije.

**Návrh:** duplikovat do vlastního configu, dokud nebude potřeba formální shared context.

**Detail:** [config-style-guide sekce Cross-plugin](proposals/config-style-guide.md#cross-plugin-data-reference).

### Chybějící logger v dvou pluginech (json, filters)

**Kde:** `krizky-json/plugin.py`, `krizky-filters/plugin.py`.

**Popis:** Photos, map, share mají `_log = logging.getLogger(__name__)`. Json a filters nikdo.

**Návrh:** Přidat modul-level logger. Jednořádková změna, ale konzistentní napříč.

### Chybějící `CLAUDE.md` a nekonzistentní docs kostra

**Kde:** všechny pluginy.

**Popis:** Core zavedl `CLAUDE.md` konvenci, žádný plugin ji nepřijal. Docs struktura variuje (jen filters má `docs/`; jen filters nemá `PLAN.md`).

**Návrh:** Přidat minimální `CLAUDE.md` do každého pluginu; doplnit `krizky-filters/PLAN.md`; aktualizovat core `PLAN.md`.

### Hardcoded Czech UI text v JS (map + share + filters)

**Kde:** `map.js` ("Otevřít detail", "Vaše poloha"), `share.js` ("Zkopírováno"), `filters.js` ("předchozí", "další", "Stránkování").

**Popis:** Žádný plugin nemá i18n mechanismus. Ekosystém je CZ-first, takže OK; ale flag do budoucnosti.

**Návrh:** ne teď. Až budou 2+ non-CZ deployments, sjednotit i18n mechanism (config `locale`, plugin dostane překlady).

### Design tokeny bez `--krizky-*` prefixu (share + map)

**Kde:** `share.css`, `map.css` čtou `--surface`, `--hairline`, `--muted`, `--ink`, `--radius`, `--mono`.

**Popis:** Pluginy expektují CSS proměnné od uživatelova projektu (Valašské nebe designový systém). Fallbacky existují.

**Návrh:** dvě cesty (viz [plugin-krizky-share.md](plugin-krizky-share.md#recommended-css-design-tokeny-bez---krizky--prefixu--leakage-projektu-valašské-nebe-do-obecného-pluginu)) — přidat plugin-specific tokeny s cascade, nebo formalizovat "plugin vyžaduje X tokenů".

---

## Kandidáti na konsolidaci do core (top 5)

| # | Kandidát | Síla | LOC úspora |
|---|---|---|---|
| 1 | `_copy_assets` idempotency | strong | ~40-50 |
| 2 | `register_plugin_templates` helper | strong | ~20-25 |
| 3 | `resolve_path(config_dir)` helper | medium | ~10-15 |
| 4 | `krizky.testing.make_db()` | medium | ~20 |
| 5 | `plugin_stylesheet`/`_script` helper | weak-medium | ~5 |

Detaily + kód: [consolidation-to-core.md](proposals/consolidation-to-core.md).

---

## Návrhy na změny plugin API

| Priorita | Akce | Riziko |
|---|---|---|
| **P0** | Přidat hook `copy_plugin_assets` (souběžně s consolidation #1) | Low |
| **P1** | Dokumentovat `register_page_processor` jako reserved (nebo odstranit) | 0 |
| **P1** | Dokumentovat `after_sources_fetched` jako reserved (nebo odstranit) | 0 |
| **P1** | Zjednodušit docstring `prepare_jinja2_environment` (odstranit historickou poznámku) | 0 |
| **P3** | Zvážit `provide_shared_context` až bude reálná potřeba | — |

Detaily: [hook-changes.md](proposals/hook-changes.md).

---

## Statistiky

### Rozložení podle projektu

| Projekt | Blocker | Recommended | Nice-to-have | Celkem |
|---|---|---|---|---|
| krizky (core) | 0 | 5 | 3 | 8 |
| krizky-photos | 1 | 4 | 2 | 7 |
| krizky-json | 0 | 3 | 2 | 5 |
| krizky-map | 0 | 6 | 3 | 9 |
| krizky-share | 0 | 5 | 2 | 7 |
| krizky-filters | 1 | 6 | 3 | 10 |
| **Celkem** | **2** | **29** | **15** | **46** |

### Rozložení podle tématu

| Téma | Findings |
|---|---|
| Duplikace / consolidation | 12 (napříč map, share, filters, photos, json) |
| Hooky | 5 (core hookspecs + implementace) |
| Python style | 8 (naming, future, logger, exceptions) |
| JS style / Py↔JS naming | 5 (var-vs-const, klíče shortening) |
| Konfigurace | 6 (placement, cross-plugin coupling, path resolution) |
| Error handling / logging | 4 |
| Dokumentace | 8 (CLAUDE.md, PLAN.md, README kostra) |

### Poznámky ke skenu

- Skip: `.venv/`, `__pycache__/`, `.pytest_cache/`, `node_modules/`, vendored třetí strany.
- Skenováno: `krizky/`, `_plugins/krizky-{photos,json,map,share,filters}/`.
- Skill: `.claude/skills/review-consistency/` (v1).
- Nespuštěno: klasická dead-code analysis nad všemi exportovanými symboly (vyžadovala by hlubší cross-reference sken — dodělat v případě zájmu samostatně).

### Doporučené další kroky

1. **Přečíst `summary.md` + relevantní per-project reporty**, roztřídit findings do (a) uděláme hned, (b) parkujeme, (c) nesouhlasíme.
2. **Začít s konsolidací:** hook `copy_plugin_assets` + helper `register_plugin_templates` v jednom PR do core. Pak PR do každého ze 3 pluginů, který ji přijme.
3. **Blockers:** dva rychlé PR — přejmenovat JS klíče v filters, přepsat photos exception handling.
4. **Docs debt:** vlastní session — jeden PR "Add CLAUDE.md to all plugins" + update core PLAN.md.
5. **Cross-plugin coupling:** rozhodnout přístup (duplikace vs helper vs shared context). Podle rozhodnutí PR do map + filters.
