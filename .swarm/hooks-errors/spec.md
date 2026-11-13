# Specifikace: hooks-errors

- **Repo:** `krizky` (core)
- **Zdroj:** revize konzistence `reports/2026-08-17-2013/` (`summary.md` bod 9, `proposals/hook-changes.md` P1, `implementation-log.md` sekce „New findings spotted“). Rozsah se ujasnil 2026-11-13: hooky se odstraní, chyba z pluginu se vypíše jedním řádkem a celý traceback se ukáže jen s `-v`.

## Cíl

Uklidit plugin API před konsolidací do core (další běh) a dát uživateli srozumitelnou chybu, když plugin během buildu vyhodí výjimku.

Dnes:
- Hooky `register_page_processor` a `after_sources_fetched` nemá implementované žádný plugin, ale core je volá a dokumentace je nabízí.
- Když plugin v build hooku vyhodí vlastní výjimku (například `FocalPointsError` z `krizky-photos`), `krizky build site` skončí syrovým tracebackem. Ošetřené jsou jen `ConfigError` a `SiteError`.

## 1. Odstranění hooků `register_page_processor` a `after_sources_fetched`

- `krizky/hooks.py`: odstranit obě hookspec.
- `krizky/pages/__init__.py`: `process_page` už se neptá pluginů a rovnou vybírá mezi detail, category a simple.
- `krizky/fetch.py`: odstranit volání `after_sources_fetched` a parametr `pm` z `fetch_sources` (bez hooku ho nic nepotřebuje). Upravit docstring.
- `krizky/cli.py` (`fetch sources`): nevytvářet plugin manager a nepředávat `pm`.
- Žádný plugin (`../krizky-*`) tyto hooky ani `fetch_sources` nepoužívá, takže změna je jen v core.

**Akceptace:**
- Test: `KrizkySpec` (nebo hook relay plugin manageru) nemá `register_page_processor` ani `after_sources_fetched`.
- Test: `fetch_sources` nemá parametr `pm` a stávající testy fetche projdou.
- `git grep -n "register_page_processor\|after_sources_fetched" -- ':!.swarm' ':!work' ':!reports'` najde nanejvýš poznámku o odstranění v `PLAN_PLUGIN.md` (viz část 4).

## 2. Docstring `prepare_jinja2_environment`

- Odstranit historický odstavec o zpětné kompatibilitě parametru `config_dir`. Zbytek docstringu zůstane. Podobné poznámky v `docs/plugins.md` upravit stejně, pokud tam jsou.

**Akceptace:**
- Docstring neobsahuje text o zpětné kompatibilitě `config_dir`.

## 3. Chyby z pluginů v `krizky build site`

Když během `krizky build site` vznikne výjimka, kterou core neošetřuje (cokoli kromě `ConfigError` a `SiteError`), CLI:
- vypíše jeden červený řádek ve stejném stylu jako ostatní chyby:
  - výjimka vznikla v kódu pluginu: `ERROR: <plugin>: <TypVýjimky>: <zpráva>`,
  - jinak: `ERROR: <TypVýjimky>: <zpráva>`,
- bez `-v` připíše řádek s nápovědou, že celý traceback ukáže `-v` (`--verbose`, přepínač už existuje),
- s `-v` vypíše celý traceback,
- skončí s exit kódem 1 (`SystemExit(1)`, stejně jako u ostatních chyb).

`<plugin>` je jméno nejvyššího balíčku nebo modulu pluginu (například `krizky_photos`, u lokálního pluginu z `plugins/` jméno jeho souboru bez `.py`). Určí se z tracebacku: nejvnitřnější rámec, jehož modul patří k některému registrovanému pluginu. Když takový rámec není (chyba v core nebo v knihovně volané z core), jméno pluginu se nevypíše.

- `KeyboardInterrupt` a `SystemExit` se nezachytávají (zachytává se `Exception`).
- Ošetřené `ConfigError` a `SiteError` se vypisují beze změny.
- Nápověda k `-v` v `--help` zmíní i traceback.
- Ostatní příkazy (`fetch sources`, příkazy pluginů z `register_commands`) jsou mimo rozsah.

**Akceptace (testy přes `click.testing.CliRunner`):**
- Plugin registrovaný v testu vyhodí z `prepare_jinja2_environment` vlastní výjimku. Výstup obsahuje jméno pluginu, typ výjimky a zprávu, neobsahuje `Traceback`, obsahuje nápovědu k `-v` a exit kód je 1.
- Totéž s `-v`: výstup obsahuje traceback.
- Výjimka vzniklá mimo kód pluginu: řádek bez jména pluginu.
- `SiteError` se vypíše jako dosud (beze jména pluginu a bez nápovědy k `-v`).

## 4. Dokumentace (docs-sync)

- `docs/plugins.md`:
  - odstranit sekce obou hooků a upravit úvodní větu (dnes slibuje nové typy stránek a reakci na dokončení fetche),
  - příklad `SitemapPlugin` už nesmí používat `after_sources_fetched`,
  - nová sekce o chybách: plugin smí v build hoocích vyhazovat vlastní výjimky (ne `click.ClickException`), core je vypíše jedním řádkem se jménem pluginu, celý traceback ukáže `-v`.
- `PLAN_PLUGIN.md` (plugin API v plánu core): v tabulce hooků oba řádky odstranit nebo označit jako odstraněné 2026-11 a u nich nezaškrtnuté úkoly zrušit.
- `README.md` core: aktualizovat, pokud popisuje hooky nebo `-v`.

**Akceptace:**
- Dokumentace nezmiňuje odstraněné hooky jako dostupné a popisuje výpis chyb z pluginů.
- `scripts/verify` projde.

## Mimo rozsah (rozhodnuto 2026-11-13)

- **Kolize `FetchError` v core a `krizky-photos`:** vyřeší se přejmenováním v `krizky-photos` v rámci konsolidace (další běh), ne v core.
- **Konsolidace `_copy_assets` a registrace šablon do core** (`copy_plugin_assets`, `register_plugin_templates`): další běh.
- **Ošetření chyb v `fetch sources` a v příkazech pluginů.**
- **`work/OVERVIEW.md`:** píše ho jen závěrečný agent.

## Poznámky pro plánovače

- Části 1 a 2 sahají do `krizky/hooks.py`, část 3 do `krizky/cli.py`, část 1 také do `krizky/cli.py` (`fetch sources`). Tikety nad stejnými soubory pusť za sebou.
- pluggy výjimky z hooků nebalí, do CLI doletí původní výjimka s tracebackem.
- Plugin manager se v `build site` vytváří uvnitř `build_site` (`krizky/site.py`), CLI ho nemá. K určení pluginu ho CLI může vytvořit samo přes `get_plugin_manager(config_dir)`, nebo jde pluginy rozpoznat jinak. Rozhodnutí nech na implementaci, chování musí odpovídat části 3.
