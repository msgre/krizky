# Swarm share-core-helpers

## Cíl
Specifikace: `.swarm/share-core-helpers/spec.md` v repu krizky-share. Plugin krizky-share používá helpery a hook `copy_plugin_assets` z core 0.2.

## Tikety
| # | Název | Stav | PR | Pokusy | Historie problémů |
|---|-------|------|----|--------|-------------------|
| 01 | Plugin používá helpery a hook copy_plugin_assets z core 0.2 | done | #2 (sloučen) | 1 | žádné |

## Co nefungovalo
Nic. Jediný tiket prošel na první pokus, bez eskalace, vrácení od revieweru, konfliktu nebo pádu agenta (podle výsledků běhu, PR #2 je MERGED).

## Návrhy úprav swarmu
- Při jediném tiketu stojí finální PR navíc jen formální krok. Zvážit, zda u takto malých běhů nespojit tiket a finální PR (hypotéza, v tomto běhu to nešlo ověřit).

## Spotřeba
### Spotřeba běhu `wf_021cf30f-036`

| agent | model | vstup | cache zápis | cache čtení | výstup | ~$ API |
|---|---|--:|--:|--:|--:|--:|
| plánovač | claude-opus-5-5 | 12 | 24 106 | 80 254 | 3 872 | 0.23 |
| impl:01#1 | claude-sonnet-5-5 | 38 | 28 332 | 355 225 | 7 703 | 0.22 |
| review:01#1 | claude-opus-5-5 | 18 | 19 643 | 123 571 | 2 275 | 0.19 |
| sloučení:01 | claude-haiku-5-5 | 8 | 11 536 | 26 569 | 1 077 | 0.00 |
| závěr | claude-sonnet-5-5 | 12 | 23 189 | 93 331 | 3 454 | 0.11 |

| model | agentů | vstup celkem* | výstup | ~$ API |
|---|--:|--:|--:|--:|
| claude-opus-5-5 | 2 | 247 604 | 6 147 | 0.42 |
| claude-sonnet-5-5 | 2 | 500 127 | 11 157 | 0.33 |
| claude-haiku-5-5 | 1 | 38 113 | 1 077 | 0.00 |

\* vstup celkem = nový vstup + zápis do cache + čtení z cache

Doba běhu: 5 min · agentů: 5 · orientačně $0.76 podle ceníku API
