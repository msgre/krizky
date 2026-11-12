# Check: pojmenování v datech

Cíl: identická sémantika = identické jméno, napříč SQL sloupci, dict klíči, config klíči, URL parametry, JS data-atributy.

## Postup

1. Prohlédni core `db.py`, `query.py` — jaké klíče generuje pro record dicty.
2. Grep `record["`, `record.get(` napříč pluginy — jaká pole tam očekávají.
3. Grep photo dict klíče, page dict klíče — konzistentní vs plugin-specific.
4. Zaznamenej mapování "sémantika → jméno" a najdi rozjezdy.

## Checklist

### Identifikátory záznamu
- [ ] `row_number` (interní pořadové), `id`, `slug`, `key` — každé má jasnou sémantiku?
- [ ] Photo dict používá `base_name` — ostatní strukturované entity (record, category, tag) používají analogické jméno pro "primary key" nebo něco jiného?
- [ ] URL slug: `slug` — konzistentně napříč záznamy? Nebo někde `handle`, `permalink`, `path`?

### URL a cesty
- [ ] URL: `url` vs `href` vs `link` — sjednocené?
- [ ] Absolutní vs relativní URL — vlastnost objektu, nebo se řeší v šabloně?
- [ ] Path v souborech: `path` vs `filepath` vs `file_path`?
- [ ] Adresář: `dir`, `folder`, `directory`?

### Kategorie a tagy
- [ ] Category klíč se jmenuje `category`, `cat`, `kategorie`? Konzistentní napříč pluginy, které to čtou?
- [ ] Tag — plural (`tags`) i single (`tag`) — konzistentní?

### Datum a čas
- [ ] `created_at`, `updated_at`, `date`, `datetime`, `timestamp` — sémantika každého jasně vymezená?
- [ ] Ve stringu (ISO) vs objekt (datetime) — konzistentní typ napříč místy?

### Metadata a extra
- [ ] `meta` vs `metadata` vs `extra` vs `attrs` — konzistentní volba pro "další data"?

### Photo dict (napříč `photos()` a JS)
Photo container ze `photos(row_number)` má klíče `primary`, `additional`, `all`, `count`, `has_photos`. Photo dict má `base_name`, `src`, `srcset`, `sources`, `variants`, `width`, `height`, `focal_point`.
- [ ] Používá kterýkoli plugin (JS nebo Python) jiné pojmenování pro tytéž věci?
- [ ] `has_photos` (bool s `has_` prefix) — jiné bool klíče používají stejný prefix, nebo někde `is_x`, někde bez prefixu?

### Config klíče vs data klíče
- [ ] Pokud config klíč (např. `output`) a data pole (např. `output_path`) souvisí, jsou pojmenovány konzistentně (společný prefix, jasná vazba)?

### Data attributes v JS ↔ šablony
- [ ] `data-share-url` v šabloně → `dataset.shareUrl` v JS — jméno je shodné (jen kebab vs camel)?
- [ ] Prefix pluginu (`data-share-*`, `data-filter-*`) — dodržený všude?

## Zvláštní pozornost

- **Kolize sémantiky:** dva pluginy použijí `key` pro jinou věc → matoucí čtenáři. → recommended.
- **Sémantický overload:** stejné jméno (`slug`) používané pro záznam, kategorii i URL fragment — pokud každé má jiný obor hodnot, může to způsobit bug. → flag jako recommended, doporuč rozlišit prefixem (`record_slug`, `category_slug`, `url_slug`) nebo dokumentací.
