# Check: dead code

Cíl: najít symboly, soubory, config klíče a helpery, které už nikdo nepoužívá.

Pozor: dead code je snadné falešně detekovat (dynamic imports, hookspec bez implementace, reserved API pro budoucnost). Klasifikuj konzervativně.

## Postup

### Python
1. Pro každý veřejný symbol (funkce, třída, konstanta) v pluginu i core: grep napříč celým workspace jestli ho někdo importuje/volá (kromě definice a testů).
2. Pro každý private symbol (`_foo`): grep uvnitř toho modulu.
3. Pro každý test: koresponduje s existujícím kódem?
4. Pro každý TODO/FIXME komentář starší než 3 měsíce (git blame): flag.

### JS
1. Funkce definovaná v IIFE a nevolaná — flag.
2. Data-atributy hledané JS-em, které šablona nevygeneruje (grep šablony na `data-<name>`).
3. Data-atributy vygenerované šablonou, které nikdo v JS nečte.
4. Nepoužité CSS třídy (méně důležité, ale flag jako nice-to-have).

### Config
1. Pro každý plugin: seznam config klíčů, které plugin čte (grep `config.get(`, `photos_cfg.get(` atd.).
2. Porovnej se `README.md` config example — jsou tam všechny klíče, které kód reálně čte?
3. Jsou v README zdokumentované klíče, které kód nikde nečte? → dead config.

## Checklist

### Python
- [ ] Nepoužité importy (linter to obvykle chytá, ale někdy protikandidát pro type-checking-only importy).
- [ ] Nepoužité funkce v `<plugin>/utils.py` (nebo obdobě).
- [ ] Metody na plugin třídě, které nejsou `@hookimpl` decorated a nikdo je nevolá.
- [ ] Vnořené třídy / dataclasses nikdy neinstancované.
- [ ] Konstanty definované a nikde nepoužité.
- [ ] Deprecated funkce s komentářem "will be removed" bez data odstranění.
- [ ] Commented-out kód víc než 5 řádků → nice-to-have odstranit.

### CLI příkazy
- [ ] Zaregistrovaný CLI command, jehož existence je zapomenutá v README → doc drift, ne dead code.
- [ ] CLI command zdokumentovaný, ale registrace zmizela z kódu → dead doc.

### Templates a assets
- [ ] Jinja šablona v `templates/` které nikdo `{% include %}` / `{% import %}` / `template=` neuvádí.
- [ ] CSS/JS soubor v `assets/`, který žádný `inject_head` / `<link>` v šabloně nezmiňuje.
- [ ] Fixtures/data v `tests/` nepoužité v žádném testu.

### Hookspecs bez implementací
- [ ] Hookspec definovaný v core, který 0 pluginů implementuje. Ne nutně dead — může být reserved. Flag jako `nice-to-have` s poznámkou.

### Config drift
- [ ] Klíč zdokumentovaný v README, kód ho nečte.
- [ ] Klíč, který kód čte, ale README ho nezmiňuje.
- [ ] Klíč čtený, ale výsledek nikde nepoužitý (načte se do proměnné, která pak leží).

## Zvláštní pozornost

- **False positive risk:** entry-point pluginy jsou volané pluggym dynamicky. Grep nemusí najít volání `PhotosPlugin.__init__`, ale je používaný. Před flag zkontroluj entry-point definice v `pyproject.toml`.
- **Nedávno přidaný kód:** git log — pokud byl symbol přidán v posledních 2 týdnech, možná je připravovaný pro brzké použití. Ne blocker, spíš nice-to-have s poznámkou "je to úmysl?".
- Kód ve `_plugins/*/.venv/`, `__pycache__/`, `node_modules/` — **nikdy** neanalyzuj.
