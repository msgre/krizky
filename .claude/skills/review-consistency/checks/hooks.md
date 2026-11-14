# Kontrola: adekvátnost hooků

Cíl: zjistit, jestli sada hooků v `krizky/hooks.py` odpovídá tomu, co pluginy dělají. Podklady pro `proposals/hook-changes.md`.

## Postup

1. Z `krizky/hooks.py` vypiš hookspecs: jméno, parametry, `firstresult`.
2. Pro každý plugin a pro `../valasske_nebe_ng/plugins/*.py` vypiš metody s `@hookimpl`.
3. Sestav matici hook × implementace.
4. Projdi těla implementací a hledej vzory z pravidel níže.

## Pravidla

### Využití hooků

- Hook bez jediné implementace v pluginech i ve webu → **nice-to-have**, návrh „zvážit odstranění“.
- Hook s jedinou implementací: v návrhu posuď, jestli jde o obecný bod rozšíření, nebo o únikovou cestu jednoho pluginu. Samostatný nález z toho nedělej.

### Chybějící rozhraní

Každý z těchto vzorů je **recommended** s podkladem do `proposals/hook-changes.md`:

- Plugin potřebuje informaci, kterou žádný hook nedává, a získává ji oklikou: znovu parsuje config, odvozuje cestu, importuje interní funkci core.
- Plugin dělá práci ve špatném bodě životního cyklu (např. jednorázovou práci v hooku volaném pro každou stránku a hlídá si to příznakem).
- Dva a více pluginů opakuje v jednom hooku stejný postup. Nejdřív zvaž helper v `krizky.plugin_helpers` (skupina duplicita), hook navrhni jen tehdy, když helper nestačí.

### Signatury a dokumentace

- Stejná věc má v různých hookspecs různé jméno parametru (`config_dir` × `base_dir`) → **recommended**.
- Implementace vynechávají parametry, které nepotřebují. To pluggy dovoluje a je to běžný idiom, není to nález.
- `firstresult=True` u hooku, kde se mají uplatnit všechny implementace, nebo naopak → **blocker**.
- Docstring hookspec neuvádí, kdy se hook volá, kolikrát, a co znamená návratová hodnota → **recommended**.
- Popis hooku v `docs/plugins.md` neodpovídá `krizky/hooks.py` nebo volání v core → **blocker** (dokumentace lže).

Každý návrh v `proposals/hook-changes.md` obsahuje motivaci s odkazy `soubor:řádek`, signaturu, kdo by ho využil, zváženou alternativu a migraci.
