# Formát reportu

Reporty se zapisují do `reports/YYYY-MM-DD-HHMM/`. Text je česky, kód, klíče a cesty zůstávají beze změny.

```
reports/YYYY-MM-DD-HHMM/
  summary.md                   # vzorce napříč projekty, priority, statistiky
  core.md                      # nálezy v core
  plugin-krizky-<jméno>.md     # jeden soubor na plugin
  proposals/                   # jen návrhy, které kontroly skutečně vytvořily
    consolidation-to-core.md   # skupina duplicita
    hook-changes.md            # skupina api
    config-style-guide.md      # skupina config-data
```

Prázdné soubory, prázdné sekce ani věty typu „žádná zjištění“ se nepíšou. Chybějící sekce to říká sama.

## Blok nálezu

Každý nález má tuto podobu, bez vaty:

```markdown
### [SEVERITA] Krátký název (max. ~70 znaků)

**Kde:** `krizky-<jméno>/cesta/soubor.py:řádek` (více míst odděl čárkou)

**Co:** 1–2 věty: v čem je rozjezd, duplicita nebo problém.

**Proč vadí:** 1 věta o skutečném dopadu.

**Doporučení:** konkrétní krok. Při volbě mezi variantami uveď obě a preferovanou.

**Pravidlo:** odkud plyne kanonická podoba (`docs/guidelines/python.md` › Logging, precedent v `krizky/render.py:40`, nebo „návrh, viz proposals/…“).

**Stav:** nový | přetrvává (`reports/<předchozí>/plugin-krizky-<jméno>.md` › „<název nálezu>“)
```

`SEVERITA` je `blocker`, `recommended` nebo `nice-to-have`.

## `core.md` a `plugin-<jméno>.md`

```markdown
# <projekt>: revize konzistence

Datum: YYYY-MM-DD HH:MM

## Souhrn

- N blocker, N recommended, N nice-to-have
- Nejdůležitější: 2–3 věty.

## Zjištění

### Hraniční API a hooky
### Duplicita
### Konfigurace a pojmenování dat
### Python a chyby
### JavaScript
### Testy
### Dokumentace
### Mrtvý kód
```

Nálezy v sekci řaď podle severity.

## `summary.md`

```markdown
# Souhrn revize konzistence

Datum: YYYY-MM-DD HH:MM
Rozsah: všechny projekty | fokus `krizky-<jméno>` (ostatní jako kontext)
Předchozí report: `reports/<adresář>/` | žádný

## Priority

Nejdůležitější nálezy napříč projekty, seřazené podle dopadu. Každý: 1 věta a odkaz na nález.

## Vzorce napříč projekty

### <Název vzorce>

**Kde:** projekty a soubory.
**Popis:** co se opakuje.
**Návrh:** konsolidace do core, sjednocení, nebo odkaz do `proposals/`.

## Vyřešeno od minula

Blocker a recommended z předchozího reportu, které už neplatí. Každý: název a odkaz na starý nález.

## Guidelines k revizi

Místa v `docs/guidelines/`, která neodpovídají dnešnímu stavu. Každé: soubor › sekce, v čem nesedí, návrh úpravy.

## Statistiky

| | blocker | recommended | nice-to-have |
|---|--:|--:|--:|
| <projekt> | | | |
| celkem | | | |

Nových: N, přetrvává: N, vyřešeno od minula: N, vyřazeno při ověření: N.
```

## Proposals

### `proposals/consolidation-to-core.md`

Kandidáti seřazení podle dopadu (ušetřené řádky × počet pluginů).

```markdown
## <Název kandidáta>

**Síla vzoru:** strong | medium
**Výskyty:**
- `krizky-<a>/soubor.py:12-45`: varianta A
- `krizky-<b>/soubor.py:8-40`: varianta B (rozdíl: …)
**Návrh API v core:** modul a signatura; přednostně rozšíření `krizky.plugin_helpers`.
**Riziko:** v čem se výskyty liší a jestli to helper unese bez nafouknutých parametrů.
```

### `proposals/hook-changes.md`

```markdown
## Přidat | Upravit | Zvážit odstranění: `<hook>`

**Motivace:** vzor z kódu s odkazy `soubor:řádek`.
**Signatura:** současná → navrhovaná.
**Kdo by to využil:** pluginy.
**Zvážená alternativa:** helper v `plugin_helpers`, zdokumentování existující funkce a podobně, a proč nestačí.
**Migrace:** co se musí změnit v pluginech a v jakém pořadí.
```

### `proposals/config-style-guide.md`

Jen když skupina config-data našla aspoň tři konvence, které většina projektů už dodržuje. Sekce: pojmenování klíčů, umístění sekcí, cesty, defaulty a vypnutí, otevřené otázky k rozhodnutí uživatele.
