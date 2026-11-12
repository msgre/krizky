# Swarm naming-logger, pokračování (2026-11-10)

## Cíl
Specifikace: `_plugins/krizky-filters/.swarm/naming-logger/spec.md`. Navazuje na [2026-11-09-01-naming-logger.md](2026-11-09-01-naming-logger.md).

## Tikety
| # | Název | Stav | PR | Pokusy | Historie |
|---|---|---|---|---|---|
| 01 | Přejmenovat FilterPlugin na FiltersPlugin | done | #2 | 1 | hotovo v předchozím běhu |
| 02 | Logger a varování při chybné konfiguraci filtrů | done | #3 | 2 | pokus 1: reviewer vrátil (2 nálezy) |

## Co nefungovalo
- Tiket 02: reviewer po prvním pokusu vrátil 2 nálezy, oprava proběhla v pokusu 2 (větev `naming-logger-02-attempt2`).
- Předchozí běh: tiket 01 zablokovala chyba merge agenta, který spustil `swarm-merge` v core repu místo v pluginu. V tomto běhu už zadání obsahovalo cestu k hlavnímu checkoutu a chyba se neopakovala.

## Návrhy úprav swarmu
1. Předávat workflow absolutní cestu hlavního checkoutu (`repo`) všem agentům bez worktree.
2. Do zadání implementátora dát kontrolní seznam typických nálezů revieweru (logger, formát varování, docs-sync), aby se snížil počet vrácení.
3. Před `swarm-merge` ověřit existenci PR přes `gh pr view` v daném repu.

## Retro (2026-11-10)
Finální PR krizky-filters #4 je sloučený. Úpravy swarmu jsou v `~/projects/ai/swarm`, commity `8ea8581` a `4fab5b5`.

| Návrh | Výsledek |
|---|---|
| Cesta k hlavnímu checkoutu (`args.repo`) | hotovo v `8ea8581`, ověřeno v tomto běhu |
| Spouštění workflow jménem `swarm:swarm` místo `scriptPath` | hotovo v `8ea8581`, ověřeno v tomto běhu |
| Ověřit PR přes `gh pr view` před `swarm-merge` | zamítnuto, `swarm-merge` to dělá jako první krok. Příčinou byl adresář, ne číslo PR |
| Kontrolní seznam nálezů pro implementátora | přeformulováno podle skutečných nálezů: test výjimek přes `pytest.raises`, ne `suppress`; okrajové vstupy (`None`); ověření, že test bez změny kódu spadne. Doplněno i do revieweru |
| `--continue` po blokaci při slučování opakoval implementaci i review | `blocked_at` v tiketu; u `merge` se pokračování pokusí PR jen znovu sloučit |
| `--continue` mohl běžet naprázdno | `/swarm:run` ho v takovém případě zastaví už v kontrolách |
| Metriky jen z posledního běhu | `.swarm/<heslo>/runs.txt` a `swarm-metrics` nad víc běhy, k PR jde součet. Za oba běhy `naming-logger`: $1,79, 12 min, 13 agentů |
| Technická chyba vypadala jako otázka, finalizer hádal příčinu | otázky nesou „technická chyba swarmu“; finalizer příčiny ověřuje, nebo je označí jako hypotézu |
| Akceptace přes `git grep` našla samotnou spec | plánovač a DESIGN: `-- ':!.swarm'` |
| Session drží starou verzi skillu | DESIGN: po úpravě pluginu restartovat Claude Code |

Poznámka k řádku 13: PR #3 měl hlavu na správné větvi tiketu `swarm/naming-logger--02-config-warnings` se 2 commity. `naming-logger-02-attempt2` byla nejspíš jen lokální větev ve worktree.

## Spotřeba
### Spotřeba běhu `wf_32481390-a0f`

| agent | model | vstup | cache zápis | cache čtení | výstup | ~$ API |
|---|---|--:|--:|--:|--:|--:|
| stav | claude-haiku-5-5 | 4 | 14 596 | 9 978 | 813 | 0.00 |
| impl:02#1 | claude-sonnet-5-5 | 32 | 35 196 | 390 765 | 8 745 | 0.25 |
| review:02#1 | claude-opus-5-5 | 14 | 26 075 | 113 998 | 3 687 | 0.25 |
| impl:02#2 | claude-opus-5-5 | 26 | 28 849 | 250 547 | 6 442 | 0.37 |
| review:02#2 | claude-opus-5-5 | 12 | 19 631 | 89 098 | 1 839 | 0.17 |
| sloučení:02 | claude-haiku-5-5 | 8 | 14 432 | 35 138 | 1 240 | 0.00 |
| závěr | claude-sonnet-5-5 | 8 | 17 279 | 39 239 | 2 263 | 0.07 |

| model | agentů | vstup celkem* | výstup | ~$ API |
|---|--:|--:|--:|--:|
| claude-haiku-5-5 | 2 | 74 156 | 2 053 | 0.01 |
| claude-sonnet-5-5 | 2 | 482 519 | 11 008 | 0.33 |
| claude-opus-5-5 | 3 | 528 250 | 11 968 | 0.79 |

\* vstup celkem = nový vstup + zápis do cache + čtení z cache

Doba běhu: 8 min · agentů: 7 · orientačně $1.13 podle ceníku API
