# Specifikace: plugin-helpers

- **Repo:** `krizky` (core)
- **Zdroj:** revize konzistence `reports/2026-08-17-2013/` (`summary.md` body 1 a 2, `proposals/consolidation-to-core.md` kandidáti 1 až 3, `proposals/hook-changes.md` P0). Rozsah se ujasnil 2026-11-13.
- **Navazuje:** běhy `map-core-helpers`, `share-core-helpers`, `filters-core-helpers` a `photos-core-helpers` v repech pluginů. Ty začnou až po sloučení tohoto běhu do `main` a používají jména z této specifikace.

## Cíl

Pluginy map, share a filters dnes každý po svém registrují své šablony do Jinja2 a kopírují své assety do výstupu. Při kopírování si samy hlídají, aby kopírovaly jen jednou za build, a kopírují z `after_page_written`. map a photos si samy řeší cesty z configu relativní k adresáři configu. Core převezme tyto části, aby je pluginy nemusely opakovat:

- nový hook `copy_plugin_assets`, který core zavolá jednou za build,
- modul `krizky/plugin_helpers.py` s pomocnými funkcemi pro pluginy.

Chování buildu bez pluginů se nemění.

## 1. Hook `copy_plugin_assets`

- `krizky/hooks.py`: nová hookspec `copy_plugin_assets(self, output_dir, config, config_dir)`. Volají se všechny implementace, návratová hodnota se ignoruje.
- `krizky/site.py`: core ji zavolá právě jednou za `build_site`:
  - až po zkopírování assetů projektu (`_copy_assets` v `_generate`),
  - před vykreslením první stránky (tedy před prvním `after_page_written`).
- Argumenty: `output_dir` je absolutní cesta k výstupu webu, `config` je celý config, `config_dir` je adresář s `config.yaml`.
- Docstring popisuje, kdy se hook volá, že ho core volá jednou za build (plugin si nemusí hlídat opakované kopírování) a že assety mají patřit do `output_dir/<jméno-pluginu>/`.

**Akceptace:**
- Test: plugin registrovaný v testu dostane během `build_site` přesně jedno volání `copy_plugin_assets` se správným `output_dir`, `config` a `config_dir`, a to i když build vykreslí víc stránek.
- Test: volání proběhne před prvním `after_page_written` a po zkopírování assetů projektu (plugin v hooku vidí soubory z `site.assets` ve výstupu).

## 2. Modul `krizky/plugin_helpers.py`

Veřejné funkce pro pluginy. Každá má docstring a testy v `tests/test_plugin_helpers.py`.

### `register_plugin_templates(env, templates_dir)`

Vloží `FileSystemLoader(templates_dir)` do `ChoiceLoader` prostředí `env` hned za první loader (šablony projektu) a před ostatní (vestavěné šablony core). Šablony projektu tak můžou přebít šablony pluginu a šablony pluginu přebijí vestavěné.

- Opakované volání se stejnou cestou loader nepřidá znovu.
- Když `env.loader` není `ChoiceLoader`, funkce nic neudělá (stejně jako dnes v pluginech).
- Odpovídá dnešnímu kódu v `prepare_jinja2_environment` pluginů map, share a filters.

**Akceptace (testy):**
- Pořadí loaderů po volání: projekt, plugin, vestavěné.
- Šablona stejného jména v projektu má přednost před šablonou pluginu, šablona pluginu před vestavěnou.
- Dvojí volání přidá loader jen jednou.
- `env` bez `ChoiceLoader` zůstane beze změny.

### `replace_tree(source, target)`

Zkopíruje adresář `source` do `target`. Když `target` existuje, nejdřív ho celý smaže, aby ve výstupu nezůstaly soubory, které plugin už nemá. Chybějící nadřazené adresáře `target` vytvoří. Stejně dnes kopíruje assety projektu core i plugin filters.

**Akceptace (testy):**
- Zkopíruje soubory i podadresáře.
- Soubor, který je v `target`, ale není v `source`, po volání v `target` není.
- Funguje i když `target` ani jeho nadřazený adresář neexistují.

### `resolve_path(path, config_dir)`

Převede cestu z configu na absolutní `Path`:
- `None` nebo prázdný řetězec vrátí `None`,
- relativní cestu vyhodnotí vůči `config_dir` a vrátí `.resolve()`,
- absolutní cestu vrátí jako `.resolve()` beze změny umístění.

Přijímá `str` i `Path`.

**Akceptace (testy):** všechny tři případy výše, `str` i `Path` na vstupu.

## 3. Verze core

- `pyproject.toml`: verze `0.2.0`.
- Důvod: pluggy hookimpl pro hook, který core nezná, tiše ignoruje (ověřeno 2026-11-13). Plugin s `copy_plugin_assets` by se starým core vůbec nezkopíroval assety. Pluginy proto v navazujících bězích budou vyžadovat `krizky>=0.2`.

**Akceptace:** `uv run python -c "import importlib.metadata as m; print(m.version('krizky'))"` vypíše `0.2.0`.

## 4. Dokumentace (docs-sync)

- `docs/plugins.md`:
  - sekce hooku `copy_plugin_assets` mezi dostupnými hooky (kdy se volá, argumenty, příklad s `replace_tree`),
  - nová sekce „Pomocné funkce pro pluginy“ se třemi funkcemi z části 2 a krátkým příkladem použití v `prepare_jinja2_environment` a `copy_plugin_assets`,
  - konvence: assety pluginu patří do `output_dir/<jméno-pluginu>/`, šablony pluginu do jeho adresáře `templates/`,
  - pokud příklady v dokumentu kopírují assety z `after_page_written`, přepsat je na nový hook.
- `PLAN_PLUGIN.md`: řádek nového hooku v tabulce hooků.
- `README.md` core: aktualizovat, pokud popisuje hooky nebo plugin API.

**Akceptace:**
- Dokumentace popisuje hook, všechny tři funkce a konvenci umístění assetů.
- `scripts/verify` projde.

## Mimo rozsah (rozhodnuto 2026-11-13)

- **Úpravy pluginů:** samostatné běhy v jejich repech po sloučení tohoto běhu.
- **Použití `resolve_path` uvnitř core:** core si cesty řeší dál po svém, helper je pro pluginy.
- **`krizky.testing.make_db` a helpery pro tagy `<link>` a `<script>`** z návrhu konsolidace: zatím ne.
- **`work/OVERVIEW.md`:** píše ho jen závěrečný agent. Při zápisu svého řádku opraví i dva zastaralé: úklid core je DONE (PR `swarm-setup` #2 sloučený) a `hooks-errors` je DONE (finální PR #5 sloučený).

## Poznámky pro plánovače

- Části 1 a 2 jsou nezávislé (`hooks.py` + `site.py` proti novému `plugin_helpers.py`). Část 4 popisuje obě, nech ji na konec, nebo ji rozděl k nim.
- Testy plugin hooků s pluginem registrovaným v testu už v `tests/` jsou (běh `hooks-errors`), použij je jako vzor.
