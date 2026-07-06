Chci s pomoci open source projektu datasette, sql-utils a jinja2 vytvorit system,
s jehoz pomoci budu generovat staticke stranky z Google tabulek, dokumentu a fotek
ulozenych na GDrive.

Prvni verzi projektu mam uz implementovanou a rozjetou na domene valasskenebe.cz

Nyni se snazim celou vec abstrahovat a vytvorit z ni univerzalni nastroj, s pomoci
ktereho by slo realizovat podobny typ stranek i pro jine spolky nez muzeum.

## Klicove komponenty

### Zdroj dat

- Google Sheet
- Google Docs
- Fotografie nahrane na Google Drive

S tabulkama jsou lidi z muzea zvykli pracovat, je to pro ne prirozene prostredi.
Stejne tak to plati i pro dokumenty. Diky integracim Google drive do systemu je 
jednoducha prace i s nim.

Jednotlive radky v tabulce reprezentuji mista sakralnich pamatek. Sloupce si
autori vymysleji sami. Domluvili jsme se na par pravidlech, jak udrzovat data
konzistentni a tech se drzi.

Jedno z hlavnich pravidel:
- radky se v tabulce nemazou, protoze cislo radku pouzivame jako ID zaznamu
- prvni sloupec tabulky vyjadruje, jestli je zaznam publikovan nebo ne

Fotografie na Google drive jsou pak pojmenovavany podle cisla radku:
- titulni fotka <id>.jpg
- doplnujic fotky do galerie <id>-<poradi>.jpg

Google tabulky jsou primarne pouzity pro zapis zaznamu, ktere pak prezentujeme
na webu. Vyuzivame ale i pomocne listy, tj. v hlavni tabulce mame napriklad sloupec
"typ", a hodnoty do nej vkladame prostrednictvim pomocneho listu "typy", ktery ma 2
sloupce: prvni se jmenem typu (ten se doplnuje do prvni tabulky) a druhy sloupec s
popisem typu. Ten slouzi posleze na webu jako uvodnik pri zobrazeni vsech zaznamu
spadajicich do dane kategorie.

Tabulky ale vyuzivame pro editaci drobnejsich fragmentu textu na webu. Typicky
jde o list klic->hodnota, kde mame texty jako claim do paticky, drobne napovedy,
apod. Pri generovani stranek se pak fragmenty vkladaji do konkretnich casti webu.
Diky tomuto principu si mohou dulezite casti webu autori spravovat sami.

Veskere Google zdroje jsou verejne dostupne na sdilene URL (jen pro cteni).

### Zpracovani dat

Ukazalo se, ze zdrojova data nejde vzit 1:1. Zpravidla byva potreba data vycistit,
prefiltrovat, nekdy zprocesovat konkretni sloupce (rozdelit na 2, vygenerovavat nove
pomocne sloupce na zaklade originalni hodnoty, apod).

Transformace jsou realizovany jako bash skripty, na ktere se odkazuje konfiguracni YAML.
Tento pristup zachovava plnou flexibilitu (mozno pouzit jakykoli nastroj — sqlite-utils,
pandoc, vlastni skripty) a zaroven drzi konfiguraci pohromade. Priklad obsahu transform
skriptu pro hlavni tabulku (ilustrace operaci; finalni skript pouziva parametry $1-$3
misto hardcodenych hodnot):

```bash
# novy import DB z CSV zdroje
sqlite-utils insert data.db krizky ./tabulka_upravena.csv --csv

# prevedeni obsahu sloupce Tagy na JSON list
sqlite-utils convert data.db krizky Tagy '[t.strip() for t in value.split(",")]'

# prevedeni NULL a '' hodnot ve sloupci Tagy na prazdny list
sqlite-utils data.db "update krizky set Tagy = '[]' where Tagy = '' or Tagy is null"

# prevedeni sloupce GPS na float sloupce latitude, longtitude
cat utils/gps_convert.py | sqlite-utils convert data.db krizky GPS --multi - --drop

# prevedeni sloupce "kdo fotil, kdy" na 2 samostatne: "autor" a "vytvoreno"
cat utils/author_date_convert.py | sqlite-utils convert data.db krizky "kdo fotil, kdy" --multi - --drop

# prejmenovani sloupcu
sqlite-utils transform data.db krizky --rename "Zveřejněno" "stav"
sqlite-utils transform data.db krizky --rename "typ: výklenková kaple /boží muka/ svatý obrázek/ výklenková socha/ kříž/ socha/ křížová cesta" "typ"
sqlite-utils transform data.db krizky --rename "příběh" "pribeh"
sqlite-utils transform data.db krizky --rename "Literatura" "literatura"
sqlite-utils transform data.db krizky --rename "Zdroj" "zdroj"
sqlite-utils transform data.db krizky --rename "Tagy" "stitky"
sqlite-utils transform data.db krizky --rename "Datace" "datace"
sqlite-utils transform data.db krizky --rename "Časové zařazení" "obdobi"
sqlite-utils transform data.db krizky --rename "poznámka" "poznamka"
sqlite-utils transform data.db krizky --rename "název (když je) / 
co je to" "nazev"
sqlite-utils transform data.db krizky --rename "umístění 
(obec, lokalizace)" "umisteni"

# smazani nepotrebnych sloupcu
sqlite-utils transform data.db krizky --drop "kdo navštívil, kdy 
(sem by se lidi mohli dopisovat či špendlíkovat)"
sqlite-utils transform data.db krizky --drop "foto"

# smazani dat, ktere nejsou urceny k publikovani (a sloupec stav je pak uz nepotrebny)
sqlite-utils data.db "DELETE FROM krizky WHERE stav = 'FALSE'"
sqlite-utils transform data.db krizky --drop "stav"

# --- pomocne sloupce pro snadnejsi generovani stranek ------------------------
# slug pro typ
cat utils/type_slug.py | PYTHONPATH=utils uv run sqlite-utils convert data.db krizky typ - --output typ_slug

# unikatni slug mista
sqlite-utils add-column data.db krizky slug text
uv run python utils/misto_slug.py

# slug pro tagy
cat utils/slug_stitky.py | PYTHONPATH=utils uv run sqlite-utils convert data.db krizky stitky - --output stitky_slug

# slug pro obdobi
cat utils/slug_obdobi.py | PYTHONPATH=utils uv run sqlite-utils convert data.db krizky obdobi - --output obdobi_slug
```

Vysledkem je SQLite databaze se cistymi daty vhodnymi pro generovani webu.

Orchestrator predava transform skriptum nasledujici poziční parametry:
- `$1` — cesta ke zdrojovemu souboru (napr. `sources/tables/data/source/data.csv`)
- `$2` — cesta k databazi (napr. `sources/data.db`)
- `$3` — jmeno tabulky v DB (odvozene od klice v konfiguraci, napr. `data`)
- `$4` — vystupni cesta; pro `tables` je to adresar (`sources/tables/data/transformed/`),
  pro `docs` je to plna cesta k vystupnimu souboru (`sources/docs/uvod/transformed/uvod.md`)
  odvozena z atributu `output`

Skripty pro `tables` vyuzivaji `$1`, `$2`, `$3`. Skripty pro `docs` vyuzivaji `$1` a `$4`.
Nepouzivane parametry ignoruji.

Atribut `transform` je pro zaznamy v `docs` povinny; atribut `output` specifikuje jmeno
vystupniho souboru a je rovnez povinny. Orchestrator po dokonceni transformace nacte
obsah `$4` a preda ho do sablony jako `{{ docs.uvod }}`.

#### Adresarova struktura zdrojovych dat

```
sources/
  data.db                          # sdilena SQLite databaze vsech tabulek
  tables/
    data/
      source/data.csv              # stazeny original z Google Sheets
      transformed/                 # vystup transform skriptu (volitelne)
    snippets/
      source/snippets.csv
      transformed/
  docs/
    uvod/
      source/uvod.docx             # stazeny original z Google Docs
      transformed/uvod.md          # vystup transform skriptu; jmeno = atribut output
```

Jmena souboru jsou odvozena od klice v konfiguraci — zadny dalsi atribut neni potreba.

Atribut `id` je ID Google Sheets dokumentu (z URL). Atribut `gid` je ID konkretniho
listu (tabulatoru) uvnitr dokumentu — jeden dokument muze obsahovat vice listu a `gid`
urcuje, ktery z nich se stahne.

Atribut `skip_rows` u tabulky rika, kolik uvodnich radku sheetu ma orchestrator
preskocit pred zpracovanim dat. Nektera Google Sheets maji na zacatku vysvetlujici
text a vlastni data zacinaji az na pozdejsim radku.

Zdrojove soubory se stahuji v nasledujicich formatech:
- Google Sheets → CSV (`.csv`)
- Google Docs → DOCX (`.docx`)

### Generovani webu

Zde se osvedcil sablonovy system Jinja2.

Kolem nich mam v prototypove verzi vymysleny kod, ktery podle dat a s pomoci sablon
generuje vysledne stranky (viz valasskenebe.cz).

Tohle bych chtel ale predelat, protoze system je navrzeny jen pro tento jeden projekt.
Myslim si ze to jde zabstrahovat a nasledne pouzit i jinde.

Napadl me tento zpusob: budeme mit jeden konfiguracni YAML soubor a v nem popsany jednotlive
klicove udaje.

Napadalo me toto:

```yaml

sources:
    output: ./sources
    database: data.db
    tables:
        data:
            id: "..."
            gid: "..."
            skip_rows: 3
            main: true
            transform: ./transforms/data.sh
        snippets:
            id: "..."
            gid: "..."
            key: key
            transform: ./transforms/snippets.sh
    docs:
        uvod:
            id: "..."
            transform: ./transforms/uvod.sh
            output: uvod.md
    photos:
        base_url: https://m.valasskenebe.cz
        source:
            type: gdrive
            folder_id: <id>
            account_key: $GDRIVE_ACCOUNT_KEY
            metadata: <cesta_k_json_file>
        destination:
            type: cloudflare
            bucket: <name>
            account_id: $CF_ACCOUNT_ID
            access_key_id: $CF_ACCESS_KEY_ID
            secret_access_key: $CF_SECRET_ACCESS_KEY
            metadata: <cesta_k_json_file>
        formats:
            - format: avif
              mime: image/avif
              quality: 60
            - format: webp
              mime: image/webp
              quality: 80
            - format: jpg
              mime: image/jpeg
              optimalizer: cjpeg
              quality: 80
        sizes:
            - name: micro
              max_width: 150
              quality:
                jpg: 82
                webp: 72
                avif: 52
            - name: thumb
              max_width: 330
              quality:
                jpg: 83
                webp: 74
                avif: 54
            - name: small
              max_width: 680
              quality:
                jpg: 85
                webp: 78
                avif: 58
            - name: medium
              max_width: 960
              quality:
                jpg: 85
                webp: 80
                avif: 60
            - name: big
              max_width: 1600
              quality:
                jpg: 90
                webp: 85
                avif: 65
site:
    base_url: https://valasskenebe.cz
    assets: ./assets
    output: ./docs/
    paginate_by: 10
    order_by: rowid
    ordering: desc
    templates: ./templates
    pages:
        homepage:
            query:
                limit: 10
            path: /index.html
            template: index.html
        all:
            path: /mista.html
            template: mista.html
        jenom_krize:
            query:
                condition: typ = 'kriz'
            path: /jenom-krize.html
            template: krize.html
        kategorie:
            category: typ
            path: "/<typ_slug>.html"
            template: kategorie.html
        obdobi:
            category: obdobi
            path: "/<obdobi_slug>.html"
            template: obdobi.html
        stitky:
            category: stitky
            many: true
            path: "/<stitky_slug>.html"
            template: stitky.html
        detail:
            detail: true
            path: "/<slug>.html"
            template: detail.html
```

### Secrets

Citlive hodnoty (API klice, tokeny) se v YAML souboru neuvadeji primo. Misto hodnoty
se uvede jmeno ENV promenne s prefixem `$` — orchestrator ji pri nacitani konfigurace
substituuje. Priklad viz atributy `account_key`, `account_id`, `access_key_id`,
`secret_access_key` v sekci `photos` vyse.

Lokalne se hodnoty udrzuji v souboru `.env` (ktery je v `.gitignore`):

```
# Google Drive
GDRIVE_ACCOUNT_KEY=

# Cloudflare R2
CF_ACCOUNT_ID=
CF_ACCESS_KEY_ID=
CF_SECRET_ACCESS_KEY=
```

V repozitari je verzovany pouze `.env.example` s prazdnymi hodnotami — slouzi jako
dokumentace toho, ktere promenne je potreba nastavit. V CI/produkci se promenne
nastavuji primo v prostredi (GitHub Actions secrets, apod.), `.env` soubor neni potreba.

V konfiguraci by byla oddelena sekce pro zdroje a pro vysledny web.
Sekce sources by resila v podstate jen download dat, pripadne jejich konverzi
(napr. docs na Markdown). Sekce site by generovala vysledne stranky.

Kazda sekce by se zpracovavala samostatnym modulem. Kazdy modul by umel
zpracovat jen to co se ho tyka (napr. ten co by se staral o zdroje by umel zpracovat
tables a docs, ten co by generoval web by se zase orientoval v paginate, pages, apod).
Konfigurace by ale byla sepsana v jednom velkem souboru, a nadrazeny orchestrator kod
by vzdy vyzobnul to co modulu patri a poslal mu to. Tim bychom si udrzeli oddeleni
modulu.

Atribut `main: true` musi byt uveden u prave jedne tabulky v sekci `sources.tables`.
Orchestrator tuto podminku validuje pri startu a pri poruseni odmitne pokracovat.

### Kontext Jinja2 sablon

V kazde sablone jsou dostupne nasledujici promenne:

- `{{ filtered }}` — zaznamy z hlavniho datasetu (`main: true`), potencialne zuzene
  query podmínkou definovanou v konfiguraci stranky; pokud stranka zadnou podmínku
  nespecifikuje, obsahuje kompletni hlavni dataset
- `{{ tables.X }}` — kompletni data tabulky X ze sekce `sources.tables`; standardne
  jde o list zaznamu indexovany cislem; pokud ma tabulka v konfiguraci atribut `key`,
  je misto toho prelozena na slovnik — hodnoty ze zadaneho sloupce se stanou klici
  a ke konkretnimu zaznamu se pristupuje pres ne (napr. `{{ tables.snippets.uvod }}`
  misto `{{ tables.snippets[0] }}`)
- `{{ docs.X }}` — obsah dokumentu X ze sekce `sources.docs` jako string

Na strankovaných strankách jsou navic k dispozici:

- `{{ page }}` — cislo aktualni stranky (1-indexed)
- `{{ total_pages }}` — celkovy pocet stranek
- `{{ has_prev }}` — boolean, zda existuje predchozi stranka
- `{{ has_next }}` — boolean, zda existuje nasledujici stranka
- `{{ prev_url }}` — cesta k predchozi strance (`None` pokud neexistuje)
- `{{ next_url }}` — cesta k nasledujici strance (`None` pokud neexistuje)

U category a stitky stranky je navic k dispozici:

- `{{ category }}` — aktualni hodnota z GROUP BY jako string (napr. `"kriz"` nebo
  `"priroda"`); reprezentuje kategorii, pro kterou se prave generuje stranka

U detail stranky je navic k dispozici:

- `{{ record }}` — single zaznam (objekt), pro ktery se prave generuje stranka;
  umoznuje primy pristup k polim bez indexovani (`{{ record.nazev }}` misto
  `{{ filtered[0].nazev }}`)

### Popis jedne sekce v sites

#### Homepage

```yaml
homepage:
    query:
        limit: 10
    path: /index.html
    template: index.html
```

Tohle rika, ze budeme mit stranku homepage. Do kontextu Jinja2 sablony se vlozi
promenna {{ filtered }}, ve ktere bude poslednich 10 zaznamu. Vysledna stranka
se vygeneruje s pomoci sablony index.html.

Viz sekci "Kontext Jinja2 sablon" vyse pro popis vsech dostupnych promennych.

#### Vsechna mista

```yaml
all:
    path: /mista.html
    template: mista.html
```

Zde bude v {{ filtered }} to same co v {{ tables.data }}.

#### Konkretni kategorie

```yaml
jenom_krize:
    query:
        condition: typ = 'kriz'
    path: /jenom-krize.html
    template: krize.html
```

Zde s pomoci podminky zuzime dataset ve {{ filtered }} pouze na ty zaznamy,
ktere maji ve sloupci typ hodnotu "kriz".

#### Automaticky generovane kategorie

```yaml
kategorie:
    category: typ
    path: "/<typ_slug>.html"
    template: kategorie.html
```

Tohle je jiny pripad nez ukazka v "Konkretni kategorie".

Zde je logika slozitejsi: s pomoci parametru "category" se definuje jmeno sloupce,
ze ktereho se s pomoci GROUP BY vytahnou vsechny non NULL a non "" zaznamy,
a pro kazdy z nich se vygeneruje samostatna stranka, ktera se pojmenuje podle sloupce
"typ_slug". V promenne {{ filtered }} budou jen ty zaznamy, ktere spadaji do zadane
kategorie. V promenne {{ category }} pak bude aktualni hodnota unikatni kategorie.

#### Automaticky generovane stitky

```yaml
stitky:
    category: stitky
    path: "/<stitky_slug>.html"
    template: stitky.html
```

Zde jde o variantu "Automaticky generovane kategorie".

Rozdil je v tom, ze hodnota ve sloupci "stitky" je seznam hodnot, namisto jednoducheho
retezce. Pokud takovouto situaci detekujes, budes iterovat nad jednotlivyma hodnotama
a resit je individualne podobne jako v pripade "Automaticky generovane kategorie".

Atribut `many: true` rika, ze hodnota ve sloupci `category` je JSON list namisto
jednoducheho retezce. Orchestrator iteruje nad jednotlivymi hodnotami v listu
a kazdu z nich zpracuje samostatne — stejne jako v pripade "Automaticky generovane
kategorie". Detekce tohoto chovani za behu se neprovadi; `many: true` je vyzadovana
explicitni deklarace.

Odpovidajici slug sloupec (`stitky_slug`) je JSON objekt, kde klicem je hodnota tagu
a hodnotou jeho slug. Napr.:

```json
{"příroda": "priroda", "kámen": "kamen"}
```

Orchestrator pri iteraci nad unikatnimi tagy vezme aktualni hodnotu kategorie
(`{{ category }}`), vyhledá ji jako klic v `stitky_slug` libovolneho zaznamu skupiny
a ziska slug pro sestaveni path.

#### Detail mista

```yaml
detail:
    detail: true
    path: "/<slug>.html"
    template: detail.html
```

Zde je klicovy parametr `detail: true`, ktery rika, ze pro kazdy zaznam z hlavniho
datasetu se vygeneruje samostatna stranka. Krome standardnich promennych je v sablone
dostupna promenna `{{ record }}` — single objekt aktualniho zaznamu.

### Strategie buildu

Generovani HTML stranek je vzdy plny rebuild — pri kazdem spusteni se pregeneruji
vsechny stranky od zacatku. Inkrementalni pristup neni implementovan, protoze
zmena jednoho zaznamu muze kaskadove ovlivnit detail, vsechny vypisy kde se zaznam
vyskytuje, i strankovani nasledujicich stranek. Plny rebuild ze SQLite pres Jinja2
je dostatecne rychly i pro tisice zaznamu.

Inkrementalni zpracovani je implementovano pouze pro fotky, kde je konverze formatu
a upload casove narocna operace (viz sekce Fotky).

### Assets

Adresar definovany klicem `assets` v sekci `site` se pri buildu kompletne zkopiruje
do vystupniho adresare (`output`). Vygenerovane stranky odkazuji na soubory v nem
(CSS, JS, fonty, obrazky) relativnimi cestami.

### Strankovani

Strankovani pujde nastavit globalne a pretizit v konkretni sekci. Budou k dispozici
parametry:

```yaml
paginate: true|false
paginate_by: <number>
```

Strankovani bude reseno na urovni jmena souboru. Prvni stranka zachova puvodni
nazev, dalsi stranky dostanou suffix s cislem:

- 1. strana: `<originalni_nazev>.html`
- 2. strana: `<originalni_nazev>-2.html`
- 3. strana: `<originalni_nazev>-3.html`
- atd.

### Metadata fotek

Metadata o fotkach na GDrive jsou JSON list objektu:

```json
[
  {
    "title": "432-3.JPG",
    "last_modified": "2026-07-05T10:51:45.061Z",
    "file_id": "1QK6cGznF6jyO5WlvT0ExDe9izfeAGiOH",
    "download_url_api": "drive:v3/files/1QK6cGznF6jyO5WlvT0ExDe9izfeAGiOH?alt=media",
    "row_number": 432,
    "subfolder_path": ""
  }
]
```

Metadata o fotkach na Cloudflare jsou JSON objekt, kde klicem je ID fotky
a hodnotou objekt s rozmerami jednotlivych velikostnich variant:

```json
{
  "057": {
    "micro":  {"w": 150,  "h": 199},
    "thumb":  {"w": 330,  "h": 439},
    "small":  {"w": 680,  "h": 1020},
    "medium": {"w": 960,  "h": 1440},
    "full":   {"w": 1600, "h": 2133}
  },
  "057-1": {
    "micro":  {"w": 150,  "h": 199},
    "thumb":  {"w": 330,  "h": 439}
  }
}
```

Rozmery slouzi k detekci, zda se definice velikostni varianty zmenila — pokud
fotka na CF existuje, ale ma jine rozmery nez aktualni konfigurace, je treba
ji pregenerovat. Datum vytvoreni by se hodilo pro uplnost, ale dostupnost
teto informace z CF API je nejista.

### Fotky

Fotky jsou s hlavnim datasetem propojeny pres cislo radku. Napr. fotka 123.jpg
patri k radku 123 a predstavuje hlavni titulni fotografii. K mistu je mozne
pridat vice fotek s pomoci suffixu s poradim, napr. 123-1.jpg, 123-2.jpg, apod.

Nas system bude fungovat takto:
- v repozitari si budeme drzet seznam fotek, ktere jsou ulozeny na gdrive
  (v JSON formatu)
- pri buildu se stahne aktualni seznam a porovna se s tim co mame ulozeny v repu
- pokud system detekuje nejake zmeny (nove fotky na gdrive, smazane fotky na gdrive,
  existujici fotka na gdrive s novejsim datumem posledni zmeny nez evidujeme),
  vyvola to procesovani fotky
- kazda fotka se prevede do nekolika ruznych formatu (viz klic formats)
  a velikosti (viz klic sizes); napr. fotka 123-1.jpg se prevede do:
  - 123-1_micro.jpg
  - 123-1_thumb.jpg
  - 123-1_small.jpg
  - 123-1_medium.jpg
  - 123-1_big.jpg
  - 123-1_micro.avif
  - 123-1_thumb.avif
  - 123-1_small.avif
  - 123-1_medium.avif
  - 123-1_big.avif
  - 123-1_micro.webp
  - 123-1_thumb.webp
  - 123-1_small.webp
  - 123-1_medium.webp
  - 123-1_big.webp
- pokud to bude vyzadovano, tak se vysledna fotka prozene jeste pres optimalizer
  (napr jpg pres cjpeg)
- vysledne fotky se uploadnou do destination (v prikladu cloudflare r2 bucket)
- pozor! system si bude udrzovat nejen seznam zdrojovych fotek na gdrive, ale i
  seznam vyslednych fotek na cloudflare; diky tomu pozna i situace, kdy je treba fotky
  z cloudflare smazat, nebo naopak doplnit jen nektere velikostni varianty ci formaty
  (predstav si situaci, ze pridame novy format, nebo novou velikostni variantu)
- v sablonach jinja2 pak budeme mit pomocne makro, s pomoci ktereho budeme
  v patricnych mistech generovat `<picture>` tag pozadovane velikosti
- u kazde velikostni varianty je uvedeno, jaka kvalita fotky se ma generovat pro kazdy
  z podporovanych formatu; pokud tam klic pro format nebude, bude se generovat podle defaultni
  kvality u formatu; pokud nebude ani tam, bude se generovat 100% kvalita

## CLI

Nastroj se jmenuje `krizky`. Vsechny prikazy prijimaji globalni flag `--config <path>`
(default: `config.yaml`).

```
krizky build                    # kompletni build
krizky build photos             # pouze fotky
krizky build site               # pouze HTML stranky (pouzije existujici DB)

krizky fetch sources            # stahne tabulky a dokumenty
krizky fetch sources --transform  # stahne a spusti transform skripty
krizky fetch photos             # stahne metadata o fotkach z GDrive a Cloudflare

krizky validate                 # overi config (schema, main: true, cesty ke skriptum)
krizky init                     # vytvori kostru noveho projektu
```

Flagy pro `build` prikazy:
- `--force` — preskoci detekci zmen, vynutí plny rebuild
- `--dry-run` — ukaze co by se stalo, nic neprovede

### Logika kompletniho buildu (`krizky build`)

1. Stahni metadata fotek z GDrive a Cloudflare
2. Stahni tabulky a dokumenty z Google
3. Porovnej fotky (GDrive metadata vs. Cloudflare metadata)
4. Porovnej zdroje (stazene soubory vs. git — `git diff`)
5. Pokud zadne zmeny → exit
6. Pokud zmeny ve fotkach → zpracuj a uploadni fotky
7. Pokud zmeny ve zdrojich → spust transform skripty → vygeneruj HTML

`krizky build site` predpoklada ze zdrojova data a SQLite DB uz existuji
(z predchoziho fetche nebo buildu).

## Nedodelky k doreseni

- **sitemap.xml a robots.txt** — rozhodnout zda a jak je generovat
- **`<picture>` makro** — specifikovat API makra pro generovani picture tagu v Jinja2 sabloně (parametry, navratova hodnota)
