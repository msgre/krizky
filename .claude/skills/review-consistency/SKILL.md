---
name: review-consistency
description: Review the core krizky project and all krizky plugins for consistency, duplication, plugin-API adequacy, and cross-project coherence. Produces markdown reports in `reports/`. Runs on Python + adjacent JavaScript together. Invoke with no argument for full sweep, or with a project name (e.g. `krizky-photos`) to narrow to one project (still reads core + other plugins as context).
---

# review-consistency

Read this file first, then load the individual check files under `checks/` as you need them. Each check file has a focused checklist for one topic. You don't have to run every check in every invocation — start with the ones the user asks about; if they invoke with no argument, run all of them.

## What this skill does

Reviews a **core project + set of plugins** that share a plugin API, and reports where they've drifted out of alignment. It looks at Python code and any JavaScript assets that live inside those plugins (JS is always a supplement to a Python plugin — treat them together).

Three goals, in this order:

1. **Find duplication** — code repeated across plugins that belongs in core.
2. **Enforce consistency** — code across all projects should read like one author wrote it (naming, patterns, error handling, docs, tests, config).
3. **Assess plugin API adequacy** — do the current hooks still fit? Should any be added, changed, removed, replaced?

Extended checks (all opt-in by topic): config style, error/logging, data naming, tests, docs, dead code, core↔plugin API boundaries.

## Discovery: what projects exist

Currently all projects live side-by-side under the working directory (they'll eventually split into separate repos — the skill must not depend on that being permanent).

Discovery rule:

- **Core** = the directory containing `krizky/hooks.py` (the pluggy hookspec definitions). Also has `krizky/plugin_manager.py`. Typical name: `krizky/`.
- **Plugins** = directories under `_plugins/` (or wherever the user points), each containing a `pyproject.toml` with a `[project.entry-points."krizky"]` section pointing at a `plugin` object.

Run this to enumerate:

```bash
# Core
grep -l 'HookspecMarker("krizky")' -r . --include='*.py' 2>/dev/null | head -5
# Plugins
grep -l 'entry-points."krizky"' -r . --include='pyproject.toml' 2>/dev/null
```

If the user passed an argument (e.g. `/review-consistency krizky-photos`), narrow the **reporting focus** to that project — but you still read core + all other plugins as context, because consistency is a cross-project property.

## Ground truth: read before checking

Before running any check, load these into your context (they're the yardstick against which everything else is compared):

1. `krizky/hooks.py` — the plugin API surface (hookspecs, signatures, docs).
2. `krizky/plugin_manager.py` — how plugins are discovered/loaded.
3. `krizky/CLAUDE.md` and `krizky/README.md` — project conventions.
4. Each plugin's `plugin.py` (entry-point class) — how it wires into the API.
5. Each plugin's `README.md` and (if present) `CLAUDE.md`, `PLAN.md`.

## Severity

Every finding gets one of three tags. Pick conservatively — inflating severity dilutes the signal.

- **blocker** — actively breaks consistency in a way users or maintainers will hit. Examples: two plugins define the same config key with different meanings; a plugin reaches into a private core symbol; a hookspec signature is called inconsistently.
- **recommended** — real drift worth fixing, but nothing breaks today. Examples: naming convention diverges (`output_dir` vs `output`), inconsistent logger setup, docstring style split, duplicated helper that belongs in core.
- **nice-to-have** — cosmetic or preference-level. Examples: comment tone, order of dict keys, unused imports.

## Deciding what's "correct"

When two projects disagree, decide as follows:

1. **Core precedent wins.** If the pattern exists in `krizky/`, that's the canonical form; plugins should conform.
2. **If it exists only in plugins:** don't pick a winner. Describe both variants neutrally, name each variant, and propose one as canonical in a `proposals/` document — but leave the final call to the user.
3. **Never invent a new convention** the user hasn't already used somewhere. This skill is about aligning what exists, not inventing style.

## Workflow

1. **Discover** projects (core + plugins). If user passed a project name, note it as the report focus.
2. **Load ground truth** (hooks.py, plugin_manager.py, core docs, each plugin's plugin.py + README).
3. **Pick checks to run.** Full sweep = all files in `checks/`. Narrow invocation = user-mentioned topics, else default to all.
4. **For each check:** open the corresponding `checks/*.md`, walk its checklist, collect findings. If a check is heavy (e.g. `duplication.md` — needs to compare code across many files), consider spawning an `Explore` sub-agent to gather evidence and return a compact summary rather than pulling raw files into your own context.
5. **Assemble reports** per `report-format.md`. One file per project + one summary + optional proposals.
6. **Announce output locations** to the user at the end. Don't try to auto-open or auto-commit the reports.

## Report location

Write reports to `reports/YYYY-MM-DD-HHMM/` under the working directory. Timestamped so re-runs don't overwrite. Create the directory if missing.

Full layout:

```
reports/2026-08-17-1430/
  summary.md                      # cross-cutting patterns + top consolidation candidates
  core.md                         # findings scoped to core (krizky/)
  plugin-krizky-photos.md         # one per plugin
  plugin-krizky-json.md
  ...
  proposals/                      # only created if a check produced one
    config-style-guide.md         # canonical config conventions (if config check ran)
    hook-changes.md               # add/change/remove hookspec proposals (if hooks check ran)
    consolidation-to-core.md      # duplicated code to lift into core (if duplication check ran)
```

See `report-format.md` for the exact structure of each file (headings, finding format, cross-references).

## What this skill does NOT do

- **Does not modify code.** Reports only. If the user wants patches applied, they'll ask separately (probably a follow-up refactor session using the report as input).
- **Does not run tests** to determine correctness. Consistency ≠ correctness. If a pattern is inconsistent but both variants work, still flag it.
- **Does not review clean code per se** (readability inside a single file, function length, complexity metrics). That's a separate, per-repo concern — a different skill.
- **Does not touch `.venv/`, `__pycache__/`, or vendored third-party JS.** Skip those directories during discovery and grep.

## Output language

Write reports in **Czech** (the codebase's user-facing docs are Czech). Keep code identifiers, file paths, and technical terms in original form. Section headings can be Czech too.

## Notes on running

- The skill is read-only w.r.t. code. Only writes are inside `reports/`.
- When a plugin has no `CLAUDE.md` or `PLAN.md`, don't flag that as a finding unless docs consistency is the topic being reviewed.
- Don't create empty proposal files. `proposals/config-style-guide.md` only exists if the config check actually produced a coherent guide.
- If the codebase has changed since the ground-truth was loaded (unlikely mid-run), re-read rather than assuming.
