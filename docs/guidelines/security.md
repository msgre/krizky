# Guidelines: security

Load jen když finding dotýká: HTML output, SQL query, path handling, subprocess, external API calls, nebo secrets.

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

Když plugin resolve-uje cesty ze user config:

```python
def resolve_path(user_path: str, config_dir: Path) -> Path:
    p = Path(user_path)
    if p.is_absolute():
        return p  # user explicit
    resolved = (config_dir / p).resolve()
    # Sanity check: konečná cesta musí být pod config_dir (žádné ../)
    if config_dir.resolve() not in resolved.parents and resolved != config_dir.resolve():
        raise ValueError(f"Path escapes config_dir: {user_path}")
    return resolved
```

- Použij `Path.resolve()` k normalizaci.
- Zkontroluj, že výsledek je pod `config_dir` — jinak `..` mohou dostat plugin mimo scope.
- Výjimka: absolutní cesty user explicitně zadal — ne blokovat.

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

## Skill enforcement

Skill při každé změně souboru, který spadá do security-relevant kategorií (HTML/SQL/subprocess/API), **rychle projede checklist**:

- Pattern `.replace("&", "&amp;")` → warning, refactor na `html.escape`.
- Pattern `f"...{var}..."` v SQL context → **stop**, refactor na parametrizovaný.
- Pattern `yaml.load(` bez `safe_load` → **stop**, refactor.
- Pattern `shell=True` v subprocess → warning, refactor pokud user vstup.
- Pattern `pickle.load(` na user data → **stop**, refactor nebo zamítni.
- Pattern `requests.<method>(url` bez `timeout=` → warning, přidat timeout.

Pokud finding sám je security-related (např. "krizky-share používá ruční escape místo html.escape") → skill je gramotný to opravit dle výše.

Pokud finding **není** security-related, ale při editaci skill zahlédne security anti-pattern → **flag do output** (spotted, not fixed), NErefactor mimo scope.
