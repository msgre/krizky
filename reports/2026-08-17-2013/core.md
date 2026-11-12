# krizky (core) — revize konzistence

Datum: 2026-08-17 20:13
Reviewer: Claude Code (review-consistency skill)

## Souhrn

- 0 blocker
- 5 recommended
- 3 nice-to-have

Nejdůležitější zjištění: v core chybí sdílené API pro tři vzorce, které pluginy opakovaně implementují (template loader, copy assets, resolve config path). `register_page_processor` a `after_sources_fetched` hookspecs nemají žádnou implementaci — je potřeba rozhodnout, jestli jsou reservované nebo mrtvé. Core `PLAN.md` je zastaralý (odkazuje na starou museum-inspirovanou fázi projektu).

## Zjištění

### Hooky

#### [recommended] `register_page_processor` a `after_sources_fetched` nemají žádnou implementaci

**Kde:** `krizky/hooks.py:53-65` (`register_page_processor`), `krizky/hooks.py:117-127` (`after_sources_fetched`)

**Co:** Oba hookspecs jsou definované v core, ale žádný z 5 pluginů (ani žádný built-in) je neimplementuje.

**Proč vadí:** Nevyužité hookspecs zvyšují kognitivní zátěž při čtení plugin API a matou nové plugin autory ("proč to tam je, co to dělá?"). Zároveň hrozí, že se signatura při reálné implementaci ukáže jako špatně navržená.

**Doporučení:** Rozhodnout: (a) doplnit do docstringu explicitní "reserved for future — no implementations yet"; (b) odstranit, dokud pro to nebude reálná potřeba. `firstresult=True` na `register_page_processor` navíc naznačuje escape-hatch pattern pro custom page types — má reálnou motivaci? Pokud ne, `nice-to-have` → recommended smazat.

**Reference:** Viz `proposals/hook-changes.md`.

#### [recommended] Chybí hook pro copy-once assets

**Kde:** používají `_copy_assets` s per-instance idempotency guardem: `_plugins/krizky-map/krizky_map/plugin.py:333-359`, `_plugins/krizky-share/krizky_share/plugin.py:151-161`, `_plugins/krizky-filters/krizky_filters/plugin.py:174-182`

**Co:** Tři pluginy implementují stejný pattern "zkopíruj své assety do `<output_dir>/<plugin_name>/` právě jednou za build". Každý má vlastní `self._assets_copied: set[str]` guard. Framework nemá centrální mechanismus.

**Proč vadí:** Duplikace + drobné rozdíly v implementaci (filters používá `shutil.copytree`+`rmtree`, map/share používají `shutil.copy2` v cyklu → různá sémantika pro odstraněné soubory).

**Doporučení:** Přidat hook nebo helper — viz `proposals/hook-changes.md` sekce "Add hook: copy_plugin_assets" a `proposals/consolidation-to-core.md`.

#### [recommended] Chybí helper pro registraci plugin templates

**Kde:** `krizky-map/plugin.py:131-140`, `krizky-share/plugin.py:68-78`, `krizky-filters/plugin.py:99-112`

**Co:** Tři pluginy replikují stejnou logiku manipulace s `ChoiceLoader`/`FileSystemLoader` — kontrola, jestli je loader už zaregistrovaný, a vložení na správnou pozici (za projekt, před built-in).

**Proč vadí:** ~10 řádků kódu × 3 pluginy = 30 řádků kopy-paste s možností drobných rozdílů. Nový plugin bude muset tento pattern opsat znovu.

**Doporučení:** Přidat helper `krizky.plugin_helpers.register_plugin_templates(env, path)` (jen helper, ne nový hook — `prepare_jinja2_environment` je pro to správný moment). Viz `proposals/consolidation-to-core.md`.

### Python style

#### [recommended] Kolize jmen: `FetchError` je v core i v `krizky-photos`

**Kde:** `krizky/fetch.py:13` (`class FetchError`) a `_plugins/krizky-photos/krizky_photos/fetch.py:10` (`class FetchError`)

**Co:** Dvě různé třídy se stejným jménem existují ve dvou různých modulech. Obě reprezentují "fetch selhal", ale sémantiky se liší (core = zdroje z Google Sheets/Docs, photos = Google Drive metadata).

**Proč vadí:** Matoucí při čtení tracebacku a při importech. Kdyby někdo v budoucnu udělal `from krizky.fetch import FetchError` a chytal by ji, plugin exception mu proteče.

**Doporučení:** Přejmenovat plugin verzi (`PhotoFetchError` nebo `GDriveFetchError`), nebo přejmenovat core verzi (`SourceFetchError`). Preferuji přejmenování plugin verze — core jméno je jasnější, protože je "master" pro fetch pipeline.

### Dokumentace

#### [recommended] `PLAN.md` v core je zastaralý

**Kde:** `PLAN.md:1-50` (poslední změna 2026-08-12)

**Co:** Top popisuje původní projekt Valašská Knínica/muzeum jako motivaci pro krizky. Plugin systém je v samostatném `PLAN_PLUGIN.md`, ale hlavní `PLAN.md` na něj neodkazuje a stále popisuje state, který už neplatí.

**Proč vadí:** Nový přispěvatel čte `PLAN.md` jako plán a získá špatnou představu o rozsahu core.

**Doporučení:** Aktualizovat top `PLAN.md` (buď na "současné hlavní směry", nebo přejmenovat na `HISTORY.md` a plán psát znovu od nuly), přidat odkaz na `PLAN_PLUGIN.md`.

#### [nice-to-have] Docstring `prepare_jinja2_environment` obsahuje zastaralou "backward-compat" poznámku

**Kde:** `krizky/hooks.py:19-21`

**Co:** Docstring říká: "Adding `config_dir` is backward-compatible in pluggy: plugins that do not need it simply omit it from their method signature." Ale všechny 4 pluginy, které tento hook implementují (photos, map, share, filters), `config_dir` reálně používají.

**Proč vadí:** Poznámka byla relevantní během migrace, teď je jen šum.

**Doporučení:** Odstranit poznámku, nebo přesunout do `PLAN.md`/CHANGELOG jako historickou informaci.

#### [nice-to-have] Sekce v README má drobné odchylky vůči plugin READMEs

**Kde:** `README.md`

**Co:** Core používá strukturu: Instalace → Nový projekt → Konfigurace → Workflow → CLI → Adresářová struktura. Většina pluginů má: Instalace → Konfigurace → Nutné úpravy šablon → [plugin-specific] → Licence. Není to špatně (core dělá jiný job než plugin), ale některé záhlaví by šla sladit (např. konzistentní pojmenování "Nutné úpravy šablon" vs. "Použití v šablonách" napříč).

**Proč vadí:** Kosmeticky. Čtenář, který proletí několik READMEs za sebou, cítí, že "něco není stejné" i když se to týká jen záhlaví.

**Doporučení:** Volitelné. Až budeš psát `proposals/config-style-guide.md`, uveď tam i doporučenou README kostru pro pluginy (a případně pro core zvlášť).

### Testy

#### [nice-to-have] Chybí `conftest.py` a shared testing helpers

**Kde:** `tests/` (jen individuální test_*.py), plus duplikát v `_plugins/krizky-json/tests/test_json_plugin.py`

**Co:** Core testy definují `_make_db()`, `_setup()`, `_base_config()` helpery ad-hoc. Krizky-json ten samý `_make_db()` znovu opsal do svého testu. Žádný `conftest.py` neexistuje.

**Proč vadí:** Kdyby core přidal 6. plugin, opsal by _make_db znovu. Kdyby se změnila schema, musí se to změnit ve všech kopiích.

**Doporučení:** Vytáhnout do `krizky/testing.py` (public helper modul, který pluginy importují ve svých testech). Viz `proposals/consolidation-to-core.md`.
