# Kontrola: hranice API mezi core, pluginy a webem

Cíl: pluginy mluví s core jen přes veřejné API a neobsahují nic, co patří jednomu konkrétnímu webu.

Veřejné API definuje `docs/plugins.md`: hooky a funkce v něm popsané. Ostatní z balíčku `krizky` je interní.

## Postup

1. Pro každý plugin vypiš importy z core: `grep -rn "from krizky\|import krizky" ../krizky-<x>/krizky_<x>/`.
2. Každý importovaný symbol porovnej s `docs/plugins.md`.
3. Vypiš hooky, které plugin implementuje, a zjisti, od které verze core existují (`docs/plugins.md`, `git log -S` v `krizky/hooks.py`). Porovnej s omezením `krizky>=` v `pyproject.toml` pluginu.
4. Porovnej revizi `krizky` v `uv.lock` všech pluginů.
5. Projdi kód, šablony a JS pluginu a hledej věci jednoho webu (pravidla níže).
6. V core hledej zmínky o konkrétních pluginech: `grep -rn "krizky_\|krizky-" krizky/`.

## Pravidla

### Importy z core

- Import symbolu s `_` z core → **blocker**.
- Import symbolu, který `docs/plugins.md` nepopisuje → **recommended**. Doporuč jedno z: zdokumentovat ho v `docs/plugins.md` jako veřejný, nahradit helperem v `krizky.plugin_helpers`, nebo nahradit hookem. Když stejný nezdokumentovaný symbol používají dva a více pluginů, přidej podklad do `proposals/hook-changes.md`.
- Monkey-patching core (přiřazení do atributů modulů `krizky.*`) → **blocker**.

### Verze core

- Plugin implementuje hook nebo volá funkci, kterou jeho minimální `krizky>=` nezná → **blocker**. Starší core takový hook tiše ignoruje.
- Pluginy mají v `uv.lock` různé revize `krizky` → **recommended**. Testují se pak proti jinému core.

### Vazby mezi pluginy a core

- Plugin importuje jiný plugin nebo detekuje jeho instalaci → **blocker**. Data mezi pluginy jdou přes hooky.
- Plugin čte config sekci jiného pluginu (např. `sources.photos`) → **recommended**. Řešení popisuje `docs/guidelines/cross-language.md` › Cross-plugin data sharing.
- Core importuje plugin nebo větví podle jména pluginu → **blocker**.

### Věci jednoho webu v pluginu

Plugin má být obecný. Web dodává vlastní `config.yaml`, `templates/`, `assets/`, `sources/` a případně `plugins/*.py`.

Jako **blocker** hlas v kódu, šablonách a JS pluginu:

- natvrdo zapsaný slug, název záznamu nebo jméno tabulky dat konkrétního webu,
- config klíč, který dává smysl jen jednomu webu,
- doménu nebo URL webu (mimo příklady v README),
- obsah šablony, který patří jednomu webu (patička s autorem, odkaz na konkrétní e-shop),
- CSS třídy se jménem značky webu.

Čeština v UI textech pluginu je konvence ekosystému (`docs/guidelines/cross-language.md`), sama o sobě není nález. Nález je text, který patří konkrétnímu webu.

Doporučení vždy pojmenuje cestu ven: přesun do `plugins/<x>.py` webu, do šablony webu (override), nebo nový config klíč pluginu.
