# Swarm plugin-helpers (2026-11-13)

## Cíl
Specifikace: `.swarm/plugin-helpers/spec.md`. Modul s pomocnými funkcemi pro pluginy, hook `copy_plugin_assets`, verze 0.2.0 a dokumentace pro pluginy.

## Tikety
| # | Název | Stav | PR | Pokusy | Problémy |
|---|-------|------|----|--------|----------|
| 01 | Modul krizky/plugin_helpers.py s pomocnými funkcemi pro pluginy | hotovo | [#6](https://github.com/msgre/krizky/pull/6) | 1 | žádné |
| 02 | Hook copy_plugin_assets, verze 0.2.0 a dokumentace pro pluginy | hotovo | [#7](https://github.com/msgre/krizky/pull/7) | 1 | žádné |

## Co nefungovalo
Nic: oba tikety prošly na první pokus, bez eskalací, vrácení od revieweru, konfliktů nebo pádů agentů (historie ve výsledcích je prázdná).

## Návrhy úprav swarmu
- Žádné konkrétní návrhy, nenastal žádný problém.
- Lokální worktrees a větve `worktree-wf_*` zůstaly po tiketech až do závěrečného úklidu. Mohl by je mazat `swarm-merge` hned po sloučení (hypotéza, nezkoumáno).

## Spotřeba
doplní swarm-metrics
