# Guidelines: cross-language consistency

Pravidla pro věci, které přesahují hranici Python ↔ JavaScript. Kratší než language-specific soubory, ale nepřehlédnout.

## Config klíče: Python ↔ JS

**Pravidlo:** Python config klíč `snake_case` → JS klíč `camelCase`. **1:1 mapping, žádné zkracování.**

```python
# Python — čte z YAML
"paginationWindow": site_cfg.get("pagination_window", 2),
"paginationBoundary": site_cfg.get("pagination_boundary", 1),
"gridSelector": "[data-filter-grid]",
```

```javascript
// JS — čte z injected configu
const paginationWindow = config.paginationWindow ?? 2;
const paginationBoundary = config.paginationBoundary ?? 1;
const gridSelector = config.gridSelector;
```

**Anti-vzor:**
- `pagination_window` (Python) → `window` (JS) — zkrácení + kolize s built-in `window` globálem.
- `foo_bar_baz` → `foo` — ztráta informace.

**Kdy se přepiš:**
- Když měníš config schéma → přepiš oboje ve stejném commitu.
- Deprecation: pokud plugin je ve verzované knihovně a klíč je veřejný, přidej accept-both pattern (`config.paginationWindow ?? config.window ?? 2`) + warning + odstranění v příští breaking verzi. Pro ne-veřejné internal keys stačí clean cut.

## Data attributes v HTML ↔ JS

Prefix per plugin (viz `guidelines/javascript.md`). Konzistentně napříč šablonou a JS.

- Šablona: `data-<plugin>-<action>` (kebab-case) — `data-share-copy`, `data-filter-value`.
- JS: `element.dataset.<action>` (camelCase automaticky) — `element.dataset.shareCopy`, `element.dataset.filterValue`.

**Kolize:** dva pluginy nesmí sdílet stejný atribut se stejnou sémantikou (potenciální stepping-on-toes v uživatelově HTML). Kolize se stejnou sémantikou (např. oba čtou `data-slug`) → refactor jednoho z nich na plugin-prefixed.

## Cross-plugin data sharing

**Anti-pattern:** plugin čte config sekci jiného pluginu (např. map a filters čtou `sources.photos.base_url`). Vzniká tím vazba na konkrétní plugin.

**Preferované řešení:** hodnotu má plugin ve vlastním configu, i za cenu, že ji uživatel zadá dvakrát:
```yaml
site:
  map:
    thumbnail_base_url: https://photos.example.com
```

Obecné řešení by byl hook pro sdílená data mezi pluginy. Návrh `provide_shared_context` je v `reports/2026-08-17-2013/proposals/hook-changes.md`, zatím se neimplementuje.

## Nemíchat jazyky v odpovědi user-facing

- Log messages, docstringy, code comments → **angličtina**.
- README, CLAUDE.md, PLAN.md, work/*.md → **čeština**.
- Commit messages → **čeština** (`CLAUDE.md` › Git).
- Config klíče (v YAML) → **angličtina** (matching konvence: `sources`, `pages`, `path`, `template`, ...).
- Jinja templates: text v šabloně → **čeština** (user-facing), variable names / macro parameters → **angličtina**.

## Naming across the stack

Pro entitu, která existuje v Python, YAML, JS i HTML — použij konzistentní kořen:

| Vrstva | Forma |
|---|---|
| Python | `snake_case` (`base_name`, `focal_point`) |
| Config YAML | `snake_case` (`base_url`, `folder_id`) |
| JS | `camelCase` (`baseName`, `focalPoint`) |
| HTML data-attr | `kebab-case` (`data-base-name`, `data-focal-point`) |

**Anti-pattern:** stejná věc jménem `photo_id` v Pythonu, `photoBaseName` v JS, `data-photo` v HTML. Zvolit jedno sémantické jméno a napříč stack transformovat jen dle konvence dané vrstvy.

## Escape na hranicích

- **HTML rendering z Pythonu:** vždy Jinja auto-escape, nebo explicitní `html.escape(value, quote=True)`. **Ne** manuální `.replace("&", "&amp;")`.
- **JSON rendering z Pythonu do JS:** `json.dumps(data, ensure_ascii=False)` — musí produkovat validní JSON i pro non-ASCII texty (české znaky). ensure_ascii=True by escape-oval, což je zbytečné plýtvání bytes.
- **JS insertion do DOM:** `textContent` pro plain text, nikdy `innerHTML` pro user data.

## Změna, která se týká Pythonu i JS

1. Starý název grepni v **obou jazycích** i v šablonách: nesmí nic zůstat.
2. Aktualizuj README (YAML příklady, mapovací tabulky) a `docs/*.md`.
3. Obě strany změň v jednom commitu, rozdělená změna by mezi commity rozbila build.
4. `scripts/verify` musí skončit s exit 0.
