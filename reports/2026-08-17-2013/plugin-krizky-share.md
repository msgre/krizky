# krizky-share — revize konzistence

Datum: 2026-08-17 20:13
Reviewer: Claude Code (review-consistency skill)

## Souhrn

- 0 blocker
- 5 recommended
- 2 nice-to-have

Nejdůležitější zjištění: CSS design tokeny (`--surface`, `--hairline`, ...) coupling na projekt Valašské nebe explicitně dokumentovaný v README — nejsilnější "project-specific leakage" v ekosystému. Vlastní `_esc()` HTML escape helper (Python) místo standardní `html.escape` z stdlib. Duplikát `_copy_assets`/template registrace patternu (viz consolidation proposal).

## Zjištění

### Hraniční API (project-specific leakage)

#### [recommended] CSS design tokeny bez `--krizky-*` prefixu — leakage projektu Valašské nebe do obecného pluginu

**Kde:** `_plugins/krizky-share/krizky_share/assets/krizky-share/share.css` + `README.md:122-124`

**Co:** Plugin CSS používá tokeny `--surface`, `--hairline`, `--muted`, `--ink`, `--radius`, `--mono`, `--brand`. README výslovně říká: "CSS vychází z tokenů projektu Valašské nebe. Pokud tvůj projekt tyhle proměnné nemá, komponenty budou vypadat jinak."

**Proč vadí:** Plugin dokumentuje coupling na konkrétní projekt. Fallback hodnoty existují (dobrá zpráva), takže nefunguje "totálně divně" bez tokenů, ale styling předpokládá cizí design system. Kdyby uživatel použil jméno tokenu jinak (`--surface: red;`), plugin se rozpadne s jeho vlastními stylistickými očekáváními.

**Doporučení:** Dvě cesty:
1. **Prefix `--krizky-share-*`**: plugin definuje vlastní tokeny s defaulty, uživatel je může přebít. `--surface` fallback můj bude `var(--krizky-share-surface, var(--surface, #FAF8F3))`.
2. **Přijmout coupling jako záměr**: aktualizovat README, aby explicitně řeklo "plugin vyžaduje X tokenů — pokud je nemáš, definuj je". Přestat zmiňovat Valašské nebe (to je artefakt vývoje, ne dokumentace).

Preferuji (1) — plugin je obecný produkt, ne extenze Valašského nebe.

### Python style

#### [recommended] Vlastní `_esc()` HTML escape místo `html.escape` ze stdlib

**Kde:** `_plugins/krizky-share/krizky_share/plugin.py:164-172`

**Co:** Plugin má lokální helper:
```python
def _esc(value: str) -> str:
    return str(value).replace("&", "&amp;").replace('"', "&quot;")...
```
Standardní `html.escape(s, quote=True)` dělá totéž (`&`, `<`, `>`, `"`, `'`). Vlastní implementace je horší (nezpracuje `'`).

**Proč vadí:** Reinvent wheel bez důvodu. Nesourodé s core (core používá Jinja2 escape, ale pro `inject_head` output nemá helper — protože do teď to nikdo nepotřeboval).

**Doporučení:** `from html import escape as _esc` (nebo přímo použít `html.escape(v, quote=True)`).

#### [recommended] Chybí `CLAUDE.md`

**Kde:** projekt kořen

**Co:** Konzistentně chybí napříč pluginy.

**Doporučení:** Přidat minimální `CLAUDE.md` s: struktura kódu (`networks.py`), jak testovat, konvence pro přidání nové sítě.

### Duplikace (viz consolidation proposal)

#### [recommended] Template registrace, `_copy_assets`, `_PLUGIN_DIR` konstanty

**Kde:** `_plugins/krizky-share/krizky_share/plugin.py:16-19` (konstanty), `plugin.py:68-78` (template registrace), `plugin.py:151-161` (copy assets)

**Co:** Stejné patterny jako v map a filters — viz `plugin-krizky-map.md` a `proposals/consolidation-to-core.md`.

**Doporučení:** Řešit centrálně jednou pro všechny 3 pluginy.

### Konfigurace

#### [recommended] `share.default_image` má implicit "relativní k base_url" chování — dokumentovat

**Kde:** `_plugins/krizky-share/krizky_share/plugin.py:116-121`, README `README.md:23`

**Co:** Kód dělá:
```python
if base_url and default_image.startswith("/"):
    default_image = f"{base_url}{default_image}"
```
Tj. leading slash → auto-prefix base_url. Absolutní URL (`https://...`) proteče. README to zmiňuje ("relativní k base_url"), ale nezmiňuje, že jinak string proteče as-is.

**Proč vadí:** Uživatel zadá `default_image: /assets/og.jpg` bez `base_url` v configu → dostane doslova `/assets/og.jpg` v `og:image` meta tagu (což OG scrapery neradi). Nefail, ale silent gotcha.

**Doporučení:** Buď (a) warn, když `default_image` je relativní a `base_url` chybí; nebo (b) explicit v README: "Pokud nemáš `base_url`, `default_image` musí být absolutní URL."

### JavaScript style

#### [nice-to-have] Hardcoded Czech UI: "Zkopírováno"

**Kde:** `_plugins/krizky-share/krizky_share/assets/krizky-share/share.js:38`

**Co:** Feedback text po kopírování odkazu. Napevno v JS.

**Doporučení:** Volitelné — konzistentní s map/filters (všechny mají hardcoded CZ). Řešit až se udělá i18n mechanismus napříč.

### Naming a data

#### [nice-to-have] Site config `share.networks` používá plurál, plugin interně `_share_links` singulár

**Kde:** `_plugins/krizky-share/README.md:22`, `plugin.py:22`

**Co:** Config klíč je `share.networks` (list sítí). Funkce, která vrací sdílecí odkazy, se jmenuje `_share_links`. Uvnitř dictu položka má klíč `"network"` (singulár). Není to špatně, ale drobná nesouladnost sing/plur napříč.

**Doporučení:** Kosmeticky. Nechat, jinak by změny prosákly do API.
