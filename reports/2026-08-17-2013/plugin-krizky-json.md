# krizky-json — revize konzistence

Datum: 2026-08-17 20:13
Reviewer: Claude Code (review-consistency skill)

## Souhrn

- 0 blocker
- 3 recommended
- 2 nice-to-have

Nejdůležitější zjištění: Nejmenší plugin ekosystému (123 řádků, jediný soubor). Import `json as _json` je unikátní odchylka. Chybí logger, chybí `CLAUDE.md`, chybí `PLAN.md`. Testy duplikují `_make_db()` helper z core.

## Zjištění

### Python style

#### [recommended] `import json as _json` — unikátní alias mezi všemi plugin

**Kde:** `_plugins/krizky-json/krizky_json/plugin.py:21`

**Co:** Plugin importuje standardní `json` jako `_json`. Ostatní pluginy (photos, map, share) používají plain `import json` a používají ho pod jménem `json`. Alias byl asi zvolen, protože config sekce se jmenuje "json" a mohla by shadow module reference — ale v tomto souboru se `json` jako lokální jméno nikde nepoužívá.

**Proč vadí:** Nekonzistence pro čtenáře, který přechází mezi pluginy. Čtení `_json.dumps(...)` je matoucí (privátní alias?).

**Doporučení:** Přejmenovat na `import json` (bez aliasu). Alias má smysl jen kdyby se `json` v kódu používal jako lokální proměnná — v tomto souboru se nepoužívá.

#### [recommended] Chybí logger

**Kde:** `_plugins/krizky-json/krizky_json/plugin.py` (celý soubor)

**Co:** Plugin nemá žádnou logging setup. `photos`, `map`, `share` používají `_log = logging.getLogger(__name__)`. `filters` také nemá — takže json + filters jsou outliers.

**Proč vadí:** Když plugin selže tiše (např. špatný `fields` config → zapíše se prázdný objekt), uživatel nemá stopu. Konzistence napříč pluginy trpí.

**Doporučení:** Přidat modul-level `_log = logging.getLogger(__name__)`. Použít alespoň pro warning, když `json_cfg` je nekompletní (např. `fields` obsahuje neexistující sloupec).

### Dokumentace

#### [recommended] Chybí `CLAUDE.md` a v README nejsou hloubkovější příklady

**Kde:** projekt kořen

**Co:** README je stručné (67 řádků), pokrývá základ. Chybí `CLAUDE.md`. Chybí příklad, jak plugin používat v kombinaci s krizky-filters (filter potřebuje JSON export → přirozený párový use case).

**Proč vadí:** Konzistence s ostatními pluginy (viz photos/map — všechny bez CLAUDE.md; jen ekosystémový drobný problém). Chybějící cross-plugin dokumentace znesnadňuje ukázání "jak filters + json spolu tančí".

**Doporučení:** Přidat sekci "Kompatibilita" nebo "Použití s krizky-filters" do README. `CLAUDE.md` volitelně (pro tak malý plugin má menší přínos, ale konvenčně by tam mělo být).

### Testy

#### [recommended] Duplikát `_make_db()` helperu z core

**Kde:** `_plugins/krizky-json/tests/test_json_plugin.py:_make_db` (podle Explore evidence, ~30 řádků SQLite setup)

**Co:** Test helper je téměř identický s `_make_db()` v `tests/test_site.py` v core. Kdyby se změnilo schema tables (např. nový povinný sloupec `_meta`), musí se změnit ve všech kopiích.

**Doporučení:** Konsolidovat do `krizky.testing.make_db(...)` a importovat z pluginů. Viz `proposals/consolidation-to-core.md`.

### Konfigurace

#### [nice-to-have] Chybí explicitní seznam všech config klíčů v README

**Kde:** `_plugins/krizky-json/README.md:46-52` (má tabulku "Volby konfigurace")

**Co:** Existuje tabulka `fields`/`exclude`/`pretty`, ale `json:` samotný klíč (bez pod-klíčů) je zmíněný jen v příkladu. Jestli je `json: true` bez pod-klíčů validní zkratka, není řečeno.

**Proč vadí:** Kosmeticky. Uživatel při skenu configu neví, jestli lze psát `json: true` nebo `json: {}` nebo je potřeba minimálně `fields`.

**Doporučení:** Doplnit do tabulky řádek pro `json:` samotné (co znamená přítomnost prázdné sekce vs. sekce s hodnotami). Nebo v příkladu zmínit minimum.

### Hooky

#### [nice-to-have] Plugin používá jen 1 hook (`after_page_written`)

**Kde:** `_plugins/krizky-json/krizky_json/plugin.py:103-119`

**Co:** Není to problém — plugin dělá jednu věc (sidecar JSON) a nepotřebuje víc. Zmiňuji jen pro úplnost matrice hooků v souhrnu.

**Doporučení:** Nic. Držet tak, jak je.
