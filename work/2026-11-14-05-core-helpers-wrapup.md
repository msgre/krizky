# Uzavření migrace pluginů na core 0.2

## Co se udělalo
- Commitnuté logy čtyř pluginových swarmů (`2026-11-14-01` až `-04`: map, share, filters, photos). Finalizery je zapsaly do `work/` v core, commit podle CLAUDE.md pluginů dělá uživatel.
- `OVERVIEW.md`: stavy PR srovnané s GitHubem. Finální PR všech pluginových běhů jsou sloučené (map #3, share #3, filters #9, photos #3), v core taky `hooks-errors` #5, `plugin-helpers` #8 a `swarm-setup` #2.
- krizky-json: `uv.lock` z core 0.1.0 (`09af781`) na 0.2.0 (`e32694e`), PR msgre/krizky-json#2. Kód beze změny, plugin implementuje jen `after_page_written` a helpery nepotřebuje. Omezení `krizky>=0.1` zůstává. `scripts/verify` prošel.

## Stav pluginů po migraci
Všech pět pluginů (filters, json, map, photos, share) má v locku core 0.2.0 (`e32694e`). U json to platí po sloučení PR #2.

## Návrhy ke swarmu z retra běhů
- Všechny čtyři jednotiketové běhy navrhly vynechat u jednoho tiketu integrační větev a finální PR. Rozhodnutí: zatím neměnit. Úspora je zanedbatelná (sloučení ~$0.00, závěr ~$0.1), log běhu by se musel přesunout do tiketového PR a jeden tok se snáz udržuje.
- K řešení zbývá úklid worktrees `wf_*` a větví `worktree-wf_*` po sloučení. Hlásí ho map i photos.
