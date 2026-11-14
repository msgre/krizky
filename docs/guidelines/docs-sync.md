# Guidelines: docs sync

Kdy a kterou dokumentaci aktualizovat spolu se změnou kódu.

## Kdy je úprava povinná

| Změna kódu | README | PLAN.md (core) | Docstring |
|---|---|---|---|
| Přidat/odstranit config klíč | **ANO** (Konfigurace) | — | — |
| Přejmenovat config klíč | **ANO** | — | — |
| Přidat/odstranit CLI příkaz | **ANO** (CLI příkazy) | — | ANO (help text) |
| Přidat/odstranit hookspec | **ANO** (core README, `docs/plugins.md`) | ANO (plugin API) | **ANO** (`hooks.py`) |
| Změnit hookspec signaturu | **ANO** (`docs/plugins.md`) | ANO | **ANO** |
| Přidat/odstranit veřejnou funkci/třídu | ANO (pokud user-facing; v core `docs/plugins.md`) | — | **ANO** |
| Přejmenovat veřejnou funkci/třídu | ANO | — | **ANO** |
| Přejmenovat interní `_foo` | — | — | pokud existuje |
| Přidat závislost (pyproject/npm) | ANO (Požadavky) | — | — |

V core se navíc aktualizují tabulky konvencí šablon v `CLAUDE.md`. Logy do `work/` řeší `CLAUDE.md` core.

Před commitem zkontroluj, jestli diff spadá do některého řádku tabulky. Pokud ano, musí obsahovat i odpovídající úpravu dokumentace.

## Kostra README pluginu

```
# krizky-<name>

Jednořádkový popis.

Odstavec: co plugin dělá, jaké hooky používá.

## Instalace

## Konfigurace

## [Nutné úpravy šablon]

## [Použití v šablonách]

## [CLI příkazy]

## Požadavky

## Licence
```

Sekce v hranatých závorkách jsou volitelné. Novou sekci vlož na správné místo. Pořadí existujících sekcí měň jen tehdy, když je to úkolem.

## CLAUDE.md

Každý projekt má `CLAUDE.md`. Pluginy ho dostaly přes `/swarm:init` se společnou kostrou (Ověření, Pravidla projektu, Git, Swarm). Úvodní odstavec popisuje daný plugin, cesty ke guidelines a ke core `work/` musí sedět.

## Docstringy

Když měníš:

- signaturu funkce nebo metody → `Args:`,
- návratovou hodnotu → `Returns:`,
- vyhazované výjimky → `Raises:`,
- chování → shrnutí a detail.

Před commitem `grep -n <staré_jméno> <změněné_soubory>`: v docstrinzích ani komentářích nesmí nic zůstat.

## Poznámka k migraci při breaking change

Když změna rozbíjí kompatibilitu (přejmenování config klíče, veřejného API), přidej do těla commitu sekci `Migration:`:

```
fix: krizky-filters přejmenování pagination_window → paginationWindow v JS configu

Tělo …

Migration:
- Uživatelský config.yaml: klíč `site.pagination_window` beze změny.
- Assety pluginu: `config.window` → `config.paginationWindow` (interní).
```
