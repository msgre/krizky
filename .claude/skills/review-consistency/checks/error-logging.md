# Check: error handling & logging

Cíl: chyby a logování vypadají stejně napříč projekty. Uživatel při čtení tracebacku pozná, že "to je krizky" bez ohledu na to, jestli zlobí core nebo plugin.

## Postup

Konvence loggeru a log zpráv jsou v `docs/guidelines/python.md` (sekce Logging): modul-level `_log = logging.getLogger(__name__)`, lazy `%s` formátování, ne `_log.error()` a `raise` současně. Odchylka od nich je zjištění, ne otázka.

1. Grep `logging.getLogger`, `logger =`, `_log =` napříč všemi projekty.
2. Grep `class .*Error`, `class .*Exception`, `raise ` — inventarizuj custom exceptions.
3. Grep `click.ClickException`, `click.echo`, `sys.exit` — jak končí uživatelsky-viditelné chyby.
4. Projdi checklist.

## Checklist

### Logger setup
- [ ] Konvence: `_log = logging.getLogger(__name__)` — všude?
- [ ] Jméno proměnné: `_log` vs `logger` vs `log` — jedno napříč?
- [ ] Kde se logger vytváří — vždy modul-level, nebo někdo per-instance?
- [ ] Konfigurace loggeru (level, handler, format) — dělá se v core CLI? Pluginy do toho nesahají?

### Log levels
- [ ] `DEBUG` — použití konzistentní (podrobnosti pro devs)?
- [ ] `INFO` — použití konzistentní (business events, ne šum)?
- [ ] `WARNING` — použití konzistentní (recoverable problems, něco chybí, ale pokračujeme)?
- [ ] `ERROR` — jen tam, kde něco selhalo, ale program pokračuje?
- [ ] `CRITICAL` — vůbec, nebo jen v extrémech?

Časté smells:
- Někdo loguje `_log.info(...)` na věci, které by měly být `debug`.
- Někdo loguje `print(...)` místo loggeru.
- Někdo loguje `_log.error(...)` a hned pak `raise` — buď to jedno, nebo to druhé, ne oboje.

### Formát log zpráv
- [ ] `_log.warning("Missing %s in config", key)` (lazy formatting) vs `_log.warning(f"Missing {key} in config")` (f-string) — konzistentně? (Lazy je Python-idiomatic pro logging.)
- [ ] Věty s tečkou vs bez tečky?
- [ ] Kontext v každé zprávě (jméno souboru, řádek dat) — konzistentně?
- [ ] Jazyk zpráv: český vs anglický? (Code je typicky EN, log zprávy taky. User-facing věci mohou být CZ.)

### Custom exceptions
- [ ] Jméno: `<Feature>Error` (viz `FocalPointsError`) — precedent, všichni ho následují?
- [ ] Umístění: v modulu, kde vznikají, vs samostatný `exceptions.py`?
- [ ] Dědí z čeho: `Exception`, vlastní base? Konzistentní?
- [ ] Message ve `__init__` vs `args`? Jednotné?
- [ ] Kdo chytá — plugin sám, core, nebo unhandled bublá k uživateli?

### User-facing chyby (CLI)
- [ ] Kdy `click.ClickException` (uživatelské chybné vstupy) vs. `raise` (bug) — konzistentní hranice?
- [ ] Barevné výstupy (`click.style`) — používají všechny CLI commands stejný styl (error = red, warning = yellow)?
- [ ] Exit codes — konzistentní? (0 = ok, 1 = uživatelská chyba, 2+ = neco jineho?)

### Boundary chování
- [ ] Chyba v jednom pluginu — položí to celý build, nebo se logne a pokračuje s ostatními pluginy? Konzistentní volba napříč hooky?
- [ ] `try/except Exception:` širší catch — kde se objevuje, je odůvodněný?
- [ ] Přepakování cizích exceptions do vlastních (`raise MyError(...) from e`) — konzistentní vzorec?

### Silent failures
- [ ] Někde `except: pass` nebo `except Exception: pass`?
- [ ] Kdyby chyběl config klíč, sekce, soubor — vždy warning nebo někde tiché no-op?

## Zvláštní pozornost

- **Nesourodý fail-mode napříč pluginy:** jeden plugin při chybějícím configu vyhodí `ClickException`, druhý tiše no-op, třetí warning + pokračuje. → recommended sjednotit (typicky: chybějící sekce = no-op + jeden info log; chybějící klíč uvnitř existující sekce = warning nebo error, podle povahy).
