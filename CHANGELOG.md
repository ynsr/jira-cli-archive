# Changelog

## Unreleased — Story Points update
- `statuses [KEY] [--project KEY]`: lists per-project statuses (ID, name, status ID, category) via `project/{key}/statuses` with workflowDesigner fallback and `statuscategory` enrichment; default key from `JIRA_PROJECT`/config.

- `issue <KEY> update --story-points <n>`: writes SP via the auto-resolved Story Points custom field (`JIRA_CLI_SP_FIELD` pins it); numeric validation, unresolved-field error, guarded by `--yes`/`--dry-run`; help/README/completions updated.

## 2.2.0 — Planner support (agent-friendly interface for jira-sp-planner)

- Layered Resolution/SP/Sprint/Epic-Link ID resolution (config override → env → exact name incl "Original story points"; per-domain+project 30d cache); structured `sprints[]` + `epic_key` in issue/search JSON, legacy `sprint` untouched.
- `search --start-at/--max-results/--all/--fields/--expand/--envelope/--changelog-fields`; per-issue normalized changelog + truncation backfill; Persian-safe JSON (`ensure_ascii=False`).
- `issue K changelog [--changelog-fields a,b] [--since 7d]` with normalized `{field,from,to,at,by,by_name}` entries.
- `board list`, `sprint list/get/issues/current` reads on `/rest/agile/1.0/` (normalized `{id,name,state,start,end,complete,board}`).
- `sprint move`, `backlog move`: journal-before-write (0600), chunks of 50 via POST (unverified live), re-read + VERIFY; `sprint restore` replays journals, refuses closed sprints.
- `permissions --project --check`, `capabilities [--project]` + `version --json`; help/README/completions updated.
