# Config style guide (návrh)

Odvozeno z revize 2026-08-17. Popisuje konvence použité v core + většině pluginů. Slouží jako vodítko pro budoucí implementace config options.

**Status:** návrh. Sjednocuje existující patterny — nic nevymýšlí. Zvláštní pozornost věnovaná drobným rozjezdům, kde bylo potřeba rozhodnout, co je kanonická forma.

---

## Struktura configu — kam patří plugin sekce

Pravidlo: **globální/build-time věci = top-level klíč. Per-page opt-in = per-page klíč. Kombinace = obě.**

| Kategorie | Umístění | Příklady |
|---|---|---|
| Data zdroje (fotky, tabulky) | `sources.<x>` | `sources.photos`, `sources.tables` |
| Site-wide defaulty + globální plugin config | `site.<x>` | `site.map`, `site.share`, `site.paginate_by` |
| Per-page opt-in a override | `pages.<page>.<x>` | `pages.detail.map: true`, `pages.mista.filters: {...}`, `pages.data.json: {...}` |

**Pravidlo v akci:**
- Plugin, který dělá globální transformaci (photos, share) → globální sekce (`sources.photos`, `site.share`).
- Plugin, který se aktivuje jen na některých stránkách (filters, json) → per-page klíč.
- Plugin s obojím (map — globální styling + per-page opt-in) → oboje.

**Anti-pattern:** míchat pravidla nekonzistentně. Např. `krizky-filters` současně používá per-page `filters:` (správně) a site-level `site.pagination_window`/`site.pagination_boundary` (nekonzistentní se zbytkem plugin scope) — viz `plugin-krizky-filters.md`. Doporučeno přesunout do per-page.

---

## Pojmenování klíčů

- **snake_case.** Vždy. Ekosystém je v tomto konzistentní.
- **Zkratky ne.** Preferuj `pagination_window` před `pag_win`. Kdyby zkratka vznikla, pojmenuj konzistentně (bez duplikace, viz Python↔JS naming níže).
- **Boolean klíče:** `<x>_enabled` se **nepoužívá**. Pattern je "přítomnost sekce = zapnuto". Např. plugin má implicitně `false`, přítomnost `filters:` na stránce = zapnuto.

Konvence pro běžné typy:

| Sémantika | Kanonický klíč | Anti-vzor |
|---|---|---|
| Výstupní adresář | `output` | `output_dir`, `dest`, `dest_dir` |
| Zdrojový adresář | `source` (pokud objekt s víc parametry) nebo `source_dir` | mix |
| URL prefix | `base_url` | `url_base`, `root_url` |
| Formátovací string | `<x>_format` | `<x>_fmt`, `<x>_pattern` |
| Cesta k souboru | `path` | `file`, `filename` |
| Boolean flag | prosté jméno bez `is_`/`has_` prefixu (např. `pretty: true`) | `is_pretty`, `has_pretty` |

---

## Cesty a URL

**Cesty k souborům v configu jsou relativní ke `config.yaml`.** Vyjimka: absolutní cesty (začínající `/` na Unixu nebo drive letterem na Windows) proteknou beze změny.

Resolving se má dít **v pluginu** přes sdílený helper (`krizky.config.resolve_path(path, config_dir)`) — viz `proposals/consolidation-to-core.md` kandidát #3.

**URL v configu:**
- Bez trailing slash. Např. `base_url: https://example.com`, ne `https://example.com/`.
- Když plugin skládá plnou URL, vždy dělá `base_url.rstrip("/") + path`.

---

## Env vars a secrets

Prefix `$` v hodnotě = jméno env var. Načítá se z `.env` nebo procesního environmentu.

**Konvence:**
- Sekce/klíče, které expectují cestu k souboru (např. `account_key: $GDRIVE_ACCOUNT_KEY`), přijmou cestu jako plaintext hodnotu env var. Ne cestu k souboru s klíčem obalenou nějakým prefixem.
- Sekce/klíče se stringem hodnotou (např. `bucket: $CF_BUCKET_NAME`) přijmou string přímo.

**Kde je popsáno:** core `README.md` sekce "Citlivé hodnoty" — každý plugin má na to odkázat, ne opakovat.

---

## Defaulty a "vypnuto"

- Plugin, jehož sekce v configu **chybí** → no-op (žádný warning, žádná chyba).
- Sekce **existuje**, ale je prázdná (`plugin_x:` bez pod-klíčů) → plugin se aktivuje s defaults.
- Klíč **chybí uvnitř sekce** → plugin použije default. Pokud default neexistuje a klíč je povinný → **error** (raise plugin-specific `<X>Error`, ne `KeyError`).

**Kanonický pattern pro čtení:**
```python
plugin_cfg = config.get("sources", {}).get("photos")
if not plugin_cfg:
    return  # plugin no-op
value = plugin_cfg.get("some_key", DEFAULT_VALUE)
```

**Anti-pattern:** `config["sources"]["photos"]["some_key"]` (KeyError na chybějící sekci = brute).

---

## Interpolace v config hodnotách

Jinja2 syntaxe v hodnotách `path`, `title`, `language` na page config. Přístup k `record`, `tables`, `category`. Viz core `README.md` sekce "Interpolace v hodnotách".

- `"/{{ record.slug }}.html"` — detail path
- `"{{ record.nazev }} — Web"` — title
- `"{{ tables.typy[record.typ_slug].nazev }}"` — cross-table lookup

**Nesmí se používat mimo tyto tři klíče** — jinak by musela projít Jinja renderer, což by komplikovalo config parsing.

---

## Python → JavaScript naming

Pluginy s JS assets injektují config do JS (přes `<script type="application/json">` nebo `window.<name>` globál).

**Pravidlo:** Python config klíč `snake_case` → JS konfigurace `camelCase`. **Beze zkracování.** Přesně jedna k jedné.

**Anti-vzor (existuje v `krizky-filters`, viz `plugin-krizky-filters.md`):** `pagination_window` (Python) → `window` (JS). Zkrácení + kolize s built-in `window` globálem.

**Kanonický pattern:**
```python
# Python
"paginationWindow": site_cfg.get("pagination_window", 2),
```
```javascript
// JS
const paginationWindow = config.paginationWindow ?? 2;
```

---

## Cross-plugin data reference

**Nikdy nesahat do configu jiného pluginu** bez formálního API.

Aktuálně **anti-pattern**: map a filters čtou `config["sources"]["photos"]["base_url"]` (viz `plugin-krizky-map.md` a `plugin-krizky-filters.md`).

Pravidla:
1. **První volba:** duplikace v vlastním configu (`map.thumbnail_base_url`). User pain (duplicity), ale žádná coupling.
2. **Druhá volba:** oficiální helper v cizím pluginu (`from krizky_photos import get_photos_base_url(config)`). Pluginy jsou volitelně vázané (extras).
3. **Třetí volba (budoucnost):** sdílený context přes hook `provide_shared_context` (viz `proposals/hook-changes.md`). Ne teď.

---

## Dokumentace configu v plugin READMEs

Každý plugin má sekci `## Konfigurace` v README s:

1. **Kompletní YAML ukázka** — všechny klíče, které plugin čte, i s defaulty.
2. **Tabulka klíčů:** `| Klíč | Typ | Výchozí | Popis |` — reference. Alespoň pro non-trivial klíče.
3. **Env vars** — pokud plugin používá `$VAR`, uvést, které vars čeká a v jakém formátu.

Formát ukázek: yaml codeblock, se stejným odsazením napříč pluginy (2 mezery).

---

## Validace

**Současný stav:** žádný plugin nedělá schema validaci configu. Používá `.get()` s defaulty a doufá.

**Doporučení:** až se objeví reálná bolest z chybného configu (uživatel dostane cryptic error, nebo si toho vůbec nevšimne), přidat do core `krizky.config.validate_plugin_section(schema, section)` helper. Zatím: nedělat nic.

**Anti-vzor:** custom validace v každém pluginu jiná. Když se to začne dít, konsolidovat.

---

## README kostra pro pluginy (doporučená)

```markdown
# krizky-<name>

Jednořádkový popis.

Odstavec: co plugin dělá, jaké hooky používá.

## Instalace

## Konfigurace

## [Nutné úpravy šablon]  — pokud plugin injektuje HTML/assety

## [Použití v šablonách]  — pokud plugin exponuje macra/globals

## [CLI příkazy]  — pokud plugin přidává CLI

## Požadavky

## Licence
```

Pořadí sekcí je závazné. Sekce v `[]` se vynechají, pokud nedávají smysl pro plugin. Nepovinné sekce navíc mohou být přidané mezi.

---

## Otevřené otázky

- **Config schema:** stálý stav "žádná validace". Kdy zavést?
- **Cross-plugin shared context:** kdy z workaroundů udělat oficiální mechanismus?
- **i18n plugin UI textů:** aktuálně vše hardcoded CZ. Kdy zavést mechanismus (config `locale: cs` + plugin dostane překlady)?
- **Config verzování:** až se změní breaking klíč (např. `paginationWindow` v filters), potřebujeme mechanismus deprecation warnings?
