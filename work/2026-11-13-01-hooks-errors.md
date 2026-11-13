# Swarm hooks-errors (2026-11-13)

## Cíl
Specifikace: `.swarm/hooks-errors/spec.md`. Odstranit nepoužívané hooky a zpřehlednit chyby z pluginů při `krizky build site`.

## Tikety
| # | Název | Stav | PR | Pokusy | Problémy |
|---|-------|------|----|--------|----------|
| 01 | Odstranit hooky register_page_processor a after_sources_fetched | hotovo | [#3](https://github.com/msgre/krizky/pull/3) | 1 | žádné |
| 02 | Jednořádkový výpis chyb z pluginů v krizky build site | hotovo | [#4](https://github.com/msgre/krizky/pull/4) | 1 | žádné |

## Co nefungovalo
Nic: oba tikety prošly na první pokus, bez eskalací, vrácení od revieweru, konfliktů nebo pádů agentů (výsledky mají prázdnou historii, oba PR jsou sloučené).

## Návrhy úprav swarmu
- Žádné konkrétní návrhy z tohoto běhu, protože nenastal žádný problém.
- Hypotéza: lokální větve `worktree-wf_*` a worktrees zůstávají po tiketech a čistí je až závěrečný agent. Pokud to jde, mohl by je mazat `swarm-merge` hned po sloučení.

## Spotřeba
doplní swarm-metrics
