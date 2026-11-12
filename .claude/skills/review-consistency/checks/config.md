# Check: konfigurace

Cíl: sjednotit konvence používání globálního `config.yaml` napříč core + pluginy. Vedlejší produkt: draft `proposals/config-style-guide.md`, pokud check najde dost konzistentního materiálu na sjednocující dokument.

## Kontext

Core i pluginy se konfigurují přes jediný `config.yaml`. Každý plugin má typicky vlastní top-level sekci (nebo pod-sekci, např. `sources.photos`). Cíl skillu: aby čtenář configu poznal styl "krizky", ne styl "krizky-photos vs krizky-json vs krizky-map".

## Postup

1. Vypiš top-level klíče, které core čte (grep `config.get(` v `krizky/`).
2. Pro každý plugin vypiš top-level klíče, které čte (grep `config.get(` a `photos_cfg.get(` apod. v `../krizky-<name>/`).
3. Zkontroluj níže uvedené checklisty. Zaznamenej zjištění per plugin.
4. Pokud najdeš ≥3 konzistentních konvencí, vygeneruj draft `proposals/config-style-guide.md`.

## Checklist

### Umístění a hierarchie
- [ ] Kam plugin ukládá své options? Top-level klíč (`filters:`), nested pod core klíč (`sources.photos`), nebo mix?
- [ ] Konzistence: mají všechny pluginy stejný vzorec (např. vždy top-level, nebo vždy pod `sources`)?
- [ ] Používá plugin jméno modulu jako klíč (`photos` pro `krizky-photos`)? Pokud ano, dělají to všechny?

### Pojmenování klíčů
- [ ] snake_case, kebab-case, camelCase — konzistentní?
- [ ] `output` vs `output_dir` vs `dest` — synonyma napříč pluginy?
- [ ] `enabled` vs `active` vs implicitní přítomnost sekce = zapnuto?
- [ ] `path` vs `file` vs `url` pro cesty a URL?
- [ ] Zkratky (`cfg`, `dir`, `id`) — jednotné napříč všemi klíči?

### Struktura hodnot
- [ ] Seznamy: `- key: value` vs `key: [...]` — konzistentní pro podobné věci?
- [ ] Mapy pojmenované vs indexované (např. `formats` v `krizky-photos` je list dictů — dělají to jiné pluginy stejně nebo mají `formats: {name: {...}}`)?
- [ ] Booleovské defaulty: implicitní `false`? implicitní `true`? Musí se explicitně nastavovat?

### Cesty a URL
- [ ] Cesty relativní k `config_dir`? Nebo absolutní? Nebo mix?
- [ ] URL: trailing slash? Bez? Jak se to řeší v core?
- [ ] Kdo dělá `.resolve()` — plugin, nebo pomocná funkce z core?

### Env vars a secrets
- [ ] `$VAR` interpolace — používají ji všechny pluginy pro citlivé hodnoty?
- [ ] Očekává se, že `$VAR` je cesta k souboru (jako `GDRIVE_ACCOUNT_KEY` v photos), nebo hodnota přímo? Konzistentní?
- [ ] Kde je popsané, jak env vars fungují (README pluginu, core README, oboje)?

### Defaulty a "vypnuto"
- [ ] Jak se plugin chová, když jeho sekce v configu chybí — no-op? Warning? Error?
- [ ] Explicitní defaulty (např. `contexts` v photos má implicit `{}`) — kde jsou uvedené (kód, README, config example)?
- [ ] `None` vs prázdný dict vs klíč chybí — konzistentní sémantika?

### Validace
- [ ] Ověřuje plugin schema configu? Kdy (při startu, líně)?
- [ ] Fail-fast nebo tolerance k chybějícím klíčům?
- [ ] Konzistentní typ chyby při špatném configu (custom exception, ValueError, `click.ClickException`)?

### Dokumentace configu
- [ ] Má každý plugin sekci "Konfigurace" v README s ukázkovým YAML?
- [ ] Ukázky používají stejné konvence (komentáře, formát env vars)?
- [ ] Je někde souhrn všech config klíčů core + pluginů (např. v core README)?

## Zvláštní pozornost

- **Kolize klíčů:** dva pluginy definují stejný top-level klíč → blocker.
- **Sémantický rozjezd:** dva pluginy použijí stejné jméno klíče (`output`) s jinou sémantikou (jeden = dir, druhý = file) → blocker.
- **"Project-specific" v pluginu:** plugin má hardcoded klíč, který dává smysl jen pro jeden konkrétní web (viz `checks/api-boundaries.md`).
