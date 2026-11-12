# Swarm js-only-widget (krizky-filters)

## Cíl
Specifikace: `_plugins/krizky-filters/.swarm/js-only-widget/spec.md`

## Tikety

| # | Název | Stav | PR | Pokusy | Problémy |
|---|-------|------|----|--------|----------|
| 01 | Statická strana widgetu – opravené odkazy, js_only, třída filter-js a CSS pravidlo | done | #6 | 1 | žádné |
| 02 | filters.js odebírá třídu filter-js při selhání a zachová text napsaný před načtením | done | #5 | 1 | žádné |

## Co nefungovalo
Nic: oba tikety prošly na první pokus, bez eskalací, vrácení od revieweru, konfliktů a pádů agentů (podle výsledků běhu, PR #5 a #6 jsou MERGED).

## Návrhy úprav swarmu
- Úklid worktrees nechává i detached HEAD worktrees `wf_*-4` a `-6`; úklid je třeba spouštět vždy hned po běhu.

## Spotřeba
### Spotřeba běhu `wf_dbfd1b90-78a`

| agent | model | vstup | cache zápis | cache čtení | výstup | ~$ API |
|---|---|--:|--:|--:|--:|--:|
| plánovač | claude-opus-5-5 | 16 | 37 610 | 170 642 | 8 808 | 0.43 |
| impl:01#1 | claude-sonnet-5-5 | 34 | 44 868 | 524 610 | 11 215 | 0.33 |
| impl:02#1 | claude-sonnet-5-5 | 18 | 28 293 | 154 599 | 5 811 | 0.16 |
| review:02#1 | claude-opus-5-5 | 18 | 24 973 | 136 931 | 2 868 | 0.24 |
| sloučení:02 | claude-haiku-5-5 | 8 | 14 131 | 35 079 | 1 228 | 0.00 |
| review:01#1 | claude-opus-5-5 | 16 | 23 623 | 129 203 | 2 851 | 0.23 |
| sloučení:01 | claude-haiku-5-5 | 8 | 11 507 | 39 529 | 1 219 | 0.00 |
| závěr | claude-sonnet-5-5 | 6 | 15 663 | 25 374 | 1 782 | 0.06 |

| model | agentů | vstup celkem* | výstup | ~$ API |
|---|--:|--:|--:|--:|
| claude-opus-5-5 | 3 | 523 032 | 14 527 | 0.90 |
| claude-sonnet-5-5 | 3 | 793 465 | 18 808 | 0.55 |
| claude-haiku-5-5 | 2 | 100 262 | 2 447 | 0.01 |

\* vstup celkem = nový vstup + zápis do cache + čtení z cache

Doba běhu: 6 min · agentů: 8 · orientačně $1.45 podle ceníku API
