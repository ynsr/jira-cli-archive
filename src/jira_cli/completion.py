"""Command: completion — print shell completion scripts for bash, zsh, or fish."""

import os
import re
import shutil
import sys
from pathlib import Path

import shlex
_COMPLETION_COMMANDS = [
    "projects",
    "search",
    "create",
    "link",
    "issue",
    "board",
    "sprint",
    "backlog",
    "permissions",
    "statuses",
    "capabilities",
    "version",
    "setup",
    "help",
    "completion",
]

_COMPLETION_SUBCOMMANDS = {
    "issue": ["comments", "comment", "add-comment", "attachments", "download", "delete-attachment", "attach", "update", "transition", "edit-comment", "changelog"],
    "board": ["list"],
    "sprint": ["list", "get", "issues", "current", "move", "restore"],
    "backlog": ["move"],
    "completion": ["bash", "zsh", "fish", "install"],
}

_COMPLETION_FLAGS = {
    "search": ["--limit", "--saved", "--list-filters", "--format", "--start-at", "--max-results", "--all", "--fields", "--expand", "--envelope", "--changelog-fields"],
    "issue": ["--limit", "--page", "--desc", "--format", "--body", "--changelog-fields", "--since"],
    "create": ["--project", "--summary", "--type", "--description", "--priority", "--assignee", "--format"],
    "link": ["--type", "--comment"],
    "board": ["--project", "--format"],
    "sprint": ["--board", "--state", "--last", "--sprint", "--journal", "--fields", "--all", "--format", "--yes", "--dry-run"],
    "backlog": ["--journal", "--yes", "--dry-run"],
    "permissions": ["--project", "--check", "--format"],
    "statuses": ["--project", "--format"],
    "capabilities": ["--project", "--format"],
    "issue-update": ["--summary", "--description", "--priority", "--assignee", "--story-points"],
    "issue-transition": [],
    "issue-edit-comment": ["--body"],
}


def cmd_completion(shell):
    """Print a shell completion script for bash, zsh, or fish."""
    shell = shell.lower().strip()
    if shell == "bash":
        print(_bash_completion())
    elif shell == "zsh":
        print(_zsh_completion())
    elif shell == "fish":
        print(_fish_completion())
    else:
        print(f"Unknown shell: {shell}", file=__import__("sys").stderr)
        print("Supported shells: bash, zsh, fish", file=__import__("sys").stderr)
        __import__("sys").exit(1)


def _bash_completion():
    """Generate bash completion script."""
    cmds = " ".join(_COMPLETION_COMMANDS) + " completion-install"
    return f"""# bash completion for jira-cli
_jira_cli()
{{
    local cur prev words cword
    _init_completion -s || return

    # top-level commands
    if [[ $cword -eq 1 ]]; then
        COMPREPLY=($(compgen -W "{cmds}" -- "$cur"))
        return
    fi

    # sub-commands / flags
    case "${{words[1]}}" in
        search)
            if [[ "$cur" == -* ]]; then
                COMPREPLY=($(compgen -W "--limit --saved --list-filters --format --help -h" -- "$cur"))
            fi
            ;;
        issue)
            if [[ $cword -eq 2 ]]; then
                if [[ "$cur" == -* ]]; then
                    COMPREPLY=($(compgen -W "--help -h" -- "$cur"))
                fi
            elif [[ $cword -eq 3 ]]; then
                local subs="comments comment add-comment attachments download delete-attachment attach update transition edit-comment"
                COMPREPLY=($(compgen -W "$subs" -- "$cur"))
            elif [[ $cword -ge 4 ]]; then
                case "${{words[3]}}" in
                    download)
                        COMPREPLY=($(compgen -W "--dir --all --help -h" -- "$cur"))
                        ;;
                    delete-attachment)
                        COMPREPLY=($(compgen -W "--all --yes --dry-run --help -h" -- "$cur"))
                        ;;
                    attach)
                        if [[ "$cur" != -* ]]; then
                            # complete local file paths
                            COMPREPLY=($(compgen -f -- "$cur"))
                        else
                            COMPREPLY=($(compgen -W "--help -h" -- "$cur"))
                        fi
                        ;;
                    comments)
                        COMPREPLY=($(compgen -W "--limit --page --desc --format --help -h" -- "$cur"))
                        ;;
                    update)
                        COMPREPLY=($(compgen -W "--summary --description --priority --assignee --story-points --yes --dry-run --help -h" -- "$cur"))
                        ;;
                    transition)
                        COMPREPLY=($(compgen -W "--yes --dry-run --help -h" -- "$cur"))
                        ;;
                    edit-comment)
                        COMPREPLY=($(compgen -W "--body --yes --dry-run --help -h" -- "$cur"))
                        ;;
                    comment)
                        if [[ "$cur" != -* ]]; then
                            # suggest numeric IDs; no dynamic lookup
                            COMPREPLY=()
                        else
                            COMPREPLY=($(compgen -W "--format --help -h" -- "$cur"))
                        fi
                        ;;
                    add-comment)
                        COMPREPLY=($(compgen -W "--body --help -h" -- "$cur"))
                        ;;
                esac
            fi
            ;;
        completion)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "bash zsh fish" -- "$cur"))
            fi
            ;;
        completion-install)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "bash zsh fish" -- "$cur"))
            elif [[ "$cur" == -* ]]; then
                COMPREPLY=($(compgen -W "--rcfile --yes --help -h" -- "$cur"))
            fi
            ;;
        *)
            if [[ "$cur" == -* ]]; then
                COMPREPLY=($(compgen -W "--help -h --version" -- "$cur"))
            fi
            ;;
    esac
}} && complete -F _jira_cli jira-cli
"""


def _zsh_completion():
    """Generate zsh completion script."""
    return """#compdef jira-cli

_jira_cli_commands() {
    local -a commands
    commands=(
        'projects:List all projects'
        'search:Search issues with JQL or saved filters'
        'create:Create a new issue'
        'link:Link two issues'
        'issue:Show issue detail and work with comments'
        'setup:Configure Jira credentials'
        'help:Print help text'
        'completion:Print a shell completion script'
        'completion-install:Install the completion eval line into your rc file'
    )
    _describe -t commands 'command' commands
}

_jira_cli_issue_sub() {
    local -a subs
    subs=(
        'comments:List paginated comments'
        'comment:Show full comment detail'
        'add-comment:Add a comment to an issue'
        'attachments:List attachment file(s)'
        'download:Download attachment file(s)'
        'delete-attachment:Delete attachment file(s)'
        'attach:Upload attachment file(s)'
        'update:Update summary/description/priority/assignee/story-points'
        'transition:Transition issue to a new status'
        'edit-comment:Edit an existing comment body'
    )
    _describe -t subcommands 'subcommand' subs
}

_jira_cli_completion_shells() {
    local -a shells
    shells=('bash:Bash shell' 'zsh:Zsh shell' 'fish:Fish shell')
    _describe -t shells 'shell' shells
}

_jira_cli() {
    local context state state_descr line
    typeset -A opt_args

    _arguments -C \\
        '(- *)'{-h,--help}'[Show help]' \\
        '1:command:->cmds' \\
        '*::arg:->args'

    case "$state" in
        cmds)
            _jira_cli_commands
            ;;
        args)
            case "$words[1]" in
                search)
                    _arguments \\
                        '(-h --help)'{-h,--help}'[Show help]' \\
                        '--limit=[Max results]:number' \\
                        '--saved=[Saved filter]:filter' \\
                        '--list-filters[List saved filters]' \\
                        '--format=[Output format]:format:(table json)' \\
                        '*:JQL string'
                    ;;
                create)
                    _arguments \\
                        '(-h --help)'{-h,--help}'[Show help]' \\
                        '--project=[Project key]:key' \\
                        '--summary=[Issue summary]:text' \\
                        '--type=[Issue type]:type:(Task Bug Story Epic)' \\
                        '--description=[Issue description]:text' \\
                        '--priority=[Priority]:priority:(Highest High Medium Low Lowest)' \\
                        '--assignee=[Assignee username]:user' \\
                        '--format=[Output format]:format:(table json)'
                    ;;
                link)
                    _arguments \\
                        '(-h --help)'{-h,--help}'[Show help]' \\
                        '--type=[Link type]:type:(Relates Blocks Duplicate)' \\
                        '--comment=[Link comment]:text' \\
                        '*:issue keys'
                    ;;
                issue)
                    if [[ $CURRENT -eq 3 ]]; then
                        _arguments '(-h --help)'{-h,--help}'[Show help]'
                        _jira_cli_issue_sub
                    elif [[ $CURRENT -eq 4 ]]; then
                        # sub-args
                        case "$words[3]" in
            comments)
                _arguments \\
                    '(-h --help)'{-h,--help}'[Show help]' \\
                    '--limit=[Comments per page]:number' \\
                    '--page=[Page number]:number' \\
                    '--desc[Newest-first order]' \\
                    '--format=[Output format]:format:(table json)'
                ;;
            comment)
                _arguments \\
                    '(-h --help)'{-h,--help}'[Show help]' \\
                    '--format=[Output format]:format:(table json)' \\
                    '*:comment ID'
                ;;
add-comment)
                    _arguments \\
                        '(-h --help)'{-h,--help}'[Show help]' \\
                        '--body=[Comment body text]:text'
                ;;
            attach)
                    _arguments \\
                        '(-h --help)'{-h,--help}'[Show help]' \\
                        '*:file:_files'
                ;;
            attachments)
                    _arguments \\
                        '(-h --help)'{-h,--help}'[Show help]' \\
                        '--format=[Output format]:format:(table json)'
                ;;
            download)
                    _arguments \\
                        '(-h --help)'{-h,--help}'[Show help]' \\
                        '--dir=[Destination directory]:dir:_directories' \\
                        '--all[Download every attachment]' \\
                        '*:attachment id'
                ;;
            delete-attachment)
                    _arguments \\
                        '(-h --help)'{-h,--help}'[Show help]' \\
                        '--all[Delete every attachment]' \\
                        '*:attachment id'
                ;;
            update)
                _arguments \\
                    '(-h --help)'{-h,--help}'[Show help]' \\
                    '--summary=[New summary]:text' \\
                    '--description=[New description]:text' \\
                    '--priority=[Priority]:priority:(Highest High Medium Low Lowest)' \\
                    '--assignee=[Assignee username]:user' \
                    '--story-points=[Story points]:points'
                ;;
                        esac
                    fi
                    ;;
                completion)
                    _arguments '1:shell:->shells'
                    ;;
                completion-install)
                    if [[ $CURRENT -eq 3 ]]; then
                        _jira_cli_completion_shells
                    else
                        _arguments '--rcfile=[Rc file to edit]:file:_files' '--yes[Skip confirmation]'
                    fi
                    ;;
                *)
                    _arguments '(-h --help)'{-h,--help}'[Show help]'
                    ;;
            esac
            ;;
        shells)
            _jira_cli_completion_shells
            ;;
    esac
}

# Registered for eval-style install: `eval "$(jira-cli completion zsh)"` in ~/.zshrc.
compdef _jira_cli jira-cli
"""


def _fish_completion():
    """Generate fish completion script."""
    return """# fish completion for jira-cli
function __fish_jira_cli_needs_command
    set -l cmd (commandline -opc)
    if [ (count $cmd) -eq 1 ]
        return 0
    end
    return 1
end

function __fish_jira_cli_using_command
    set -l cmd (commandline -opc)
    if [ (count $cmd) -gt 1 ]
        if [ $argv[1] = $cmd[2] ]
            return 0
        end
    end
    return 1
end

function __fish_jira_cli_using_subcommand
    # True when $argv[1] appears as a subcommand token after the program name,
    # e.g. `jira-cli issue <KEY> comments` -> __fish_jira_cli_using_subcommand comments
    set -l cmd (commandline -opc)
    if [ (count $cmd) -ge 3 ]
        if contains -- $argv[1] $cmd[3..-1]
            return 0
        end
    end
    return 1
end
# top-level commands
complete -c jira-cli -f -n '__fish_jira_cli_needs_command' -a projects -d 'List all projects'
complete -c jira-cli -f -n '__fish_jira_cli_needs_command' -a search -d 'Search issues with JQL or saved filters'
complete -c jira-cli -f -n '__fish_jira_cli_needs_command' -a issue -d 'Show issue detail and work with comments'
complete -c jira-cli -f -n '__fish_jira_cli_needs_command' -a setup -d 'Configure Jira credentials'
complete -c jira-cli -f -n '__fish_jira_cli_needs_command' -a help -d 'Print help text'
complete -c jira-cli -f -n '__fish_jira_cli_needs_command' -a completion -d 'Print a shell completion script'

# global flags
complete -c jira-cli -f -n '__fish_jira_cli_needs_command' -s h -l help -d 'Show help'

# search flags
complete -c jira-cli -f -n '__fish_jira_cli_using_command search' -s h -l help -d 'Show help'
complete -c jira-cli -f -n '__fish_jira_cli_using_command search' -l limit -d 'Max results'
complete -c jira-cli -f -n '__fish_jira_cli_using_command search' -l saved -d 'Saved filter (comma-separated)'
complete -c jira-cli -f -n '__fish_jira_cli_using_command search' -l list-filters -d 'List saved filters'
complete -c jira-cli -f -n '__fish_jira_cli_using_command search' -l format -d 'Output format' -xa 'table json'

# create flags
complete -c jira-cli -f -n '__fish_jira_cli_using_command create' -s h -l help -d 'Show help'
complete -c jira-cli -f -n '__fish_jira_cli_using_command create' -l project -d 'Project key'
complete -c jira-cli -f -n '__fish_jira_cli_using_command create' -l summary -d 'Issue summary'
complete -c jira-cli -f -n '__fish_jira_cli_using_command create' -l type -d 'Issue type' -xa 'Task Bug Story Epic'
complete -c jira-cli -f -n '__fish_jira_cli_using_command create' -l description -d 'Issue description'
complete -c jira-cli -f -n '__fish_jira_cli_using_command create' -l priority -d 'Priority' -xa 'Highest High Medium Low Lowest'
complete -c jira-cli -f -n '__fish_jira_cli_using_command create' -l assignee -d 'Assignee username'
complete -c jira-cli -f -n '__fish_jira_cli_using_command create' -l format -d 'Output format' -xa 'table json'

# link flags
complete -c jira-cli -f -n '__fish_jira_cli_using_command link' -s h -l help -d 'Show help'
complete -c jira-cli -f -n '__fish_jira_cli_using_command link' -l type -d 'Link type' -xa 'Relates Blocks Duplicate'
complete -c jira-cli -f -n '__fish_jira_cli_using_command link' -l comment -d 'Link comment'

# issue subcommands
complete -c jira-cli -f -n '__fish_jira_cli_using_command issue' -a comments -d 'List paginated comments'
complete -c jira-cli -f -n '__fish_jira_cli_using_command issue' -a 'comment' -d 'Show full comment detail'
complete -c jira-cli -f -n '__fish_jira_cli_using_command issue' -a 'add-comment' -d 'Add a comment'
complete -c jira-cli -f -n '__fish_jira_cli_using_command issue' -a 'attachments' -d 'List attachment file(s)'
complete -c jira-cli -f -n '__fish_jira_cli_using_command issue' -a 'download' -d 'Download attachment file(s)'
complete -c jira-cli -f -n '__fish_jira_cli_using_command issue' -a 'delete-attachment' -d 'Delete attachment file(s)'
complete -c jira-cli -f -n '__fish_jira_cli_using_command issue' -a 'attach' -d 'Upload attachment file(s)'
complete -c jira-cli -f -n '__fish_jira_cli_using_command issue' -a 'update' -d 'Update summary/description/priority/assignee/story-points'
complete -c jira-cli -f -n '__fish_jira_cli_using_command issue' -a 'transition' -d 'Transition issue to a new status'
complete -c jira-cli -f -n '__fish_jira_cli_using_command issue' -a 'edit-comment' -d 'Edit an existing comment body'
complete -c jira-cli -f -n '__fish_jira_cli_using_command issue' -s h -l help -d 'Show help'

# issue comments flags
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand comments' -s h -l help -d 'Show help'
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand comments' -l limit -d 'Comments per page'
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand comments' -l page -d 'Page number'
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand comments' -l desc -d 'Newest-first order'
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand comments' -l format -d 'Output format' -xa 'table json'

# issue comment flags
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand comment' -s h -l help -d 'Show help'
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand comment' -l format -d 'Output format' -xa 'table json'

# issue add-comment flags
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand add-comment' -s h -l help -d 'Show help'
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand add-comment' -l body -d 'Comment body text'

# issue attach files
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand attach' -a '(__fish_complete_path)'

# issue attachments flags
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand attachments' -s h -l help -d 'Show help'
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand attachments' -l format -d 'Output format' -xa 'table json'

# issue download flags
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand download' -s h -l help -d 'Show help'
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand download' -l dir -d 'Destination directory' -a '(__fish_complete_directories)'
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand download' -l all -d 'Download every attachment'

# issue delete-attachment flags
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand delete-attachment' -s h -l help -d 'Show help'
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand delete-attachment' -l all -d 'Delete every attachment'

# issue update flags
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand update' -s h -l help -d 'Show help'
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand update' -l summary -d 'New summary'
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand update' -l description -d 'New description'
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand update' -l priority -d 'Priority' -xa 'Highest High Medium Low Lowest'
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand update' -l assignee -d 'Assignee username'
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand update' -l story-points -d 'Story points (number)'

# issue transition flags
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand transition' -s h -l help -d 'Show help'

# issue edit-comment flags
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand edit-comment' -s h -l help -d 'Show help'
complete -c jira-cli -f -n '__fish_jira_cli_using_subcommand edit-comment' -l body -d 'Comment body text'

# completion subcommand
complete -c jira-cli -f -n '__fish_jira_cli_using_command completion' -a bash -d 'Bash completions'
complete -c jira-cli -f -n '__fish_jira_cli_using_command completion' -a zsh -d 'Zsh completions'
complete -c jira-cli -f -n '__fish_jira_cli_using_command completion' -a fish -d 'Fish completions'
complete -c jira-cli -f -n '__fish_jira_cli_using_command completion' -a install -d 'Install completion into rc file'
"""


# ---------------------------------------------------------------------------
# completion-install — idempotent marker-block rc editor
# ---------------------------------------------------------------------------

PROG = "jira-cli"
SUPPORTED_SHELLS = ("bash", "zsh", "fish")
RC_FILES = {
    "bash": "~/.bashrc",
    "zsh": "~/.zshrc",
    "fish": "~/.config/fish/config.fish",
}
START_MARKER = f"# >>> {PROG} completions >>>"
END_MARKER = f"# <<< {PROG} completions <<<"


def detect_shell():
    """Best-effort shell name from $SHELL; None if unknown/unsupported."""
    shell = os.path.basename(os.environ.get("SHELL", "")).strip()
    return shell if shell in SUPPORTED_SHELLS else None


def eval_line(shell):
    """The rc line the user sources. fish pipes instead of eval."""
    if shell == "fish":
        return f"{PROG} completion fish | source"
    return f'eval "$({PROG} completion {shell})"'


def install_snippet(shell):
    """Marker block written into the rc file. zsh needs compinit first."""
    lines = [START_MARKER]
    if shell == "zsh":
        lines.append("autoload -U compinit && compinit")
    lines.append(eval_line(shell))
    lines.append(END_MARKER)
    return "\n".join(lines) + "\n"


def install_completion(shell, rcfile=None):
    """Idempotently ensure the marker block is in the rc file.

    Returns (rc path, changed). Atomic write (tmp + rename); keeps a ``.bak``
    copy before the first modification. Re-running is a byte-identical no-op.
    A stale block from an older install is replaced, not duplicated.
    Raises ValueError on unsupported shell.
    """
    if shell not in SUPPORTED_SHELLS:
        raise ValueError(f"unsupported shell {shell!r} (choose from: {', '.join(SUPPORTED_SHELLS)})")
    rc = Path(rcfile).expanduser() if rcfile else Path(RC_FILES[shell]).expanduser()
    snippet = install_snippet(shell)
    existing = rc.read_text(encoding="utf-8") if rc.is_file() else ""
    if snippet.strip() in existing:
        return rc, False
    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER) + r"\n?",
        re.DOTALL,
    )
    if pattern.search(existing):
        updated = pattern.sub(lambda _m: snippet, existing)
    else:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        updated = existing + snippet
    rc.parent.mkdir(parents=True, exist_ok=True)
    if rc.is_file():
        shutil.copy2(rc, rc.parent / (rc.name + ".bak"))
    tmp = rc.parent / (rc.name + ".tmp")
    tmp.write_text(updated, encoding="utf-8")
    tmp.replace(rc)
    return rc, True


def _install_usage():
    """Print completion-install usage to stderr."""
    print("Usage: jira-cli completion-install [shell] [--rcfile PATH] [--yes]", file=sys.stderr)
    print("Shells: bash, zsh, fish (omit to detect from $SHELL)", file=sys.stderr)


def cmd_completion_install(args):
    """Install the completion eval line into the shell rc file (idempotent).

    Requires --yes when stdin is not a TTY; on a TTY confirms before editing.
    """
    shell = None
    rcfile = None
    yes = False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--rcfile" and i + 1 < len(args):
            rcfile = args[i + 1]
            i += 2
        elif a.startswith("--rcfile="):
            rcfile = a.split("=", 1)[1]
            i += 1
        elif a == "--yes":
            yes = True
            i += 1
        elif a.startswith("-"):
            print(f"Unknown option: {a}", file=sys.stderr)
            _install_usage()
            sys.exit(2)
        else:
            shell = a
            i += 1

    if shell is None:
        shell = detect_shell()
        if shell is None:
            print(f"Error: cannot detect shell from $SHELL={os.environ.get('SHELL', '')!r}; pass bash, zsh, or fish explicitly.", file=sys.stderr)
            sys.exit(2)
    if shell.lower() not in SUPPORTED_SHELLS:
        print(f"Unknown shell: {shell}", file=sys.stderr)
        print("Supported shells: bash, zsh, fish", file=sys.stderr)
        sys.exit(2)
    shell = shell.lower()

    if not yes:
        if sys.stdin.isatty():
            try:
                answer = input(f"Add {PROG} completion to your {shell} rc file? [y/N] ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                answer = ""
            if answer not in ("y", "yes"):
                print("Aborted.", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"Error: editing the {shell} rc file non-interactively requires --yes (or run interactively).", file=sys.stderr)
            sys.exit(2)

    try:
        rc, changed = install_completion(shell, rcfile)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)
    if changed:
        print(f"installed {PROG} completion for {shell} in {rc}", file=sys.stderr)
        print(f"restart your shell or run: source {rc}", file=sys.stderr)
    else:
        print(f"already installed in {rc}", file=sys.stderr)
