---
id: "02"
slug: build-plugin-errors
title: Jednořádkový výpis chyb z pluginů v krizky build site
status: pending
depends_on: []
files:
  - krizky/cli.py
  - tests/test_cli.py
  - docs/plugins.md
  - README.md
attempts: 0
pr: ""
---

## Cíl
Když plugin během `krizky build site` vyhodí vlastní výjimku (například `FocalPointsError` z `krizky-photos`), uživatel dnes dostane syrový traceback. CLI místo toho vypíše jeden červený řádek se jménem pluginu, typem výjimky a zprávou. Celý traceback ukáže až s `-v`. Specifikace `.swarm/hooks-errors/spec.md`, část 3 a ta část 4, která se týká výpisu chyb.

## Akceptační kritéria
- `krizky build site` zachytí v bloku kolem `_build_site(...)` kromě `SiteError` i obecnou `Exception` (`KeyboardInterrupt` ani `SystemExit` ne) a:
  - vypíše jeden červený řádek (`click.style(..., fg="red")`, stejně jako ostatní chyby):
    - pokud výjimka vznikla v kódu pluginu: `ERROR: <plugin>: <TypVýjimky>: <zpráva>`,
    - jinak: `ERROR: <TypVýjimky>: <zpráva>`,
  - bez `-v` připíše řádek s nápovědou, že celý traceback ukáže `-v` / `--verbose`,
  - s `-v` vypíše celý traceback (text obsahuje `Traceback`),
  - skončí `raise SystemExit(1)`.
- `<plugin>` je jméno nejvyššího balíčku nebo modulu pluginu (například `krizky_photos`, u lokálního pluginu z `plugins/` jméno souboru bez `.py`). Určí se z tracebacku jako nejvnitřnější rámec, jehož modul (`frame.f_globals["__name__"]`, nejvyšší část před tečkou) patří některému registrovanému pluginu. Pokud takový rámec není, jméno pluginu se nevypíše.
- `ConfigError` a `SiteError` se vypisují beze změny: žádné jméno pluginu, žádná nápověda k `-v`.
- Text nápovědy přepínače `-v` v `--help` zmiňuje i traceback.
- `fetch sources` a příkazy pluginů (`register_commands`) se nemění.
- `docs/plugins.md` má novou sekci o chybách: plugin smí v build hoocích vyhazovat vlastní výjimky (ne `click.ClickException`), core je vypíše jedním řádkem se jménem pluginu a celý traceback ukáže `-v`. Uveď ukázku výstupu.
- `README.md`: řádek `krizky build site` v tabulce příkazů doplň o `-v` a o to, že přepínač ukáže i traceback chyby.
- `scripts/verify` projde.

## Testy
Napiš je nejdřív. Vzniknou v novém `tests/test_cli.py` přes `click.testing.CliRunner` a `krizky.cli.cli`:
- Projekt se postaví v `tmp_path`: `config.yaml` (YAML, musí projít `validate_config`), existující SQLite DB v `sources/`, adresář `templates/` s šablonou a lokální plugin `plugins/boom.py` s `class FocalPointsError(Exception)` a `plugin` objektem, jehož `@hookimpl prepare_jinja2_environment` výjimku vyhodí. DB a šablony musí existovat, protože `build_site` volá hook až po kontrole DB a adresáře šablon. Inspiraci najdeš v helperech `tests/test_site.py`.
  - Bez `-v`: exit kód 1, výstup obsahuje `boom`, `FocalPointsError` a zprávu, nápovědu k `-v` a neobsahuje `Traceback`.
  - S `-v` (`build site -v`): výstup obsahuje `Traceback`, exit kód 1.
- Výjimka mimo kód pluginu: například `monkeypatch.setattr("krizky.site.build_site", ...)` s funkcí, která vyhodí `RuntimeError("x")` (CLI importuje `build_site` až uvnitř funkce, takže monkeypatch zabere). Výstup obsahuje `ERROR: RuntimeError: x` bez jména pluginu, exit kód 1.
- `SiteError` (například chybějící DB): výstup jako dosud (`ERROR: Database not found…`), bez nápovědy k `-v`, exit kód 1.
- Doporučení: vytáhni čisté funkce (například určení jména pluginu z tracebacku podle množiny modulů pluginů a formátování chybového řádku) a otestuj je zvlášť jednotkovými testy.

## Poznámky
- pluggy výjimky z hooků nebalí, do CLI doletí původní výjimka s tracebackem.
- CLI plugin manager nemá, vytváří ho až `build_site` v `krizky/site.py`. Jména pluginů jde získat přes `get_plugin_manager(config_dir).get_plugins()` (u objektu `type(p).__module__`, u modulu `p.__name__`), nebo bez opětovného načtení: názvy souborů v `<config_dir>/plugins/*.py` plus moduly entry pointů skupiny `krizky`. Pozor, `get_plugin_manager` lokální pluginy znovu spouští (`exec_module`). Rozhodnutí je na tobě, chování musí odpovídat specifikaci.
- Lokální plugin se načítá přes `spec_from_file_location(py_file.stem, ...)`, takže `__name__` jeho rámců je stem souboru (`boom`).
- Rámce core (`krizky.*`) a knihoven (`jinja2`, `pluggy`) se za plugin nepovažují.
- `krizky/cli.py` upravuje i tiket 01 (jinou funkci, `fetch sources`). Měň jen `build_site` v CLI a nápovědu `-v`.
- `docs/plugins.md` upravuje i tiket 01 (mazání sekcí hooků). Tady jen přidej sekci o chybách.
- Guidelines: `docs/guidelines/python.md`, `docs/guidelines/docs-sync.md`, `docs/guidelines/security.md` (traceback jen s `-v`).

## Otázky
