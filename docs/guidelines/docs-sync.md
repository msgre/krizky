# Guidelines: docs sync

Kdy skill musí updatovat dokumentaci a kterou.

## Trigger table — kdy update povinný

| Kód změna | README | CLAUDE.md | PLAN.md | Docstring | work/ log |
|---|---|---|---|---|---|
| Přidat/odstranit config klíč | **ANO** (Konfigurace sekce) | — | — | — | ANO |
| Přejmenovat config klíč | **ANO** | — | — | — | ANO |
| Přidat/odstranit CLI příkaz | **ANO** (CLI sekce) | — | — | ANO (helper text) | ANO |
| Přidat/odstranit hookspec | **ANO** (core README) | — | ANO (core PLAN plugin API) | **ANO** (v hooks.py) | ANO |
| Změnit hookspec signaturu | **ANO** (docstring) | — | ANO | **ANO** | ANO |
| Přidat/odstranit veřejnou funkci/třídu | ANO (pokud user-facing) | — | — | **ANO** | ANO |
| Přejmenovat veřejnou funkci/třídu | ANO | — | — | **ANO** | ANO |
| Přejmenovat internal `_foo` | — | — | — | pokud existuje | ANO |
| Refactor (bez API change) | — | — | — | — | ANO |
| Přidat závislost (pyproject/npm) | ANO (Požadavky sekce) | — | — | — | ANO |
| Změnit config style guide (např. escape rule) | ANO | ANO | — | — | ANO |

**Skill enforcement:** před commitem grepni: "obsahuje diff změnu, která spadá do řádku výše? Pokud ano, obsahuje diff i příslušnou docs update? Pokud ne → nekomitovat, doplnit."

## README kostra pro pluginy (canonical)

Pořadí sekcí — vyplývá z `proposals/config-style-guide.md` (v původním reportu). Skill při editaci README ji **respektuje**, ale **neupravuje pořadí existujících sekcí** (mimo scope). Nové sekce vkládá na správné místo.

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

## CLAUDE.md — kdy plugin má mít

Pravidlo z config-style-guide: **každý plugin má mít CLAUDE.md**. Aktuálně chybí ve všech pluginech (známý finding).

Kdy skill **vytváří** CLAUDE.md pro plugin:
- Jen když je to explicitní finding v reportu.
- Ne jako side-effect jiné implementace.

Minimální obsah CLAUDE.md pro plugin:

```markdown
# CLAUDE.md — <plugin name>

## Struktura kódu

- `plugin.py` — hookimpl třída.
- `<helper.py>` — <role>.

## Testy

```bash
uv run pytest
```

## Konvence

- <plugin-specific konvence, např. "photo files musí být pojmenované jako 007.jpg">.

## Po každé implementační session

Aktualizuj log v `work/YYYY-MM-DD-NN-<slug>.md` a `work/OVERVIEW.md`. Viz core `CLAUDE.md`.
```

## work/ log per plugin

Core `CLAUDE.md` říká: po každé implementační session vytvořit `work/YYYY-MM-DD-NN-heslo.md` + aktualizovat `work/OVERVIEW.md`.

**Aktuální stav:** jen core to má. Plugin nemá `work/`.

Skill:
- **Pro core:** vždycky aktualizuje `work/` (dle core CLAUDE.md).
- **Pro plugin bez `work/` adresáře:** NEZAKLÁDÁ ho. Zakládat plugin `work/` je samostatný finding (docs consistency).
- **Pro plugin s existujícím `work/`:** dodržuje konvence.

## Docstring update triggers

Vždy, když měníš:
- Signatura funkce/metody → update `Args:` sekci.
- Návratovou hodnotu → update `Returns:`.
- Vyhazované exceptions → update `Raises:`.
- Popis chování → update prvotní shrnutí + detail.

**Grep helper:** před commitem `grep -n <old_name> <changed_files>` — nesmí nic zbýt v docstringy ani komentářích.

## Migration notes při breaking change

Když skill dělá breaking change (rename config klíče, rename public API), v commit body přidá **Migration note**:

```
krizky-filters: přejmenovat pagination_window → paginationWindow v JS configu

Body ...

Migration:
- Uživatelský config.yaml: klíč `site.pagination_window` beze změny.
- Pluginové JS assety: `config.window` → `config.paginationWindow` (interní, uživatel by neměl řešit).

Reference: reports/2026-08-17-2013/plugin-krizky-filters.md
```

## Interakce s config-style-guide

`proposals/config-style-guide.md` v každém reportu popisuje "kanonické" konvence. Skill se jimi řídí. Když finding říká něco v rozporu se stylem guide → hierarchie:

1. **Finding wins** (finding je konkrétní; style guide obecný).
2. Ale: skill v log entry poznamená "tento fix rozporuje style guide sekci X — user by měl aktualizovat guide nebo finding".

## Post-commit verifikace docs

Po každém commitu:

1. `git diff HEAD~1 --stat` — vypsat, které soubory se změnily.
2. Pokud kód změněný, ale docs ne → warning v log entry (i když skill sám před commitem toto kontroluje, druhá kontrola je safety net).
