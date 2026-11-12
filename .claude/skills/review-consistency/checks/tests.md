# Check: testy

Cíl: konzistentní struktura, styl a rozsah testů napříč projekty.

## Postup

1. Vypiš `tests/` obsah každého projektu (`ls tests/`).
2. Grep konfigurace: `[tool.pytest]` v `pyproject.toml`, `conftest.py`, `pytest.ini`.
3. Vzorek 2-3 test souborů z každého projektu (jméno, top-level struktura).
4. Projdi checklist.

## Checklist

### Layout
- [ ] `tests/` adresář v rootu každého projektu — všude?
- [ ] Zrcadlení struktury source kódu (`tests/test_render.py` ↔ `krizky/render.py`) — dodržené konzistentně?
- [ ] Podskupiny (unit vs integration, `tests/unit/`, `tests/integration/`) — všude nebo nikde?
- [ ] JS testy: `tests/js/*.test.mjs` přes `node --test`, jen čisté funkce (DOM se netestuje) — dodržené v pluginech s JS?

### Naming testů
- [ ] Test soubory: `test_<module>.py` — konzistentní?
- [ ] Test funkce: `test_<what>_<when>` (např. `test_render_page_with_pagination`) — konzistentní styl?
- [ ] Class-based testy (`class TestX`) vs volné funkce — konzistentní volba?

### Fixtures a conftest
- [ ] Sdílená fixture (např. `sample_config`, `tmp_db`) — je v `conftest.py`? Duplikuje se napříč projekty?
- [ ] Kandidát na consolidation-to-core: fixtura, kterou definují ≥2 projekty stejně nebo skoro stejně → do core `krizky.testing` (helper modul pro pluginy).
- [ ] Fixture naming: `tmp_config_dir`, `sample_data`, `built_site` — jednotné?

### Assertions
- [ ] `assert x == y` styl (pytest idiomatic) vs `unittest.TestCase.assertEqual` — konzistentní?
- [ ] Použití `pytest.raises` (nebo variace) — konzistentní pattern?
- [ ] Snapshot testing / golden files — kdo, kde?

### Coverage
- [ ] Existuje `pytest --cov` konfigurace v core? Používají to pluginy?
- [ ] Existují `.coveragerc` nebo `[tool.coverage.*]` sekce — konzistentně?

### Fixtures pro plugin testování
- [ ] Plugin, který se testuje, potřebuje fake core context (config dict, config_dir, conn, jinja env). Kdo tohle poskytuje? Duplikuje se? Existuje-li v core `TestingPluginManager` nebo obdoba — používají ho pluginy?

### Data
- [ ] Testovací data — inline v testech, `tests/fixtures/`, `tests/data/` — kde konzistentně?
- [ ] Velké fixture soubory (JSON, YAML, HTML) — jednotné umístění napříč pluginy?

### Brána `scripts/verify`
CI zatím není. Jedinou bránou je `scripts/verify` v každém repu.
- [ ] Spouští `verify` ve všech repech totéž (ruff, pytest; s JS i ESLint, Prettier a `node --test`)?
- [ ] Pluginy se testují proti core z GitHubu podle `uv.lock`. Je revize `krizky` v `uv.lock` stejná napříč pluginy?

### Značky
- [ ] `@pytest.mark.slow`, `@pytest.mark.integration` — registrované v konfigu, používané konzistentně?

## Zvláštní pozornost

- **Fixture, kterou má ≥2 pluginy shodně:** primární kandidát na `krizky.testing.<x>` v core → consolidation-to-core proposal.
- **Plugin bez testů:** flag jako `recommended` (ne blocker — testy nejsou vždy nutné, ale absence je znak drift).
- **Testy volají soukromá `_foo` core API:** flag — pokud plugin potřebuje sáhnout na private, buď je to znak chybějícího public API, nebo se testuje moc "dovnitř".
