# Kontrola: testy

Cíl: testy všech projektů mají stejnou strukturu a styl a pokrývají veřejné API.

Pravidla jsou v `docs/guidelines/python.md` › Pytest a › Test coverage. Styl, který hlídá ruff (`PT`), se nehlásí.

## Postup

1. Vypiš `tests/` každého projektu a `conftest.py`.
2. Porovnej `[tool.pytest*]` v `pyproject.toml` napříč repy.
3. Z každého projektu přečti dva až tři testové soubory.
4. Porovnej fixtury a pomocné funkce napříč projekty (`grep -rn "@pytest.fixture\|^def make_\|^def _make" */tests/`).

## Pravidla

- Projekt bez testů → **recommended**.
- Veřejná funkce nebo hookimpl bez testu → **recommended**.
- Testy jako třídy (`class TestX`), jména mimo `test_<co>_<podmínka>`, ruční `tempfile` místo `tmp_path` → **nice-to-have**.
- Fixtura definovaná znovu v jednotlivých souborech místo v `conftest.py` → **nice-to-have**.
- Stejná fixtura nebo pomocná funkce (testovací databáze, config, Jinja prostředí) ve dvou a více projektech → **recommended**, karta do `proposals/consolidation-to-core.md` (skupina duplicita).
- Test mockuje interní kód místo hranice (síť, Google API) → **recommended**.
- Test pluginu volá soukromou funkci core → **recommended**. Je to znak chybějícího veřejného API.
- Plugin s JS bez `tests/js/*.test.mjs` pro čisté funkce, které JS obsahuje → **nice-to-have**.
- Testová data na různých místech (`tests/fixtures/`, `tests/data/`, inline) bez zjevného důvodu → **nice-to-have**.
