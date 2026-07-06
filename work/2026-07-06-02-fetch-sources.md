# 2026-07-06-02 — Fetch sources (Fáze 2)

## Co bylo implementováno

### `krizky/fetch.py` — nový soubor

- `FetchError` — vlastní výjimka pro selhání HTTP stahování
- `TransformError` — vlastní výjimka pro selhání transform skriptů
- `fetch_sheet(id, gid, output_path, skip_rows=0)` — stáhne Google Sheet jako CSV přes `urllib.request`; podporuje přeskočení prvních N řádků; vytváří parent adresáře automaticky; vyhodí `FetchError` při HTTP chybě
- `fetch_doc(id, output_path)` — stáhne Google Doc jako DOCX (binárně); vytváří parent adresáře; vyhodí `FetchError` při HTTP chybě
- `run_transform(script, source_file, db_path, table_name, output_path=None)` — spustí bash skript s standardními argumenty; streamuje stdout/stderr do terminálu; vyhodí `TransformError` při nenulové návratové hodnotě
- `fetch_sources(config, config_dir, transform=False)` — orchestruje stahování všech tabulek a dokumentů; při `transform=True` spouští transform skripty; pro docs ověřuje existenci výstupního souboru po transformaci

### `krizky/cli.py` — aktualizace

- Příkaz `krizky fetch sources [--transform]` plně implementován (nahrazen stub `"not implemented"`)
- Načítá a validuje config, volá `fetch_sources`, tiskne barevný výstup OK/ERROR

### `tests/test_fetch.py` — nový soubor

7 testů, vše prochází:
- `test_fetch_sheet_basic` — základní stahování CSV
- `test_fetch_sheet_skip_rows` — přeskočení prvních 2 řádků
- `test_fetch_doc_basic` — stahování binárního DOCX
- `test_run_transform_success` — skript exit 0 → žádná výjimka
- `test_run_transform_failure` — skript exit 1 → `TransformError`
- `test_fetch_sheet_http_error` — HTTP 403 → `FetchError`
- `test_fetch_doc_http_error` — HTTP 404 → `FetchError`

## Výsledky testů

```
18 passed in 0.19s
```

Všechny stávající testy `test_config.py` (11 testů) + nové testy `test_fetch.py` (7 testů) prošly bez chyb.

## Technické poznámky

- Žádné extra závislosti — použit `urllib.request` ze standardní knihovny
- Subprocess volání streamuje stdout/stderr přímo do terminálu (bez capture)
- Type hints na všech veřejných funkcích
- Žádné globální proměnné; konfigurace předávána explicitně
