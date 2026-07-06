# Práce se zdroji dat

Krizky stahuje data ze tří typů zdrojů — tabulek, dokumentů a fotek. Všechny jsou od Google a všechny se konfigurují v sekci `sources` souboru `config.yaml`.

## Přehled a konfigurace

| Typ | Klíč v config | Google služba | Povinné atributy |
|---|---|---|---|
| Tabulky | `sources.tables` | Google Sheets | `id`, `gid`, `transform` |
| Dokumenty | `sources.docs` | Google Docs | `id`, `transform`, `output` |
| Fotografie | `sources.photos` | Google Drive | `folder_id` + viz níže |

### Jak najít ID

ID každého zdroje se vždy bere z URL dokumentu v prohlížeči.

> **Důležité:** Dokument musí být sdílený [jako čtenář](https://support.google.com/drive/answer/2494822) — buď konkrétní osobě s přístupem ke službě, nebo veřejně. Krizky pracuje jen s publikovanými dokumenty a bez oprávnění ke čtení se ke zdroji nedostane.

**Google Sheets:**
```
https://docs.google.com/spreadsheets/d/<ID>/edit#gid=<GID>
```
Tabulky potřebují obě hodnoty: `id` (ID dokumentu) a `gid` (ID konkrétního listu).

**Google Docs:**
```
https://docs.google.com/document/d/<ID>/edit
```
Dokumenty potřebují jen `id`.

**Google Drive** (složka s fotkami):
```
https://drive.google.com/drive/folders/<FOLDER_ID>
```

---

## Společné atributy

```yaml
sources:
    output: ./sources   # kam se ukládají stažená data (gitignore!)
    database: data.db   # název SQLite souboru (relativně k output)
```

`output` je pracovní adresář pro všechna stažená data — CSV soubory, DOCX soubory i SQLite databáze. Celý adresář se generuje při fetchi a patří do `.gitignore`.

`database` je název SQLite souboru, který vznikne uvnitř `output`. Do této databáze importují tabulkové transform skripty svá data a z ní pak generátor webu čte záznamy při sestavování stránek.

---

## Tabulky (`sources.tables`)

Každý klíč odpovídá jedné tabulce v Google Sheets a jedné tabulce v SQLite databázi. V Jinja2 šablonách jsou dostupné jako `{{ tables.<název> }}`, například `{{ tables.typy }}`.

```yaml
sources:
    tables:
        krizky:
            id: "1RmjhfrbgASDyyv64nWXZjxEU2wWulE69a7fl3jCp6gI"
            gid: "1158998617"
            skip_rows: 4
            main: true
            transform: ./transforms/data.sh   # povinné
        typy:
            id: "11DFObgY-MwwQI-RP8R4YLG_q69KBuWlKD1FIULovkuI"
            gid: "280152183"
            transform: ./transforms/typy.sh   # povinné
```

`transform` je pro tabulky povinný. Minimální skript musí alespoň naimportovat CSV do SQLite — generátor webu čte data z databáze, ne přímo ze stažených souborů.

### `skip_rows`

Tabulky v Google Sheets občas mají v horní části dokumentu metadata pro redaktory — nadpisy, legendu, prázdné řádky — které nejsou součástí dat. `skip_rows` říká, kolik takových řádků krizky přeskočí, než začne číst záznamy.

Není povinné (výchozí hodnota: `0`). Pokud data začínají hned prvním řádkem, `skip_rows` se neuvádí.

Hodnota se předává i do transform skriptů jako `$5`, takže skript ji může využít — například pro výpočet absolutních čísel řádků z originálu (viz příklad v sekci sqlite-utils níže).

### `main: true`

Právě jedna tabulka musí být označena jako hlavní. Tato tabulka tvoří hlavní dataset, ze kterého se generují stránky webu — detail stránky, kategorie, stránkování.

Ostatní tabulky (bez `main`) jsou dostupné v šablonách jako `{{ tables.<název> }}`, ale neřídí generování stránek.

---

## Dokumenty (`sources.docs`)

```yaml
sources:
    docs:
        krysi_hlidka:
            id: "16mXJdjqLMCvf4QAjhD30UE1GD-5Ixk7YisbGJEZLcKk"
            transform: ./transforms/krysi_hlidka.sh   # povinné
            output: krysi_hlidka.md                    # povinné
```

Dokument se stáhne jako DOCX. Oba atributy `transform` a `output` jsou pro dokumenty povinné — bez transform skriptu by krizky nevědělo, jak DOCX zpracovat. Výsledný soubor (typicky Markdown) zůstane na disku a před generováním webu se načte odtamtud. V šablonách je dostupný jako `{{ docs.<název> }}`, například `{{ docs.krysi_hlidka }}`.

---

## Fotografie (`sources.photos`)

Fotografie se konfigurují jako Google Drive → Cloudflare R2 pipeline. Citlivé hodnoty (klíče, tokeny) se do `config.yaml` nepíší přímo — používá se `$ENV_VAR` syntaxe (viz README).

```yaml
sources:
    photos:
        base_url: https://photos.example.com
        source:
            type: gdrive
            folder_id: $GDRIVE_FOLDER_ID
            account_key: $GDRIVE_ACCOUNT_KEY
            metadata: ./sources/photos/gdrive_metadata.json
        destination:
            type: cloudflare
            bucket: $CF_BUCKET_NAME
            account_id: $CF_ACCOUNT_ID
            access_key_id: $CF_ACCESS_KEY_ID
            secret_access_key: $CF_SECRET_ACCESS_KEY
            metadata: ./sources/photos/cf_metadata.json
        formats:
            - {format: avif, mime: image/avif, quality: 60}
            - {format: webp, mime: image/webp, quality: 80}
            - {format: jpg,  mime: image/jpeg, optimalizator: cjpeg, quality: 80}
        sizes:
            - {name: micro,  max_width: 150}
            - {name: thumb,  max_width: 330}
            - {name: small,  max_width: 680}
            - {name: medium, max_width: 960}
            - {name: big,    max_width: 1600}
```

---

## Transform skripty

Příkaz `krizky fetch sources` stáhne data ze všech nakonfigurovaných zdrojů, ale transformace defaultně nespustí. Teprve příznak `--transform` zajistí, že se po stažení spustí i transform skripty:

```bash
krizky fetch sources            # jen stažení (CSV, DOCX)
krizky fetch sources --transform  # stažení + transformace
```

Toto rozdělení je záměrné — transform skripty lze pouštět opakovaně nad již staženými zdrojovými soubory bez nutnosti znovu stahovat z Google.

### Proč transform?

**Tabulky** — stáhnou se jako CSV, ale generátor webu čte data ze SQLite databáze. Transform skript musí CSV naimportovat do DB, a typicky ho při tom také vyčistí: přejmenuje sloupce, odstraní nepublikované záznamy, přidá odvozené hodnoty (slugy, parsované souřadnice apod.).

**Dokumenty** — stáhnou se jako DOCX. Generátor šablon ale potřebuje obsah v jednoduché textové podobě. Transform skript je proto nutnost — typicky zavolá pandoc a DOCX převede na Markdown.

---

## Poziční parametry transform skriptu

Každý bash skript dostane 5 pozičních parametrů:

```bash
SOURCE_PATH=$1    # cesta ke zdrojovému souboru (CSV nebo DOCX)
SQLITE_PATH=$2    # cesta k SQLite databázi
TABLE_NAME=$3     # název tabulky v DB
OUTPUT_PATH=$4    # výstupní cesta (pro docs: plná cesta k výstupnímu souboru)
SKIP_ROWS=$5      # hodnota skip_rows z konfigurace (pro docs: vždy 0)
```

Standardní hlavička každého transform skriptu:

```bash
#!/bin/bash

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

SOURCE_PATH=$1
SQLITE_PATH=$2
TABLE_NAME=$3
OUTPUT_PATH=$4
SKIP_ROWS=$5
```

`SCRIPT_DIR` se hodí pro relativní odkazování na Python helpery ve stejném adresáři.

---

## sqlite-utils: kuchařka vzorů

Tabulkové transform skripty pracují s nástrojem [sqlite-utils](https://sqlite-utils.datasette.io/). Vždy se spouštějí přes `uv run`.

### Import CSV do databáze

```bash
uv run sqlite-utils insert $SQLITE_PATH $TABLE_NAME $SOURCE_PATH --csv
```

### Přejmenování sloupce

```bash
uv run sqlite-utils transform $SQLITE_PATH $TABLE_NAME --rename "Původní název" "novy_nazev"
```

Sloupce z Google Sheets mívají dlouhé nebo diakritické názvy — přejmenování na ASCII slugy ulehčí práci v šablonách. Lze řetězit více `--rename` v jednom příkazu nebo volat opakovaně.

### Smazání sloupce

```bash
uv run sqlite-utils transform $SQLITE_PATH $TABLE_NAME --drop "nepotrebny_sloupec"
```

### Přidání nového sloupce s vypočtenou hodnotou

```bash
uv run sqlite-utils add-column $SQLITE_PATH $TABLE_NAME nazev_sloupce integer
uv run sqlite-utils $SQLITE_PATH "UPDATE $TABLE_NAME SET nazev_sloupce = <výraz>"
```

Příklad — přidání čísla řádku z originálu (s zohledněním přeskočených řádků):

```bash
uv run sqlite-utils add-column $SQLITE_PATH $TABLE_NAME id_radku integer
uv run sqlite-utils $SQLITE_PATH "UPDATE $TABLE_NAME SET id_radku = rowid + $SKIP_ROWS"
```

### Libovolný SQL dotaz

```bash
uv run sqlite-utils $SQLITE_PATH "DELETE FROM $TABLE_NAME WHERE stav = 'FALSE'"
```

### Inline Python konverze (jeden sloupec → jeden sloupec)

Hodí se pro odvození nové hodnoty z původní hodnoty v buňce — například parsování textu, normalizaci formátu nebo převod na jiný typ.

```bash
uv run sqlite-utils convert $SQLITE_PATH $TABLE_NAME nazev_sloupce '<python výraz>'
```

Proměnná `value` obsahuje aktuální hodnotu buňky. Výsledek výrazu přepíše původní hodnotu.

```bash
# CSV string → JSON list
uv run sqlite-utils convert $SQLITE_PATH $TABLE_NAME Tagy \
    '[t.strip() for t in value.split(",")]'

# oprava NULL a prázdných hodnot
uv run sqlite-utils $SQLITE_PATH \
    "UPDATE $TABLE_NAME SET Tagy = '[]' WHERE Tagy = '' OR Tagy IS NULL"
```

### Python skript: jeden vstupní sloupec

Pokud je logika složitější, než zvládne jednořádkový výraz, lze předat Python skript přes stdin. Skript musí definovat funkci `convert(value)`:

```bash
# přepis původního sloupce
cat $SCRIPT_DIR/data/slug_type.py | uv run sqlite-utils convert $SQLITE_PATH $TABLE_NAME typ -

# výsledek do nového sloupce (původní zůstane)
cat $SCRIPT_DIR/data/slug_type.py | \
    uv run sqlite-utils convert $SQLITE_PATH $TABLE_NAME typ - --output typ_slug
```

```python
# slug_type.py
from common import slugify

def convert(value):
    return f"kategorie-{slugify(value)}"
```

Se `--multi` může skript vrátit `dict` — každý klíč se stane samostatným sloupcem. S `--drop` se původní sloupec odstraní:

```bash
cat $SCRIPT_DIR/data/convert_gps.py | \
    uv run sqlite-utils convert $SQLITE_PATH $TABLE_NAME GPS --multi - --drop
```

```python
# convert_gps.py — vrací dict, sqlite-utils vytvoří sloupce latitude a longitude
def convert(value):
    # parsování GPS stringu
    return {"latitude": lat, "longitude": lon}
```

### Python skript: více vstupních sloupců

`sqlite-utils convert` funguje vždy jen s jedním vstupním sloupcem. Pokud výsledek závisí na více sloupcích najednou (typicky generování slugu z názvu a GPS souřadnic), je potřeba standalone Python skript:

```bash
uv run sqlite-utils add-column $SQLITE_PATH $TABLE_NAME slug text
PYTHONPATH=$SCRIPT_DIR/data uv run python $SCRIPT_DIR/data/slug_misto.py $SQLITE_PATH $TABLE_NAME
```

Skript přijme cestu k DB a název tabulky jako poziční argumenty a provede UPDATE přímo přes `sqlite_utils.Database`:

```python
import sys
import sqlite_utils

db_path = sys.argv[1]
table_name = sys.argv[2]

db = sqlite_utils.Database(db_path)
with db.conn:
    safe_table_name = db.quote(table_name)
    db.register_function(generate_slug, name="generate_slug_fn")
    db.execute(
        f"UPDATE {safe_table_name} SET slug = generate_slug_fn(nazev, latitude, longitude)"
    )
```

---

## `uv run` a PYTHONPATH

Všechny příkazy se spouštějí přes `uv run`, aby se použilo správné virtuální prostředí projektu.

Pokud Python skript importuje ze sdíleného modulu (například `from common import slugify`), je potřeba nastavit `PYTHONPATH`:

```bash
# pro sqlite-utils convert se skriptem ze stdin
PYTHONPATH=$SCRIPT_DIR/data uv run sqlite-utils convert $SQLITE_PATH $TABLE_NAME typ - --output typ_slug

# pro standalone Python skript
PYTHONPATH=$SCRIPT_DIR/data uv run python $SCRIPT_DIR/data/slug_misto.py $SQLITE_PATH $TABLE_NAME
```

Adresář předaný v `PYTHONPATH` (typicky `data/` vedle transform skriptu) pak může obsahovat sdílené moduly dostupné pro všechny Python konverze v projektu.
