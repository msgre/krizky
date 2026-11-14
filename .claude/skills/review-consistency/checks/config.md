# Kontrola: konfigurace

Cíl: config core a všech pluginů má jeden styl. Čtenář `config.yaml` pozná styl krizky, ne styl jednotlivých pluginů. Při dostatku materiálu vzniká `proposals/config-style-guide.md`.

## Postup

1. Vypiš klíče, které čte core: `grep -rn "config.get(\|\[\"" krizky/*.py`.
2. Pro každý plugin vypiš klíče, které čte, a kde v configu leží (top-level sekce, nebo pod `sources.`, `site.`).
3. Porovnej s ukázkovým YAML v README pluginu a s `../valasske_nebe_ng/config.yaml`.
4. Zjisti, jak se plugin chová, když jeho sekce chybí, a jak hlásí chybný config.

## Pravidla

- Dva pluginy používají stejný klíč na stejném místě → **blocker** (kolize).
- Stejné jméno klíče znamená v různých projektech něco jiného (`output` jednou adresář, jednou soubor) → **blocker**.
- Pro stejnou věc se používají různá jména (`output` × `output_dir`, `enabled` × `active`, `path` × `file`) → **recommended**. Kanonická je varianta z core, jinak návrh do proposals.
- Cesta z configu se neřeší vůči `config_dir`, nebo ji plugin převádí po svém místo `resolve_path` z `krizky.plugin_helpers` → **recommended**.
- Pluginy se liší v tom, co dělají při chybějící sekci (jeden mlčí, druhý varuje, třetí padá) → **recommended**. Rozumný výchozí stav: chybějící sekce znamená vypnuto, chybějící povinný klíč v existující sekci je chyba pluginu (`docs/guidelines/python.md` › Exceptions).
- Klíč, který kód čte, chybí v README pluginu, nebo README popisuje klíč, který kód nečte → **recommended** (docs-sync).
- Klíče v configu jsou anglicky a ve `snake_case` (`docs/guidelines/cross-language.md`). Odchylka → **recommended**.

`proposals/config-style-guide.md` napiš jen tehdy, když najdeš aspoň tři konvence, které většina projektů už dodržuje.
