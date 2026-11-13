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
### Spotřeba běhu `wf_86d0770d-c30`

| agent | model | vstup | cache zápis | cache čtení | výstup | ~$ API |
|---|---|--:|--:|--:|--:|--:|
| plánovač | claude-opus-5-5 | 14 | 32 264 | 122 022 | 7 434 | 0.36 |
| impl:01#1 | claude-sonnet-5-5 | 18 | 26 453 | 162 602 | 4 274 | 0.14 |
| review:01#1 | claude-opus-5-5 | 12 | 18 572 | 72 643 | 1 344 | 0.15 |
| sloučení:01 | claude-haiku-5-5 | 8 | 14 290 | 35 459 | 1 126 | 0.00 |
| impl:02#1 | claude-sonnet-5-5 | 44 | 38 152 | 637 485 | 11 972 | 0.34 |
| review:02#1 | claude-opus-5-5 | 12 | 18 861 | 90 656 | 1 732 | 0.17 |
| sloučení:02 | claude-haiku-5-5 | 8 | 11 487 | 39 702 | 1 244 | 0.00 |
| závěr | claude-sonnet-5-5 | 10 | 16 836 | 55 515 | 2 183 | 0.08 |

| model | agentů | vstup celkem* | výstup | ~$ API |
|---|--:|--:|--:|--:|
| claude-opus-5-5 | 3 | 355 056 | 10 510 | 0.67 |
| claude-sonnet-5-5 | 3 | 937 115 | 18 429 | 0.56 |
| claude-haiku-5-5 | 2 | 100 954 | 2 370 | 0.01 |

\* vstup celkem = nový vstup + zápis do cache + čtení z cache

Doba běhu: 6 min · agentů: 8 · orientačně $1.24 podle ceníku API