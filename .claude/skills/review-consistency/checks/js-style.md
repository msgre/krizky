# Check: JavaScript style

Cíl: JS napříč pluginy vypadá jako od jednoho autora a je konzistentní se svým Python protějškem.

## Kontext

JS je vždy doplněk konkrétního Python pluginu. Neexistuje sdílený JS core. Native JS (žádný build step, žádný framework). Assety jsou typicky pod `<plugin>/assets/<plugin-name>/*.js`.

**Vazba na Python:** JS často čte konfiguraci vloženou Python stranou (např. `<script type="application/json" id="filter-config">`), reaguje na data-atributy vygenerované šablonami, nebo používá globální objekty vložené `inject_head` hookem (např. `window.krizkyPhotos`). Konzistence názvů mezi Pythonem a JS je zásadní.

## Postup

1. Najdi všechny JS soubory v pluginech (mimo `.venv/` a `node_modules/`):
   ```bash
   find _plugins -name "*.js" -not -path "*/.venv/*" -not -path "*/node_modules/*"
   ```
2. Přečti hlavičku a top-level strukturu každého (typicky do 100 řádků stačí).
3. Projdi checklist.

## Checklist

### Header a wrapping
- [ ] IIFE `(function () { 'use strict'; ...})();` — používá to každý plugin? Nebo někdo modul-globals? Nebo někdo `if (typeof window !== 'undefined')` guard?
- [ ] `'use strict'` uvnitř IIFE — všude?
- [ ] Header komentář: co dělá, jaké data-atributy hostí, jaké elementy hledá. Konzistentní formát?

### Language features
- [ ] `var` / `let` / `const` — konzistentní policy? (Existující kód mixuje — `const` pro top-level konstanty, `let` pro reassign, ale i `var` uvnitř starších funkcí.)
- [ ] Arrow functions vs `function` — kdy? `document.querySelectorAll(...).forEach(function(x) {...})` vs `(x) => {...}`.
- [ ] Template literals vs string concatenation — konzistentní volba?
- [ ] Optional chaining `?.` / nullish coalescing `??` — používá se jednotně?
- [ ] `for...of` vs `forEach` vs `Array.from(...).map` — konzistentně?

### Naming
- [ ] Funkce: camelCase (`setupShare`) — všude?
- [ ] Konstanty: `UPPER_SNAKE` nebo camelCase? (`nativeShare` je camelCase, `paginationWindow` taky.)
- [ ] Data attributes v HTML: `data-share-copy`, `data-filter-value` — kebab-case, plugin-prefixed. Konzistentní pravidlo?
- [ ] CSS třídy managed by JS: `is-copied`, `is-active` — konzistentní modifier styl?
- [ ] Globální objekty: `window.krizky<X>` (např. `window.krizkyPhotos`) — konzistentní namespace prefix?

### DOM APIs
- [ ] `querySelector` vs `getElementById` — konzistentní volba?
- [ ] Event delegace vs per-element listener — kdy?
- [ ] `addEventListener('click', fn)` vs `element.onclick = fn` — jednotné?
- [ ] `dataset.foo` vs `getAttribute('data-foo')` — konzistentní?

### Config injection & bootstrapping
- [ ] Config je čtený z `<script type="application/json" id="X">` (jako `krizky-filters`) — dělají to všichni podobně?
- [ ] Nebo z globálního objektu vloženého do `<head>` (jako `window.krizkyPhotos` u photos)? Kdo použije co a proč?
- [ ] Fail-safe: co dělá plugin, když config chybí? (`filters.js` early-returns tiše — dělají to všichni, nebo někdo hodí chybu do konzole?)
- [ ] Naming klíčů v injected JSON — camelCase (JS konvence) nebo snake_case (Python konvence)? Konzistentní?

### Vazba Python ↔ JS
- [ ] Klíče v injected configu odpovídají Python config klíčům, nebo se transformují? Konzistentní pravidlo?
- [ ] Data-atributy generuje Jinja šablona — jméno se shoduje s tím, co JS čte? (`data-share-url` v šabloně → `dataset.shareUrl` v JS.)
- [ ] Prefix atributů (`data-<plugin>-*`) — konzistentně?

### Error handling
- [ ] `try / catch` kolem `JSON.parse` — všude, kde parsuje uživatelské/injected data?
- [ ] Silent fail vs `console.warn` — konzistentní volba?
- [ ] Neexistující DOM elementy — early return vs. skip vs. warn?

### Progressive enhancement
- [ ] Fallback pro chybějící features (Web Share API, Clipboard API) — všechny pluginy mají fallback path?
- [ ] Nezávislost na JS (základní funkčnost bez JS) — respektováno konzistentně?

### Formátování
- [ ] Odsazení: 2 mezery vs 4 — konzistentní?
- [ ] Uvozovky: `'single'` vs `"double"` — sjednocené?
- [ ] Trailing semicolons — všude nebo nikde?
- [ ] Linter/formatter (prettier, eslint) — nakonfigurovaný?

## Zvláštní pozornost

- **Sémantický rozjezd napříč pluginy:** dva pluginy používají stejný data-atribut (`data-active`, `data-toggle`) s jinou sémantikou → potenciální kolize v uživatelově webu → blocker.
- **Globální namespace polluce:** plugin exportuje na `window` něco bez `krizky` prefixu → recommended.
