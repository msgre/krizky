# krizky-photos — revize konzistence

Datum: 2026-08-17 20:13
Reviewer: Claude Code (review-consistency skill)

## Souhrn

- 1 blocker
- 4 recommended
- 2 nice-to-have

Nejdůležitější zjištění: photos je jediný plugin s CLI. Vyhazuje `click.ClickException` z `prepare_jinja2_environment` hooku, který nemusí běžet v Click kontextu → potenciální leak Click abstrakce. `FetchError` má stejné jméno jako core `FetchError` (kolize). Chybí `CLAUDE.md`.

## Zjištění

### Hooky

#### [blocker] `click.ClickException` vyhazován z hooku, který nemusí běžet v Click kontextu

**Kde:** `_plugins/krizky-photos/krizky_photos/plugin.py:56-59`

**Co:** V `prepare_jinja2_environment` (build hook, ne CLI hook) plugin chytá `FocalPointsError` a přepakuje ho jako `click.ClickException`. Pokud by hook někdy běžel mimo Click CLI (např. programový build API, testy, budoucí web UI), tato výjimka nebude vlídně vyrenderovaná — pluggy ji předá dál, Click ji nezachytí, uživatel dostane raw traceback.

**Proč vadí:** Plugin API by nemělo být coupled na jeden konkrétní frontend. `prepare_jinja2_environment` je build hook, ne CLI hook — a měl by vracet plugin-vlastní chyby.

**Doporučení:** Přepakovat na plugin-vlastní chybu (`FocalPointsError` samotný nebo `PhotosError` obecně). CLI handler (v `register_commands`) chybu chytí a přepíše na `click.ClickException` — to je jeho zodpovědnost.

### Error handling a logging

#### [recommended] Kolize jmen: `FetchError` v pluginu vs core

**Kde:** `_plugins/krizky-photos/krizky_photos/fetch.py:10`, kolize s `krizky/fetch.py:13`

**Co:** Viz `core.md` sekce Python style. Plugin má vlastní `FetchError`, core má taky `FetchError`. Různé sémantiky, stejné jméno.

**Doporučení:** Přejmenovat plugin verzi na `PhotoFetchError` (nebo `GDriveFetchError`). Preferuji tuto stranu — core jméno je master, plugin se má odlišit.

#### [recommended] CLI chybové handlery používají `SystemExit(1)` místo `click.ClickException`

**Kde:** `_plugins/krizky-photos/krizky_photos/plugin.py:104, 113, 126, 135`

**Co:** V `register_commands` handler dělá:
```python
click.echo(click.style(f"ERROR: {exc.message}", fg="red"))
raise SystemExit(1) from None
```
Ale `prepare_jinja2_environment` používá `raise click.ClickException(str(exc))`. Dva různé fail styly pro Click-based chyby v jednom pluginu.

**Proč vadí:** Nesourodý fail-mode. `ClickException` má vlastní pretty printing, exit code a message. Ruční `click.echo` + `SystemExit(1)` obchází to.

**Doporučení:** Sjednotit na `click.ClickException` v CLI handleru. Pro non-CLI kód použít plugin-vlastní výjimky (viz blocker výše).

### Python style

#### [recommended] Lazy imports uvnitř metod bez konzistentního pravidla

**Kde:** `_plugins/krizky-photos/krizky_photos/plugin.py:36` (`from krizky_photos.context import PhotoContext`), `plugin.py:93` (`from krizky.config import ConfigError, load_config`), `plugin.py:106` (`from krizky_photos.fetch import FetchError, fetch_gdrive_metadata`), `plugin.py:128` (`from krizky_photos.build import PhotoError, build_photos`)

**Co:** Photos používá lazy imports uvnitř metod hooků/CLI handlerů. Ostatní pluginy importují nahoře modulu. Není zřejmé, jestli jde o performance optimalizaci (import je pomalý → odkládat), nebo dependency cycle avoidance, nebo náhoda.

**Proč vadí:** Bez explicitního důvodu je to nekonzistentní vůči zbytku ekosystému. Nový přispěvatel neví, jestli lazy import zopakovat, nebo importovat nahoře.

**Doporučení:** Pokud důvod je "import je pomalý (google-api-client startup)", uvést v komentáři. Jinak přesunout imports nahoře modulu.

### Dokumentace

#### [recommended] Chybí `CLAUDE.md`

**Kde:** projekt kořen (očekáváno vedle `README.md` a `PLAN.md`)

**Co:** Plugin nemá `CLAUDE.md` s pokyny pro Claude Code. Core `CLAUDE.md` popisuje globální konvence, ale plugin-specific věci (jak spustit fotky test suite, jak přidat novou format variantu, jak testovat R2 upload) by se hodily.

**Proč vadí:** Nekonzistence napříč ekosystémem — CLAUDE.md je konvence, kterou zavedl core, a pluginy by měly následovat.

**Doporučení:** Přidat minimální `CLAUDE.md` (~30-50 řádků) s: struktura kódu, jak spustit testy, jak přidat novou format/size variantu, konvence naming fotek (`007.jpg`).

### Konfigurace

#### [nice-to-have] Config path resolution je duplikovaná v `focal.py` a v core (jinde v pluginu i v `krizky-map`)

**Kde:** `_plugins/krizky-photos/krizky_photos/focal.py` (`load_focal_points` s vlastním resolvingem cesty), viz i `_plugins/krizky-map/krizky_map/plugin.py:361-368` (`_resolve_source_path`)

**Co:** Foto plugin řeší "cesta relativní ke `config_dir`" pro `focal_points` config klíč. Map plugin řeší totéž pro `mask.polygon` a `overlays[].source`. Jiná implementace, stejný logic.

**Proč vadí:** Duplikace + drobné rozdíly (photos má fallback default cestu, map ne).

**Doporučení:** Konsolidovat do `krizky.config.resolve_path(path, config_dir)`. Viz `proposals/consolidation-to-core.md`.

### Testy

#### [nice-to-have] Testy `plugin.py` mají jen 97 LOC vůči 610 LOC celkem

**Kde:** `_plugins/krizky-photos/tests/test_plugin.py`

**Co:** Většina test volumu je na helper modulech (`test_build_photos.py` 196, `test_photo_context.py` 171, `test_focal.py` 146). Vlastní hook implementace v `plugin.py` má nejmenší pokrytí. Není to samo o sobě problém — hooky se hodně "propojují" a testují se end-to-end.

**Proč vadí:** Kosmeticky. Pokud přidáváš nový hook, chceš snadno vidět, jak se testuje.

**Doporučení:** Volitelné. Zvážit přidání end-to-end testu, který ověří, že `inject_head` vrací correct payload při zapnutém/vypnutém photos configu.
