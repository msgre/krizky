# krizky

Univerzální generátor statických webů z Google Sheets, Google Docs a fotek na Google Drive.

Data se stahují z veřejně sdílených Google dokumentů, transformují bash skripty, ukládají do SQLite a renderují přes Jinja2 šablony. Výstupem jsou statické HTML stránky.

## Instalace

### Systémové závislosti

- **[pandoc](https://pandoc.org/)** — konverze Google Docs (DOCX → Markdown) v transform skriptech
- **[cjpeg](https://www.ijg.org/)** — optimalizace JPEG fotek

```bash
# macOS
brew install pandoc jpeg
```

### Python

Projekt vyžaduje Python 3.12+ a [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

### Testy

```bash
uv run pytest
```

## Nový projekt

```bash
uv run krizky init            # inicializuje projekt v aktuálním adresáři
uv run krizky init ./muj-web  # nebo v konkrétním adresáři
```

Vytvoří `config.yaml`, `.env.example` a adresáře `templates/`, `assets/`, `transforms/`.

## Konfigurace

Celá konfigurace je v `config.yaml`. Skládá se ze dvou sekcí:
- `sources` — zdroje dat (tabulky, dokumenty, fotky)
- `site` — generování webu (šablony, stránky, stránkování)

### Citlivé hodnoty

API klíče a tokeny se do `config.yaml` nepíší přímo. Místo hodnoty se uvede název ENV proměnné s prefixem `$`:

```yaml
account_key: $GDRIVE_ACCOUNT_KEY
account_id: $CF_ACCOUNT_ID
```

Hodnoty se načítají ze souboru `.env` nebo z prostředí (vhodné pro CI/CD).

```bash
cp .env.example .env
# vyplňte hodnoty
```

### Stručný přehled `sources`

```yaml
sources:
    output: ./sources   # kam se ukládají stažená data (gitignore!)
    database: data.db

    tables:
        data:
            id: "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"     # ID z URL
            gid: "0"                                               # ID listu (gid= v URL)
            skip_rows: 3                                           # přeskočit N úvodních řádků (volitelné)
            main: true                                             # právě jedna tabulka musí být hlavní
            transform: ./transforms/data.sh                        # povinné

    docs:
        uvod:
            id: "..."
            transform: ./transforms/uvod.sh   # povinné
            output: uvod.md                   # povinné
```

Podrobný popis zdrojů, transform skriptů a sqlite-utils vzorů: **[docs/sources.md](docs/sources.md)**

### Stručný přehled `site`

```yaml
site:
    title: Název webu                  # povinné; dostupné v šabloně jako {{ site.title }}
    description: Popis webu            # volitelné; {{ site.description }}
    language: cs                       # volitelné; {{ site.language }}
    base_url: https://example.com
    assets: ./assets                   # zdrojový adresář assets (zkopíruje se do output)
    assets_url: /assets                # URL prefix assets v šablonách; {{ build.assets_url }}
    output: ./docs/
    paginate_by: 10
    order_by: rowid
    ordering: desc
    templates: ./templates

    pages:
        homepage:
            query: {limit: 10}
            path: /index.html
            template: index.html
        detail:
            detail: true
            path: "/{{ record.slug }}.html"
            title: "{{ record.nazev }} — Název webu"  # volitelné přetížení title pro tuto stránku
            template: detail.html
        kategorie:
            category: typ
            path: "/{{ category.slug }}.html"
            template: kategorie.html
```

#### Kontext šablon

| Proměnná | Dostupnost | Popis |
|---|---|---|
| `filtered` | vždy | záznamy aktuální stránky |
| `tables.X` | vždy | všechny DB tabulky (list nebo dict dle `key`) |
| `docs.X` | vždy | obsah dokumentů jako string |
| `record` | detail stránka | aktuální záznam |
| `category` | category stránka | hodnota aktuální kategorie |
| `site.title` | vždy | název webu (přetížitelný na úrovni pages) |
| `site.description` | vždy | popis webu |
| `site.language` | vždy | kód jazyka (přetížitelný na úrovni pages) |
| `site.date_format` | vždy | formátovací řetězec pro datum |
| `site.time_format` | vždy | formátovací řetězec pro čas |
| `site.datetime_format` | vždy | formátovací řetězec pro datum a čas |
| `build.last_update` | vždy | `datetime` spuštění buildu |
| `build.assets_url` | vždy | URL prefix pro assets |
| `build.inline_css` | vždy | obsah `assets/css/style.css` (pro inline vložení) |
| `pagination.paginated` | vždy | `True` pokud je stránkování aktivní |
| `pagination.page` | stránkované | číslo aktuální stránky |
| `pagination.total_pages` | stránkované | celkový počet stran |
| `pagination.has_prev` / `has_next` | stránkované | existence sousední stránky |
| `pagination.prev_url` / `next_url` | stránkované | URL sousední stránky nebo `None` |

#### Interpolace v hodnotách `path`, `title`, `language`

Hodnoty v pages configu jsou Jinja2 šablony s přístupem k `record`, `tables` a `category`:

```yaml
path: "/{{ record.slug }}.html"
title: "{{ record.nazev }} — Valašské nebe"
path: "/{{ category.slug }}.html"
title: "{{ tables.typy[record.typ_slug].nazev }} — Web"  # cross-table
```

## Workflow

```bash
# 1. Stáhnutí zdrojů (+ spuštění transform skriptů)
uv run krizky fetch sources --transform

# 2. Generování webu
uv run krizky build site

# 3. Nebo oboje najednou
uv run krizky build
```

## CLI

```
krizky [--config <path>] <příkaz>
```

| Příkaz | Popis |
|---|---|
| `krizky validate` | Ověří konfigurační soubor |
| `krizky init [DIR]` | Vytvoří kostru nového projektu |
| `krizky fetch sources [--transform]` | Stáhne tabulky a dokumenty; s `--transform` spustí i transform skripty |
| `krizky fetch photos` | Stáhne metadata fotek z Google Drive a Cloudflare |
| `krizky build` | Kompletní build (fotky + web) |
| `krizky build site [--force] [--dry-run]` | Pouze HTML stránky (použije existující DB) |
| `krizky build photos [--force] [--dry-run]` | Pouze zpracování a upload fotek |

## Adresářová struktura projektu

```
config.yaml          # konfigurace
.env                 # citlivé hodnoty (necommitovat)
.env.example         # šablona pro .env (commitovat)
templates/           # Jinja2 šablony
assets/              # statické soubory (CSS, JS, …)
transforms/          # bash transform skripty
sources/             # generováno při fetchi (gitignore)
  data.db
  tables/<name>/source/<name>.csv
  docs/<name>/source/<name>.docx
docs/                # výstupní HTML (gitignore, nebo naopak pro GitHub Pages)
```

Doporučený `.gitignore`:

```
.env
sources/
docs/
```
