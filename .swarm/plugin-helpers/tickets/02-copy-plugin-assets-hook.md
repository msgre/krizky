---
id: "02"
slug: copy-plugin-assets-hook
title: Hook copy_plugin_assets, verze 0.2.0 a dokumentace pro pluginy
status: pending
depends_on: ["01"]
files:
  - krizky/hooks.py
  - krizky/site.py
  - tests/test_hooks.py
  - tests/test_site.py
  - pyproject.toml
  - uv.lock
  - docs/plugins.md
  - PLAN_PLUGIN.md
  - README.md
attempts: 0
pr: ""
---

## Cíl
Pluginy dnes kopírují své assety z `after_page_written` a samy si hlídají, aby to udělaly jen jednou za build. Core přidá hook `copy_plugin_assets`, který zavolá právě jednou za build po zkopírování assetů projektu a před vykreslením první stránky. Protože starý core neznámý hookimpl tiše ignoruje, verze core stoupne na `0.2.0`. Tiket zároveň zdokumentuje hook i pomocné funkce z `krizky/plugin_helpers.py` (vznikly v tiketu 01). Specifikace `.swarm/plugin-helpers/spec.md`, části 1, 3 a 4.

## Akceptační kritéria
- `krizky/hooks.py`: nová hookspec `copy_plugin_assets(self, output_dir, config, config_dir)` (bez `firstresult`, návratová hodnota se ignoruje). Docstring popisuje, kdy se volá (jednou za build, po zkopírování `site.assets` projektu, před první stránkou a prvním `after_page_written`), že plugin si nemusí hlídat opakované kopírování, že assety patří do `output_dir/<jméno-pluginu>/`, a popisuje argumenty (`output_dir` absolutní cesta k výstupu, `config` celý config, `config_dir` adresář s `config.yaml`).
- `krizky/site.py`: v `_generate` se hook zavolá hned po `_copy_assets(site, config_dir, output_dir)` a před smyčkou přes stránky, právě jednou za `build_site`, s keyword argumenty `output_dir=output_dir, config=config, config_dir=config_dir`. Respektuj stávající vzor `if pm is not None`.
- `tests/test_hooks.py`: `EXPECTED_HOOKS` obsahuje `copy_plugin_assets`.
- `pyproject.toml`: `version = "0.2.0"`; `uv.lock` aktualizovaný (`uv lock`). `uv run python -c "import importlib.metadata as m; print(m.version('krizky'))"` vypíše `0.2.0`.
- `docs/plugins.md`:
  - v „Dostupné hooky“ sekce `copy_plugin_assets(output_dir, config, config_dir)`: kdy se volá, argumenty, příklad s `replace_tree` z `krizky.plugin_helpers`,
  - nová sekce „Pomocné funkce pro pluginy“ s `register_plugin_templates`, `replace_tree` a `resolve_path` (signatura, chování včetně okrajových případů) a krátkým příkladem pluginu, který používá `register_plugin_templates` v `prepare_jinja2_environment` a `replace_tree` v `copy_plugin_assets`,
  - konvence: assety pluginu patří do `output_dir/<jméno-pluginu>/`, šablony pluginu do jeho adresáře `templates/`,
  - pokud některý příklad kopíruje assety z `after_page_written`, přepiš ho na nový hook (CSV/sitemap sidecary generované per stránka zůstávají v `after_page_written`).
- `PLAN_PLUGIN.md`: v tabulce hooků řádek `copy_plugin_assets(output_dir, config, config_dir)` | `site.py` | all; jednou za build, kopírování assetů pluginu.
- `README.md`: pokud popisuje hooky nebo plugin API, doplň hook a helpery; jinak beze změny (dnes je nezmiňuje).
- Build bez pluginů se chová stejně jako dosud (stávající testy v `tests/test_site.py` projdou beze změny).
- `scripts/verify` projde.

## Testy
Napiš je nejdřív, v `tests/test_site.py` (helpery `_setup`, `_base_config`, `_make_template`, `_make_db` už tam jsou):
- Plugin registrovaný v testu: vytvoř `pm = get_plugin_manager(tmp_path)` a `pm.register(TestPlugin())`, kde třída má `@hookimpl copy_plugin_assets` a `@hookimpl after_page_written` zapisující do společného seznamu událostí. Hookimpl marker `pluggy.HookimplMarker("krizky")` nebo `krizky.hooks.hookimpl` (vzor v `tests/test_cli.py`). Spusť `build_site(config, config_dir=tmp_path, pm=pm)`.
  - Config s více stránkami (například simple + detail s několika záznamy): `copy_plugin_assets` je zavolán přesně jednou, s `output_dir` rovným `(tmp_path / site.output).resolve()`, `config` je tentýž objekt a `config_dir == tmp_path`.
  - První událost v seznamu je `copy_plugin_assets`, všechny `after_page_written` přijdou až po něm.
  - S nastaveným `site.assets` (adresář se souborem, např. `assets/css/style.css`): plugin v hooku ověří (nebo si poznamená), že soubor už ve výstupu existuje (`output_dir / "assets" / "css" / "style.css"`).

## Poznámky
- `krizky/plugin_helpers.py` z tiketu 01 neměň, jen ho dokumentuj; přečti si jeho docstringy, ať dokumentace odpovídá skutečnému chování.
- Docs-sync (`docs/guidelines/docs-sync.md`): v `docs/plugins.md` je u `prepare_jinja2_environment` uvedená signatura bez `config_dir`, zatímco hookspec ji má. Při úpravě příkladu oprav i ji.
- `work/OVERVIEW.md` ani `work/` neměň, píše je závěrečný agent.
- Úpravy pluginů jsou mimo rozsah.

## Otázky
