---
name: review-consistency
description: Revize konzistence core krizky a všech pluginů krizky-*. Hledá duplicitu vhodnou k přesunu do core, odchylky od guidelines a společných vzorů a slabá místa plugin API. Výstupem jsou reporty v `reports/`. Bez argumentu projde všechny projekty, s názvem projektu (např. `krizky-photos`) zaměří report na něj.
---

# review-consistency

Revize konzistence mezi core a pluginy, které sdílejí plugin API. Kontroluje Python i JavaScript pluginů dohromady, protože JS je vždy doplněk konkrétního Python pluginu.

Tři cíle, v tomto pořadí:

1. **Duplicita**: kód opakovaný v pluginech, který patří do core.
2. **Konzistence**: kód všech projektů má působit jako od jednoho autora (pojmenování, vzory, chyby, dokumentace, testy, config).
3. **Adekvátnost API**: sedí hooky a veřejné funkce core tomu, co pluginy skutečně potřebují?

## Projekty

Skill se spouští z core (`/Users/msgre/projects/muzeum/krizky`). Každý projekt je samostatné git repo.

```bash
# core: soubor s hookspecs
grep -l 'HookspecMarker("krizky")' -r krizky --include='*.py'
# pluginy: sourozenecké adresáře s entry pointem
grep -l 'entry-points."krizky"' ../krizky-*/pyproject.toml
```

- **Core** je toto repo.
- **Pluginy** jsou sourozenecké adresáře `../krizky-*/` s entry pointem `krizky`.
- **Web** `../valasske_nebe_ng/` je reálný web postavený na core a všech pluginech. Nereviduje se. Slouží jako doklad, jak se API skutečně používá (`config.yaml`, `templates/`, `assets/`, případně `plugins/*.py`). Než něco označíš za mrtvý kód nebo za věc jednoho webu, ověř to v něm.

Argument s názvem projektu zužuje jen to, o čem se píše report. Core a ostatní pluginy čti dál jako kontext, protože konzistence je vlastnost napříč projekty. Argument s tématem (např. „hooky“, „testy“) zužuje, které skupiny kontrol se spustí.

Adresáře `.venv/`, `__pycache__/`, `node_modules/` a přibalené cizí JS knihovny se nečtou.

## Podklady

Tohle je měřítko, se kterým se vše porovnává:

1. `docs/plugins.md`: **definice veřejného API**. Hooky a funkce, které tu jsou popsané, jsou veřejné. Ostatní z balíčku `krizky` je interní.
2. `krizky/hooks.py` a `krizky/plugin_manager.py`: hookspecs a načítání pluginů.
3. `docs/guidelines/*.md`: dohodnuté konvence pro core i pluginy.
4. `CLAUDE.md` a `README.md` core.
5. U každého pluginu `plugin.py`, `pyproject.toml`, `README.md` a `CLAUDE.md`.

Fakta o projektech (které moduly existují, co je veřejné, jaké hooky jsou) zjišťuj z těchto souborů za běhu. Instrukce v `checks/` popisují pravidla, ne aktuální stav kódu.

Formátování a lint hlídá `scripts/verify` v každém repu (ruff, u pluginů s JS i ESLint a Prettier). Co tyto nástroje vynucují, se nehlásí. Hlásí se jen repo, kterému `scripts/verify` chybí, nebo které má konfiguraci odlišnou od ostatních.

## Co je správně

Když se projekty liší, rozhoduj takto:

1. **Guidelines.** Když otázku řeší `docs/guidelines/`, je to kanonická podoba a odchylka je nález. Když guideline zjevně neodpovídá dnešnímu stavu (popisuje „aktuální stav“, který už neplatí, nebo odkazuje na neexistující soubor), nevymáhej ji. Zapiš ji do sekce „Guidelines k revizi“ v `summary.md`.
2. **Precedent v core.** Vzor, který existuje v `krizky/`, je kanonický a pluginy se mu mají přizpůsobit.
3. **Vzor jen v pluginech.** Vítěze nevybírej. Popiš obě varianty neutrálně a jednu navrhni jako kanonickou v `proposals/`. Rozhodnutí patří uživateli.
4. **Jen existující konvence.** Skill srovnává to, co už v projektech je. Nová konvence smí vzniknout jen jako návrh v `proposals/`.

## Severity

Každý nález má jednu severitu. Volí se střídmě, nafouknutá severita ředí signál.

- **blocker**: rozbíjí konzistenci tak, že na to narazí uživatel nebo správce. Například dva pluginy mají stejný config klíč s jiným významem, plugin importuje soukromý symbol core (`_foo`), plugin implementuje hook, který jeho minimální verze core nezná.
- **recommended**: skutečný rozjezd, dnes nic nerozbíjí. Například jiné pojmenování téhož, plugin si píše vlastní verzi helperu z `krizky.plugin_helpers`, plugin závisí na nezdokumentované funkci core.
- **nice-to-have**: kosmetika a preference.

## Postup

### 1. Příprava

Zjisti projekty, poznač si fokus z argumentu a přečti podklady. Najdi předchozí report: nejnovější adresář v `reports/` podle jména. Hotovo, když máš seznam projektů, cestu k předchozímu reportu (nebo víš, že žádný není) a přečtené `docs/plugins.md`.

### 2. Kontroly po skupinách

Kontroly jsou v `checks/` a běží v šesti skupinách. Každá skupina čte stejný kód, proto běží v jednom sub-agentovi:

| Skupina | Kontroly |
|---|---|
| api | `api-boundaries.md`, `hooks.md` |
| duplicita | `duplication.md` |
| config-data | `config.md`, `naming-data.md` |
| python | `python-style.md`, `error-logging.md` |
| js | `js-style.md` (jen když některý plugin má JS) |
| testy-docs | `tests.md`, `docs.md`, `dead-code.md` |

Spusť skupiny paralelně jako sub-agenty `general-purpose`. Do zadání každého dej:

- seznam projektů a fokus,
- cesty k podkladům (sekce výše) a ke kontrolám skupiny, které má přečíst celé,
- blok nálezu z `report-format.md`,
- že jen čte kód a nic nezapisuje,
- že vrací nálezy jako bloky nálezu seskupené podle projektu, a k tomu podklady pro `proposals/` (u skupin api, duplicita a config-data),
- že každý nález cituje konkrétní `soubor:řádek`, který sám otevřel.

Hotovo, když se vrátily všechny spuštěné skupiny.

### 3. Ověření

Každý nález se severitou blocker nebo recommended ověř sám: otevři místa z `Kde` a potvrď, že tvrzení platí. U mrtvého kódu a „věcí jednoho webu“ prohledej i `../valasske_nebe_ng/`.

- Potvrzený nález zůstává.
- Vyvrácený nález vyřaď a započítej do statistiky „vyřazeno při ověření“.
- Nález, který nejde rozhodnout, ponech a do `Co` připiš „Nejisté: …“ s důvodem.

Duplicitní nálezy ze dvou skupin slouč do jednoho. Hotovo, když má každý blocker a recommended jeden z těchto výsledků.

### 4. Srovnání s předchozím reportem

Každému nálezu nastav `Stav`: `nový`, nebo `přetrvává` s odkazem na nález v předchozím reportu. Blocker a recommended z předchozího reportu, které v novém nejsou, a jejich místo v kódu se změnilo, vypiš v `summary.md` v sekci „Vyřešeno od minula“. Hotovo, když má stav každý nález.

### 5. Report

Zapiš report do `reports/YYYY-MM-DD-HHMM/` podle `report-format.md`. Na konci uživateli vypiš cestu k reportu a počty nálezů podle severity. Report necommituj.

## Mimo rozsah

- Úpravy kódu. Nálezy implementuje `/swarm:run`, který report z `reports/` vezme jako vstup.
- Správnost chování. Konzistence není správnost: když jsou dvě varianty nekonzistentní a obě fungují, je to pořád nález.
- Čistota kódu uvnitř jednoho souboru (délka funkcí, složitost).
- `TODO.md` ve všech repech a `PLAN.md` v pluginech jsou lokální poznámky v `.gitignore`. Jejich obsah ani absence nejsou nálezy.

## Jazyk

Report se píše česky. Identifikátory, cesty a technické termíny zůstávají v původní podobě.
