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
### Spotřeba běhu `wf_88db53da-215`

| agent | model | vstup | cache zápis | cache čtení | výstup | ~$ API |
|---|---|--:|--:|--:|--:|--:|
| plánovač | claude-opus-5-5 | 18 | 43 111 | 224 527 | 9 525 | 0.50 |
| impl:01#1 | claude-sonnet-5-5 | 24 | 33 464 | 261 456 | 5 440 | 0.19 |
| review:01#1 | claude-opus-5-5 | 14 | 25 023 | 106 143 | 2 627 | 0.22 |
| sloučení:01 | claude-haiku-5-5 | 8 | 14 243 | 35 468 | 1 368 | 0.00 |
| impl:02#1 | claude-sonnet-5-5 | 42 | 35 129 | 586 412 | 10 497 | 0.31 |
| review:02#1 | claude-opus-5-5 | 18 | 24 324 | 149 552 | 3 308 | 0.25 |
| sloučení:02 | claude-haiku-5-5 | 8 | 10 939 | 39 544 | 974 | 0.00 |
| závěr | claude-sonnet-5-5 | 8 | 18 169 | 40 983 | 2 199 | 0.08 |

| model | agentů | vstup celkem* | výstup | ~$ API |
|---|--:|--:|--:|--:|
| claude-opus-5-5 | 3 | 572 730 | 15 460 | 0.96 |
| claude-sonnet-5-5 | 3 | 975 687 | 18 136 | 0.58 |
| claude-haiku-5-5 | 2 | 100 210 | 2 342 | 0.01 |

\* vstup celkem = nový vstup + zápis do cache + čtení z cache

Doba běhu: 8 min · agentů: 8 · orientačně $1.55 podle ceníku API
