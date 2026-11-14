# Kontrola: dokumentace

Cíl: každý projekt má stejnou kostru dokumentace a dokumentace odpovídá kódu.

Pravidla jsou v `docs/guidelines/docs-sync.md` (kostra README pluginu, kdy se co aktualizuje) a v `cross-language.md` › Nemíchat jazyky.

## Postup

1. Vypiš dokumenty v kořeni každého projektu a jeho `docs/`.
2. Z každého README vypiš nadpisy (`grep '^#' README.md`) a porovnej je s kostrou v `docs-sync.md`.
3. Porovnej ukázky configu, CLI příkazy, popsané šablonové funkce a hooky s kódem.
4. Projdi `CLAUDE.md` pluginů: úvodní odstavec a cesty ke guidelines a k `work/` v core.

## Pravidla

### Dokumentace lže

Každé z tohoto je **blocker**:

- README popisuje config klíč, příkaz, makro nebo šablonovou funkci jinak, než jak funguje kód.
- `docs/plugins.md` nebo docstring hookspec neodpovídá skutečné signatuře nebo okamžiku volání.

### Dokumentace chybí nebo zaostává

- Config klíč, CLI příkaz nebo šablonová funkce, která v README chybí → **recommended**.
- README pluginu neodpovídá kostře v `docs-sync.md` → **recommended**.
- Projekt bez `README.md` nebo `CLAUDE.md` → **recommended**.
- `CLAUDE.md` pluginu má úvodní odstavec, který nepopisuje daný plugin, nebo chybné cesty ke guidelines či ke core `work/` → **recommended**.
- Core README nemá aktuální seznam pluginů → **nice-to-have**.
- Odkaz na core repo se liší od `https://github.com/msgre/krizky` → **nice-to-have**.

### Jazyk

- Uživatelská dokumentace není česky, nebo kód a docstringy nejsou anglicky → **recommended**.
- Chybějící diakritika v české dokumentaci → **nice-to-have**.

### Logy

Logy se píšou jen do core `work/`, i za práci v pluginech a za běhy swarmu.

- Log mimo formát `work/YYYY-MM-DD-NN-heslo.md`, nebo log bez řádku ve `work/OVERVIEW.md` → **nice-to-have**.
- Plugin má vlastní `work/` → **recommended**.
