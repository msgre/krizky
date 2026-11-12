# Návrhy na změny plugin API

Odvozeno z revize 2026-08-17. Zaměření: adekvátnost současné sady hookspecs vůči skutečnému užití 5 pluginů.

## Matice využití

| Hook | photos | json | map | share | filters | # impl. |
|---|---|---|---|---|---|---|
| `prepare_jinja2_environment` | ✓ | | ✓ | ✓ | ✓ | 4 |
| `extra_template_vars` | | | | | ✓ | 1 |
| `register_commands` | ✓ | | | | | 1 |
| `register_page_processor` (firstresult) | | | | | | **0** |
| `after_page_written` | | ✓ | ✓ | ✓ | ✓ | 4 |
| `inject_head` | ✓ | | ✓ | ✓ | ✓ | 4 |
| `inject_body_end` | | | ✓ | ✓ | ✓ | 3 |
| `after_sources_fetched` | | | | | | **0** |

---

## Přidat hook: `copy_plugin_assets`

**Motivace:** vzorec, který 3 pluginy (map, share, filters) řeší ad-hoc s vlastním `_assets_copied: set` guardem. Sémantiky se drobně liší. Viz `plugin-krizky-map.md` a `proposals/consolidation-to-core.md` kandidát #1.

**Signatura:**
```python
@hookspec
def copy_plugin_assets(self, output_dir: Path, config: dict) -> None:
    """Called once per build to copy plugin assets into the output directory.

    Fires before the first `after_page_written` call. Framework guarantees
    idempotency (called at most once per output_dir per build).

    Plugins that don't ship assets simply omit this hook.

    Args:
        output_dir: Path to the site output directory.
        config: Full krizky config dict.
    """
```

**Kdo by ho implementoval:** map, share, filters (3 pluginy z 5). Photos ne (nemá assets, injektuje inline JS).

**Alternativy zvažované:**
- **Helper místo hooku** (`AssetCopier` třída z `krizky.plugin_helpers`) — jednodušší, ale plugin musí volat `self._copier.copy_once(output_dir)` uvnitř `after_page_written`. Coupling na page hook.
- **Deklarativní API** — plugin v `__init__` řekne `self.assets = [(source, dest)]`, framework je zkopíruje. Nejčistší, ale nejinvazivnější změna.
- **Event bus** — přehnaně komplexní pro tento use case.

**Preferuji: nový hook `copy_plugin_assets`.** Explicitně signalizuje lifecycle bod, framework zaručí idempotency, kód pluginu se zjednoduší z ~15 řádků na ~5.

**Migrace:** plugin `MapPlugin._copy_assets` přejde do `MapPlugin.copy_plugin_assets(self, output_dir, config)`. Guard `self._assets_copied` se odstraní (framework).

**Riziko:** map plugin má `_copy_assets` volání i **před** `after_page_written` (v `_register_data_urls` — sanity check). Refactor musí zajistit, že map může spoléhat na `copy_plugin_assets` firing předtím, než začne první render.

---

## Odstranit / dokumentovat jako reserved: `register_page_processor`

**Aktuální signatura:**
```python
@hookspec(firstresult=True)
def register_page_processor(self, page_cfg):
    """Return a PageProcessor for *page_cfg*, or None to defer to core."""
```

**Důvod k řešení:** 0 implementací napříč všemi 5 pluginy. `firstresult=True` naznačuje escape-hatch pattern pro custom page types (kdyby plugin chtěl přebít core `detail`/`category`/`simple`).

**Doporučení:**
1. **Ponechat jako reserved** — přidat do docstringu explicitní "No implementations yet — reserved for plugins that need custom page types beyond core `detail`/`category`/`simple`." Toto je nejméně invazivní.
2. **Odstranit** — pokud za 6 měsíců stále 0 implementací a žádný plugin autor to nechtěl, znamená to, že API not needed. Odstranění je bezpečné (0 implementations = 0 breaking changes).

Preferuji (1) — API je konceptuálně jasné a levné držet.

**Riziko:** 0.

---

## Odstranit / dokumentovat jako reserved: `after_sources_fetched`

**Aktuální signatura:**
```python
@hookspec
def after_sources_fetched(self, config, config_dir, sources_output):
    """Called after all tables and docs are fetched and transformed."""
```

**Důvod k řešení:** 0 implementací. Použitelné pro pluginy, které chtějí zpracovat data hned po fetchi (např. build search index, validate schema).

**Doporučení:** Ponechat jako reserved (analogicky s `register_page_processor`). Zvažit, jestli by krizky-filters mohl z toho těžit — teď filters generuje filter JSON až v `after_page_written`, ale mohl by ho generovat jednou v `after_sources_fetched` (výkonově lepší). Pokud ano, hook má reálný use case a stojí za to.

**Akce:** nechat, přidat do docstringu poznámku o "reserved for future".

---

## Zjednodušit docstring: `prepare_jinja2_environment`

**Aktuální docstring (řádky 19-21):**
> Adding `config_dir` is backward-compatible in pluggy: plugins that do not need it simply omit it from their method signature.

**Motivace:** všichni 4 implementátoři (photos, map, share, filters) `config_dir` **používají**. Poznámka byla relevantní během migrace, teď je jen šum.

**Doporučení:**
1. Odstranit poznámku z docstringu.
2. Přesunout do `PLAN.md` nebo `CHANGELOG` jako historický záznam ("v0.X: added config_dir to prepare_jinja2_environment; backward-compatible via pluggy").

**Riziko:** 0. Historie zachována v gitu.

---

## Zvážit: nový hook `provide_shared_context` pro cross-plugin data sharing

**Motivace:** map i filters čtou `sources.photos.base_url` (viz `plugin-krizky-map.md` a `plugin-krizky-filters.md`). Tj. sahají do configu jiného pluginu, což znamená (a) implicit ordering (photos config musí existovat, když map/filters startují), (b) fragile když photos přejmenuje klíč.

**Návrh:**
```python
@hookspec
def provide_shared_context(self) -> dict:
    """Return a dict merged into a shared context that other plugins can read.

    Called once per build after prepare_jinja2_environment. Keys are namespaced
    by plugin (framework prepends plugin name). Access via env.globals['plugin_context'].
    """
```

Photos by vracelo `{"photos_base_url": ..., "photo_sizes": [...], "focal_points_available": bool}`. Map by četl `env.globals["plugin_context"]["photos"]["photos_base_url"]`.

**Kdo by ho implementoval:** photos primárně. Consumers: map, filters (a jakýkoli budoucí plugin).

**Alternativy:**
- **Config-level klíč** (option b v report doporučeních) — map dostane `map.thumbnail_base_url` v vlastním configu, uživatel duplikuje URL. Duplikace configu = user pain, ale žádné cross-plugin coupling.
- **Přímý import** — `from krizky_photos import get_photos_base_url(config)` — pluginy jsou pak volitelně vázané (map.pyproject.toml má `krizky-photos` jako optional dep). Křehké.

**Doporučení:** ne teď. `provide_shared_context` je zajímavý, ale je to preemptivní API. Zvážit až budou 3+ pluginy potřebovat cross-plugin data. Teď jde o 2 spotřebitele 1 hodnoty (`base_url`) → radši option (b): map/filters dostanou vlastní `thumbnail_base_url` config klíč.

**Zaznamenávám jako "reserved thought", ne návrh na okamžitou implementaci.**

---

## Souhrn akcí

| Priorita | Akce | Riziko |
|---|---|---|
| **P0** | Přidat hook `copy_plugin_assets` (viz consolidation #1) | Low |
| **P1** | Dokumentovat `register_page_processor` jako reserved | 0 |
| **P1** | Dokumentovat `after_sources_fetched` jako reserved | 0 |
| **P1** | Zjednodušit docstring `prepare_jinja2_environment` | 0 |
| **P3** | Zvážit `provide_shared_context` až bude reálná potřeba | — |

P0 = udělat s consolidation-to-core refactorem. P1 = quick wins do docs. P3 = odložit.
