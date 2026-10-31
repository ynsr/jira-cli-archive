# jira-cli

Query, list, and interact with Jira issues from the terminal.
Connects to any Jira instance (self-hosted or Cloud) with Basic Auth.

## Install

```bash
pipx install .
```

> **Troubleshooting**: If `jira-cli` is not found after install, the pipx
> symlink in `~/.local/bin/` may be missing. Re-run with `--force`:
> ```bash
> pipx install --force .
> ```
> Make sure `~/.local/bin` is on your `$PATH`.

Or from a remote source once published.

## Usage

```
jira-cli <command> [args...] [-h] [flags]
```

### Commands

| Command     | Description                                 |
|-------------|---------------------------------------------|
| `projects`  | List all projects                           |
| `search`    | Search issues with JQL or saved filters     |
| `create`    | Create a new issue                          |
| `link`      | Link two issues                             |
| `issue`     | Issue detail, comments, add-comment, attachments (list/download/delete), attach, update, changelog |
| `board`     | `list` agile boards                         |
| `sprint`    | `list/get/issues/current` reads; `move/restore` journaled membership moves |
| `backlog`   | `move` issues to the backlog (journaled, verified) |
| `statuses`  | List all available statuses for a project   |
| `permissions` | Check project permissions                 |
| `capabilities` | CLI version, server flavor, features, resolved field IDs |
| `setup`     | Configure Jira credentials                  |
| `help`      | Print help text (AI-agent friendly)         |
| `completion`| Print shell completion script               |
| `completion-install` | Install completion into your rc file (idempotent) |

### Examples

```bash
jira-cli projects
jira-cli search "project=BANKING" --format json
jira-cli search --list-filters
jira-cli search --saved my-issues --limit 5 --format json
jira-cli search --saved my-issues+blocked
jira-cli issue PROJ-123
jira-cli issue PROJ-123 --format json --include-raw   # JSON view (--json alias also works)
jira-cli issue PROJ-123 comments --limit 10 --desc
jira-cli issue PROJ-123 comment 54321
jira-cli issue PROJ-123 add-comment --body "Working on this"
jira-cli issue PROJ-123 attach ./screenshot.png ./error.log
jira-cli issue PROJ-123 attachments
jira-cli issue PROJ-123 download --all --dir ./attachments
jira-cli issue PROJ-123 download 10001
jira-cli issue PROJ-123 delete-attachment 10001
jira-cli issue PROJ-123 update --summary "New title" --priority High
jira-cli issue PROJ-123 update --description "New description" --assignee jane.doe
jira-cli issue PROJ-123 update --story-points 5 --yes   # writes SP (needs --yes; --dry-run to preview)
jira-cli create --project BANKING --summary "Fix bug" --type Bug --priority High
jira-cli link BANKING-123 BANKING-456 --type Blocks --comment "Depends on this"
jira-cli completion bash
jira-cli completion zsh
jira-cli completion fish
jira-cli completion-install bash --yes
jira-cli issue PROJ-123 delete-attachment 10001 --dry-run   # preview the request
jira-cli issue PROJ-123 delete-attachment 10001 --yes       # execute non-interactively
jira-cli search "project=IPG" --all --envelope --format json   # every page, envelope
jira-cli issue IPG-1 changelog --changelog-fields status,assignee --since 7d
jira-cli board list --project IPG
jira-cli sprint list --board 3 --state active,future
jira-cli sprint current --board 3
jira-cli sprint move --sprint 548 IPG-1 --dry-run   # preview; journal written first on real runs
jira-cli backlog move IPG-1 --dry-run
jira-cli permissions --project IPG --check MOVE_ISSUES --format json
jira-cli statuses IPG   # all statuses for a project (ID, name, status ID, category)
jira-cli capabilities --format json
```

### Planner field resolution (agent-friendly)

Resolution, Story Points, Sprint, and Epic Link IDs are resolved per
domain+project (30-day cache) by exact customfield-ID match first
(`cfg["fields"][kind]` → `cfg["<kind>_field"]` → `JIRA_CLI_*_FIELD` env),
falling back to name matching ("Original story points" included).
JSON detail views carry `resolution`, `story_points`, `sprint` (legacy
`Name (STATE)` strings), `sprints` (structured `{id,name,state,start,end}`),
and `epic_key`.

### Config

Set `JIRA_URL`, `JIRA_USER`, `JIRA_PASS` env vars, or run `jira-cli setup`
to save credentials to `~/.jira-cli.json` (chmod 600).

### Jira Server/DC & Cloud compatibility

jira-cli works with both **Jira Server/Data Center** (REST API v2) and
**Jira Cloud** (REST API v3):

- Reads and JQL searches always use API v2 (served by both platforms).
- Write operations (create, update, comments, links) use the version
  auto-detected from `/rest/api/2/serverInfo` (`deploymentType`).
- On Server/DC the `description` and comment bodies are sent as plain
  wiki-markup strings; on Cloud they are sent as Atlassian Document Format
  (ADF) documents — handled automatically.
- Force a version if needed: `JIRA_API_VERSION=2` or `JIRA_API_VERSION=3`
  (default `auto`).

## Development

```bash
pip install -e .
python -m pytest tests/
```
