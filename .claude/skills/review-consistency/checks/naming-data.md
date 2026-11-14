# Kontrola: pojmenování v datech

Cíl: stejný význam má stejné jméno ve sloupcích SQL, klíčích dictů, configu, data-atributech a JS.

Pravidla transformace mezi vrstvami (`snake_case` v Pythonu a YAML, `camelCase` v JS, `kebab-case` v data-atributech) popisuje `docs/guidelines/cross-language.md` › Naming across the stack.

## Postup

1. Z `krizky/db.py` a `krizky/query.py` zjisti, jaké klíče mají záznamy, kategorie a stránky.
2. Vypiš, jaká pole pluginy čtou: `grep -rn 'record\[\|record.get(\|record\.' ../krizky-*/`.
3. Vypiš klíče dictů, které pluginy předávají do šablon nebo do JS (photo dict, config pro JS, GeoJSON vlastnosti).
4. Sestav mapu „význam → jména“ napříč projekty a hledej, kde má jeden význam víc jmen nebo jedno jméno víc významů.

## Pravidla

- Jeden význam má v různých projektech různá jména (`url` × `href` × `link`, `path` × `file_path`, `meta` × `metadata`) → **recommended**. Kanonické je jméno z core.
- Jedno jméno má ve dvou projektech jiný význam (`key`, `slug`) → **recommended**. Doporuč rozlišit jménem nebo dokumentací.
- Jméno se mezi vrstvami nemění jen podle konvence vrstvy (`base_name` v Pythonu, `photoId` v JS) → **recommended**.
- Pravdivostní klíče mají v jednom projektu různé předpony (`has_`, `is_`, bez předpony) pro stejný druh informace → **nice-to-have**.
- Datum a čas: jedna věc jednou jako ISO řetězec, jindy jako `datetime` → **recommended**.
