# Kontrola: mrtvý kód

Cíl: najít symboly, šablony, assety a config klíče, které nikdo nepoužívá.

Mrtvý kód se snadno označí falešně: pluggy volá hookimpl dynamicky, šablony web volá podle jména, veřejné API může používat jen web. Než nález zapíšeš, ověř každý symbol grepem napříč core, všemi `../krizky-*/` a `../valasske_nebe_ng/`. Nepoužité importy a proměnné hlídá ruff, ty se nehlásí.

## Postup

1. Pro každou veřejnou funkci, třídu a konstantu v core a pluginech: grep jména napříč projekty a webem, mimo definici a testy.
2. Pro každou šablonu v `templates/` pluginu: grep jejího jména v `{% include %}`, `{% import %}`, `{% from %}`, `template:` v configu a Python kódu.
3. Pro každý soubor v `assets/` pluginu: grep jména v šablonách a Python kódu (`inject_head`, `<link>`, `<script>`).
4. Pro JS: funkce bez volání, data-atributy, které JS čte a šablona negeneruje, a naopak.

## Pravidla

- Veřejná funkce, třída nebo konstanta, kterou nevolá nikdo mimo testy → **recommended**. Když byla přidána za poslední dva týdny (`git log`), **nice-to-have** s otázkou „je to připravené pro další krok?“.
- Metoda třídy pluginu bez `@hookimpl`, kterou nikdo nevolá → **recommended**.
- Šablona nebo asset pluginu, na které nic neodkazuje → **recommended**.
- Test, který testuje už neexistující kód, nebo fixtura, kterou žádný test nepoužívá → **recommended**.
- Zakomentovaný kód delší než pět řádků → **nice-to-have**.
- Nepoužité CSS třídy → **nice-to-have**.

Hooky bez implementace patří do `hooks.md`, config klíče, které kód nečte, do `config.md`.
