# Swarm photos-core-helpers

## Cíl
Specifikace: `/Users/msgre/projects/muzeum/krizky-photos/.swarm/photos-core-helpers/spec.md` (krizky-photos na core 0.2: resolve_path pro focal points, PhotosFetchError).

## Tikety

| # | Název | Stav | PR | Pokusy | Historie problémů |
|---|-------|------|----|--------|-------------------|
| 01 | Core 0.2, resolve_path pro focal points a přejmenování na PhotosFetchError | done | #2 (sloučen) | 1 | žádné |

## Co nefungovalo
Nic: jediný tiket prošel na první pokus, bez eskalace, vrácení od revieweru, konfliktů nebo pádů agentů.
Po běhu zůstaly jen osiřelé worktrees `wf_*` a lokální větve (uklizeno závěrečným agentem).

## Návrhy úprav swarmu
- Pro běh s jediným tiketem zvážit přeskočení samostatné integrační větve a finálního PR. Je to hypotéza, z jednoho běhu to nelze potvrdit.

## Spotřeba
### Spotřeba běhu `wf_55f7a987-ee8`

| agent | model | vstup | cache zápis | cache čtení | výstup | ~$ API |
|---|---|--:|--:|--:|--:|--:|
| plánovač | claude-opus-5-5 | 12 | 21 634 | 71 577 | 3 924 | 0.22 |
| impl:01#1 | claude-sonnet-5-5 | 22 | 21 045 | 149 729 | 4 339 | 0.13 |
| review:01#1 | claude-opus-5-5 | 16 | 18 230 | 92 820 | 2 089 | 0.17 |
| sloučení:01 | claude-haiku-5-5 | 8 | 10 909 | 25 824 | 1 189 | 0.00 |
| závěr | claude-sonnet-5-5 | 6 | 21 159 | 27 687 | 1 823 | 0.08 |

| model | agentů | vstup celkem* | výstup | ~$ API |
|---|--:|--:|--:|--:|
| claude-opus-5-5 | 2 | 204 289 | 6 013 | 0.39 |
| claude-sonnet-5-5 | 2 | 219 648 | 6 162 | 0.20 |
| claude-haiku-5-5 | 1 | 36 741 | 1 189 | 0.00 |

\* vstup celkem = nový vstup + zápis do cache + čtení z cache

Doba běhu: 4 min · agentů: 5 · orientačně $0.59 podle ceníku API
