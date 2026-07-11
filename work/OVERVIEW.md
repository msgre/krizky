# Krizky — implementační přehled

Nástroj `krizky` je univerzální generátor statických webů z Google Sheets, Google Docs a Google Drive fotek.
Plná specifikace je v `../PLAN.md` (relativně k tomuto souboru).

**Tech stack:** Python 3.14, Jinja2, sqlite-utils, uv, pytest, pyproject.toml  
**Vstupní bod CLI:** `krizky` (click)  
**Konfigurace:** `config.yaml` (globální `--config` flag)

---

## Stav fází

| Fáze | Název                           | Status  | Log soubor |
|------|---------------------------------|---------|------------|
| 1    | Projekt + Config                | DONE    | [2026-07-06-01-project-setup.md](2026-07-06-01-project-setup.md) |
| 2    | Fetch sources                   | DONE    | [2026-07-06-02-fetch-sources.md](2026-07-06-02-fetch-sources.md) |
| 3    | Site generation – základní typy | DONE    | [2026-07-11-01-site-generation.md](2026-07-11-01-site-generation.md) |
| 4    | Site generation – stitky + stránkování | DONE | [2026-07-11-01-site-generation.md](2026-07-11-01-site-generation.md) |
| 5    | Photos                          | TODO    | —          |
| 6    | Kompletní build + integrace     | TODO    | —          |

---

## Pravidlo pro logování

**Po každé dokončené implementaci nebo interaktivní session musí agent vytvořit nebo zaktualizovat log soubor** ve složce `work/`:

- Jméno souboru: `work/<YYYY>-<MM>-<DD>-<NN>-<HESLO>.md`
  - `<NN>` začíná `01` každý den, zvyšuje se o 1 s každou realizací
  - `<HESLO>` je stručné anglické shrnutí (kebab-case), např. `project-setup`, `config-loading`
- Zároveň zaktualizuj řádek v tabulce "Stav fází" výše (změň TODO → IN PROGRESS / DONE + doplň odkaz na log)

---

## Adresářová struktura výsledného projektu

```
krizky/                     # CLI package
  __init__.py
  cli.py                    # click entry point
  config.py                 # YAML loading + ENV substitution + validace
  fetch.py                  # stahování Google Sheets/Docs
  build_site.py             # generování HTML
  build_photos.py           # zpracování fotek
  orchestrator.py           # krizky build (celý flow)
sources/                    # generováno při fetchi (v .gitignore)
  data.db
  tables/
    <name>/
      source/<name>.csv
      transformed/
  docs/
    <name>/
      source/<name>.docx
      transformed/<name>.md
utils/                      # stávající pomocné funkce (zachovat, případně refactorovat)
transforms/                 # bash transform skripty (uživatelské)
templates/                  # Jinja2 šablony (uživatelské)
assets/                     # statické soubory (CSS, JS, …)
tests/
  fixtures/
config.yaml                 # příklad konfigurace projektu
```

---

## Fáze 1 — Projekt + Config

### Co implementovat

1. **`pyproject.toml`** — přejmenovat projekt na `krizky`, přidat závislosti:
   - `click>=8.0`
   - `jinja2>=3.0`
   - `pyyaml>=6.0`
   - `python-dotenv>=1.0`
   - `sqlite-utils>=3.39`
   - Dev závislosti: `pytest`, `pytest-cov`
   - Entry point: `krizky = "krizky.cli:cli"`

2. **`krizky/config.py`** — načtení a validace konfigurace:
   - Funkce `load_config(path: str) -> dict` — načte YAML, substituuje ENV proměnné
   - ENV substituce: hodnoty začínající `$` se nahradí hodnotou proměnné prostředí; pokud proměnná neexistuje, vyhodí `ConfigError` s popisem
   - Načítat `.env` soubor pokud existuje (python-dotenv, `load_dotenv()`)
   - Funkce `validate_config(config: dict)` — ověří:
     - Existuje sekce `sources` a `site`
     - V `sources.tables` existuje právě jedna tabulka s `main: true`
     - Cesty ke transform skriptům (pokud jsou uvedeny) existují na disku
     - Pro každý `docs` záznam jsou přítomny povinné atributy `transform` a `output`
   - Vlastní výjimka `ConfigError(message)`

3. **`krizky/cli.py`** — click CLI skeleton:
   - Globální skupina `cli` s `--config` parametrem (default: `config.yaml`)
   - Příkazy (zatím jen stub, který vypíše "not implemented"):
     - `krizky validate`
     - `krizky init`
     - `krizky fetch sources [--transform]`
     - `krizky fetch photos`
     - `krizky build [--force] [--dry-run]`
     - `krizky build site [--force] [--dry-run]`
     - `krizky build photos [--force] [--dry-run]`
   - `krizky validate` musí být plně funkční: načte config, spustí `validate_config`, vypíše OK nebo chyby

4. **`krizky init`** — vytvoří kostru nového projektu:
   - Vygeneruje `config.yaml` (šablona s komentáři, ukázkový obsah)
   - Vygeneruje `.env.example`
   - Vytvoří adresáře: `templates/`, `assets/`, `transforms/`
   - Pokud cílový adresář není prázdný, vyžádá si potvrzení

### Testy (`tests/test_config.py`)

- `test_load_config_basic` — načte platný YAML, vrátí dict
- `test_env_substitution` — hodnota `$MY_VAR` se substituuje z env
- `test_env_substitution_missing` — chybějící proměnná vyhodí `ConfigError`
- `test_validate_main_true_missing` — žádné `main: true` → `ConfigError`
- `test_validate_main_true_duplicate` — dvě tabulky s `main: true` → `ConfigError`
- `test_validate_docs_missing_output` — docs záznam bez `output` → `ConfigError`

### Poznámky

- Existující `utils/` zachovat beze změny, jen přidat `krizky/` package vedle
- Nevytvářet žádné HTML, žádné šablony — to patří do pozdějších fází

---

## Fáze 2 — Fetch sources

### Co implementovat

**`krizky/fetch.py`**

#### Google Sheets → CSV

Veřejný Google Sheet jde stáhnout bez autentizace:
```
https://docs.google.com/spreadsheets/d/<id>/export?format=csv&gid=<gid>
```

Funkce `fetch_sheet(id: str, gid: str, output_path: Path, skip_rows: int = 0)`:
- Stáhne CSV přes HTTP (requests nebo urllib — preferovat urllib, bez extra závislostí)
- Pokud `skip_rows > 0`, přeskočí prvních N řádků
- Uloží do `output_path`

#### Google Docs → DOCX

```
https://docs.google.com/document/d/<id>/export?format=docx
```

Funkce `fetch_doc(id: str, output_path: Path)`:
- Stáhne DOCX, uloží do `output_path`

#### Transform skript

Funkce `run_transform(script: Path, source_file: Path, db_path: Path, table_name: str, output_path: Path = None)`:
- Spustí bash skript s parametry:
  - `$1` = `source_file`
  - `$2` = `db_path`
  - `$3` = `table_name`
  - `$4` = `output_path` (může být `None` → předá prázdný string)
- Streamuje stdout/stderr do terminálu (subprocess.run se `check=True`)
- Při nenulové návratové hodnotě vyhodí `TransformError`

#### Příkaz `krizky fetch sources [--transform]`

Algoritmus:
1. Načti config
2. Pro každou tabulku v `sources.tables`:
   - Vytvoř adresář `<sources.output>/tables/<name>/source/`
   - Stáhni CSV do `<sources.output>/tables/<name>/source/<name>.csv`
3. Pro každý doc v `sources.docs`:
   - Vytvoř adresář `<sources.output>/docs/<name>/source/`
   - Stáhni DOCX do `<sources.output>/docs/<name>/source/<name>.docx`
4. Pokud `--transform`:
   - Pro každou tabulku s `transform`: spusť transform skript
   - Pro každý doc s `transform`: spusť transform skript; po dokončení načti `$4` a ověř, že soubor existuje

### Testy (`tests/test_fetch.py`)

- Mockovat HTTP volání (unittest.mock nebo responses knihovna)
- `test_fetch_sheet_basic` — stáhne CSV, uloží na disk
- `test_fetch_sheet_skip_rows` — skip_rows=2 odstraní první 2 řádky
- `test_run_transform_success` — skript s exit 0 proběhne bez výjimky
- `test_run_transform_failure` — skript s exit 1 vyhodí `TransformError`

---

## Fáze 3 — Site generation: základní typy stránek

### Co implementovat

**`krizky/build_site.py`**

#### Načtení kontextu

Funkce `load_context(config: dict) -> dict`:
- Načte všechny tabulky z SQLite DB (`sources.database`)
- Pro každou tabulku v `sources.tables`:
  - Načti záznamy jako `list[dict]` (sqlite-utils: `db[table].rows_where(...)`)
  - Pokud má tabulka `key` atribut: převeď na `dict` keyed by hodnotou daného sloupce
  - Vlož do kontextu jako `tables.<name>`
- Pro každý doc v `sources.docs`:
  - Načti obsah transformed souboru (markdown string)
  - Vlož do kontextu jako `docs.<name>`
- Tabulka s `main: true` → `tables.<name>` + zároveň jako základ pro `filtered`

Funkce `get_filtered(records: list, query: dict, order_by: str, ordering: str) -> list`:
- Aplikuje `query.condition` jako WHERE klauzuli (přes sqlite-utils nebo Python filtrování)
- Aplikuje `query.limit`
- Respektuje `order_by` a `ordering` z konfigurace

#### Renderování stránky

Funkce `render_page(template_name: str, context: dict, output_path: Path, templates_dir: Path)`:
- Načte Jinja2 šablonu z `templates_dir`
- Renderuje s daným kontextem
- Zapíše do `output_path`

#### Typy stránek (tato fáze)

1. **Jednoduchá stránka** (`query` nebo nic):
   ```yaml
   homepage:
       query:
           limit: 10
       path: /index.html
       template: index.html
   ```
   Kontext: `filtered` = záznamy dle query, všechny ostatní `tables`, `docs`

2. **All stránka** (bez `query`, bez `category`, bez `detail`):
   ```yaml
   all:
       path: /mista.html
       template: mista.html
   ```
   Kontext: `filtered` = kompletní main dataset

3. **Category stránka** (`category`, bez `many: true`):
   ```yaml
   kategorie:
       category: typ
       path: "/<typ_slug>.html"
       template: kategorie.html
   ```
   - GROUP BY `category` sloupec → unikátní non-NULL, non-empty hodnoty
   - Pro každou hodnotu: vygeneruj stránku pojmenovanou dle slug sloupce (`<category>_slug`)
   - Kontext: `filtered` = záznamy dané kategorie, `category` = aktuální hodnota

4. **Detail stránka** (`detail: true`):
   ```yaml
   detail:
       detail: true
       path: "/<slug>.html"
       template: detail.html
   ```
   - Pro každý záznam z main datasetu jedna stránka
   - Path se sestaví z `slug` sloupce záznamu (hodnota sloupce, jehož jméno odpovídá placeholder v path)
   - Kontext: `filtered`, `record` = aktuální záznam

#### Assets

Funkce `copy_assets(assets_dir: Path, output_dir: Path)`:
- `shutil.copytree` s `dirs_exist_ok=True`

#### Příkaz `krizky build site [--force] [--dry-run]`

Algoritmus:
1. Načti config, načti kontext
2. Vytvoř output adresář
3. Zkopíruj assets
4. Pro každou stránku v `site.pages`: vygeneruj dle typu
5. `--dry-run`: vypiš co by se vygenerovalo, ale nezapisuj
6. DB se načítá vždy z existující `sources/data.db` — příkaz neprovádí fetch

### Testy (`tests/test_build_site.py`)

Vytvořit fixture: malá SQLite DB se 3-5 záznamy, jednoduchou tabulkou `items` (sloupce: id, nazev, typ, slug, typ_slug).

- `test_simple_page` — vygeneruje `index.html` s limit=2
- `test_all_page` — vygeneruje stránku se všemi záznamy
- `test_category_page` — GROUP BY typ → 2 soubory pro 2 kategorie
- `test_detail_page` — 3 záznamy → 3 soubory
- `test_assets_copy` — assets se zkopírují do output

---

## Fáze 4 — Site generation: stitky + stránkování

### Co implementovat

Rozšíření `krizky/build_site.py`.

#### Typ stránky: Stitky (`many: true`)

```yaml
stitky:
    category: stitky
    many: true
    path: "/<stitky_slug>.html"
    template: stitky.html
```

- Sloupec `stitky` obsahuje JSON list stringů, např. `["příroda", "kámen"]`
- Sloupec `stitky_slug` obsahuje JSON objekt `{"příroda": "priroda", "kámen": "kamen"}`
- Algoritmus:
  1. Projdi všechny záznamy main datasetu
  2. Pro každý záznam parsuj JSON list ze sloupce `category`
  3. Akumuluj unikátní hodnoty tagů (použij set)
  4. Pro každý unikátní tag:
     - `filtered` = záznamy, kde JSON list obsahuje tento tag
     - slug = lookup v `<category>_slug` JSON objektu libovolného záznamu skupiny
     - vygeneruj stránku dle path šablony

#### Stránkování

Globální nastavení v `site`:
```yaml
paginate_by: 10
```

Přetížení na úrovni stránky:
```yaml
all:
    paginate: true
    paginate_by: 20
    path: /mista.html
    template: mista.html
```

Logika stránkování:
- Pokud `paginate: true` nebo globální `paginate_by` > 0 a stránka to nevypíná explicitně:
  - Rozděl `filtered` na chunks po `paginate_by` záznamech
  - 1. stránka → `<path>` (beze změny)
  - 2. stránka → `<stem>-2<ext>` (např. `mista-2.html`)
  - 3. stránka → `<stem>-3<ext>`
- Kontext navíc: `page`, `total_pages`, `has_prev`, `has_next`, `prev_url`, `next_url`
- `prev_url` / `next_url` jsou relativní cesty (string nebo None)

Stránkování se aplikuje i na category a stitky stránky.

### Testy (`tests/test_pagination.py`, `tests/test_stitky.py`)

- `test_pagination_single_page` — 5 záznamů, paginate_by=10 → 1 soubor
- `test_pagination_multi_page` — 25 záznamů, paginate_by=10 → 3 soubory (`mista.html`, `mista-2.html`, `mista-3.html`)
- `test_pagination_context` — správné hodnoty `page`, `total_pages`, `has_prev`, `has_next`, `prev_url`, `next_url`
- `test_stitky_basic` — 3 záznamy s různými tagy → správný počet stránek
- `test_stitky_multi_tag` — záznam s více tagy se objeví na více stránkách

---

## Fáze 5 — Photos

### Co implementovat

**`krizky/build_photos.py`**

#### Fetch GDrive metadata

Funkce `fetch_gdrive_metadata(folder_id: str, account_key_path: str) -> list[dict]`:
- Stáhne seznam fotek z Google Drive složky přes Service Account
- Vrátí list objektů dle formátu v PLAN.md (klíče: `title`, `last_modified`, `file_id`, `download_url_api`, `row_number`, `subfolder_path`)
- Uloží do `sources/photos/gdrive_metadata.json`
- `row_number` odvozuje z názvu souboru (`123.jpg` → 123, `123-1.jpg` → 123)

Funkce `fetch_cloudflare_metadata(bucket: str, account_id: str, ...) -> dict`:
- Stáhne seznam objektů z Cloudflare R2 přes S3 API (boto3)
- Vrátí dict dle formátu v PLAN.md (key = base name bez přípony, value = dict variant → `{w, h}`)
- Uloží do `sources/photos/cf_metadata.json`
- Dimenze načte z object metadata (custom HTTP headers při uploadu)

#### Porovnání fotek

Funkce `compare_photos(gdrive_meta: list, cf_meta: dict, config: dict) -> dict`:
- Vrátí `{to_process: list[str], to_delete: list[str]}`
- `to_process`: fotky nové na GDrive, nebo s novějším `last_modified`, nebo chybí některá velikostní varianta/formát na CF
- `to_delete`: fotky na CF, jejichž zdrojová fotka už není na GDrive

#### Zpracování fotky

Funkce `process_photo(gdrive_entry: dict, config: dict, cf_client, dry_run=False)`:
- Stáhne originál z GDrive API
- Pro každý `sizes` × `formats` záznam:
  - Resize na `max_width` (zachovat poměr stran, Pillow)
  - Encode do formátu s danou kvalitou
  - Pokud `optimalizator: cjpeg`: provolej `cjpeg` přes subprocess
  - Uploadni na CF R2 s key `<base>_<size>.<format>` a custom metadata `w`, `h`
- Aktualizuj CF metadata v paměti

#### Jinja2 picture makro

Soubor `krizky/picture_macro.html` — Jinja2 macro `picture(photo, size, alt="")`:
- Renderuje `<picture>` tag s `<source>` elementy pro každý format (avif, webp)
- Poslední `<img>` fallback pro jpg
- `srcset` generuje dle dostupných variant
- Parametr `size` určuje, která varianta se použije jako výchozí

#### Příkazy

- `krizky fetch photos` — stáhne metadata z GDrive a CF, uloží do `sources/photos/`
- `krizky build photos [--force] [--dry-run]`
  - `--force`: přeskočí detekci změn, zpracuje vše
  - `--dry-run`: vypíše co by se zpracovalo, nestahuje, nenahrává

### Testy (`tests/test_photos.py`)

- `test_compare_photos_new` — nová fotka na GDrive → v `to_process`
- `test_compare_photos_modified` — novější `last_modified` → v `to_process`
- `test_compare_photos_missing_variant` — chybí size varianta na CF → v `to_process`
- `test_compare_photos_delete` — fotka na CF ale ne na GDrive → v `to_delete`
- `test_compare_photos_unchanged` — shodná data → prázdné listy
- Foto processing testy mockovat Pillow a boto3

---

## Fáze 6 — Kompletní build + integrace

### Co implementovat

**`krizky/orchestrator.py`**

Funkce `full_build(config: dict, force=False, dry_run=False)`:
1. Fetch GDrive metadata, fetch CF metadata
2. Fetch Google Sheets + Docs
3. `compare_photos(...)` → změny fotek
4. `git diff` na sources/ → detekce změn zdrojů (subprocess, porovnej hash nebo mtime)
5. Pokud `force` nebo žádné změny nejsou → resp. rebuild vše / exit
6. Pokud změny fotek → `build_photos(...)`
7. Pokud změny zdrojů → spusť transform skripty → `build_site(...)`

#### `krizky build` příkaz

Plně implementován dle logiky výše.

#### Integrace sitemap + robots (volitelné — viz PLAN.md "Nedodelky")

Pokud bude čas: generovat `sitemap.xml` a `robots.txt` jako součást `build_site`.

### Integrační testy (`tests/test_integration.py`)

- Použít fixture s kompletní adresářovou strukturou (tmpdir)
- `test_full_build_site_only` — spustit `krizky build site` end-to-end s ukázkovou DB a šablonami
- Ověřit, že výstupní HTML soubory existují a obsahují správná data

---

## Sdílené konvence

- Všechny chyby hlásit přes vlastní výjimky (`ConfigError`, `TransformError`, `FetchError`, `BuildError`)
- CLI výstup: `click.echo` s barvami (`click.style`) — zelená OK, červená ERROR
- Logování: `logging` modul (ne print mimo CLI vrstvu)
- Type hints všude
- Žádné globální proměnné; konfigurace se předává explicitně jako `dict`
- Existující kód v `utils/` lze importovat a využít — zejména `slugify`, `PhotoManager`
