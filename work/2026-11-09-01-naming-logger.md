# Swarm naming-logger (2026-11-09)

## Cíl
Specifikace: `_plugins/krizky-filters/.swarm/naming-logger/spec.md`

## Tikety
| # | Název | Stav | PR | Pokusy | Historie |
|---|---|---|---|---|---|
| 01 | Přejmenovat FilterPlugin na FiltersPlugin | blocked | #2 | 1 | pokus 1: sloučení selhalo |
| 02 | Logger a varování při chybné konfiguraci filtrů | skipped | - | 0 | závisí na 01 |

## Co nefungovalo
- Tiket 01: `swarm-merge 2` skončil exit kódem 6, `gh pr view 2` hlásí "Could not resolve to a PullRequest with the number of 2". PR #2 se v repozitáři nenašlo (pravděpodobně špatné číslo PR nebo jiný repozitář pro `gh`; swarm-merge běžel v core repu `krizky`, ne v pluginu). Větev tiketu `swarm/naming-logger--01-rename-filters-plugin` zůstala nesloučená.
- Tiket 02 byl přeskočen kvůli závislosti na 01.

## Návrhy úprav swarmu
1. `swarm-merge` spouštět v repu, kam PR patří (plugin), ne v core checkoutu.
2. Před sloučením ověřit existenci PR přes `gh pr view` a číslo PR brát z výstupu `gh pr create`.
3. Chybu "PR nenalezen" hlásit jako chybu prostředí, ne jako otázku pro uživatele.

### Doplněno po běhu (orchestrátor)
- Ověřená příčina: PR #2 existuje (`msgre/krizky-filters#2`, OPEN, `swarm/naming-logger--01-rename-filters-plugin` → `swarm/naming-logger`). Merger (`sloučení:01`) první příkaz spustil jako `cd /Users/msgre/projects/muzeum/krizky && swarm-merge 2`. „Hlavní checkout“ ze zadání si vyložil jako core repo, protože CLAUDE.md pluginu uvádí cestu ke core a plugin leží v jeho podadresáři `_plugins/`. Scribe (`blokace:01`) udělal stejnou chybu, ale sám se opravil.
- Návrh: workflow ať dostane v `args` absolutní cestu k hlavnímu checkoutu (např. `repo`) a dává ji do zadání agentů bez worktree (merger, scribe, finalizer), např. „pracuj v `<repo>`, jinam necd-uj“. Při `--continue` se odpověď uživatele dostane jen k implementátorovi, ne k mergeru, takže bez úpravy swarmu se chyba nejspíš zopakuje.
- `/swarm:run` nemohl spustit Workflow přes `scriptPath`, protože `/Users/msgre/projects/ai/swarm/workflows/swarm.js` leží mimo pracovní adresáře session. Skript proto šel beze změny přes `script`. Je potřeba skill upravit, nebo přidat adresář swarmu do `additionalDirectories`.

## Spotřeba
### Spotřeba běhu `wf_434973fb-005`

| agent | model | vstup | cache zápis | cache čtení | výstup | ~$ API |
|---|---|--:|--:|--:|--:|--:|
| plánovač | claude-opus-5-5 | 14 | 33 770 | 136 739 | 6 503 | 0.35 |
| impl:01#1 | claude-sonnet-5-5 | 16 | 18 294 | 103 185 | 2 300 | 0.09 |
| review:01#1 | claude-opus-5-5 | 12 | 18 469 | 72 659 | 1 389 | 0.15 |
| sloučení:01 | claude-haiku-5-5 | 4 | 11 138 | 9 891 | 633 | 0.00 |
| blokace:01 | claude-haiku-5-5 | 14 | 15 719 | 75 283 | 2 435 | 0.00 |
| závěr | claude-sonnet-5-5 | 10 | 14 494 | 50 000 | 2 035 | 0.07 |

| model | agentů | vstup celkem* | výstup | ~$ API |
|---|--:|--:|--:|--:|
| claude-opus-5-5 | 2 | 261 663 | 7 892 | 0.50 |
| claude-sonnet-5-5 | 2 | 185 999 | 4 335 | 0.16 |
| claude-haiku-5-5 | 2 | 112 049 | 3 068 | 0.01 |

\* vstup celkem = nový vstup + zápis do cache + čtení z cache

Doba běhu: 4 min · agentů: 6 · orientačně $0.66 podle ceníku API
