# 2026-08-14-01 — Plugin krizky-share + `absolute_url` v core

## Cíle

1. Přidat do krizky core drobnou infrastrukturu pro absolutní URL: hodnotu `site.base_url` v template kontextu a Jinja2 global `absolute_url(path)`. Znovupoužitelné mimo tento plugin (RSS, hreflang, JSON-LD u jiných zdrojů).
2. Nový plugin `krizky-share` — meta tagy pro sociální sítě (Open Graph, Twitter Cards), Schema.org strukturovaná data a sdílecí widget (Facebook, WhatsApp, Pinterest, X/Twitter + Kopírovat odkaz).

## Krok 1 — prep commit v core

**Změněné soubory:**
- `krizky/site.py` — přidána funkce `_make_absolute_url(base_url)` (factory pro closure), registrace jako Jinja2 global v `render_site` před `prepare_jinja2_environment` hookem. Do `base_ctx["site"]` přidán klíč `"base_url"` (normalizovaný — bez trailing slashe).
- `README.md` — doplněno v tabulce "Kontext šablon".
- `tests/test_site.py` — 7 nových testů pro `absolute_url`.

**Sémantika `absolute_url(path)`:**
- Absolutní URL (`http://`, `https://`, `//`) prochází beze změny.
- Relativní path se spojí s `site.base_url` (single `/` separator, tolerance na chybějící leading slash).
- Prázdný path → jen `base_url`.
- Prázdný `base_url` (dev/preview) → path se vrátí jak je (fallback).

Reason pro registraci před `prepare_jinja2_environment` hookem: plugin může helper potřebovat už při setupu (např. rozhodnout, jestli něco injektovat). Base URL čte z configu, ne z `base_ctx`, takže na inicializační pořadí `_generate` nespoléhá.

## Krok 2 — plugin krizky-share

**Struktura** (shodná s krizky-photos / krizky-filters):

```
_plugins/krizky-share/
├── PLAN.md, README.md, pyproject.toml
├── krizky_share/
│   ├── plugin.py         — 4 hooky
│   ├── networks.py       — URL buildery + resolve_networks
│   ├── templates/_share.html
│   └── assets/krizky-share/{icons.svg, share.css, share.js}
└── tests/{test_networks.py, test_plugin.py, test_macros.py}
```

### Hooky

| Hook | Vypíše |
|---|---|
| `prepare_jinja2_environment` | plugin templates do loaderu; Jinja2 global `share_links(url, title, image)` |
| `inject_head` | `og:site_name`, `og:locale`, `twitter:card=summary_large_image`, `twitter:site` (pokud v configu), default `og:image` (absolutizovaný), `<link>` na share.css |
| `inject_body_end` | inline SVG sprite + `<script src="/krizky-share/share.js" defer>` |
| `after_page_written` | zkopíruje share.css a share.js do `output/krizky-share/` (jednou per build) |

### Explicit přes makra (per stránka)

Šablona projektu volá 3 makra z `_share.html`:
- `share_meta(url, title, description, image, type)` — per-page `og:type/url/title/description/image`, `twitter:*` mirror, `<link rel="canonical">`.
- `share_schema_place(type, name, description, latitude, longitude, image, url)` — JSON-LD Schema.org (`geo` blok se generuje automaticky když jsou obě souřadnice).
- `share_buttons(url, title, image, label)` — HTML widget (desktop řada + mobil `<details>` dropdown).

### Sítě a URL

- Facebook, WhatsApp, Pinterest, X/Twitter.
- URL šablony v `networks.py::NETWORKS`. `build_share_link()` percent-encoduje URL/title/image.
- **Pinterest bez `image` → `build_share_link` vrací `None`**, makro tlačítko silently skipne.
- Konfig `site.share.networks: [twitter, facebook]` řídí pořadí a filtr; default = všechny.

### Ikony

SVG sprite se 6 symboly (`i-share-toggle`, `-facebook`, `-whatsapp`, `-pinterest`, `-twitter`, `-copy`). Prvních pět je vytažených z projektového design manuálu (`/workspace/design_manual.html` — v JSON-escaped formátu, extrahováno Python skriptem). Copy ikona (clipboard) je nová, ve stejném stylu (`currentColor` stroke, viewBox 24×24, stroke-width 1.4). Prefix `i-share-*` aby ID nekolidovala s uživatelovými ikonami (`i-mark`, `i-kategorie-*`, …).

### Widget — desktop vs. mobil

Podle screenshotu `socky.png` + tokenů z `tmp/style.css`:
- **Desktop** (`@media min-width: 640px`): řada 36×36 kruhových ikon (`border-radius:100px`, hairline border, muted ikona → ink na hover).
- **Mobil**: jedno pill tlačítko „Sdílet" (ikona + text). Rozbaluje dropdown 220px, radius 4px, hairline separátory mezi položkami, shadow `0 12px 28px rgba(...)`. Použit `<details>` + `<summary>` — funguje **bez JS**.
- S JS: klik na „Sdílet" na mobilu volá `navigator.share()` (pokud API existuje); `<details>` toggle se přeskočí.
- Klik na položku dropdownu (Facebook, …) otevře share URL v novém tabu a zavře menu.
- „Kopírovat odkaz" (5. položka mobilního dropdownu) — `navigator.clipboard.writeText()` s fallbackem na `document.execCommand("copy")`. Vizuální feedback: text se změní na „Zkopírováno" na 1.6 sekundy.
- Escape zavře otevřený dropdown; click outside taky.

### Kritika návrhu HTML z předchozí zprávy

Původní HTML (Framer/OM export) mělo problémy: inline styly, `data-om-id`, `<a>` bez `href`, chybějící `aria-label`, `<a>` místo `<button>` pro native share. Přepracováno:
- Inline styly → třídy v CSS.
- `data-om-id` odstraněny.
- Všechna tlačítka mají `href` (bez JS funguje) a `aria-label` (screen readery).
- „Sdílet" toggle přes `<summary>` v `<details>` — správný semantic + no-JS fallback.
- „Kopírovat" je `<button type="button">`, ne `<a>`.
- Ikony v `<svg aria-hidden="true" focusable="false">`.

## Konfigurace

```yaml
site:
  base_url: https://valasskenebe.cz    # nezbytné pro absolutní URL
  language: cs-CZ                      # BCP 47 (existující core klíč); og:locale se odvodí (cs_CZ)
  share:
    twitter_site: '@valasskenebe'
    default_image: /assets/og.jpg
    networks: [facebook, whatsapp, pinterest, twitter]
```

Vše volitelné kromě `base_url` (bez ní `absolute_url` degraduje na relative path).

**`og:locale` bez samostatného configu**: BCP 47 (`site.language: cs-CZ`) → OG (`cs_CZ`) automatickou konverzí pomlčky za podtržítko. Uživatel jazyk konfiguruje na jednom místě; plugin neduplikuje.

## Výsledky testů

```
tests/                              95 passed  (core, +7 pro absolute_url)
_plugins/krizky-photos/tests/       60 passed
_plugins/krizky-filters/tests/      45 passed
_plugins/krizky-share/tests/        35 passed  (nový plugin)
                              ─────────────
                                   235 passed
```

## Změněné/vytvořené soubory

**Core (prep commit):**
- `krizky/site.py`, `tests/test_site.py`, `README.md`

**Nový plugin `krizky-share`:**
- `_plugins/krizky-share/pyproject.toml`, `README.md`, `PLAN.md`
- `_plugins/krizky-share/krizky_share/__init__.py`, `plugin.py`, `networks.py`
- `_plugins/krizky-share/krizky_share/templates/_share.html`
- `_plugins/krizky-share/krizky_share/assets/krizky-share/{icons.svg, share.css, share.js}`
- `_plugins/krizky-share/tests/{__init__.py, test_networks.py, test_plugin.py, test_macros.py}`

**Log + přehled:**
- `work/2026-08-14-01-share-plugin.md`
- `work/OVERVIEW.md` — nový řádek

## Co si musí projekt uživatele udělat

Aplikováno na projekt Valašské nebe (`temp/`) — pro dokumentaci pluginu obecně platí to samé:

1. Do `config.yaml` doplnit `site.base_url` (nutné) a volitelně `site.share:` (twitter_site, default_image, locale, networks).
2. Do `base.html` přidat `{% block extra_meta %}{% endblock %}` do `<head>` (přidáno za `{{ head_injections | safe }}`).
3. Do `detail.html` a `_category_list.html` (parent kategorie/obdobi/stitek/vsechna_mista) importovat makra ze `_share.html`, přidat blok `extra_meta` a vložit `share_buttons` do content.
4. Homepage (`index.html`) dostal jen `share_meta` bez tlačítek (uživatel netlačil na explicit share widget).

### Změněné šablony v temp/templates/

- `base.html` — nový `{% block extra_meta %}` v `<head>`.
- `detail.html` — import maker, top-level `set` pro `imgs`, `page_url`, `og_image` (sdíleno mezi bloky); extra_meta s `share_meta(article)` + `share_schema_place(LandmarksOrHistoricalBuilding)`; `share_buttons` mezi detail-grid a příběhem.
- `_category_list.html` — top-level `page_url` (kategorie/obdobi/stitek dostávají `absolute_url('/' ~ category.slug ~ '.html')`, vsechna_mista `absolute_url(page_urls[page_name])` — canonical bez paginačního suffixu, sdílí se první stránka tematické skupiny); extra_meta se `share_meta`; `share_buttons` na konci wrap.
- `index.html` — jen `share_meta` v extra_meta.
- `config.yaml` — přidán nový `site.share:` blok jako reference (twitter_site, default_image, locale, networks).

### Sanity render všech 6 šablon (index, detail, kategorie, vsechna_mista, obdobi, stitek) přes izolovaný Jinja2 env prošel bez chyb. Ověřené:
- `og:type=article` pro detail, `og:type=website` pro ostatní.
- `og:url` je absolutní URL správně sestavená z `site.base_url`.
- Detail obsahuje JSON-LD `LandmarksOrHistoricalBuilding` s `name`, `geo`, `url`.
- `share_buttons` renderuje `.share-desktop` + `.share-mobile` s data atributy.

## Technické poznámky

- **Cross-plugin coupling**: share plugin nemá žádnou Python závislost na krizky-photos ani krizky-filters. Sprite se injektuje **na každou stránku** (bez detekce, jestli je na ní widget vůbec použit) — je to malé (2.6 kB) a jednodušší než hook API pro "detekci použití". Stejně tak CSS/JS.
- **Autoescape a `head_injections`**: šablona projektu musí použít `{{ head_injections | safe }}` (stejný pattern jako filters plugin, žádná změna) — jinak by se HTML z hooků escapovalo.
- **Ikony přes JSON-encoded string v manuálu**: SVG obsah je v souboru zakódován (escaped `\"`, `\/`, `/`). Extrakce v jednoduchém Python skriptu s třemi replace pravidly. Pokud manuál dostane update s dalšími sítěmi, stejný postup je opakovatelný.
- **Design manuál "standalone"** (`Redesign filtrovací dimenze.zip` / `/workspace/tmp/design_manual/`) social ikony **neobsahuje** — je to starší verze. Nová `/workspace/design_manual.html` je má. Extrakce tedy sáhla po novější verzi.
