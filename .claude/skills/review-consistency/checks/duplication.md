# Check: duplikace a kandidáti na konsolidaci do core

Cíl: najít kód, který se opakuje napříč pluginy a patří do core. Výstup: `proposals/consolidation-to-core.md`.

Tento check je jeden ze tří hlavních cílů skillu (spolu s konzistencí a hook adekvátností). Věnuj mu čas.

## Postup

Tenhle check je náročný na "přehled napříč všemi soubory". Zvaž spuštění `Explore` sub-agenta s dotazem typu "najdi ve všech pluginech vzorce X" — vrací sumář, ne raw kód, což šetří tvůj kontext.

1. Rozdělené prohledávání:
   - Pro každou hookimpl metodu v každém pluginu → přečti její tělo. Hledej, jestli podobná logika (10+ řádků) existuje v jiném pluginu.
   - Grep `def <name>(` u utility helperů — pokud stejné jméno funkce existuje ve dvou pluginech, prověř těla.
   - Prohledej JS soubory na podobné boilerplate (config parsing, event delegation, IIFE bootstrap).
2. Pro každý nalezený vzorec sepiš karta (viz šablona v `report-format.md`).
3. Priority: rank podle "kolik LOC ušetří" × "kolik pluginů z toho těží".

## Kde hledat (hot spots)

Zkušenost říká, že tady se duplicity typicky rodí:

### Konfigurace
- Načtení a resolving `sources.<x>` sekce (kontrola existence, `.get(...)` s defaulty).
- Resolving cest relativně ke `config_dir`.
- Interpolace `$VAR` env vars.
- Kandidát na core: `krizky.config.get_plugin_section(name, config, config_dir)` nebo obdoba.

### Loggery
- `_log = logging.getLogger(__name__)` — trivial, spíš konvence než konsolidace.
- Ale pokud plugin má vlastní `def _setup_logging(): ...`, → do core.

### Cesty a I/O
- Otevírání/zápis JSON s error handlingem.
- Otevírání YAML.
- `mkdir(parents=True, exist_ok=True)`.
- Kandidát na core: `krizky.io.read_json(path)` s konzistentním fail chováním.

### CLI příkazy
- `@click.command`, `@click.option` boilerplate — pokud několik pluginů má identický pattern (např. `--force`, `--dry-run` s totožnou sémantikou), pull do `krizky.cli_helpers`.

### Templates helpers
- Jinja filtery/globals registrace — pokud několik pluginů dělá stejnou orchestraci, do core `register_filters(env, {"x": fn, ...})` helperu.

### Zpracování záznamů
- Iterace přes `records` s pomocí `row_number` klíče a přiřazení asset dat — kdo to dělá?
- Kandidát: `krizky.records.attach_assets(records, key, values)` helper.

### JS bootstrapping
- IIFE + `'use strict'` + config parsing z `<script type="application/json">` + graceful degradation — vzorec, který se opakuje.
- Konsolidace: extract do sdíleného `krizky/assets/bootstrap.js` a linkni ho z pluginů. Nebo pull do core (`inject_head` hook + shared JS lib).

### Progressive enhancement patterns
- Detekce native API (Web Share, Clipboard) + fallback — pokud podobný pattern v ≥2 JS souborech, → sdílený helper.

### Data-attribute selection
- `document.querySelectorAll('[data-<x>]').forEach(...)` — pokud vzorec je 90 % boilerplate, → helper `krizkyOn('[data-x]', setupFn)`.

## Klasifikace kandidátů

Každý kandidát má vlastnost "sila vzoru":

- **strong** — ≥3 pluginy, minimální rozdíly, jasné volume. → doporuč konsolidaci s vysokou prioritou.
- **medium** — 2 pluginy, drobné variace. → doporuč jako "zvážit", ne "nutně udělat".
- **weak** — 2 pluginy, ale s významnými rozdíly. → možná není pravá duplicita, jen podobný "shape". Nekonsoliduj.

**Silné vzory rank podle:**
1. LOC ušetřené × počet pluginů (impact),
2. minus riziko rozbití API (pokud helper změní volací konvence, migrace stojí čas),
3. minus riziko premature abstraction (pokud vzory se liší v detailech, může helper vytvořit ošklivá parametrizace).

## Anti-pattern: příliš agresivní konsolidace

Rovnou označ jako `nice-to-have` nebo vůbec nedoporučuj:
- Tři řádky, které "vypadají podobně" ale sémanticky dělají jinou věc.
- Vzory, kde konsolidace by přidala více parametrů, než by uspořila řádků.
- Vzory specifické pro jeden plugin, které se náhodou podobají něčemu jinému.

**Rule of three:** duplicity flag až od třetího výskytu, pokud dva výskyty nemají silně identickou strukturu. Dva podobné kusy = coincidence. Tři = pattern.

## Výstup

Do `proposals/consolidation-to-core.md` napiš pro každý strong/medium kandidát kartu podle šablony v `report-format.md`. Do `summary.md` uveď TOP 5 s odkazem.
