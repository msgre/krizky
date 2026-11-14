# Kontrola: chyby a logování

Cíl: chyby a logy vypadají stejně v core i v pluginech. Uživatel z výpisu pozná krizky bez ohledu na to, který plugin zlobí.

Pravidla jsou v `docs/guidelines/python.md` › Logging a › Exceptions. Jak core zachází s chybou v pluginu, popisuje `docs/plugins.md` › Chyby v pluginech.

## Postup

1. `grep -rn "getLogger\|_log\.\|logger\.\|print(" krizky/ ../krizky-*/krizky_*/`
2. `grep -rn "class .*\(Error\|Exception\)\b\|raise \|except " krizky/ ../krizky-*/krizky_*/`
3. `grep -rn "ClickException\|click.echo\|sys.exit" krizky/ ../krizky-*/krizky_*/`

## Pravidla

### Logování

- Logger jinak než modulový `_log = logging.getLogger(__name__)` → **recommended**.
- f-string nebo `.format()` ve volání `_log.*` → **recommended**.
- `_log.error()` a hned potom `raise` téže chyby → **recommended**.
- Plugin nastavuje handlery nebo úrovně loggingu → **recommended**. Logging konfiguruje core CLI.
- Úroveň neodpovídá významu (`info` na ladicí detail, `warning` na běžný stav) → **nice-to-have**.
- Log zprávy nejsou anglicky → **recommended** (`docs/guidelines/cross-language.md`).

### Výjimky

- Vlastní výjimka nemá jméno `<Feature>Error`, nebo plugin nemá společnou bázovou třídu svých výjimek → **recommended**.
- `click.ClickException` vyhozená z hooku → **blocker**. Hook neběží vždy v kontextu Click.
- Cizí výjimka přebalená bez `from` → **recommended**.
- `except: pass` nebo `except Exception: pass` → **recommended**. Pokud skrývá chybu, kterou by uživatel měl vidět, **blocker**.

### Chování napříč pluginy

- Pluginy reagují na stejný druh problému různě (chybějící soubor: jeden mlčí, druhý varuje, třetí padá) → **recommended**. Popiš varianty a navrhni jednu.
