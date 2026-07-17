# CLAUDE.md — instrukce pro Claude Code

## Po každé implementační session

Po dokončení implementace (nebo na konci session s uživatelem) **vždy**:

1. **Vytvoř nebo aktualizuj log soubor** ve složce `work/`:
   - Název: `work/YYYY-MM-DD-NN-HESLO.md` (NN = pořadí ten den od 01, HESLO = kebab-case anglické shrnutí)
   - Obsah: co bylo implementováno, které soubory byly vytvořeny/změněny, výsledky testů, technické poznámky
   - Viz existující logy jako vzor: `work/2026-07-06-01-project-setup.md`, `work/2026-07-06-02-fetch-sources.md`

2. **Aktualizuj `work/OVERVIEW.md`** — tabulka "Stav fází":
   - Změň TODO → IN PROGRESS nebo DONE
   - Doplň odkaz na log soubor

3. **Aktualizuj `README.md`** pokud se změnilo veřejné API, konfigurace, nebo konvence šablon.

## Práce na projektu

- Projekt je dokumentován v `work/OVERVIEW.md` a `PLAN.md`
- Kód je v `krizky/` package, testy v `tests/`
- Spouštění testů: `uv run pytest` nebo `python -m pytest`
- Konfigurace se načítá z `config.yaml` (vzorový soubor generuje `krizky init`)

## Konvence šablon (aktuální stav)

Kontext dostupný ve všech Jinja2 šablonách:

| Namespace | Obsah |
|---|---|
| `site.*` | config: `title`, `description`, `language`, `date_format`, `time_format`, `datetime_format`; plus `page_title` a `page_description` (hodnoty z page config nebo fallback na globální) |
| `build.*` | build-time: `last_update` (datetime), `assets_url`, `inline_css` |
| `pagination.*` | `paginated`, `page`, `total_pages`, `has_prev`, `has_next`, `prev_url`, `next_url` |
| `tables.*` | všechny DB tabulky (list nebo keyed dict dle `key`) |
| `docs.*` | obsah dokumentů jako string |
| `page_urls.*` | URL stránek dle jména z configu: `page_urls.vsechna_mista` → `"/vsechna-mista.html"` |
| `page_name` | klíč aktuální stránky z config `pages` (např. `"vsechna_mista"`) |
| `query(name, **params)` | funkce; spustí pojmenovanou SQL query ze sekce `queries:` a vrátí `list[dict]`; výsledky jsou cachované per (name, params) |
| `filtered` | záznamy aktuální stránky |
| `record` | aktuální záznam (pouze detail stránky) |
| `category` | hodnota aktuální kategorie jako string (pouze category stránky) |

Interpolace v `path`, `title`, `language` config hodnotách a v `site.title`, `site.description` používá Jinja2 syntaxi:
- `"/{{ record.slug }}.html"` — hodnota ze záznamu
- `"/{{ category.slug }}.html"` — slug kategorie
- `"{{ tables.typy[record.typ_slug].nazev }}"` — cross-table lookup
- `"{{ tables.konfig.nazev.hodnota }}"` — v `site.title`/`site.description` dostupné `tables` a `docs`
