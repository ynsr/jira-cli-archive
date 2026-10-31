"""Help texts for all jira-cli commands."""

from jira_cli.filters import FILTERS

HELP = {}

HELP["main"] = """JIRA-CLI HELP — AI-agent friendly

COMMANDS:
  projects                    List all projects
  search <jql> [flags]        Search issues with JQL + saved filters
  create                      Create a new issue
  link <KEY> <KEY>            Link two issues
  issue <KEY>                 Show issue detail + latest comment
  issue <KEY> comments        Paginated comment list (truncated text)
  issue <KEY> comment <ID>    Full single comment detail
  issue <KEY> add-comment     Add a comment
  issue <KEY> attachments     List attachment file(s)
  issue <KEY> download        Download attachment file(s) (ids or --all)
  issue <KEY> delete-attachment  Delete attachment file(s) (ids or --all)
  issue <KEY> attach <file>   Upload attachment file(s)
  issue <KEY> update          Update summary/description/priority/assignee/story-points
  issue <KEY> transition <ID>     Transition issue to a new status
  issue <KEY> edit-comment <ID>   Edit an existing comment body
  issue <KEY> changelog       Normalized change history (--changelog-fields, --since)
  board list                  List agile boards (--project)
  sprint list|get|issues|current  Read sprints for a board
  sprint move|restore         Move issues into a sprint / restore from a journal
  backlog move K...           Move issues to the backlog (journaled, verified)
  permissions                 Check project permissions (--check)
  statuses [KEY]              List all available statuses for a project
  capabilities                Server flavor/version, features, resolved field IDs
  setup                       Configure credentials
  completion <shell>          Print a shell completion script (bash, zsh, fish)
  completion-install [shell]  Install the completion eval line into your rc file
  help                        This help text

EXAMPLES:
  jira-cli projects
  jira-cli search "project=BANKING" --format json
  jira-cli search --list-filters
  jira-cli search --saved my-issues+in-progress
  jira-cli issue PROJ-123
  jira-cli issue PROJ-123 comments --limit 5 --desc
  jira-cli issue PROJ-123 comment 12345
  jira-cli issue PROJ-123 add-comment --body "Looking into this"
  jira-cli issue PROJ-123 attach ./screenshot.png ./error.log
  jira-cli create --project BANKING --summary "Fix bug" --type Bug --priority High
  jira-cli link BANKING-123 BANKING-456 --type Relates --comment "Blocks"
  jira-cli issue PROJ-123 update --summary "New title" --priority High --assignee jane.doe
  jira-cli issue PROJ-123 update --description "New description text"
  jira-cli issue PROJ-123 transition 41
  jira-cli issue PROJ-123 edit-comment 12345 --body "Updated comment"
  jira-cli completion bash
  jira-cli completion-install bash --yes

AI USAGE:
  issues = run("jira-cli search --saved my-issues --limit 5 --format json")
  detail = run("jira-cli issue PROJ-123 --format json")  # curated JSON (--json also works)
  cmts   = run("jira-cli issue PROJ-123 comments --limit 3 --format json")

Run 'jira-cli <command> -h' for per-command help with examples.

GLOBAL FLAGS:
  --version                   Print the version and exit
  --timeout <sec>             Per-request network timeout (default: 30)
  --retries <N>               Retries on timeout/5xx/429 with exponential backoff (default: 0)
  --retry-delay <sec>         Base delay between retries; doubles each attempt (default: 1.0)

DESTRUCTIVE ACTIONS (issue delete-attachment, edit-comment, transition, update):
  --dry-run                   Print the request that would be sent, change nothing
  --yes                       Execute without confirmation (required when non-interactive)

Exit codes: 0 success, 1 error, 2 usage/refused destructive action.
"""

HELP["completion-install"] = """jira-cli completion-install — install shell completion into your rc file

Usage:
  jira-cli completion-install [shell] [--rcfile PATH] [--yes]

Args:
  [shell]           bash, zsh, or fish; omit to detect from $SHELL
  --rcfile <PATH>   Rc file to edit (default: ~/.bashrc, ~/.zshrc, or ~/.config/fish/config.fish)
  --yes             Skip confirmation (required when non-interactive)

Writes an idempotent marker block into the rc file:
  # >>> jira-cli completions >>>
  eval "$(jira-cli completion bash)"
  # <<< jira-cli completions <<<

Re-running is a no-op; an existing block is replaced in place and a .bak
backup is kept. After a change, restart your shell or run: source <rcfile>.

EXAMPLES:
  jira-cli completion-install bash
  jira-cli completion-install zsh --rcfile ~/.zshrc --yes
  jira-cli completion-install fish
"""

HELP["search"] = """jira-cli search — search issues with JQL

Usage:
  jira-cli search <jql> [--saved <filter>] [--limit N] [--format <table|json>]
  jira-cli search --list-filters                 List saved filters with JQL
  jira-cli search --saved <name> [<name>...]     Run saved filters (AND-joined)

Args:
  <jql>               Raw JQL query (required unless --saved is used)
  --saved <filter>    AND-join a predefined filter (repeatable, comma-separated)
  --list-filters      List all saved filters and exit
  --limit <N>         Page size (default: 20)
  --start-at <N>      First result offset (default: 0)
  --max-results <N>   Cap on total collected results (default: 1000)
  --all               Walk every page until total (fetch_all)
  --fields <a,b>      JQL fields to fetch (default: curated navigable set)
  --expand <x,y>      Passed to the API (changelog auto-enables inline history)
  --envelope          Wrap output as {total,start_at,returned,next_start_at,issues}
  --changelog-fields <a,b>  Attach normalized per-issue changelog (summary/comment/sprint are noisy — excluded by default; use --expand changelog for full text)
  --format <fmt>      Output: table (default) or json

Output: table rows show summary + a Resolution/SP/Sprint suffix when present;
  json payloads add curated resolution, story_points, sprint (legacy string),
  sprints (structured list), and epic_key keys.

Available --saved filters:
""" + "\n".join(f"  {n:20} {v['desc']}" for n, v in sorted(FILTERS.items())) + """

EXAMPLES:
  jira-cli search "project=BANKING AND status='In Progress'"
  jira-cli search --list-filters
  jira-cli search --saved my-issues --limit 10 --format json
  jira-cli search --saved my-issues,in-progress "project=BANKING"
  jira-cli search --saved todo
"""

HELP["issue"] = """jira-cli issue — show issue detail and work with comments

Usage:
  jira-cli issue <KEY> [--format json]         Show issue detail + latest comment (or JSON view)
  jira-cli issue <KEY> comments [flags]        List paginated comments (truncated)
  jira-cli issue <KEY> comment <ID>            Show full single comment
  jira-cli issue <KEY> add-comment [--body <text>]  Add a comment
  jira-cli issue <KEY> attachments [--format json]  List attachment file(s)
  jira-cli issue <KEY> download [<id>...] [--dir <dir>] [--all]  Download attachment file(s)
  jira-cli issue <KEY> delete-attachment <id>... [--all]  Delete attachment file(s)
  jira-cli issue <KEY> attach <file> [<file>...]    Upload attachment file(s)
  jira-cli issue <KEY> update [flags]               Update fields (summary/description/priority/assignee/story-points)
  jira-cli issue <KEY> changelog [--changelog-fields a,b] [--since <when>]  Normalized change history
  jira-cli issue <KEY> -h                      This help text

Flags for 'issue <KEY>' detail view:
  --format <fmt>      table (default) or json
  --json              Shorthand for --format json
  --include-raw       With json output: add "raw" key holding the untouched Jira payload

Detail views always include Resolution, Story Points, and Sprint when set
(json keys: resolution, story_points, sprint plus sprints and epic_key).

Flags for 'changelog' subcommand:
  --changelog-fields <a,b>  Only these normalized fields (status, assignee, Sprint, ...)
  --since <when>      Only entries at/after this time (absolute datetime or '7d'/'24h'/'30m')
  --format <fmt>      table (default) or json

Flags for 'comments' subcommand:
  --limit <N>         Comments per page (default: 5)
  --page <N>          Page number, 1-based (default: 1)
  --desc              Newest-first order
  --format <fmt>      table (default) or json

Flags for 'add-comment' subcommand:
  --body <text>       Comment body text (omit to read from stdin until Ctrl+D)

Flags for 'update' subcommand:
  --summary <text>    New summary/title
  --description <text>  New description (wiki markup on Jira Server/DC; plain text on Cloud)
  --priority <name>   New priority (e.g. High, Medium, Low)
  --assignee <user>   New assignee (by username; empty string to unassign)
  --story-points <n>  Story points (number; resolves the server's SP custom field, or JIRA_CLI_SP_FIELD)

EXAMPLES:
  jira-cli issue PROJ-123                                        # detail + latest comment
  jira-cli issue PROJ-123 --format json --include-raw            # JSON view + raw payload
  jira-cli issue PROJ-123 comments --limit 10 --page 2 --desc    # paginated comments
  jira-cli issue PROJ-123 comment 54321                          # full comment detail
  jira-cli issue PROJ-123 add-comment --body "Working on this"   # add comment
  jira-cli issue PROJ-123 update --summary "New title" --priority High
  echo "Done" | jira-cli issue PROJ-123 add-comment              # add from stdin
"""

HELP["projects"] = """jira-cli projects — list all Jira projects

Usage:
  jira-cli projects

Output: table with Key, Name, Lead, Type columns.

EXAMPLE:
  jira-cli projects
"""

HELP["create"] = """jira-cli create — create a new issue

Usage:
  jira-cli create --project <KEY> --summary "<text>" [flags]

Required:
  --project <KEY>         Project key (e.g. BANKING)
  --summary "<text>"      Issue summary/title

Optional:
  --type <name>           Issue type (default: Task; e.g. Bug, Story, Epic)
  --description "<text>"  Issue description (wiki markup on Jira Server/DC; plain text on Cloud)
  --priority <name>       Priority (e.g. Highest, High, Medium, Low, Lowest)
  --assignee <user>       Assignee username (empty string to leave unassigned)
  --format <fmt>          Output: table (default) or json

EXAMPLES:
  jira-cli create --project BANKING --summary "Fix login bug" --type Bug --priority High
  jira-cli create --project BANKING --summary "Write docs" --description "Add README" --format json
"""

HELP["link"] = """jira-cli link — link two issues

Usage:
  jira-cli link <outward-key> <inward-key> [--type <link-type>] [--comment <text>]

Args:
  <outward-key>       First issue key (outward side of the link)
  <inward-key>        Second issue key (inward side of the link)
  --type <link-type>  Link type name (default: Relates; e.g. Blocks, Duplicate)
  --comment <text>    Optional comment attached to the link (outward issue)

EXAMPLES:
  jira-cli link BANKING-123 BANKING-456
  jira-cli link BANKING-123 BANKING-456 --type Blocks --comment "Depends on fix"
"""

HELP["setup"] = """jira-cli setup — configure Jira credentials

Usage:
  jira-cli setup

Prompts for Jira URL, username, and password.
Saves to ~/.jira-cli.json (chmod 600).
Can be overridden by env vars: JIRA_URL, JIRA_USER, JIRA_PASS.

COMPATIBILITY:
  Works with both Jira Server/Data Center (REST API v2) and Jira Cloud
  (REST API v3). The API version is auto-detected; force it with
  JIRA_API_VERSION=2|3 if needed.

EXAMPLE:
  jira-cli setup
"""

HELP["board"] = """jira-cli board — list agile boards

Usage:
  jira-cli board list [--project KEY] [--format <table|json>]

EXAMPLES:
  jira-cli board list
  jira-cli board list --project IPG --format json
"""

HELP["sprint"] = """jira-cli sprint — read and move sprints

Usage:
  jira-cli sprint list --board ID [--state active,future,closed] [--last N] [--format <table|json>]
  jira-cli sprint get ID [--format <table|json>]
  jira-cli sprint issues ID [--fields a,b] [--all] [--format <table|json>]
  jira-cli sprint current --board ID [--format <table|json>]
  jira-cli sprint move --sprint ID K1 K2 ... [--dry-run] [--yes] [--journal PATH]
  jira-cli sprint restore --journal FILE [--dry-run] [--yes]

Sprint objects: {id, name, state, start, end, complete, board}.
'sprint list --last N' needs --state closed: the API returns oldest first,
so all closed pages are read and the tail by (completeDate, endDate, id) kept.
'current' prints the active sprint, else the earliest future sprint (exit 1 if none).

Moves write a journal file BEFORE any write call (0600), move in chunks of 50
via POST sprint/{id}/issue (unverified live — a 405 names method+path), then
re-read each issue and VERIFY membership. 'restore' replays a journal grouped
by recorded origin sprint (source journal never modified — a separate
sprint.restore audit journal is written first); closed destinations are refused (exit 1).

EXAMPLES:
  jira-cli sprint list --board 3 --state active,future
  jira-cli sprint list --board 3 --state closed --last 3 --format json
  jira-cli sprint current --board 3
  jira-cli sprint move --sprint 548 IPG-1 IPG-2 --dry-run
  jira-cli sprint restore --journal ./jira-cli-sprint.move-20261018-120000.json --yes
"""

HELP["backlog"] = """jira-cli backlog — move issues to the backlog

Usage:
  jira-cli backlog move K1 K2 ... [--dry-run] [--yes] [--journal PATH]

Same journal-before-write / chunks-of-50 / re-read-and-VERIFY contract as
'sprint move', via POST backlog/issue (unverified live).

EXAMPLES:
  jira-cli backlog move IPG-1 IPG-2 --dry-run
  jira-cli backlog move IPG-1 --yes --journal ./backlog.json
"""

HELP["permissions"] = """jira-cli permissions — check project permissions

Usage:
  jira-cli permissions --project KEY [--check A,B] [--format <table|json>]

Reads GET /rest/api/2/mypermissions. --check names are always present in
json output (false when absent).

EXAMPLES:
  jira-cli permissions --project IPG
  jira-cli permissions --project IPG --check MOVE_ISSUES,EDIT_ISSUES --format json
"""

HELP["capabilities"] = """jira-cli capabilities — describe this CLI + server

Usage:
  jira-cli capabilities [--project KEY] [--format <table|json>]
  jira-cli version --json     Same payload (natural alias)

Output: {version, flavor, jira_version, features[], resolved_fields{story_points,sprint,epic_link}}.
flavor comes from GET /rest/api/2/serverInfo deploymentType, cross-checked
with the write-API detection (v3 => cloud).

EXAMPLES:
  jira-cli capabilities --format json
"""
HELP["statuses"] = """jira-cli statuses — list all available statuses for a project

Usage:
  jira-cli statuses [KEY] [--project KEY] [--format <table|json>]

Project resolution: --project/positional KEY > JIRA_PROJECT env > config
'project'/'default_project' key. Output columns: ID, status name,
status ID, category (To Do / In Progress / Done).

Fetch chain (first hit wins): GET project/{key}/statuses, then the
workflowDesigner fallback (Software Simplified Workflow for Project <KEY>),
then the global GET status list (with GET statuscategory enrichment).

EXAMPLES:
  jira-cli statuses IPG
  jira-cli statuses --project IPG --format json
"""



def print_help(topic="main"):
    """Print help text for a topic."""
    text = HELP.get(topic, HELP["main"])
    print(text.strip())
