# Revize skillu review-consistency

## Proč
Skill byl napsaný podle stavu ze srpna 2026. Po core 0.2 neznal `krizky.plugin_helpers`, za veřejné API považoval jen `hookimpl` a „`krizky.query`, `krizky.render` — pokud jsou veřejné“, nálezy neověřoval a checklisty byly hlavně otázky bez rozhodovacího pravidla.

## Co se změnilo
Soubory v `.claude/skills/review-consistency/`: `SKILL.md`, `report-format.md` a všech 11 souborů v `checks/`. Celkem 608 řádků místo ~1000, kontroly 349 místo 715.

- **Veřejné API definuje `docs/plugins.md`.** Fakta o projektech si skill zjišťuje za běhu, kontroly obsahují jen pravidla. Odstraněné zastaralé údaje (builtin pluginy, poznámka o `config_dir`, navrhované helpery, které už pokrývá `plugin_helpers`).
- **Nová pravidla:** plugin si píše vlastní verzi helperu z `plugin_helpers`; plugin implementuje hook, který jeho `krizky>=` nezná; pluginy mají v `uv.lock` různé revize core; import nezdokumentovaného symbolu core.
- **Checklisty → pravidla se severitou.** Pravidla, která jsou v `docs/guidelines/`, se odkazují, ne opisují.
- **Workflow:** kontroly běží v šesti skupinách jako paralelní sub-agenti, hlavní agent ověřuje každý blocker a recommended v kódu a srovnává s předchozím reportem (pole `Stav`, sekce „Vyřešeno od minula“).
- **Zastaralé guidelines** se nevymáhají, ale hlásí v sekci „Guidelines k revizi“ v `summary.md`.
- **Odstraněné rozpory:**
  - duplicita: strong = tři a více výskytů, medium = dva téměř shodné výskyty;
  - nepoužité importy už se nehlásí (hlídá je ruff);
  - čeština v UI textech pluginu není nález, nálezem je jen text konkrétního webu;
  - zbytek z konverzace „uživatel na něj výslovně upozornil“.
- Celý skill je česky.

## Úklid guidelines
Při revizi se ukázalo, že zastaralé jsou i `docs/guidelines/`. Upravené soubory:

- **Všechny:** pryč zbytky zrušeného skillu `implement-review` (věty „Load this file when…“, sekce „Skill enforcement“).
- **`python.md`:**
  - opsaná konfigurace ruff (neodpovídala, chyběly TID a banned-api) → odkaz na `pyproject.toml` core a `scripts/verify`,
  - `from __future__` jen jako zákaz (TID251),
  - příklad docstringu podle skutečného `register_plugin_templates` (dřív tvrdil `ValueError`),
  - příklad výjimek s obecnými jmény místo neexistujících tříd photos,
  - pryč `krizky.testing` a návod na `uv add`,
  - „Před commitem“ → `scripts/verify`.
- **`javascript.md`:**
  - `.eslintrc.json`, `.prettierrc.json` a neexistující `.editorconfig` → popis shodných `eslint.config.mjs` a `.prettierrc.json` v pluginech,
  - `package.json` je jen pro vývojové nástroje,
  - „Před commitem“ → `scripts/verify`.
- **`docs-sync.md`:**
  - pryč sekce o chybějícím `CLAUDE.md` v pluginech, `work/` v pluginech, interakci s config-style-guide a post-commit verifikaci,
  - z tabulky vypadl sloupec `work/` log (řeší ho `CLAUDE.md`),
  - přibyly `docs/plugins.md` a tabulky šablon v `CLAUDE.md`.
- **`cross-language.md`:**
  - cross-plugin data sharing bez „aktuálního“ stavu, s cestou ke starému návrhu hooku,
  - commity odkazují na `CLAUDE.md` místo paměti,
  - verifikační kroky bez duplikace `scripts/verify`.
- **`security.md`:** pryč „Skill enforcement“.

Odkazy: první řádek `eslint.config.mjs` ve filters, map a share odkazoval na odstraněný blok `.eslintrc.json` (PR msgre/krizky-filters#10, msgre/krizky-map#4, msgre/krizky-share#4). Názvy sekcí, na které odkazuje skill a `pyproject.toml` (`python.md`), zůstaly. Historické tikety v `.swarm/` jsem neměnil.

## Rozhodnutí: path traversal
`security.md` › Path traversal požadoval, aby relativní cesta z configu nevedla mimo `config_dir`, což `krizky.plugin_helpers.resolve_path` nekontroluje. Uživatel rozhodl, že platí helper: config píše vlastník webu a je důvěryhodný. Guideline teď rozlišuje cesty z configu (důvěryhodné, `resolve_path`, `..` se neblokuje) a cesty odvozené z dat (slug, jména souborů z Drive), které musí po `resolve()` zůstat v cílovém adresáři.

## Poznámky
- Skill se zatím nespouštěl.
