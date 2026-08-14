# 2026-08-12-02 — Lightbox caption per fotka

## Motivace

Lightbox na detail stránce dnes ve spodku zobrazuje jen counter `1 / 3`. Uživatel potřebuje pod fotkou další údaje ze SSR — konkrétně autora a datum vytvoření fotografie, s tím, že tyto údaje mohou být jiné pro každou fotku téhož místa.

Cílový formát popisku: `[<index> / <count>] Foto: <autor>, <datum dle site.date_format>.`
Příklad: `[1 / 3] Foto: Jan Novak, 10.12.2013.`

## Datový model (uživatel doplní do zdrojů)

Nový volitelný sloupec v hlavní DB tabulce `record.autori_fotek`:

```python
{
  "0": {"autor": "Jan Novak", "vytvoreno": date(2013, 12, 10)},   # primary
  "1": {"autor": "Petr Svoboda", "vytvoreno": date(2015, 5, 3)},  # 007-1
  "2": {"autor": "Jan Novak", "vytvoreno": date(2014, 3, 22)},    # 007-2
}
```

- Klíč = suffix v pojmenování fotky (`0` = primary bez suffixu, `1`+ = additional).
- Chybí-li klíč pro danou fotku → fallback na globální `record.autor` / `record.vytvoreno` (už existují).
- Chybí-li i fallback → jen counter `[i / N]` (nebo prázdno pro 1 fotku).

## Kam se to implementovalo

Feature je **výhradně v projektu uživatele** (`temp/`, `tmp/`). Plugin `krizky-photos` se **nemění** — data přicházejí z DB záznamu, plugin je jen zprostředkovává přes existující photo dict.

### `temp/templates/_macros.html` — nové makro

`caption_for_photo(record, imgs, index, suffix)` skládá popisek podle formátu výše. Ošetřuje:
- Fallback per-photo → per-record.
- Prefix `[i / N]` jen když `imgs.count > 1`.
- Prázdný autor / prázdné datum (vypustí zbytečné čárky).
- Bezpečné čtení `record.autori_fotek or {}` — funguje i před přidáním sloupce do DB.

### `temp/templates/detail.html`

- Import: `from _macros.html import ..., caption_for_photo`.
- `<div class="main" data-caption="{{ caption_for_photo(record, imgs, 1, 0) }}">` — pro případ jedné fotky (thumbnails se v šabloně negenerují).
- `<button data-caption="{{ caption_for_photo(record, imgs, loop.index, loop.index0) }}">` — na každém thumbnailu; `loop.index0` mapuje 1:1 na suffix (0=primary, 1=první additional…).

### `tmp/site.js`

Tři drobné úpravy v lightbox handleru:
1. `lbImages.push(...)` — přidán klíč `caption: btn.dataset.caption || ''`.
2. Fallback pro 1-photo case čte `mainBox.dataset.caption`.
3. `lbShow()` používá `lbImages[lbIdx].caption`, ponechává původní `[i / N]` fallback pro případ, kdy `data-caption` na buttonu chybí (backward-compat).

Prefix `[i / N]` se generuje v šabloně (šablona zná `imgs.count` a `loop.index`), JS ho jen kopíruje z `data-caption`. Konzistentní s tím, jak se v projektu už formátuje datum (přes Jinja2 filter `strftime`).

## Ověřené scénáře (sanity render)

| # | Situace | Výstup |
|---|---------|--------|
| 1 | Per-photo autor+datum, 3 fotky | `[1 / 3] Foto: Jan Novak, 10.12.2013.` |
| 2 | Fallback per-record autor+datum, 3 fotky | `[2 / 3] Foto: Fallback Franta, 10.12.2013.` |
| 3 | Bez dat, 3 fotky | `[2 / 3]` |
| 4 | Per-photo data, 1 fotka | `Foto: Jan Novak, 10.12.2013.` |
| 5 | Bez dat, 1 fotka | `` (prázdno) |
| 6 | Jen autor | `[1 / 3] Foto: Jan Novak.` |
| 7 | Jen datum | `[1 / 3] Foto: 10.12.2013.` |

Test `/workspace/work/` neexistuje — jde o interaktivní sanity check přes samostatný Python script (viz git history této session).

## Změněné soubory

- `temp/templates/_macros.html` — nové makro `caption_for_photo`.
- `temp/templates/detail.html` — import + `data-caption` na `<div class="main">` a na `<button>`.
- `tmp/site.js` — 3 řádkové úpravy v lightbox handleru.

## Technické poznámky

- **Suffix vs. loop.index0**: `imgs.all = [primary, additional_1, additional_2, …]` → `loop.index0` (0, 1, 2, …) přesně odpovídá suffixu v pojmenování souborů (`007`, `007-1`, `007-2`). Uživatel v datech nebo v tabulce zadává `"0"`, `"1"`, `"2"` (stringové klíče, jak to přijde z JSON).
- **Strftime filter** parsuje i ISO stringy (`_strftime` v `krizky/site.py:20`), takže `vytvoreno` může být uložené jako `datetime.date`, `datetime.datetime` nebo `"2013-12-10"` string.
- **1-photo case**: fallback na `mainBox.dataset.caption` je záměrně tam — když je fotka jen jedna, šablona thumbnails negeneruje (`{% if imgs.count > 1 %}`), takže lightbox by neměl žádný data atribut. Přidáváme ho na `data-gallery-main` div.
- **Uživatel musí do DB doplnit `autori_fotek`.** Šablona bez sloupce funguje — `record.autori_fotek or {}` degraduje na fallback per-record.
- **`site` jako parametr makra**: Jinja2 makra mají uzavřený scope a nevidí globals — první verze na tom padla (`UndefinedError: 'site' is undefined`). Konzistentní s existujícím makrem `karta(place, site, distance)` v `_macros.html:32` jsem `site` přidal do signatury. Volání v `detail.html` proto všude `caption_for_photo(record, imgs, index, suffix, site)`.
