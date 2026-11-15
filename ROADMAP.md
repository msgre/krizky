# Roadmapa

Na začátku každé session si přečti sekci **Teď**, na konci ji přepiš. Podrobnosti hotové práce jsou ve `work/` a `work/OVERVIEW.md`.

## Cíl

1. **Obecný a vyladěný framework krizky** (core a pluginy), který jde nasadit i pro jiné zájmové weby, nejen pro Valašské nebe.
2. **Nová verze valasskenebe.cz postavená na krizky.** Je to reálný web s vlastním účelem a zároveň ukázka toho, co framework umí.

### Hranice: framework × web

- **Framework** (`krizky` a `krizky-*`) je obecný. Neobsahuje data, texty, barvy, souřadnice, šablony ani řešení, která dávají smysl jen Valašskému nebi.
- **Web** (`valasske_nebe_ng`) je reálný projekt a zároveň ukázka. Framework používá a dodává k němu všechno svoje: `config.yaml`, šablony, CSS a JS, transformace, data a případně `plugins/*.py`. Šablony a CSS jsou taky forma konfigurace webu.
- Když web něco potřebuje, nejdřív to řeší ve svých souborech. Do frameworku jde změna jen tehdy, když by dávala smysl i jinému webu. Pak ji formulujeme obecně, bez dat Valašského nebe.

Web je hlavní měřítko toho, co se ve frameworku ladí. Rozhodnutí, co do frameworku patří, ale dělá tahle hranice, ne potřeba webu.

## Teď

**Krok 1: Úklid stavu.** Další akce: dostat šablony a CSS webu do gitu (viz níže).

## Kroky

| # | Krok | Hotovo, když | Stav |
|---|---|---|---|
| 1 | Úklid stavu | Web má všechno své v gitu, letní práce je commitnutá, `OVERVIEW.md` a tahle roadmapa sedí | TODO |
| 2 | Web na core 0.2 | `valasske_nebe_ng` běží na aktuálním core a pluginech, má `scripts/verify` a `CLAUDE.md` a je připravený pro swarm | TODO |
| 3 | Blockery z revize | Opravené chyby viditelné na webu a dokumentace veřejného API | TODO |
| 4 | Nasazovací pipeline | Nový web se sám buildí v GitHub Actions a běží na zkušební adrese | TODO |
| 5 | Web funkčně kompletní | Nový web umí všechno, co starý, a TODO pro web je hotové | TODO |
| 6 | Spuštění | Na valasskenebe.cz běží nový web | TODO |
| 7 | Framework pro další weby | Nový web jde založit přes `krizky init` podle návodu, bez kopírování z Valašského nebe | TODO |

### 1. Úklid stavu

- [ ] **Šablony a CSS webu nejsou v žádném gitu.** `valasske_nebe_ng/templates` je symlink na `krizky/temp/templates` a `assets/css/style.css` na `krizky/tmp/style.css`. Oba adresáře core ignoruje (`.gitignore`). Přesunout je do `valasske_nebe_ng` a commitnout. Ve webu pak nezůstane žádný symlink do frameworku.
- [ ] **Zapsat hranici framework × web tam, kde ji čtou agenti, kteří kód píšou.** Dnes ji zná jen skill `review-consistency` (`checks/api-boundaries.md`), a to jen pro pluginy:
  - `docs/guidelines/`: nová sdílená guideline,
  - `CLAUDE.md` core a všech pluginů: odkaz na ni v sekci Pravidla projektu,
  - `valasske_nebe_ng/CLAUDE.md` (vzniká v kroku 2): role webu a postup, když web potřebuje změnu frameworku,
  - skill `review-consistency`: kontrolu rozšířit i na core.
- [ ] Commitnout letní práci ve `valasske_nebe_ng` (od 19. 7. necommitnutá) po logických celcích:
  - `pyproject.toml` a `uv.lock` (necommitnuté vůbec),
  - transformace: `typy` → `kategorie`, `umisteni_zkracene`, autoři fotek, automatické období z datace,
  - config pluginů: filters, map, share a json,
  - stažená data (`sources/`).
- [ ] **Pozor, existují dvě verze `style.css`.** Web dnes přes symlink čte starší `tmp/style.css` (12. 8., 31 788 B). Novější `temp/style.css` (16. 8., 32 117 B) se liší jen blokem přidaným na konec: přizpůsobení krizky-map tokenům webu (`.k-cluster`, `.k-panel-thumb`). **Platná je pravděpodobně ta novější.** Před přesunem potvrdit s uživatelem.
- Proč symlinky vznikly: uživatel si pamatuje jen potíže s vývojem ve více adresářích. Náhrada: práci na webu spouštět ve `valasske_nebe_ng`, nebo v session v core použít `/add-dir ../valasske_nebe_ng` (natrvalo přes `additionalDirectories` v `.claude/settings.json`).
- [ ] **Design manuál a podklady k návrhu** přesunout do `valasske_nebe_ng/design/` a doplnit `design/README.md` s popisem, odkud manuál pochází a co který soubor je. Zdroje manuálu:
  - projekt v Claude Design: https://claude.ai/design/p/682f8b89-8b5e-4be0-a2ec-f7e049f2eaef?file=uploads%2Fmanual.html&via=share
  - konverzace: https://claude.ai/share/9334ef70-14a6-4682-bf9d-11c376e6dec2

  Podklady dnes v core (vybrat platnou verzi, zbytek do archivu nebo smazat):
  - manuál ve třech podobách (stav zjištěný 2026-11-15):
    - `temp/manual.html` (17. 7., 76 KB) je shodný s `tmp/design_manual/uploads/manual.html`. Jde nejspíš o výchozí podklad nahraný do Claude Design.
    - `tmp/design_manual/Valašské nebe - Design manuál (standalone).html` (14. 8. 08:17, 808 KB) je export z Claude Design. Vedle něj jsou `uploads/` se dvěma screenshoty a `.thumbnail`.
    - `tmp/design_manual.html` (14. 8. 08:25, 826 KB) má stejný titulek, je o 8 minut novější a mírně větší. **Pravděpodobně jde o nejaktuálnější verzi.** Před smazáním ostatních ověřit s uživatelem, případně proti projektu v Claude Design.
  - `temp/fonts.css`,
  - návrhy: `tmp/filtrovani-mist-navrh.md`, `tmp/filtrovani.png`, `tmp/Redesign filtrovací dimenze.zip`, `tmp/kategorie-socha.html`, `tmp/socky.png`, `temp/ukazka_01.html` a `temp/ukazka_02.html`.
- [ ] Zbytek `krizky/temp/` a `krizky/tmp/` roztřídit:
  - patří webu: `temp/config.yaml` (starší kopie configu?), `temp/transforms/`, `tmp/focal_points.json`, `tmp/site.js` (shodný s webem),
  - archiv starého webu: `temp/predchozi_projekt/`, `temp/fotky/`,
  - zastaralé: `tmp/implement-review/`, `tmp/skills/` (staré verze skillů), `tmp/pyproject.toml`.

  Cíl: v `krizky/` nezůstane nic, co patří Valašskému nebi.
- [ ] `work/OVERVIEW.md`: zavřít zastaralé řádky („Review konzistence“ IN PROGRESS, fáze 5 Photos, fáze 6).
- [ ] `TODO.md`: platné položky jsou přenesené sem, soubor zrušit nebo nechat jen jako archiv.

### 2. Web na core 0.2

- [ ] `uv lock --upgrade` ve `valasske_nebe_ng` (dnes core `09af781`, tedy před 0.2, a pluginy ze srpna).
- [ ] Opravit šablony a config podle změn v pluginech (například přejmenované klíče stránkování ve filters, `data-filter-js-only`).
- [ ] `krizky build site` projde a výsledek ručně proklikat.
- [ ] Příprava pro swarm: `scripts/verify` (fetch nebo lokální data → transformace → build), `CLAUDE.md`, `.claude/settings.json` a ruleset na `main`.

### 3. Blockery z revize (`reports/2026-11-14-2156/`)

- [ ] Swarm „web“: `og:site_name` dostává nevykreslený `site.title` (share) a klíč `optimalizator` vs. `optimizer` (core `init`, `docs/sources.md`, photos).
- [ ] Swarm „docs“: `docs/plugins.md` (chybí `inject_*`, obrácené pořadí hooků, neexistující `JsonExportPlugin`), README core a filters (`paginate_by`).
- [ ] Swarm „hranice“: dostat z frameworku data a vzhled Valašského nebe (stav 2026-11-15):
  - krizky-map: výchozí střed `[49.4, 17.95]` a zoom 9 (`plugin.py:206`, `map.js:110`). Barva markeru `#850000`, která je `--brand` webu (`plugin.py:175`, `map.js:267`, `map.css:105`, `:137`).
  - krizky-map `map.css`: používá tokeny webu (`--ink`, `--muted`, `--hairline`, `--surface`, `--surface-2`, `--radius`, `--s3`–`--s5`, `--mono`). Jako fallbacky má přesně barvy palety Valašského nebe.
  - krizky-share `share.css`: stejné tokeny webu, tentokrát bez fallbacků, takže na jiném webu widget nemá barvy. README to přiznává: „CSS vychází z tokenů projektu Valašské nebe“.
  - **Rozhodnout:** každý plugin bude mít vlastní prefixované proměnné (např. `--krizky-map-ink`) s neutrálními výchozími hodnotami a web si je ve svém CSS namapuje na svoje tokeny. Nebo zavedeme sdílenou sadu obecných tokenů `--krizky-*` pro všechny pluginy.
  - Příklady v dokumentaci: README share (`valasskenebe.cz`, `@valasskenebe`), README map (`valassko.geojson`). Jako příklady jsou přípustné, ale lepší je `example.com`.
  - Core: v kódu nic, jen příklady v `CLAUDE.md` a `docs/sources.md` používají jména z webu (`vsechna_mista`, `tables.typy`). Nízká priorita.

### 4. Nasazovací pipeline

Starý web (`../valasske_nebe/.github/workflows/update.yml`):
- běží po každém push a každých 6 hodin,
- stáhne tabulky a metadata fotek a změny pozná přes `git diff`,
- fotky zpracuje a nahraje do R2,
- HTML commitne do `docs/`.

- [ ] **Rozhodnout:** orchestraci (stáhnout, poznat změny, zpracovat fotky, build) dělá jeden příkaz `krizky build` v core, nebo ji každý web skládá v YAML workflow sám. Viz PLAN.md › Logika kompletního buildu.
- [ ] Workflow pro `valasske_nebe_ng` a zkušební nasazení mimo hlavní doménu.

### 5. Web funkčně kompletní

- [ ] Porovnat se starým webem, co nový neumí (například data z OpenStreetMap, editor focal points, minifikace HTML).
- [ ] Panel filtrů jen s JS: do přebité `templates/_filter_widget.html` přidat `data-filter-js-only`.
- [ ] krizky-map: oddělit JS a statiku jako ve filters (bez JS mapa nefunguje).
- [ ] Detail: klik na GPS zkopíruje souřadnice do schránky.
- [ ] `sitemap.xml` a `robots.txt` (PLAN.md › Nedodělky).

### 6. Spuštění

- [ ] Přejmenovat fotky na R2: starý web používá `448-3.avif`, nový `448-3_big.avif`.
- [ ] Přepnout doménu na nový web a starý workflow vypnout.

### 7. Framework pro další weby

- [ ] `krizky init` vytvoří kostru, ze které jde rovnou buildit.
- [ ] Návod „nový web od nuly“ včetně workflow pro nasazení.
- [ ] Zásobník níže a nová revize konzistence.

## Zásobník

Nálezy recommended a nice-to-have z revize (`reports/2026-11-14-2156/summary.md`), návrhy v `proposals/` a guidelines k revizi. Bereme je, jen když blokují některý krok výše. Novou revizi pouštíme až po kroku 6.

## Pravidla

- Jedna session = jedna věc ze sekce **Teď**. Na konci session přepiš **Teď** a odškrtni hotové body.
- Detaily, které se objeví cestou, jdou do zásobníku, ne do aktuálního kroku.
