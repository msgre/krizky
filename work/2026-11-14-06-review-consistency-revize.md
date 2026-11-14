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

## Poznámky
- Při revizi se ukázalo, že zastaralé jsou i části `docs/guidelines/`:
  - `docs-sync.md`: „CLAUDE.md aktuálně chybí ve všech pluginech“, sekce o `work/` v pluginech;
  - `python.md`: `krizky.testing` „po jeho vzniku“;
  - `cross-language.md`: „aktuální anti-pattern“ se `sources.photos.base_url`;
  - sekce „Skill enforcement“ pro zrušený `implement-review`.

  Neměnil jsem je, první běh nového skillu je zachytí v sekci „Guidelines k revizi“.
- Skill se zatím nespouštěl.
