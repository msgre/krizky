---
id: "01"
slug: remove-unused-hooks
title: Odstranit hooky register_page_processor a after_sources_fetched
status: pending
depends_on: []
files:
  - krizky/hooks.py
  - krizky/pages/__init__.py
  - krizky/fetch.py
  - krizky/cli.py
  - tests/test_hooks.py
  - tests/test_fetch.py
  - docs/plugins.md
  - PLAN_PLUGIN.md
attempts: 0
pr: ""
---

## Cíl
Uklidit plugin API: hooky `register_page_processor` a `after_sources_fetched` nemá implementované žádný plugin, a přesto je core volá a dokumentace je nabízí. Tiket je odstraní z kódu i z dokumentace a zároveň smaže zastaralou poznámku o zpětné kompatibilitě v docstringu `prepare_jinja2_environment`. Specifikace `.swarm/hooks-errors/spec.md`, části 1, 2 a ta část 4, která se týká odstraněných hooků.

## Akceptační kritéria
- `krizky/hooks.py`: `KrizkySpec` nemá hookspec `register_page_processor` ani `after_sources_fetched`. Ostatní hookspec zůstanou beze změny.
- Docstring `prepare_jinja2_environment` už neobsahuje odstavec „Adding ``config_dir`` is backward-compatible in pluggy…“. Zbytek docstringu (popis, `Args:`) zůstane.
- `krizky/pages/__init__.py`: `process_page` se neptá pluginů a rovnou vybírá mezi `detail`, `category` a `simple`. `RenderContext.pm` zůstává, protože ho dál používají jiné hooky (`after_page_written`, `inject_*`).
- `krizky/fetch.py`: `fetch_sources(config, config_dir, transform=False)` nemá parametr `pm` a hook nevolá. Docstring odpovídá nové signatuře.
- `krizky/cli.py`, příkaz `fetch sources`: nevytváří plugin manager a nepředává `pm`. Modulové volání `register_commands` na konci souboru zůstává.
- `docs/plugins.md`: úvodní věta už neslibuje nové typy stránek ani reakci na dokončení fetche. Sekce `register_page_processor` a `after_sources_fetched` zmizí. Příklad `SitemapPlugin` nepoužívá `after_sources_fetched`, takže reset `_urls` vyřeš jinak nebo ho vynech. Pokud v `docs/plugins.md` je poznámka o zpětné kompatibilitě `config_dir`, odstraň ji také.
- `PLAN_PLUGIN.md`: v tabulce hooků oba řádky odstraň, nebo je označ „odstraněno 2026-11“. Nezaškrtnuté úkoly, které je zapojují (`pages/__init__.py: wire register_page_processor`, `fetch.py: fetch_sources(..., pm=None) — wire after_sources_fetched`), zruš: buď je přeškrtni, nebo k nim připiš, že jsou zrušené.
- `git grep -n "register_page_processor\|after_sources_fetched" -- ':!.swarm' ':!work' ':!reports'` najde nanejvýš poznámku o odstranění v `PLAN_PLUGIN.md`. Proto ani nové testy nesmějí jména odstraněných hooků obsahovat jako text.
- `scripts/verify` projde.

## Testy
- Nejdřív vznikne `tests/test_hooks.py` s testem, že množina hookspec v `KrizkySpec` (nebo v `get_plugin_manager().hook`) přesně odpovídá očekávanému seznamu zbývajících hooků: `prepare_jinja2_environment`, `extra_template_vars`, `register_commands`, `after_page_written`, `inject_head`, `inject_body_end`. Test porovnává s tímto kladným seznamem, a díky tomu jména odstraněných hooků v repu nezůstanou. Před změnou test selže.
- Test v `tests/test_fetch.py`: `"pm" not in inspect.signature(fetch_sources).parameters`. Stávající testy fetche musí projít, a pokud některý předává `pm`, uprav ho.
- Dispatch v `process_page` pokrývají stávající testy v `tests/test_site.py` (detail, category, simple). Ty musí projít beze změny.

## Poznámky
- Žádný plugin v `../krizky-*` tyto hooky ani `fetch_sources` nevolá, takže změna je jen v core. Sousední repa neupravuj.
- `krizky/cli.py` upravuje i tiket 02 (jinou funkci, `build_site`). Měň jen `fetch_sources` v CLI.
- `docs/plugins.md` upravuje i tiket 02, který přidává novou sekci o chybách z pluginů. Novou sekci tady nepřidávej.
- Guidelines: `docs/guidelines/python.md`, `docs/guidelines/docs-sync.md`.

## Otázky
