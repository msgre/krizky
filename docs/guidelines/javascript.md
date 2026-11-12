# Guidelines: JavaScript

Vanilla JS, žádný framework (React/Angular/Vue/Svelte jsou explicitně vyloučené). Kvalitní third-party balíčky OK (viz "Package selection" níže). Cílový browser: moderní evergreen (Chromium/Firefox/Safari poslední 2 roky, Firefox ESR OK).

Load this file when a finding touches JS code.

## ESLint + Prettier config

Přidat do každého pluginu, který má JS (`_plugins/<name>/`):

### `.eslintrc.json`

```json
{
  "root": true,
  "env": {
    "browser": true,
    "es2022": true
  },
  "parserOptions": {
    "ecmaVersion": 2022,
    "sourceType": "script"
  },
  "extends": ["eslint:recommended"],
  "rules": {
    "no-var": "error",
    "prefer-const": "error",
    "prefer-arrow-callback": "error",
    "no-unused-vars": ["warn", { "argsIgnorePattern": "^_" }],
    "eqeqeq": ["error", "always"],
    "curly": ["error", "all"],
    "no-console": ["warn", { "allow": ["warn", "error"] }],
    "no-implicit-globals": "error",
    "prefer-template": "warn",
    "object-shorthand": ["warn", "always"]
  },
  "ignorePatterns": ["node_modules/", "dist/", "*.min.js"]
}
```

### `.prettierrc.json`

```json
{
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5",
  "arrowParens": "always",
  "endOfLine": "auto"
}
```

### Root workspace `.editorconfig` (aby všechny pluginy měly stejné basics)

```ini
root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.py]
indent_size = 4

[Makefile]
indent_style = tab
```

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

Skill má povinnost při navrhování nového balíčku ověřit body 1-5 a **oznámit uživateli** před `uv add` / `npm install`. Body 6-9 uvést jako sanity check.

**Preferuj stdlib.** Než přidáš 3rd party dep, pokus se to napsat s pomocí stdlib. Rule of thumb: <30 řádků, kde stdlib nabízí building blocks → nepřidávat dep.

## Před commitem

Pro každý změněný `*.js` soubor:

1. `npx eslint <file>` (pokud .eslintrc existuje v projektu) — clean.
2. `npx prettier --check <file>` — pass. Pokud fail: `npx prettier --write <file>`, re-check.
3. `node --check <file>` — syntax pass.
4. Manuální browser sanity check pokud změna dotýká DOM interakce (skill to sám nespustí, ale upozorní uživatele v log entry: "Doporučuji manuální test v prohlížeči").

Pokud eslint/prettier config v projektu chybí, skill navrhne přidání (viz sekce nahoře) a zeptá se — **ne** ho přidá automaticky. Přidání linter configu je separátní finding.

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
- Console.log v committnutém kódu (ESLint pravidlo to flagne).

## Cizí JS knihovny v projektu (npm not required)

Aktuální ekosystém: **žádný `package.json`, žádný build step.** JS soubory jsou zkopírované do output přímo z `assets/`.

Pokud chceš přidat 3rd party knihovnu:

- **Preferovaně:** uživatel si ji stáhne sám (jako Leaflet v krizky-map) a v configu odkáže URL. Plugin ji nedodává.
- **Výjimka:** velmi malé utility (< 5KB gzipped, žádné závislosti) — lze zkopírovat do `assets/<plugin>/vendor/<name>.js` a includnout. Vždy s licencí + attributionem v hlavičce.
- **Nikdy:** vlastní `package.json` v pluginu, dokud si celý ekosystém neustanoví jednotný build tooling.
