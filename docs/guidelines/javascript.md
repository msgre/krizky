# Guidelines: JavaScript

Vanilla JS, žádný framework (React/Angular/Vue/Svelte jsou explicitně vyloučené). Kvalitní third-party balíčky OK (viz "Package selection" níže). Cílový browser: moderní evergreen (Chromium/Firefox/Safari poslední 2 roky, Firefox ESR OK).

## ESLint a Prettier

Pluginy s JS mají `eslint.config.mjs` (flat config ESLint 9+) a `.prettierrc.json`. Oba soubory jsou ve všech pluginech shodné byte po bytu a `scripts/verify` je vynucuje (ESLint, Prettier, `node --test` pro `tests/js/*.test.mjs`). Nový plugin s JS je zkopíruje z existujícího pluginu. Změna konfigurace se dělá ve všech pluginech najednou.

## JS quality — canonical patterns

### Modul-level struktura

Existující konvence (map/share/filters): IIFE + `'use strict'`. **Držet.**

```javascript
(function () {
  'use strict';

  // ── Bootstrap ─────────────────────────────────────────────────────
  const rootEl = document.querySelector('[data-my-plugin-root]');
  if (!rootEl) return;  // graceful degradation

  // ...
})();
```

- Pokud plugin bude v budoucnu ES module, IIFE odpadne. **Ne migrovat proaktivně** — jen když existuje jiný důvod (např. tree-shaking, sdílení kódu).

### Variables

- **`const` default.** Nemuteš → const.
- **`let`** jen když reassign.
- **`var` nikdy** — ani ve starém kódu, když ho refactoreš.

### Functions

- **Arrow function** pro callbacks (`arr.forEach((x) => ...)`, `addEventListener('click', (e) => ...)`).
- **Function declaration** pro top-level utility (má jméno v stacktrace, jednodušší debug).
- **Method shorthand** v objektech: `{ foo() {} }`, ne `{ foo: function() {} }`.

### Modern ES features

- Optional chaining: `obj?.prop?.method?.()` — bezpečně pro deep access.
- Nullish coalescing: `val ?? default` — pro **jen** null/undefined defaulting (ne `||` — to zachytí i `0`/`""`).
- Spread/rest: `{...a, ...b}`, `[...arr]`, `(...args)`.
- Destructuring: `const { url, title } = data;` — čitelnější.
- Template literals: `` `${x}` `` — preferovat před `+` konkatenací.
- Private class fields: `#priv` — když píšeš class.

### Strings

- Single quotes (`'foo'`) — dle prettier configu.
- Template literals (` `${x}` `) — dle prettier.

### DOM APIs

- `document.querySelector` / `querySelectorAll` — preferuj před `getElementById` (konzistentní).
- `element.dataset.fooBar` — preferuj před `getAttribute('data-foo-bar')` (idiomatic).
- Event listeners: `element.addEventListener('click', handler, { passive: true })` — kde `preventDefault()` nikdy nevoláš, přidej `{ passive: true }` (browser optimalizace scrollu).
- Cleanup listenerů — pluginy typicky mají 1 lifecycle per page load, tak není potřeba. Pokud plugin dynamicky attachne/detachne, cleanup **je** potřeba (memory leak jinak).

### Error handling

- `try { ... } catch (err) { ... }` kolem uživatelských/injected JSON dat (parse) a kolem `navigator.<featuredetection>` volání.
- Silent fail (`return` bez `console.error`) pro missing DOM — plugin je optional enhancement.
- `console.warn` (dovoleno ESLint pravidlem) pro developer-notable problems (např. malformed config JSON).
- **Ne** `alert()`, `confirm()`, `prompt()` — narušuje UX.

### Naming

- camelCase pro funkce, proměnné, class instance properties.
- PascalCase pro classes a constructors.
- UPPER_SNAKE pro modul-level konstanty (`const PAGINATION_WINDOW_DEFAULT = 2;`).
- Boolean funkce/proměnné: `isX`, `hasX`, `canX` (matching Python konvence).

### Data attributes

- Prefix per plugin: `data-<plugin-slug>-*` (e.g. `data-filter-value`, `data-map-config`, `data-share-url`).
- Konzistentní s existujícím kódem — nezavádět nové bez prefixu.
- Camel version v JS: `element.dataset.filterValue` (automatický kebab-to-camel).

## Package selection (Python i JS)

Před přidáním balíčku ověř **všechny** kriteria:

1. **Popularita:** ≥1000 stars na GitHub, NEBO známý autor / organizace (např. Sindre Sorhus, Vercel, T3, PyPA, Microsoft).
2. **Údržba:** poslední release **do 12 měsíců**. Když déle → značka opuštěného projektu, hledej alternativu.
3. **Nedeprecated:** balíček nesmí být označen jako deprecated (npm `deprecated` field, pypi `Development Status :: 7 - Inactive`, dead-project markers v README).
4. **Bez známého CVE bez fixu:** rychlý `npm audit` / `pip-audit` scan.
5. **Licence:** MIT, Apache 2.0, BSD (permissive). GPL/AGPL vyžaduje explicitní schválení uživatele.
6. **Ne "utility":** vyhýbat se micro-balíčkům, které dělají 1 řádek kódu (`is-even`, `left-pad`) — buď je opsat, nebo použít větší balíček s lepším scope.
7. **Bundle size (JS):** pro browser assety balíček by neměl přidat >10KB gzipped bez silného zdůvodnění. Použij bundlephobia.com nebo `npx bundle-phobia <pkg>`.
8. **Tree-shakeable (JS):** balíček exportuje ES modules a nemá top-level side effects.
9. **Žádné katastrofální transitive deps:** rychlý `npm ls <pkg>` / `pipdeptree` — hledat balíčky s 50+ transitive deps (známé warning sign).

Před `uv add` nebo `npm install` ověř body 1–5 a zeptej se uživatele. Body 6–9 uveď jako doplňkovou kontrolu.

**Preferuj stdlib.** Než přidáš 3rd party dep, pokus se to napsat s pomocí stdlib. Rule of thumb: <30 řádků, kde stdlib nabízí building blocks → nepřidávat dep.

## Před commitem

`scripts/verify` musí skončit s exit 0. Když změna mění interakci s DOM, uveď v PR, že je potřeba ruční test v prohlížeči.

## Anti-patterns v JS

- `var` (i v existujícím kódu, když ho refactoreš).
- `==` / `!=` — použij `===` / `!==`.
- `eval()`, `new Function(...)`, `setTimeout("string", ...)`.
- Modifikace built-in prototypů (`Array.prototype.myFn = ...`).
- jQuery. Vanilla JS má vše potřebné.
- Modul-level side effects mimo IIFE / mimo entry point.
- Inline event handlery v HTML (`onclick="..."`). Použij `addEventListener`.
- `document.write()`.
- `innerHTML` s user-controlled contentem bez escape. Použij `textContent` nebo DOMPurify (pokud opravdu potřebuješ HTML).

## Cizí JS knihovny

Žádný build step: JS se kopíruje do výstupu přímo z `assets/`. `package.json` v pluginu (`private`) nese jen vývojové nástroje (ESLint, Prettier), runtime závislosti nemá.

Pokud chceš přidat 3rd party knihovnu:

- **Preferovaně:** uživatel si ji stáhne sám (jako Leaflet v krizky-map) a v configu odkáže URL. Plugin ji nedodává.
- **Výjimka:** velmi malé utility (< 5KB gzipped, žádné závislosti) — lze zkopírovat do `assets/<plugin>/vendor/<name>.js` a includnout. Vždy s licencí + attributionem v hlavičce.
- **Nikdy:** runtime závislosti v `package.json` pluginu, dokud ekosystém nemá jednotný build.
