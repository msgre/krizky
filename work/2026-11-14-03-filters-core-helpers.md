# filters-core-helpers (2026-11-14)

## Cíl
Specifikace: `.swarm/filters-core-helpers/spec.md` (krizky-filters). Přechod pluginu na krizky 0.2 (register_plugin_templates, copy_plugin_assets).

## Tikety
| # | Název | Stav | PR | Pokusy | Problémy |
|---|-------|------|----|--------|----------|
| 01 | Přechod na krizky 0.2 (register_plugin_templates, copy_plugin_assets) | done | #8 (sloučeno) | 1 | žádné |

## Co nefungovalo
Nic: jeden tiket, 1 pokus, bez eskalací, vrácení a konfliktů.

## Návrhy úprav swarmu
- Pro takto malé běhy (jeden tiket) zvážit přeskočení samostatné integrační větve a PR rovnou do main.

## Spotřeba
### Spotřeba běhu `wf_a3ac6d05-7fa`

| agent | model | vstup | cache zápis | cache čtení | výstup | ~$ API |
|---|---|--:|--:|--:|--:|--:|
| plánovač | claude-opus-5-5 | 12 | 23 252 | 78 090 | 3 677 | 0.22 |
| impl:01#1 | claude-sonnet-5-5 | 30 | 29 142 | 287 650 | 6 891 | 0.20 |
| review:01#1 | claude-opus-5-5 | 18 | 19 903 | 113 975 | 2 410 | 0.19 |
| sloučení:01 | claude-haiku-5-5 | 8 | 11 353 | 26 429 | 1 195 | 0.00 |
| závěr | claude-sonnet-5-5 | 14 | 14 299 | 70 965 | 2 871 | 0.08 |

| model | agentů | vstup celkem* | výstup | ~$ API |
|---|--:|--:|--:|--:|
| claude-opus-5-5 | 2 | 235 250 | 6 087 | 0.41 |
| claude-sonnet-5-5 | 2 | 402 100 | 9 762 | 0.28 |
| claude-haiku-5-5 | 1 | 37 790 | 1 195 | 0.00 |

\* vstup celkem = nový vstup + zápis do cache + čtení z cache

Doba běhu: 4 min · agentů: 5 · orientačně $0.69 podle ceníku API
