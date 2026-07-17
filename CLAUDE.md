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
| `photos(row_number)` | funkce; vrátí `{primary, additional, all, count, has_photos}` — photo dict pro `<picture>` makro; dostupné jen pokud je v configu sekce `sources.photos` |
| `filtered` | záznamy aktuální stránky |
| `record` | aktuální záznam (pouze detail stránky) |
| `category` | hodnota aktuální kategorie jako string (pouze category stránky) |

## Fotky v šablonách

Dostupné jen pokud je v configu sekce `sources.photos`. Metadata se načítají z `sources/photos/cf_metadata.json` a `sources/photos/focal_points.json`.

### `photos(row_number)` → photo container

```jinja2
{% set imgs = photos(record.row_number) %}
{{ imgs.has_photos }}    {# bool #}
{{ imgs.count }}         {# celkový počet fotek pro tento záznam #}
{{ imgs.primary }}       {# photo dict nebo None #}
{{ imgs.additional }}    {# list photo dictů (007-1, 007-2, …) #}
{{ imgs.all }}           {# [primary] + additional #}
```

### Struktura photo dictu

```
photo.base_name      → "007" nebo "007-1"
photo.src            → "https://cdn.example.com/007_big.jpg"   (největší JPEG varianta)
photo.srcset         → "https://.../007_micro.jpg 150w, ..., 007_big.jpg 1600w"
photo.sources        → [{mime: "image/avif", srcset: "..."}, {mime: "image/webp", srcset: "..."}]
photo.variants       → {"micro": {url, w, h}, "thumb": {url, w, h}, "big": {url, w, h}, …}
photo.width          → int (šířka největší varianty)
photo.height         → int (výška největší varianty)
photo.focal_point    → "50% 46%" nebo None  (CSS hodnota pro object-position)
```

### `_picture.html` — built-in makro

```jinja2
{% from "_picture.html" import picture %}

{# základní použití #}
{{ picture(imgs.primary, sizes="(max-width:520px) 100vw, 330px", alt=record.nazev) }}

{# s výběrem velikostní varianty pro src hint (lepší LCP) #}
{{ picture(imgs.primary, sizes="650px", alt=record.nazev, size="medium", lazy=False) }}

{# galerie #}
{% for photo in imgs.all %}
  {{ picture(photo, sizes="76px", alt=record.nazev, size="micro") }}
{% endfor %}
```

Parametry makra:

| Parametr | Výchozí | Popis |
|---|---|---|
| `photo` | — | photo dict z `photos(row_number)` |
| `sizes` | `"100vw"` | CSS `sizes` atribut — přizpůsob každému kontextu |
| `alt` | `""` | alt text pro `<img>` |
| `lazy` | `True` | `True` → `loading="lazy"`, `False` → `fetchpriority="high"` (hero) |
| `size` | `None` | název varianty pro `src` + `width`/`height` hint (např. `"thumb"`, `"medium"`) |

Makro generuje `<source>` pro každý non-JPEG formát (AVIF, WebP) + `<img>` s JPEG srcset jako fallback. Pokud je `focal_point` nastaven, přidá `style="object-position:..."`.

### Kde se berou data

| Soubor | Kdo spravuje | Obsah |
|---|---|---|
| `sources/photos/gdrive_metadata.json` | `krizky fetch photos` | seznam fotek na GDrive |
| `sources/photos/cf_metadata.json` | `krizky build photos` | rozměry variant + `_last_modified` |
| `sources/photos/focal_points.json` | ručně | `{"007": "50% 46%", …}` |

---

## JSON export

Každá page může volitelně generovat JSON vedle HTML. Přidej klíč `json:` do definice stránky:

```yaml
pages:
  vsechna_mista:
    path: /mista.html
    template: mista.html
    json:
      fields: [slug, nazev, latitude, longitude]  # nebo "*" pro vše
      exclude: [interni_pole]                      # volitelný blacklist (lze kombinovat s "*")
      pretty: true                                 # volitelné, default false
```

- Výstup: `<output>/jsons/<stejné jméno jako HTML>.json`
- Simple/category stránky → JSON array všech záznamů (stránkování se ignoruje)
- Detail stránky → jeden JSON objekt per záznam
- Bez klíče `json:` se JSON negeneruje

---

Interpolace v `path`, `title`, `language` config hodnotách a v `site.title`, `site.description` používá Jinja2 syntaxi:
- `"/{{ record.slug }}.html"` — hodnota ze záznamu
- `"/{{ category.slug }}.html"` — slug kategorie
- `"{{ tables.typy[record.typ_slug].nazev }}"` — cross-table lookup
- `"{{ tables.konfig.nazev.hodnota }}"` — v `site.title`/`site.description` dostupné `tables` a `docs`
