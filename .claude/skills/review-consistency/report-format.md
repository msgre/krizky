# Report format

All reports go under `reports/YYYY-MM-DD-HHMM/`. Prose is Czech; code, keys, and paths stay as-is.

## Finding block (used everywhere)

Every finding uses this structure. Keep it tight — no filler prose.

```markdown
### [SEVERITY] Krátký název (max ~70 znaků)

**Kde:** `plugin-name/path/to/file.py:line` (i více míst, oddělených čárkou)

**Co:** 1–2 věty popisu drift/duplicity/problému.

**Proč vadí:** 1 věta — reálný dopad (nekonzistence, matoucí pro čtenáře, blokuje refaktor, atd.).

**Doporučení:** konkrétní krok. Pokud jde o volbu mezi variantami, uveď obě a preferovanou.

**Reference:** (volitelné) odkazy na core precedent nebo jiné plugin varianty.
```

Severity je jedno z: `blocker`, `recommended`, `nice-to-have`.

## Per-project report — `core.md` / `plugin-<name>.md`

```markdown
# <projekt> — revize konzistence

Datum: YYYY-MM-DD HH:MM
Reviewer: Claude Code (review-consistency skill)

## Souhrn

- N blocker
- N recommended
- N nice-to-have

Nejdůležitější zjištění: (2–3 věty)

## Zjištění

### Konfigurace
<finding blocks>

### Hooky
<finding blocks>

### Python style
<finding blocks>

### JavaScript style
<finding blocks — vynechat sekci pokud plugin nemá JS>

### Error handling a logging
<finding blocks>

### Pojmenování v datech
<finding blocks>

### Testy
<finding blocks>

### Dokumentace
<finding blocks>

### Dead code
<finding blocks>

### Hraniční API (jen pro pluginy — core tuto sekci vynechá)
<finding blocks>
```

Prázdné sekce vynechej. Nepiš "žádná zjištění" — absence sekce už to říká.

## Summary report — `summary.md`

```markdown
# Souhrn revize konzistence

Datum: YYYY-MM-DD HH:MM
Rozsah: <full sweep | jen krizky-photos jako focus, ostatní jako kontext>

Projekty v revizi:
- `krizky` (core) — viz [core.md](core.md)
- `krizky-photos` — viz [plugin-krizky-photos.md](plugin-krizky-photos.md)
- ...

## Top priority

Seznam nejdůležitějších věcí napříč projekty, seřazený podle dopadu (ne podle abecedy).
Každá položka = 1 věta + odkaz na příslušný per-project report.

## Vzorce napříč projekty

Sekce pro cross-cutting patterny — věci, které nejsou "chyba jednoho projektu",
ale vzorec, který se objevuje ve více projektech.

### <Jméno vzorce> (např. "Duplicitní logika načítání assetů")

**Kde:** seznam projektů + souborů.

**Popis:** co se opakuje.

**Návrh:** konsolidovat do core / sjednotit styl / vytvořit shared helper.

**Detail:** odkaz na `proposals/consolidation-to-core.md` sekce X, pokud relevantní.

## Kandidáti na konsolidaci do core

Krátký seznam s odkazy do `proposals/consolidation-to-core.md`.

## Návrhy na změny plugin API

Krátký seznam s odkazy do `proposals/hook-changes.md`.

## Statistiky

- Počet zjištění celkem: N (X blocker, Y recommended, Z nice-to-have)
- Rozložení podle projektu: tabulka
- Rozložení podle tématu: tabulka
```

## Proposals

Proposals jsou samostatné dokumenty, které vzniknou jen tehdy, pokud check produkoval smysluplný obsah. Nevytvářej prázdné proposals.

### `proposals/config-style-guide.md`

Pouze pokud config check měl dost materiálu na sjednocující dokument. Struktura:

```markdown
# Config style guide (návrh)

Odvozeno z revize <datum>. Popisuje konvence použité v core + většině pluginů.
Slouží jako vodítko pro budoucí implementace config options.

## Konvence pojmenování

- <pravidlo> — <příklad z existujícího kódu>
- ...

## Struktura sekcí

...

## Interpolace hodnot

...

## Defaulty a "vypnuto"

...

## Otevřené otázky

Seznam míst, kde konvence není jasná — čeká na uživatelské rozhodnutí.
```

### `proposals/hook-changes.md`

```markdown
# Návrhy na změny plugin API

## Přidat hook: `<name>`

**Motivace:** vzorec, který X pluginů řeší ad-hoc.
**Signatura:** `def hook_name(...)`.
**Kdo by ho implementoval:** seznam pluginů, které by z toho těžily.
**Alternativy:** (proč hook a ne shared helper / mixin / event bus).

## Upravit hook: `<name>`

**Aktuální signatura:** ...
**Navrhovaná signatura:** ...
**Důvod:** ...
**Migrace:** ...

## Zvážit odstranění: `<name>`

**Důvod:** N implementací / používá se jen X-krát / duplikuje jiný hook.
**Riziko:** ...
```

### `proposals/consolidation-to-core.md`

```markdown
# Kandidáti na konsolidaci do core

Kandidáty seřaď podle "efektu na řádek konsolidovaného kódu"
(kolik LOC ušetří napříč pluginy).

## <Jméno kandidáta>

**Vzorec:** stručný popis, co se opakuje.

**Výskyty:**
- `krizky-photos/foo.py:12-45` — varianta A
- `krizky-json/bar.py:8-40` — varianta B (drobný rozdíl: X)

**Návrh API v core:** kam by to patřilo (`krizky/helpers.py`?), jaká signatura.

**Riziko / poznámky:** liší se pluginy v detailu, který by měl helper pokrýt parametrem?
```
