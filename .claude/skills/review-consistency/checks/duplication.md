# Kontrola: duplicita a kandidáti na přesun do core

Cíl: najít kód opakovaný v pluginech, který patří do core. Výstupem je `proposals/consolidation-to-core.md`. Je to první ze tří cílů skillu, věnuj jí čas.

## Postup

1. Přečti `docs/plugins.md` › Pomocné funkce pro pluginy. Ke každému helperu z `krizky.plugin_helpers` najdi v pluginech kód, který dělá totéž po svém.
2. Přečti těla všech `@hookimpl` metod ve všech pluginech a porovnej implementace stejného hooku mezi pluginy.
3. Najdi stejně pojmenované funkce v různých pluginech (`grep -rn "^def \|^    def " ../krizky-*/krizky_*/`) a porovnej jejich těla.
4. Porovnej JS soubory pluginů: bootstrap, čtení configu, práci s data-atributy, detekci API prohlížeče s fallbackem.
5. Porovnej `tests/conftest.py` a pomocné funkce v testech napříč projekty.

Typická místa vzniku duplicity: čtení config sekce s defaulty, cesty vůči `config_dir`, čtení a zápis JSON, kopírování assetů, registrace šablon a Jinja globals, Click příkazy se stejnými přepínači, fixtury s testovací databází.

## Pravidla

- Plugin si píše vlastní verzi helperu, který `krizky.plugin_helpers` už má → **recommended**. Doporučení: nahradit helperem.
- **strong** kandidát: tři a více výskytů s minimálními rozdíly → **recommended**, karta do proposals.
- **medium** kandidát: dva výskyty s téměř shodnou strukturou o deseti a více řádcích → **nice-to-have**, karta do proposals s doporučením „zvážit“.
- Dva výskyty s podstatnými rozdíly nejsou duplicita, ale podobný tvar. Nehlas je.
- Nehlas ani kód, kde by helper potřeboval víc parametrů, než kolik řádků ušetří, a tři řádky, které vypadají podobně, ale dělají něco jiného.

Kandidáty řaď podle ušetřených řádků × počtu pluginů, mínus riziko změny volacích konvencí. Pět nejsilnějších uveď v `summary.md`.
