# Check: hraniční API mezi core a pluginy

Cíl: pluginy komunikují s core jen přes veřejné API (hooky + explicitně veřejné moduly). Zároveň pluginy nemají v sobě věci, které patří do **uživatelského projektu** (typicky do jeho `plugins/` složky, `templates/` nebo `config.yaml`).

Tento check je nejdůležitější — uživatel na něj výslovně upozornil.

## Postup

1. Pro každý plugin: `grep -r "from krizky" krizky_<name>/` — jaké core moduly importuje.
2. Pro každý import: je cílový symbol veřejný (žádný `_` prefix, dokumentovaný)? Existuje k dispozici přes hook?
3. Grep monkey-patchingu, `krizky.render.foo = ...`, přepisů globálů.
4. V pluginu hledej hardcoded věci, které mají patřit do uživatelského projektu (viz níže).

## Checklist — pluginy vůči core

### Imports
- [ ] Plugin importuje pouze:
  - `from krizky.hooks import hookimpl` (pro dekorátor)
  - dokumentované veřejné moduly (`krizky.query`, `krizky.render` — pokud jsou veřejné)
- [ ] Import z `krizky._foo`, `krizky.<module>._something` → **blocker** (pokud není zdokumentován jako veřejný).
- [ ] Duplicitní import obalu, který by měl core exportovat centrálně (`from krizky.hooks import hookimpl` OK; `from krizky.pluginlib.hookimpl import ...` špatně).

### Coupling
- [ ] Plugin cituje jméno jiného pluginu (`if photos_plugin_installed: ...`) → **blocker**. Cross-plugin coupling patří přes hooky, ne přes import/detekci.
- [ ] Core cituje jméno konkrétního pluginu (`if "krizky-photos" in installed: ...`) → **blocker**. Core neví o konkrétních pluginech.
- [ ] Plugin monkey-patchuje core → **blocker**.

### Chybějící rozhraní
- [ ] Plugin dělá něco přes obcházku (řetězec re-parse configu, manuální inspekce cesty), protože potřebná informace není přes hook dostupná → flag do `hooks.md` proposal.
- [ ] Plugin potřebuje data z běhu jiného pluginu → nemá být přímý import, má být hook / shared context.

## Checklist — plugin vs uživatelský projekt (project-specific leakage)

**Uživatel má vlastní web (v tomto workspace pravděpodobně `../mujpivo` nebo obdoba), který si instaluje `krizky` + pluginy a dodává:**
- svůj `config.yaml`
- svoje `templates/` (přepisy nebo vlastní stránky)
- svoji `sources/` (data)
- svoje `plugins/` (per-project pluginy)

**Plugin má být obecný.** Nesmí obsahovat věci vázané na jeden konkrétní web.

Zaznamenej jako **blocker** cokoli z těchto vzorců:

- [ ] Hardcoded slug nebo název záznamu (`if record["slug"] == "svaty-jan": ...`) v plugin kódu.
- [ ] Hardcoded config klíč, který dává smysl jen pro jeden web (`config["mujpivo"]["nazev"]`).
- [ ] Šablona v pluginu s obsahem specifickým pro jeden web (např. footer s "Copyright Michal 2026", CTA na konkrétní e-shop).
- [ ] URL / doménové jméno hardcoded v Pythonu nebo JS (mimo příkladů v README).
- [ ] Konkrétní SQL query hardcoded, která reflektuje uživatelovo schéma dat (např. `SELECT nazev, latitude FROM mista_v_krkonosich`).
- [ ] JS s texty v uživatelově jazyce (dobře: "Kopírováno" ve `krizky-share` je akceptovatelné, protože plugin sám je čs. produkt — ale "Objednat pivo" už ne). Rozhoduj podle toho, jestli text je vlastnost pluginu nebo vlastnost webu.
- [ ] CSS třídy s brand jmény webu.

**Recommended (ne blocker) vzorce:**
- Plugin má lokalizaci fixně v češtině (bez fallback / bez i18n). Je to OK pro krizky ekosystém (čs. projekt), ale flag jako recommended s poznámkou.
- Plugin nabízí default vzhled, který úzce cílí na jeden web — ale nechává ho přebít v config → OK.

### Recovery cesta (co říct)
Když najdeš project-specific věc v pluginu, doporuč jednu z:
1. **Přesunout do uživatelova `plugins/<x>.py`** (per-project plugin dir).
2. **Přesunout do uživatelovy šablony** (override).
3. **Vytáhnout ven jako config option** (plugin zůstane obecný, uživatel doplní config).

Ve zjištění uveď konkrétní doporučení, ne jen "je to špatně".

## Checklist — core vůči pluginům

- [ ] Core neimportuje z `krizky_<x>` (žádný plugin package). Core interaguje s pluginy jen přes pluggy PM.
- [ ] Core nemá `if plugin_name == "photos": ...` větve.
- [ ] Core dokumentuje veřejné API (co je bezpečné importovat, co je private).
- [ ] `krizky/__init__.py` — pokud re-exportuje symboly, je jasné, co je "public API"?

## Zvláštní pozornost

- **Historický kontext:** photos byl původně builtin, teď je oddělený plugin. Zkontroluj, jestli v core nezůstaly artefakty (`# JsonExportPlugin moved to krizky-json package.` — takové komentáře jsou OK jako TODO markery, ale pokud tam zůstal i mrtvý kód, → dead-code check.
- **Sanity check:** pokud plugin importuje `krizky.render.render_html` (fiktivní příklad) a jiný plugin importuje `krizky.render.render`, ale oba dělají totéž — jde o výběr veřejného API core → doporuč sjednotit.
