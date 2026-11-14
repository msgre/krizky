# Guidelines: security

Platí pro HTML výstup, SQL, cesty z configu, subprocess, externí API a secrets.

## HTML/XSS escape

- **Jinja2 templates:** autoescape musí být ON (v core je default). Pokud plugin registruje vlastní env, ověř `autoescape=True`.
- **Python string → HTML:** vždy `html.escape(value, quote=True)`, nebo přes Jinja2 (`markupsafe.escape`). **Nikdy** ruční `.replace(...)` — vynechá edge cases (např. `'`).
- **JS → DOM insertion:** `textContent` pro plain text. `innerHTML` **pouze** pro contentem, který **generuje sám plugin** (ne uživatelská data). Když opravdu potřebuješ HTML z uživatelských dat → DOMPurify.
- **JSON → JS injection (přes `<script>`):** `json.dumps(data, ensure_ascii=False)` — output je bezpečný, pokud `data` neobsahuje speciální stringy s `</script>`. Konzervativně: `data_json.replace("</", "<\\/")` v templateu.

## SQL injection

- **Vždy parametrizované queries.** `conn.execute("SELECT * FROM t WHERE x = ?", (value,))`.
- **Nikdy** f-string do SQL: `conn.execute(f"SELECT * FROM t WHERE x = '{value}'")` — SQL injection.
- **Dynamické jméno tabulky/sloupce:** whitelist match, ne string concat. Např. `if col not in ALLOWED_COLS: raise ValueError`, pak `f'SELECT "{col}" FROM t'` (jméno OK zvenku ne, jméno OK po whitelistu).

## Path traversal

**Cesty z configu** jsou důvěryhodné. `config.yaml` píše vlastník webu a krizky ho spouští nad vlastním projektem. Plugin je převádí přes `resolve_path` z `krizky.plugin_helpers`: relativní cesta se vyhodnotí vůči `config_dir`, absolutní zůstane, `..` se neblokuje.

**Cesty odvozené z dat** (slug záznamu, jméno souboru z Google Drive, hodnota z tabulky) důvěryhodné nejsou. Data může upravovat i někdo jiný než vlastník webu. Výsledná cesta po `Path.resolve()` musí ležet uvnitř cílového adresáře (typicky výstupu webu), jinak chyba:

```python
target = (output_dir / f"{slug}.html").resolve()
if not target.is_relative_to(output_dir.resolve()):
    raise FooError(f"Path escapes output directory: {slug!r}")
```

## Subprocess

- `subprocess.run([cmd, arg1, arg2], check=True, capture_output=True)` — list arguments, ne shell string.
- **Nikdy** `subprocess.run(f"cmd {user_input}", shell=True)` — command injection.
- Pokud opravdu potřebuješ shell, `shlex.quote(user_input)`.
- Explicit `check=True` — nefail silently.

## External APIs a secrets

- **Secrets v log:** neloguj hodnoty env vars ani config klíčů, které vypadají jako secret (klíče končící `_key`, `_token`, `_secret`, `_password`, `_credentials`, `access_key_id`, `bucket_key`).
- **Traceback:** exception message může leakovat secret, když ho konstruuješ z API response. Sanitize.
- **HTTPS only:** requests na external URL musí být `https://`, ne `http://` (i pro CDN). Fetch specific URL s HTTP → validate URL nebo zamítni.
- **Timeouts:** `requests.get(url, timeout=(3, 30))` — všechny externí volání s timeoutem. Bez timeoutu můžeš viset navěky.

## Deserializace

- **JSON:** OK, native Python `json.loads()` je bezpečný.
- **YAML:** `yaml.safe_load()`, **nikdy** `yaml.load()` (arbitrary code execution).
- **Pickle:** **nikdy** unpickle user-provided data — arbitrary code execution.
