# krizky

Univerzální generátor statických webů z Google Sheets, Google Docs a fotek na Google Drive.

Data se stahují z veřejně sdílených Google dokumentů, transformují bash skripty, ukládají do SQLite a renderují přes Jinja2 šablony. Výstupem jsou statické HTML stránky.

## Instalace

Projekt vyžaduje Python 3.12+ a [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Nový projekt

```bash
uv run krizky init            # inicializuje projekt v aktuálním adresáři
uv run krizky init ./muj-web  # nebo v konkrétním adresáři
```

Příkaz vytvoří:
- `config.yaml` — konfigurační soubor s komentáři
- `.env.example` — šablona pro citlivé hodnoty
- `templates/`, `assets/`, `transforms/` — pracovní adresáře

## Konfigurace

Celá konfigurace je v jednom souboru `config.yaml`. Skládá se ze dvou sekcí: `sources` (zdroje dat) a `site` (generování webu).

### Citlivé hodnoty (ENV proměnné)

Citlivé hodnoty (API klíče, tokeny) se do `config.yaml` **nepíší přímo**. Místo hodnoty se uvede název ENV proměnné s prefixem `$`:

```yaml
account_key: $GDRIVE_ACCOUNT_KEY
account_id: $CF_ACCOUNT_ID
```

Při načítání konfigurace se proměnné automaticky substituují z prostředí nebo ze souboru `.env`.

**Soubor `.env`** (nikdy necommitovat, přidejte do `.gitignore`):

```bash
cp .env.example .env
# vyplňte hodnoty v .env
```

V CI/CD (GitHub Actions apod.) se proměnné nastavují přímo v prostředí — soubor `.env` není potřeba.

---

## Sekce `sources`

Definuje zdroje dat: tabulky z Google Sheets, dokumenty z Google Docs a fotografie z Google Drive.

```yaml
sources:
    output: ./sources      # kam se ukládají stažená data (dát do .gitignore)
    database: data.db      # název SQLite databáze (relativně k output)
```

### `sources.tables`

Každý klíč odpovídá jedné tabulce v Google Sheets a jedné tabulce v SQLite databázi.

```yaml
sources:
    tables:
        data:
            id: "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"     # ID dokumentu z URL
            gid: "0"                                               # ID listu (gid= v URL)
            skip_rows: 3                                           # přeskočit N úvodních řádků (volitelné, výchozí: 0)
            main: true                                             # PRÁVĚ JEDNA tabulka musí být označena jako hlavní
            transform: ./transforms/data.sh                        # transform skript (volitelné)

        snippets:
            id: "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"
            gid: "123456"
            key: key                                               # sloupec, jehož hodnoty se stanou klíči slovníku v šabloně
            transform: ./transforms/snippets.sh
```

**Povinná pravidla:**
- Právě jedna tabulka musí mít `main: true`. Tato tabulka tvoří hlavní dataset pro generování stránek.
- Pokud je uveden `transform`, musí skript existovat na disku (ověří `krizky validate`).

**Jak najít `id` a `gid`:**
URL Google Sheets vypadá takto:
```
https://docs.google.com/spreadsheets/d/<ID>/edit#gid=<GID>
```

### `sources.docs`

Dokumenty z Google Docs. Každý klíč je dostupný v šablonách jako `{{ docs.<klíč> }}`.

```yaml
sources:
    docs:
        uvod:
            id: "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"  # ID dokumentu z URL
            transform: ./transforms/uvod.sh   # povinné — konverze DOCX → Markdown
            output: uvod.md                   # povinné — název výstupního souboru
```

**Oba atributy `transform` i `output` jsou pro záznamy v `docs` povinné.**

### `sources.photos`

Fotografie z Google Drive s výstupem do Cloudflare R2.

```yaml
sources:
    photos:
        base_url: https://photos.example.com   # základ URL pro generování odkazů v šablonách
        source:
            type: gdrive
            folder_id: YOUR_GDRIVE_FOLDER_ID
            account_key: $GDRIVE_ACCOUNT_KEY   # cesta k JSON klíči service accountu
            metadata: ./sources/photos/gdrive_metadata.json
        destination:
            type: cloudflare
            bucket: my-bucket
            account_id: $CF_ACCOUNT_ID
            access_key_id: $CF_ACCESS_KEY_ID
            secret_access_key: $CF_SECRET_ACCESS_KEY
            metadata: ./sources/photos/cf_metadata.json
        formats:
            - format: avif
              mime: image/avif
              quality: 60
            - format: webp
              mime: image/webp
              quality: 80
            - format: jpg
              mime: image/jpeg
              optimalizator: cjpeg   # volitelný post-procesor
              quality: 80
        sizes:
            - name: micro
              max_width: 150
              quality:          # přetíží výchozí kvalitu formátu pro tuto velikost
                jpg: 82
                webp: 72
                avif: 52
            - name: thumb
              max_width: 330
            - name: small
              max_width: 680
            - name: medium
              max_width: 960
            - name: big
              max_width: 1600
```

**Požadované ENV proměnné pro fotky:**

| Proměnná | Popis |
|---|---|
| `GDRIVE_ACCOUNT_KEY` | Cesta k JSON souboru service accountu pro Google Drive |
| `CF_ACCOUNT_ID` | Cloudflare Account ID |
| `CF_ACCESS_KEY_ID` | Cloudflare R2 Access Key ID |
| `CF_SECRET_ACCESS_KEY` | Cloudflare R2 Secret Access Key |

---

## Sekce `site`

Definuje, jak se mají vygenerovat výsledné HTML stránky.

```yaml
site:
    base_url: https://example.com
    assets: ./assets       # adresář se statickými soubory (CSS, JS, …); zkopíruje se do output
    output: ./docs/        # výstupní adresář pro HTML stránky
    paginate_by: 10        # globální stránkování (záznamy na stránku); 0 = vypnuto
    order_by: rowid        # sloupec pro řazení záznamů
    ordering: desc         # směr řazení: asc nebo desc
    templates: ./templates # adresář s Jinja2 šablonami
```

### `site.pages`

Každý klíč definuje jednu nebo více generovaných stránek.

#### Jednoduchá stránka

```yaml
site:
    pages:
        homepage:
            query:
                limit: 10          # limit záznamů
                condition: "typ = 'kriz'"  # volitelná WHERE podmínka
            path: /index.html
            template: index.html
```

V šabloně je dostupná proměnná `{{ filtered }}` se záznamy dle query. Bez `query` obsahuje celý hlavní dataset.

#### Stránka pro každý záznam (detail)

```yaml
        detail:
            detail: true
            path: "/<slug>.html"   # placeholder odpovídá sloupci v DB
            template: detail.html
```

Pro každý záznam z hlavního datasetu se vygeneruje samostatná stránka. V šabloně je navíc dostupná proměnná `{{ record }}` s aktuálním záznamem.

#### Automaticky generované kategorie

```yaml
        kategorie:
            category: typ          # sloupec s hodnotou kategorie
            path: "/<typ_slug>.html"  # placeholder odpovídá sloupci se slugem
            template: kategorie.html
```

Pro každou unikátní non-prázdnou hodnotu sloupce `typ` se vygeneruje samostatná stránka. V šabloně je navíc `{{ category }}` s aktuální hodnotou kategorie.

#### Kategorie z JSON listu (štítky)

```yaml
        stitky:
            category: stitky       # sloupec obsahuje JSON list: ["příroda", "kámen"]
            many: true             # nutné explicitně uvést
            path: "/<stitky_slug>.html"  # stitky_slug je JSON objekt {"příroda": "priroda", …}
            template: stitky.html
```

#### Stránkování

Globální `paginate_by` v sekci `site` se aplikuje na všechny stránky. Přetížit lze na úrovni konkrétní stránky:

```yaml
        all:
            paginate: true
            paginate_by: 20        # přetíží globální hodnotu
            path: /mista.html
            template: mista.html
```

Pojmenování souborů při stránkování:
- 1. strana: `mista.html`
- 2. strana: `mista-2.html`
- 3. strana: `mista-3.html`

---

## Kontext Jinja2 šablon

Ve všech šablonách jsou dostupné tyto proměnné:

| Proměnná | Obsah |
|---|---|
| `{{ filtered }}` | Záznamy z hlavního datasetu, případně filtrované dle `query` |
| `{{ tables.X }}` | Kompletní data tabulky `X`; pokud má tabulka `key`, jde o slovník |
| `{{ docs.X }}` | Obsah dokumentu `X` jako Markdown string |

Na stránkovaných stránkách navíc:

| Proměnná | Obsah |
|---|---|
| `{{ page }}` | Číslo aktuální stránky (1-indexed) |
| `{{ total_pages }}` | Celkový počet stránek |
| `{{ has_prev }}` | `true` pokud existuje předchozí stránka |
| `{{ has_next }}` | `true` pokud existuje následující stránka |
| `{{ prev_url }}` | Cesta k předchozí stránce (nebo `None`) |
| `{{ next_url }}` | Cesta k následující stránce (nebo `None`) |

Na stránkách kategorií/štítků navíc: `{{ category }}` — aktuální hodnota kategorie.

Na detail stránkách navíc: `{{ record }}` — single objekt aktuálního záznamu.

---

## Transform skripty

Transform skripty jsou bash skripty, které přijímají poziční parametry:

| Parametr | Obsah |
|---|---|
| `$1` | Cesta ke zdrojovému souboru (CSV nebo DOCX) |
| `$2` | Cesta k SQLite databázi |
| `$3` | Název tabulky v DB |
| `$4` | Výstupní cesta (pro `docs`: plná cesta k výstupnímu souboru) |

Skripty pro `tables` využívají `$1`, `$2`, `$3`. Skripty pro `docs` využívají `$1` a `$4`.

Ukázka skriptu pro tabulku (`transforms/data.sh`):

```bash
#!/usr/bin/env bash
set -euo pipefail

sqlite-utils insert "$2" "$3" "$1" --csv --truncate

# Přejmenování sloupců
sqlite-utils transform "$2" "$3" --rename "Název" "nazev"

# Smazání nepublikovaných záznamů
sqlite-utils "$2" "DELETE FROM $3 WHERE stav = 'FALSE'"
sqlite-utils transform "$2" "$3" --drop "stav"
```

---

## CLI

```
krizky [--config <path>] <příkaz>
```

Globální flag `--config` (výchozí: `config.yaml`) lze použít u všech příkazů.

| Příkaz | Popis |
|---|---|
| `krizky validate` | Ověří konfigurační soubor |
| `krizky init [DIR]` | Vytvoří kostru nového projektu |
| `krizky fetch sources [--transform]` | Stáhne tabulky a dokumenty; s `--transform` spustí i transform skripty |
| `krizky fetch photos` | Stáhne metadata fotek z Google Drive a Cloudflare |
| `krizky build` | Kompletní build (fotky + web) |
| `krizky build site [--force] [--dry-run]` | Pouze HTML stránky (použije existující DB) |
| `krizky build photos [--force] [--dry-run]` | Pouze zpracování a upload fotek |

---

## Adresářová struktura projektu

```
config.yaml          # konfigurace
.env                 # citlivé hodnoty (necommitovat)
.env.example         # šablona pro .env (commitovat)
templates/           # Jinja2 šablony
assets/              # statické soubory (CSS, JS, …)
transforms/          # bash transform skripty
sources/             # generováno při fetchi (dát do .gitignore)
  data.db
  tables/
    <name>/
      source/<name>.csv
      transformed/
  docs/
    <name>/
      source/<name>.docx
      transformed/<name>.md
  photos/
    gdrive_metadata.json
    cf_metadata.json
docs/                # výstupní HTML stránky (output z config.yaml)
```

Doporučený `.gitignore`:

```
.env
sources/
docs/
```
