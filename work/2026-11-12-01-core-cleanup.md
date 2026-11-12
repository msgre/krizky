# Úklid core a přesun pluginů vedle core (2026-11-12)

## Cíl
Připravit core repo na `/swarm:init`. Init vyžaduje čistý pracovní strom, ale v core zůstávalo hodně necommitnutých souborů. Pluginy ležely jako samostatná git repa v `krizky/_plugins/`.

## Přesun pluginů
Všech 5 pluginů je přesunutých z `krizky/_plugins/krizky-*` do `/Users/msgre/projects/muzeum/krizky-*`, tedy vedle core. Adresář `_plugins/` je smazaný. Důvody:
- `CLAUDE.md` z core se načítal v každé session pluginu, protože plugin ležel v podadresáři core. Po initu core by tam přibyla i sekce „Ověření“ se `scripts/verify` core.
- Slučovací agent v běhu `naming-logger` spustil `swarm-merge` v core repu (swarm `DESIGN.md`).
- pytest v core sbíral i `_plugins/*/tests` a hlásil 15 chyb při sběru, protože se tam opakuje jméno balíčku `tests`. Ruff by procházel i pluginy.

Po přesunu:
- `uv sync --frozen --reinstall` v každém pluginu, protože shebangy v `.venv/bin` ukazovaly na starou cestu.
- `scripts/verify` skončil s exit 0 ve všech pluginech (filters 73, json 9, map 70, photos 60, share 37 testů).
- `uv run pytest` v core projde bez parametrů (95 testů), takže `testpaths` už není potřeba.
- Absolutní cesty do core v `CLAUDE.md` a `.claude/settings.json` pluginů platí dál.

Stará cesta `_plugins/` zůstala v historických logech ve `work/`, ve swarm `DESIGN.md` a v `docs/guidelines/javascript.md` (řádek 9).

## core: větev `core-cleanup`
1. **`.gitignore` a `uv.lock`:**
   - `.gitignore`: `TODO.md` (stejně jako v pluginech) a `tmp/`,
   - `uv.lock`: `uv lock --upgrade`, takže core má stejné verze jako pluginy (`sqlite-utils` 4.2.1, `python-dateutil` 4.0.0, `pluggy` 1.7.0, `click` 8.5.1). Prošlo 95 testů.
2. **`docs/guidelines/`** commitnuté beze změny. Jsou shodné s `.claude/skills/implement-review/guidelines/`.
3. **`work/`:** dosud necommitnuté logy a `OVERVIEW.md`.
4. **Skill `review-consistency`** ve dvou commitech: nejdřív původní podoba, pak úpravy podle současného stavu:
   - pluginy jsou samostatná repa vedle core (`../krizky-*`) a web `../valasske_nebe_ng/` slouží jako kontext pro to, jak se API používá,
   - `docs/guidelines/` jsou závazné a mají přednost před precedentem v core,
   - nehlásí se to, co vynucuje `scripts/verify` (ruff, ESLint, Prettier), jen rozdíly v jejich konfiguraci mezi repy,
   - nálezy implementuje `/swarm:run`,
   - logy jsou jen v core `work/` a `TODO.md` a `PLAN.md` pluginů jsou lokální poznámky.
5. **`reports/2026-08-17-2013/`**: report revize konzistence, zadání prvního běhu swarmu.

Skill `implement-review` (jeho práci teď dělá swarm) a duplicitní `skills/` (přesná kopie `.claude/skills/`) jsou přesunuté do `tmp/`.

Do `tmp/` se přesunuly `Redesign filtrovací dimenze.zip`, `filtrovani.png`, `socky.png`, `design_manual.html` a `filtrovani-mist-navrh.md`. Úklid `tmp/` a `docs/` přijde později.

## Zbývá před initem core
- Pracovní strom core je čistý. Zbývá sloučit PR `core-cleanup` a potom spustit `/swarm:init --from …/krizky-filters`. Init přepíše `CLAUDE.md` core podle swarm docs, protože ten je starší (pravidlo pro logy).
