# Swarm map-core-helpers

## Cíl
Přechod krizky-map na core 0.2 (plugin_helpers, hook copy_plugin_assets). Specifikace: `.swarm/map-core-helpers/spec.md` v repu krizky-map.

## Tikety
| # | Název | Stav | PR | Pokusy | Problémy |
|---|-------|------|----|--------|----------|
| 01 | Přechod na core 0.2 (plugin_helpers a hook copy_plugin_assets) | done | #2 (sloučen) | 1 | žádné |

## Co nefungovalo
Nic. Jediný tiket prošel na první pokus, bez eskalace, vrácení od revieweru, konfliktů či pádů agentů (historie ve výsledcích je prázdná).

## Návrhy úprav swarmu
- Při jednom tiketu zvážit přeskočení samostatné integrační větve: tiketový PR a finální PR nesou stejnou změnu.
- Po sloučení zůstaly worktrees `wf_*` a větve `worktree-wf_*`; hypotéza: mohl by je mazat už swarm-merge.

## Spotřeba
### Spotřeba běhu `wf_097f3fd1-d56`

| agent | model | vstup | cache zápis | cache čtení | výstup | ~$ API |
|---|---|--:|--:|--:|--:|--:|
| plánovač | claude-opus-5-5 | 14 | 28 754 | 116 226 | 5 330 | 0.30 |
| impl:01#1 | claude-sonnet-5-5 | 38 | 37 802 | 431 006 | 10 633 | 0.29 |
| review:01#1 | claude-opus-5-5 | 16 | 23 501 | 113 837 | 2 536 | 0.21 |
| sloučení:01 | claude-haiku-5-5 | 8 | 12 234 | 27 261 | 1 056 | 0.00 |
| závěr | claude-sonnet-5-5 | 14 | 23 471 | 116 510 | 3 691 | 0.12 |

| model | agentů | vstup celkem* | výstup | ~$ API |
|---|--:|--:|--:|--:|
| claude-opus-5-5 | 2 | 282 348 | 7 866 | 0.51 |
| claude-sonnet-5-5 | 2 | 608 841 | 14 324 | 0.41 |
| claude-haiku-5-5 | 1 | 39 503 | 1 056 | 0.00 |

\* vstup celkem = nový vstup + zápis do cache + čtení z cache

Doba běhu: 5 min · agentů: 5 · orientačně $0.92 podle ceníku API
