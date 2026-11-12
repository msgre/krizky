# /swarm:init pro core (2026-11-12)

## Cíl
Zařadit core repo do swarmu. Navazuje na úklid core ([2026-11-12-01-core-cleanup.md](2026-11-12-01-core-cleanup.md)), PR `core-cleanup` (#1) je sloučený. Spuštěno jako `/swarm:init --from /Users/msgre/projects/muzeum/krizky-filters`.

## Před initem
Kontroly prošly bez zásahu: `main` čistý a srovnaný s `origin/main`, větev `swarm-setup` neexistovala. Core nemá závislost na `krizky` z gitu, takže problém se zastaralou revizí v `uv.lock` tu nehrozí. Ve výchozím stavu prošlo 95 testů.

## core: PR [#2](https://github.com/msgre/krizky/pull/2) (`swarm-setup`)
1. `c543cee` **Konfigurace** (bez JS: v gitu nejsou žádné `*.js` ani `*.css`, jen v ignorovaných `temp/` a `tmp/`):
   - `scripts/verify` jen s Python částí,
   - sekce `[tool.ruff*]` z filters a `ruff>=0.16` v dev skupině. `pytest>=9.1.1` a `pytest-cov` zůstaly. `uv.lock` přidává jen ruff 0.17.4,
   - `.claude/settings.json` beze změny,
   - `.gitignore`: `.verify-logs/`, `.claude/worktrees/`, `.claude/settings.local.json`. Bez `node_modules/` a bez `PLAN.md`, který core má v gitu,
   - `CLAUDE.md`: úvod o core a pluginech, sekce Ověření, Pravidla projektu, Git a Swarm. Z guidelines jen `python.md`, `docs-sync.md` a `security.md`, protože core nemá JS stranu,
   - pravidlo pro logy: „Po každé implementační session“ platí mimo swarm. Ve swarmu píše jeden log za běh závěrečný agent do `work/` a commituje ho s řádkem v `OVERVIEW.md` do `swarm/<heslo>`. Stejná výjimka je v pravidle pro logy ve `work/OVERVIEW.md`.
2. `4a3a1db` **Automatický úklid:** ruff opravil 27 nálezů (11× I001, 8× F401, 2× SIM117, 2× SIM300, RUF023, RUF100 a návazné) a přeformátoval 21 souborů. Ruff 0.17 formátuje i bloky Pythonu v Markdownu, takže se změnily ukázky kódu v `PLAN_PLUGIN.md`, `docs/guidelines/python.md`, `docs/plugins.md`, `docs/sources.md`, v jednom reportu a ve dvou historických logech.
3. `443e05c` **Ruční úklid**, 19 nálezů:
   - 5× TID251 (`plugin_manager.py` a 4 testy). Ověřeno na Pythonu 3.13, kde se anotace vyhodnocují hned,
   - 6× PT018: složené asserty rozdělené,
   - 5× RUF001: nezlomitelné mezery ve výchozích `date_format` a `datetime_format` zapsané jako ` `, řetězec za běhu je stejný,
   - 2× A002: `fetch_sheet(sheet_id, …)` a `fetch_doc(doc_id, …)`. Volající předávají `id` pozičně, pluginy tyhle funkce nevolají,
   - B904: `raise SiteError(...) from exc`.

**Testy:** 95 prošlo před úklidem i po něm. `scripts/verify` skončil s exit 0.

**GitHub:** ruleset `main` (id 27101455) je aktivní, bez bypassu, s pravidly `deletion`, `non_fast_forward` a `pull_request`. Automatické mazání větví je zapnuté. Obojí prošlo bez zásahu auto mode.

## Poznámka
Ruleset na `main` core platí i pro logy z běhů swarmu v pluginech. Ty zůstávají v `work/` core necommitnuté a do `main` se dostanou jen přes PR.

## Další krok
Po sloučení PR #2 je core připravené pro `/swarm:run`.
