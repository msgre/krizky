# /swarm:init a příprava krizky-map pro swarm (2026-11-11)

## Cíl
Zařadit do swarmu další repa. Místo ruční přípravy každého repa vznikl ve swarm pluginu skill `/swarm:init`. Ten přenese konfiguraci z už připraveného referenčního repa. Poprvé použitý na `krizky-map` s referencí `krizky-filters`.

## Rozhodnutí
- **Zdroj konfigurace** je referenční repo (`--from`), ne šablony ve swarmu. Pravidla projektu zůstávají v repech krizky a swarm je obecný.
- **Nástroje pro JS** (`package.json`, ESLint, Prettier) jen tam, kde je JS nebo CSS. `krizky-photos` a `krizky-json` je nedostanou.
- **Jednorázový úklid** se stejnými pravidly jako filters, ve třech commitech: konfigurace, automatické opravy a ruční opravy. Když jedno pravidlo vyžaduje přibližně víc než 10 ručních oprav, init se zeptá.
- **GitHub:** ruleset na `main` (zákaz smazání a force push, jen přes PR s 0 schváleními, bez bypassu) a automatické mazání větví po sloučení. Nastavuje se přes `gh`, a když to auto mode zakáže, init vypíše příkazy.
- **Pořadí:** map, potom photos, share a json. `valasske_nebe_ng` a core později (`TODO.md`, 2026-11-11).

## Swarm (`~/projects/ai/swarm`)
- Nový `skills/init/SKILL.md`. `DESIGN.md` popisuje init a stav zařazování rep.
- Commit `9245e15`, zatím nepushnutý.

## krizky-map: PR [#1](https://github.com/msgre/krizky-map/pull/1) (`swarm-setup`)
1. `12954db` **Konfigurace:**
   - `scripts/verify` (vzor pro Prettier `krizky_map/assets/**`),
   - ruff v `pyproject.toml` a dev skupina `pytest>=9.1`, `ruff>=0.16`, k tomu `uv.lock`,
   - `eslint.config.mjs`, `.prettierrc.json`, `package.json` a `package-lock.json`,
   - `.claude/settings.json`, `CLAUDE.md` a `.gitignore`.
2. `9e6ba27` **Automatický úklid:**
   - ruff opravil 10 nálezů a přeformátoval 5 souborů,
   - ESLint opravil 176 ze 197 nálezů,
   - Prettier přeformátoval `map.js` a `map.css`.
3. `7268c01` **Ruční úklid:**
   - `map.js`:
     - `/* global L */` pro Leaflet (17× `no-undef`),
     - `catch {}` bez nepoužité proměnné,
     - 3× `== null` přepsané se zachováním chování: `=== null || === undefined` a `?? ''`;
   - `plugin.py`: RUF005;
   - `test_geojson.py`: PT018;
   - 5× odstraněné `from __future__ import annotations` (TID251).

**Testy:** 70 prošlo před úklidem i po něm. `scripts/verify` skončil s exit 0.

**GitHub:** ruleset `main` je aktivní (`deletion`, `non_fast_forward`, `pull_request`) a automatické mazání větví je zapnuté. Obojí prošlo bez zásahu auto mode.

## krizky-photos: PR [#1](https://github.com/msgre/krizky-photos/pull/1) (`swarm-setup`)
**Před initem:**
- Lokální `main` byl o commit `bba6905` napřed před `origin/main`, takže init se zastavil. Uživatel `main` pushnul.
- `.venv` měl shebangy na starou cestu (`/Users/msgre/projects/muzeum/krizky-photos`, před přesunem do `_plugins/`). Opraveno přes `uv sync --reinstall`, repo se nemění.
- Testy na `main` se zamčenými závislostmi padaly: `uv.lock` držel `krizky` na `dcd9ff0`, kde chybí `krizky.hooks`. Po souhlasu uživatele je `krizky` zvednuté na `09af781`, stejně jako v krizky-filters, a změna je v commitu 1. Potom prošlo 60 testů.

**Commity:**
1. `e912872` **Konfigurace** (bez JS, repo nemá `*.js` ani `*.css`):
   - `scripts/verify` jen s Python částí,
   - ruff v `pyproject.toml` a dev skupina `pytest>=9.1`, `ruff>=0.16`,
   - `uv.lock` včetně zvednutého `krizky`,
   - `.claude/settings.json`, `CLAUDE.md` a `.gitignore` (bez `node_modules/`). V `CLAUDE.md` chybí `javascript.md`, ale `cross-language.md` zůstal kvůli `window.krizkyPhotos`.
2. `be84a17` **Automatický úklid:** ruff opravil 10 nálezů (I001, F401) a přeformátoval 9 souborů.
3. `44dc43c` **Ruční úklid**, 19 nálezů:
   - 9× TID251,
   - 4× B904 (`from err` u re-raise ImportError),
   - 3× RUF012 (falešné `_Env` v testech, `globals` v `__init__`),
   - SIM102, RUF005 a F841 (`fmt_names`).

**Testy:** 60 prošlo před úklidem i po něm. `scripts/verify` skončil s exit 0.

**GitHub:** ruleset `main` (id 27067603) je aktivní, bez bypassu, s pravidly `deletion`, `non_fast_forward` a `pull_request`. Automatické mazání větví je zapnuté. Obojí prošlo bez zásahu auto mode.

**Poučení zapsaná do skillu** (swarm `0f70c35`, pushnutý):
- Když testy ve výchozím stavu padají kvůli zastaralé revizi `krizky` v `uv.lock`, porovnat ji s referencí, zkusit `uv lock --upgrade-package` a zeptat se.
- Když `uv run` hlásí `Failed to spawn`, je `.venv` po přesunu repa a pomůže `uv sync --reinstall`.
- Tělo PR z initu má teď podobu details-summary podle Simona Willisona, stejně jako PR z `/swarm:run`. Dosud to skill neříkal, takže PR z initu u krizky-map ho nedodrželo. Tělo krizky-photos PR #1 je přepsané.

## krizky-share: PR [#1](https://github.com/msgre/krizky-share/pull/1) (`swarm-setup`)
**Před initem:** kontroly prošly bez zásahu. Repo nemělo `uv.lock` ani `.venv`. Nový `uv lock` zamkl `krizky` na `09af781`, stejně jako v krizky-filters. Ve výchozím stavu prošlo 37 testů.

**Commity:**
1. `3662dca` **Konfigurace** (s JS, repo má `share.js` a `share.css`):
   - `scripts/verify` (vzor pro Prettier `krizky_share/assets/**`),
   - ruff v `pyproject.toml` a dev skupina `pytest>=9.1`, `ruff>=0.16`, k tomu nový `uv.lock`,
   - `eslint.config.mjs`, `.prettierrc.json`, `package.json` (`krizky-share-dev`) a `package-lock.json`,
   - `.claude/settings.json`, `CLAUDE.md` a `.gitignore`.
2. `0ebdfae` **Automatický úklid:**
   - ruff opravil 6 nálezů (4× I001, PT001, F401) a přeformátoval 5 souborů,
   - ESLint opravil 20 z 21 nálezů (11× `prefer-arrow-callback`, 7× `curly`, 2× `object-shorthand`). Žádný callback nepoužívá `this`.
   - Prettier přeformátoval `share.js` a `share.css`.
3. `4ffa5ac` **Ruční úklid**, 10 nálezů:
   - 5× TID251 (všechny anotace jsou za běhu platné typy),
   - 3× E741 (`l` → `link` v `test_plugin.py`),
   - RUF005 v `plugin.py` (core předává `ChoiceLoader` seznam),
   - `share.js`: `catch {}` bez nepoužité proměnné.

**Testy:** 37 prošlo před úklidem i po něm. `scripts/verify` skončil s exit 0.

**GitHub:** ruleset `main` (id 27069484) je aktivní, bez bypassu, s pravidly `deletion`, `non_fast_forward` a `pull_request`. Automatické mazání větví je zapnuté. Obojí prošlo bez zásahu auto mode.

## krizky-json: PR [#1](https://github.com/msgre/krizky-json/pull/1) (`swarm-setup`)
**Před initem:** kontroly prošly bez zásahu. Repo nemělo v gitu `uv.lock` a `.venv` byl ze staré cesty (`/Users/msgre/projects/muzeum/krizky-json`). Shebangy opravil `uv sync` po přidání dev skupiny, `--reinstall` nebyl potřeba. Nový `uv lock` zamkl `krizky` na `09af781`, stejně jako v krizky-filters. Ve výchozím stavu prošlo 9 testů.

**Commity:**
1. `ade08e6` **Konfigurace** (bez JS, repo nemá `*.js` ani `*.css`):
   - `scripts/verify` jen s Python částí,
   - ruff v `pyproject.toml` a dev skupina `pytest>=9.1`, `ruff>=0.16` (dříve `pytest>=8.0`), k tomu nový `uv.lock`,
   - `.claude/settings.json`, `CLAUDE.md` a `.gitignore` (bez `node_modules/`). V `CLAUDE.md` chybí `javascript.md` i `cross-language.md`, protože plugin nemá žádnou JS stranu. Pravidlo `docs-sync.md` míří jen na `README.md`, repo nemá `docs/`.
2. `71c8cbf` **Automatický úklid:** ruff opravil 3 nálezy (2× I001, F401 nepoužitý `import pytest`) a přeformátoval 2 soubory.
3. `26af06e` **Ruční úklid:** 2× TID251 (`plugin.py`, `test_json_plugin.py`). Všechny anotace jsou za běhu platné typy.

**Testy:** 9 prošlo před úklidem i po něm. `scripts/verify` skončil s exit 0.

**GitHub:** ruleset `main` (id 27069952) je aktivní, bez bypassu, s pravidly `deletion`, `non_fast_forward` a `pull_request`. Automatické mazání větví je zapnuté. Obojí prošlo bez zásahu auto mode.

## Poučení pro init (zapsané do skillu)
- `eqeqeq` u `x == null` nejde nahradit prostým `=== null`, protože by se změnilo chování pro `undefined`.
- Globální proměnné knihoven deklarovat v souboru (`/* global L */`), ne v konfiguraci ESLint.
- Hranice 10 nálezů se týká ručních oprav. Jedna deklarace, která vyřeší 17 nálezů, ji nepřekračuje.

## Další krok
- krizky-photos PR #1 a krizky-share PR #1 jsou sloučené (2026-11-11).
- krizky-json PR #1 je sloučené (2026-11-12).

## Kontrola všech pluginů (2026-11-12)
Všech 5 pluginů (filters, json, map, photos, share) je připravených pro `/swarm:run`:
- lokálně `main`, čistý strom, srovnaný s `origin/main`,
- v gitu je `scripts/verify`, `.claude/settings.json` (shodné s filters), `CLAUDE.md` (sekce Ověření, Pravidla projektu, Git, Swarm) a `uv.lock` s `krizky` na `09af781`,
- `scripts/verify` na `main` skončil s exit 0: filters 73, json 9, map 70, photos 60, share 37 testů; ESLint a Prettier prošly u filters, map a share,
- GitHub: ruleset `main` je aktivní, bez bypassu, s pravidly `deletion`, `non_fast_forward` a `pull_request`, mazání větví po sloučení je zapnuté a žádné PR nejsou otevřené.

Drobnost: v krizky-filters zůstala na `origin` sloučená větev `swarm-setup` z PR #1. Mazání větví po sloučení se tam zapnulo až potom. Uživatel ji smazal 2026-11-12.
