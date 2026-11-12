# Check: adekvátnost plugin API (hooky)

Cíl: zjistit, jestli současná sada hookspecs stále vyhovuje. Výstup: draft `proposals/hook-changes.md`, pokud najdeš věci k přidání/změně/odebrání.

## Kontext

Plugin API je definované v `krizky/hooks.py` přes pluggy. Každý hookspec má docstring, který popisuje semantics (kdy se volá, `firstresult`, apod.). Plugin loadning je v `krizky/plugin_manager.py`.

## Postup

1. Vypiš všechny hookspecs z `krizky/hooks.py` (jméno, signatura, `firstresult`, docstring).
2. Pro každý plugin: kterou podmnožinu hookspecs implementuje (`@hookimpl` decorated metody v `plugin.py`).
3. Sestav matici (hooks × plugins) — jaké pole je "husté", jaké prázdné.
4. Projdi checklist níže.

## Checklist

### Nevyužité hookspecs
- [ ] Existuje hookspec, který nikdo neimplementuje? (Pokud ano — je to reserved pro budoucnost, nebo mrtvé API?)
- [ ] Existuje hookspec s právě jednou implementací? Je to jednorázová únik-hatch, nebo znak, že "extension point" nebyl potřeba obecně?

### Chybějící hookspecs (kandidáti na přidání)
Zkoumej pro každý plugin:
- [ ] Dělá plugin něco na "životním cyklu" (start buildu, konec buildu, per-record, per-page), kde současné hooky nejsou v přesně tom bodu, kde by potřeboval? → potenciální nový hook.
- [ ] Sahá plugin do core internals (např. `from krizky.render import ...`) místo aby dostal data přes hook? → nový hook by zbavil coupling.
- [ ] Duplikuje více pluginů stejné boilerplate okolo hooků (např. všichni v `prepare_jinja2_environment` dělají `env.globals[...] = ...` se stejným vzorcem)? → možná chybí vyšší-level hook (`register_template_global`).
- [ ] Řeší plugin něco monkey-patchem, výjimkovou cestou nebo re-parsováním configu? → tam patří hook.

### Konzistence signatur
- [ ] Přidávaly se parametry existujícím hookům postupně (např. `config_dir` přidán později do `prepare_jinja2_environment`)? Kdo z pluginů nový parametr přijal, kdo ne?
- [ ] Pluggy dovolí plugin vynechat neznámý param — ale konzistence pro čtenáře trpí. Doporuč sjednocení.
- [ ] Používají různé hooky konzistentně pojmenované parametry pro stejnou věc? (`config`, `cfg`, `configuration`; `config_dir` vs `root_dir` vs `base_dir`.)
- [ ] `firstresult` je použit tam, kde má smysl (jedna implementace vyhrává), a nikde jinde?

### Dokumentace hookspecs
- [ ] Docstring každého hookspec popisuje: (1) kdy se volá, (2) kolik reimplementací se očekává, (3) sémantiku návratové hodnoty, (4) jaké argumenty a proč?
- [ ] Existuje-li v docstringu "backward-compatible" poznámka (viz `prepare_jinja2_environment` s `config_dir`), je to pravda pořád? Nebo už všechny pluginy nový param používají a poznámku lze odstranit?

### Registrace pluginů a lifecycle
- [ ] Registrační logika v `plugin_manager.py` — je jasné, které priority má co? (Local dir > entry points > builtin.)
- [ ] Objevily se nějaké lifecycle problémy (např. `register_commands` je volaný před `config_dir` je známý — je to fundamentální nebo řešitelné novým hookem `configure`)?
- [ ] Má nějaký plugin logiku typu "za jistých podmínek se zaregistruj, jinak ne"? Dělá to čistě, nebo hackem?

### Doporučení k jednotlivým hookům

Pro každý existující hook rozhodni:

- **Ponechat beze změny** — pokud je používán ≥2 pluginy nebo je zjevně obecný/užitečný.
- **Rozšířit signaturu** — pokud implementace potřebují další parametr a musí ho získávat oklikou.
- **Sloučit s jiným** — pokud dva hooky mají překrývající se zodpovědnosti.
- **Zúžit / odstranit** — pokud je jen 0-1 implementací a užití je specifické.

## Formát návrhů

Sepiš do `proposals/hook-changes.md` podle šablony v `report-format.md`. Pro každý návrh uveď:
- motivaci vzorem z reálného kódu (odkaz na plugin/soubor/řádek),
- signaturu,
- kdo by z toho těžil (které pluginy by hook implementovaly),
- alternativu, kterou jsi zvažoval a zamítl (shared helper, mixin, event bus, atd.).
