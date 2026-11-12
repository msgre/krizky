# Check: dokumentace

Cíl: každý projekt má stejnou "kostru" dokumentace, ve stejné hloubce. Čtenář nemusí hádat, kde co najde.

## Postup

1. Vypiš dokumenty v rootu každého projektu (`README.md`, `CLAUDE.md`, `docs/*`; v core navíc `PLAN.md` a `work/*`).
2. Pro README: přečti nadpisy (`grep '^#' README.md`).
3. Projdi checklist.

## Checklist

### Přítomnost základních dokumentů
- [ ] `README.md` — má každý projekt.
- [ ] `CLAUDE.md` — má každý projekt. Pluginy ho dostaly přes `/swarm:init` se stejnou kostrou (Ověření, Pravidla projektu, Git, Swarm).
- [ ] `PLAN.md` — v core commitnutý: je aktuální? V pluginech je lokální a v `.gitignore`, nehlas.
- [ ] `TODO.md` je všude lokální a v `.gitignore`, nehlas.
- [ ] `LICENSE` — přítomná?
- [ ] Změny (`CHANGELOG.md`, `HISTORY.md`) — existují? Konzistentní formát?

### README struktura
Ideál: každé README má stejnou kostru sekcí ve stejném pořadí. Ověř:
- [ ] `# <název>` s jednořádkovým popisem
- [ ] Krátký odstavec: co plugin dělá
- [ ] `## Instalace` (pip install / uv add)
- [ ] `## Konfigurace` (config.yaml sekce) — jazyk a formát ukázek konzistentní?
- [ ] `## Použití` nebo `## CLI příkazy` (pokud plugin přidává příkazy)
- [ ] `## Šablony` nebo API pro Jinja (pokud plugin exponuje globals/filtery/makra)
- [ ] `## Vývoj` (jak spustit testy, konvence commitů)

Odchylky → recommended.

### Rozdělené dokumenty
- [ ] Který plugin má `docs/` složku a proč? (Např. `krizky-filters/docs/` — je tam co? Je to potřeba?)
- [ ] Pravidlo pro "kdy README → kdy docs/": stačí nekonzistence, aby to bylo finding, ale doporuč spíš pragmatické pravidlo (`docs/` když README přesáhne ~500 řádků).

### Jazyk
- [ ] Uživatelské docs (README, PLAN, docs/, work/) — český. Kód a docstringy — anglický. Ověř dodržení napříč pluginy.
- [ ] Diakritika — správně, konzistentní?

### `work/` log konvence
Logy se píšou jen do core `work/`, i za práci v pluginech a za běhy swarmu. Pluginy vlastní `work/` nemají a jejich `CLAUDE.md` odkazuje na core.
- [ ] Formát `work/YYYY-MM-DD-NN-HESLO.md` — dodržený?
- [ ] `work/OVERVIEW.md` — aktualizovaná tabulka fází?
- [ ] `CLAUDE.md` každého pluginu odkazuje na core `work/` a `OVERVIEW.md` správnou cestou?

### Aktuálnost vůči kódu (viz `docs-sync.md`)
- [ ] README config example — je pořád validní vůči tomu, co plugin skutečně čte?
- [ ] README CLI commands sekce — obsahuje všechny commands, které plugin registruje?
- [ ] Docstring `KrizkySpec.<hook>` — reálná signatura hook implementací se shoduje?
- [ ] Zmíněné funkce/makra existují (`_picture.html` makro popisované v README existuje)?

### Cross-reference
- [ ] README pluginu odkazuje na krizky repo — konzistentní link, správný URL (`https://github.com/msgre/krizky`)?
- [ ] Core README zmiňuje ekosystém pluginů? Aktualizovaný seznam?

### Docstring vs README overlap
- [ ] Doc v docstringech (API reference) se nesmí příliš rozjíždět s README (user guide) — pokud README popisuje jinak, než jak funkce reálně funguje, → blocker (docs lžou).

## Zvláštní pozornost

- **CLAUDE.md v pluginu:** vychází ze šablony `/swarm:init`. Hlídej, aby úvodní odstavec popisoval daný plugin a cesty ke guidelines a `work/` seděly.
- **README hlavičkový odstavec:** používají všechny pluginy shodnou formulaci "Plugin pro [X] do krizky"? Menší věc, ale recommended pro dojmovou konzistenci.
