"""CLI dispatcher — main entry point for jira-cli."""

import sys

from jira_cli.config import load_config
from jira_cli.help_texts import print_help
from jira_cli.flags import parse_flags, has_help_flag, build_jql
from jira_cli.filters import FILTERS
from jira_cli.commands import (
    cmd_projects,
    cmd_search,
    cmd_issue,
    cmd_issue_comments,
    cmd_issue_comment,
    cmd_issue_changelog,
    cmd_issue_add_comment,
    cmd_setup,
    cmd_issue_update_status,
    cmd_issue_update_comment,
    cmd_create_issue,
    cmd_link_issues,
    cmd_issue_update,
    cmd_issue_attach,
    cmd_issue_attachments,
    cmd_issue_download_attachment,
    cmd_issue_delete_attachment,
)
from jira_cli.completion import cmd_completion, cmd_completion_install

def print_usage_err():
    """Print short usage to stderr."""
    print("Usage: jira-cli <command> [args...] [-h]", file=sys.stderr)
    print("Commands: projects, search, issue, create, link, setup, help, completion, completion-install, statuses", file=sys.stderr)


def main():
    """Main entry point — dispatches to sub-commands and exits 0 on success.

    Command handlers may return values (used by tests); they must never
    leak into the setuptools sys.exit(main()) wrapper.
    """
    _dispatch()


def _extract_network_flags():
    """Pull --timeout/--retries/--retry-delay out of argv (global flags) and
    apply them to the http module. Must run before command dispatch."""
    from jira_cli import http

    out = [sys.argv[0]]
    vals = {}
    i = 1
    while i < len(sys.argv):
        a = sys.argv[i]
        if a in ("--timeout", "--retries", "--retry-delay") and i + 1 < len(sys.argv):
            vals[a] = sys.argv[i + 1]
            i += 2
            continue
        out.append(a)
        i += 1
    sys.argv[:] = out
    if vals:
        try:
            http.set_network_settings(
                timeout=vals.get("--timeout"),
                retries=vals.get("--retries"),
                retry_delay=vals.get("--retry-delay"),
            )
        except ValueError:
            print("Error: --timeout/--retries/--retry-delay need numeric values.", file=sys.stderr)
            sys.exit(2)


def _dispatch():
    """Dispatch argv to sub-commands; returns None after each command."""
    _extract_network_flags()
    cfg = load_config()

    # Config check — skip for setup and help
    needs_config = {"projects", "search", "issue", "create", "link", "board",
                    "sprint", "backlog", "permissions", "capabilities", "version", "statuses"}
    cmd = sys.argv[1] if len(sys.argv) > 1 else None
    if cmd not in ("setup", "help", "completion", "completion-install", None):
        if not cfg.get("url") or not cfg.get("user") or not cfg.get("pass"):
            print("Jira not configured.", file=sys.stderr)
            print("  jira-cli setup", file=sys.stderr)
            print("  or: export JIRA_URL=... JIRA_USER=... JIRA_PASS=...", file=sys.stderr)
            sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: jira-cli <command> [args...] [-h]")
        print("Commands: projects, search, issue, create, link, setup, help, completion, completion-install, statuses")
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    # --version (before anything else; no config needed)
    if cmd == "--version":
        from jira_cli import __version__
        print(f"jira-cli {__version__}")
        return

    # --help / -h / help on root command
    if cmd in ("--help", "-h", "help"):
        print_help("main")
        return

    if cmd == "setup":
        if has_help_flag(args):
            print_help("setup")
            return
        return cmd_setup(cfg)

    if cmd == "completion":
        if has_help_flag(args) or not args:
            if not args:
                print("Usage: jira-cli completion <shell>", file=sys.stderr)
                print("Shells: bash, zsh, fish", file=sys.stderr)
                print("  jira-cli completion bash   # print bash completion script", file=sys.stderr)
                print("  jira-cli completion zsh    # print zsh completion script", file=sys.stderr)
                print("  jira-cli completion fish   # print fish completion script", file=sys.stderr)
                return
            print_help("main")
            return
        return cmd_completion(args[0])

    if cmd == "completion-install":
        if has_help_flag(args) or not args:
            print_help("completion-install")
            return
        return cmd_completion_install(args)

    # --- projects ---
    if cmd == "projects":
        if has_help_flag(args):
            print_help("projects")
            return
        return cmd_projects(cfg)

    # --- search ---
    if cmd == "search":
        if has_help_flag(args):
            print_help("search")
            return
        rest, flags = parse_flags(args)
        if flags.get("list_filters"):
            from jira_cli.filters import FILTERS
            print("AVAILABLE SAVED FILTERS:\n")
            for name in sorted(FILTERS.keys()):
                info = FILTERS[name]
                print(f"  {name:20} {info['desc']}")
                print(f"  {'':20} JQL: {info['jql']}")
                print()
            print("EXAMPLES:")
            print("  jira-cli search --saved my-issues                        # single filter")
            print("  jira-cli search --saved my-issues,in-progress            # comma combined")
            print("  jira-cli search --saved my-issues 'project=BANKING'      # filter + JQL")
            print("  jira-cli search --saved todo --limit 5 --format json     # with flags")
            return
        jql = build_jql(flags["saved"], rest)
        if not jql:
            print_help("search")
            sys.exit(1)
        return cmd_search(cfg, jql, flags["limit"], flags["format"],
                          start_at=flags.get("start_at", 0),
                          fetch_all=flags.get("all", False),
                          max_results=flags.get("max_results", 1000),
                          fields=flags.get("fields"),
                          expand=flags.get("expand") or None,
                          envelope=flags.get("envelope", False),
                          changelog_fields=flags.get("changelog_fields"))

    # --- create ---
    if cmd == "create":
        if has_help_flag(args):
            print_help("create")
            return
        rest, flags = parse_flags(args)
        if not flags.get("project") or not flags.get("summary"):
            print("Usage: jira-cli create --project <KEY> --summary \"<text>\" [--type <type>] [--description <text>] [--priority <p>] [--assignee <user>] [--format json]", file=sys.stderr)
            sys.exit(1)
        return cmd_create_issue(
            cfg,
            flags["project"],
            flags["summary"],
            issue_type=flags.get("type") or "Task",
            description=flags.get("description"),
            priority=flags.get("priority"),
            assignee=flags.get("assignee"),
            fmt=flags["format"],
        )

    # --- link ---
    if cmd == "link":
        if has_help_flag(args):
            print_help("link")
            return
        if not args:
            print("Usage: jira-cli link <outward-key> <inward-key> [--type <link-type>] [--comment <text>]", file=sys.stderr)
            sys.exit(1)
        outward = args[0].upper()
        inward = args[1].upper() if len(args) > 1 else None
        if inward is None:
            print("Usage: jira-cli link <outward-key> <inward-key> [--type <link-type>] [--comment <text>]", file=sys.stderr)
            sys.exit(1)
        rest, flags = parse_flags(args[2:])
        return cmd_link_issues(
            cfg,
            outward,
            inward,
            link_type=flags.get("link_type") or "Relates",
            comment=flags.get("comment"),
        )

    # --- issue ---
    if cmd == "issue":
        if has_help_flag(args):
            print_help("issue")
            return
        rest, flags = parse_flags(args)
        if not rest:
            print("Usage: jira-cli issue <issue-key> [subcommand] [args...]", file=sys.stderr)
            print("Subcommands: comments, comment <id>, add-comment, attachments, download, delete-attachment, attach, update, transition, edit-comment", file=sys.stderr)
            sys.exit(1)
        issue_key = rest[0].upper()
        sub = rest[1] if len(rest) > 1 else None

        # issue <key> — detail view (table or json)
        if sub is None:
            return cmd_issue(cfg, issue_key, fmt=flags["format"], include_raw=flags["include_raw"])

        sub_args = rest[2:]

        # issue <key> comments
        if sub == "comments":
            return cmd_issue_comments(
                cfg, issue_key,
                limit=flags["limit"],
                page=flags["page"],
                desc=flags["desc"],
                fmt=flags["format"],
            )

        # issue <key> changelog
        if sub == "changelog":
            return cmd_issue_changelog(
                cfg, issue_key,
                changelog_fields=flags.get("changelog_fields"),
                since=flags.get("since"),
                fmt=flags["format"],
            )

        # issue <key> comment <id>
        if sub == "comment":
            if not sub_args:
                print("Usage: jira-cli issue <issue-key> comment <comment-id> [--format json]", file=sys.stderr)
                sys.exit(1)
            return cmd_issue_comment(cfg, issue_key, sub_args[0], flags["format"])

        # issue <key> add-comment
        if sub == "add-comment":
            return cmd_issue_add_comment(cfg, issue_key, flags["body"])

        # issue <key> transition <id|name>
        if sub == "transition":
            if not sub_args:
                print("Usage: jira-cli issue <issue-key> transition <transition-id-or-name>", file=sys.stderr)
                sys.exit(1)
            return cmd_issue_update_status(cfg, issue_key, sub_args[0],
                                           yes=flags.get("yes", False),
                                           dry_run=flags.get("dry_run", False))

        # issue <key> edit-comment <id>
        if sub == "edit-comment":
            if not sub_args:
                print("Usage: jira-cli issue <issue-key> edit-comment <comment-id> --body <text>", file=sys.stderr)
                sys.exit(1)
            return cmd_issue_update_comment(cfg, issue_key, sub_args[0], flags.get("body", ""),
                                            yes=flags.get("yes", False),
                                            dry_run=flags.get("dry_run", False))

        # issue <key> attachments [--format json]
        if sub == "attachments":
            return cmd_issue_attachments(cfg, issue_key, flags["format"])

        # issue <key> download [<id>...] [--dir <dir>] [--all]
        if sub == "download":
            return cmd_issue_download_attachment(
                cfg, issue_key,
                attachment_ids=sub_args,
                dest_dir=flags.get("dir") or ".",
                all_attachments=flags.get("all", False),
            )

        # issue <key> delete-attachment <id>... | --all
        if sub == "delete-attachment":
            if not sub_args and not flags.get("all"):
                print("Usage: jira-cli issue <issue-key> delete-attachment <attachment-id>... [--all]", file=sys.stderr)
                sys.exit(1)
            return cmd_issue_delete_attachment(
                cfg, issue_key,
                attachment_ids=sub_args,
                all_attachments=flags.get("all", False),
                yes=flags.get("yes", False),
                dry_run=flags.get("dry_run", False),
            )

        # issue <key> attach <file> [<file>...]
        if sub == "attach":
            if not sub_args:
                print("Usage: jira-cli issue <issue-key> attach <file> [<file>...]", file=sys.stderr)
                sys.exit(1)
            return cmd_issue_attach(cfg, issue_key, sub_args)

        # issue <key> update
        if sub == "update":
            return cmd_issue_update(
                cfg, issue_key,
                summary=flags.get("summary"),
                description=flags.get("description"),
                priority=flags.get("priority"),
                assignee=flags.get("assignee"),
                story_points=flags.get("story_points"),
                yes=flags.get("yes", False),
                dry_run=flags.get("dry_run", False),
            )

        print(f"Unknown issue subcommand: {sub}", file=sys.stderr)
        print("Subcommands: comments, comment <id>, add-comment, attachments, download, delete-attachment, attach, update, transition, edit-comment, changelog", file=sys.stderr)
        sys.exit(1)

    # --- board ---
    if cmd == "board":
        if has_help_flag(args) or not args:
            print_help("board")
            return
        rest, flags = parse_flags(args)
        if not rest or rest[0] != "list":
            print("Usage: jira-cli board list [--project KEY] [--format json]", file=sys.stderr)
            sys.exit(1)
        from jira_cli.agile import cmd_board_list
        return cmd_board_list(cfg, project=flags.get("project"), fmt=flags["format"])
    # --- statuses ---
    if cmd == "statuses":
        if has_help_flag(args):
            print_help("statuses")
            return
        rest, flags = parse_flags(args)
        from jira_cli.statuses import cmd_statuses
        key = flags.get("project") or (rest[0] if rest else None)
        return cmd_statuses(cfg, project=key, fmt=flags["format"])


    # --- sprint ---
    if cmd == "sprint":
        if has_help_flag(args) or not args:
            print_help("sprint")
            return
        sub = args[0]
        rest, flags = parse_flags(args[1:])
        from jira_cli.agile import (cmd_sprint_list, cmd_sprint_get,
                                    cmd_sprint_issues, cmd_sprint_current,
                                    cmd_sprint_move, cmd_sprint_restore)
        if sub == "list":
            if not flags.get("board"):
                print("Usage: jira-cli sprint list --board ID [--state active,future,closed] [--last N] [--format json]",
                      file=sys.stderr)
                sys.exit(1)
            return cmd_sprint_list(cfg, flags["board"], state=flags.get("state"),
                                   last=flags.get("last"), fmt=flags["format"])
        if sub == "get":
            if not rest:
                print("Usage: jira-cli sprint get ID [--format json]", file=sys.stderr)
                sys.exit(1)
            return cmd_sprint_get(cfg, rest[0], fmt=flags["format"])
        if sub == "issues":
            if not rest:
                print("Usage: jira-cli sprint issues ID [--fields a,b] [--all] [--format json]",
                      file=sys.stderr)
                sys.exit(1)
            return cmd_sprint_issues(cfg, rest[0], fields=flags.get("fields"),
                                     fetch_all=flags.get("all", False),
                                     max_results=flags.get("max_results", 1000),
                                     fmt=flags["format"])
        if sub == "current":
            if not flags.get("board"):
                print("Usage: jira-cli sprint current --board ID [--format json]", file=sys.stderr)
                sys.exit(1)
            return cmd_sprint_current(cfg, flags["board"], fmt=flags["format"])
        if sub == "move":
            sprint_id = flags.get("sprint")
            keys = [k for k in rest if "-" in k]
            if not sprint_id or not keys:
                print("Usage: jira-cli sprint move --sprint ID K1 K2 ... [--dry-run] [--yes] [--journal PATH]",
                      file=sys.stderr)
                sys.exit(1)
            return cmd_sprint_move(cfg, sprint_id, keys, journal=flags.get("journal"),
                                   yes=flags.get("yes", False), dry_run=flags.get("dry_run", False))
        if sub == "restore":
            journal = flags.get("journal") or (rest[0] if rest else None)
            if not journal:
                print("Usage: jira-cli sprint restore --journal FILE [--dry-run] [--yes]",
                      file=sys.stderr)
                sys.exit(1)
            return cmd_sprint_restore(cfg, journal, yes=flags.get("yes", False),
                                      dry_run=flags.get("dry_run", False))
        print(f"Unknown sprint subcommand: {sub}", file=sys.stderr)
        print("Subcommands: list, get, issues, current, move, restore", file=sys.stderr)
        sys.exit(1)

    # --- backlog ---
    if cmd == "backlog":
        if has_help_flag(args) or not args:
            print_help("backlog")
            return
        if args[0] != "move":
            print("Usage: jira-cli backlog move K1 K2 ... [--dry-run] [--yes] [--journal PATH]",
                  file=sys.stderr)
            sys.exit(1)
        rest, flags = parse_flags(args[1:])
        keys = [k for k in rest if "-" in k]
        if not keys:
            print("Usage: jira-cli backlog move K1 K2 ... [--dry-run] [--yes] [--journal PATH]",
                  file=sys.stderr)
            sys.exit(1)
        from jira_cli.agile import cmd_backlog_move
        return cmd_backlog_move(cfg, keys, journal=flags.get("journal"),
                                yes=flags.get("yes", False), dry_run=flags.get("dry_run", False))

    # --- permissions ---
    if cmd == "permissions":
        if has_help_flag(args):
            print_help("permissions")
            return
        rest, flags = parse_flags(args)
        if not flags.get("project"):
            print("Usage: jira-cli permissions --project KEY [--check A,B] [--format json]",
                  file=sys.stderr)
            sys.exit(1)
        from jira_cli.agile import cmd_permissions
        return cmd_permissions(cfg, flags["project"], check=flags.get("check") or (),
                               fmt=flags["format"])

    # --- version (alias for --version; --json gives capabilities) ---
    if cmd == "version":
        if has_help_flag(args):
            print_help("main")
            return
        rest, flags = parse_flags(args)
        if flags["format"] == "json":
            from jira_cli.agile import cmd_capabilities
            return cmd_capabilities(cfg, project=flags.get("project"), fmt="json")
        from jira_cli import __version__
        print(f"jira-cli {__version__}")
        return

    # --- capabilities ---
    if cmd == "capabilities":
        if has_help_flag(args):
            print_help("capabilities")
            return
        rest, flags = parse_flags(args)
        from jira_cli.agile import cmd_capabilities
        return cmd_capabilities(cfg, project=flags.get("project"), fmt=flags["format"])

    # --- unknown ---
    print(f"Unknown: {cmd}", file=sys.stderr)
    print_usage_err()
    sys.exit(1)


if __name__ == "__main__":
    main()
