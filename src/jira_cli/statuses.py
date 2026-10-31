"""Project statuses: per-project status list with categories and transitions.

Fetch chain (first hit wins):
  1. GET /rest/api/2/project/{key}/statuses — public, per-project (Cloud + newer DC).
  2. GET /rest/api/2/status + GET /rest/api/2/statuscategory — global fallback,
     filtered to statuses actually used by the project via the issue-type/status
     mapping (GET /rest/api/2/project/{key}/statuses is preferred when present).
  3. GET /rest/workflowDesigner/latest/workflows?name=Software Simplified
     Workflow for Project <KEY>&draft=false — private UI endpoint the user
     asked to generalize; parses statuses + workflow transitions.
"""

import json
import os
import urllib.parse
import urllib.request

from jira_cli.http import auth_header, jira_get


def resolve_project_key(cfg, explicit=None):
    """Resolve project key: explicit > JIRA_PROJECT env > config file keys."""
    if explicit:
        return str(explicit).strip().upper()
    env = (os.environ.get("JIRA_PROJECT") or "").strip()
    if env:
        return env.upper()
    for k in ("project", "default_project", "defaultProject"):
        v = (cfg.get(k) or "").strip() if isinstance(cfg.get(k), str) else ""
        if v:
            return v.upper()
    return ""


def _raw_get(cfg, base_path, params=None):
    """GET against a non-/rest/api/N/ path (e.g. /rest/workflowDesigner/...)."""
    from jira_cli.http import _send

    url = f"{cfg['url']}/{base_path.lstrip('/')}"
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers=auth_header(cfg), method="GET")
    req.add_header("Accept", "application/json")
    return _send(req)


def _category_name(status):
    """Extract category name from a status object (several shapes)."""
    cat = status.get("statusCategory") or {}
    if isinstance(cat, dict):
        return cat.get("name") or ""
    if isinstance(status.get("category"), str):
        return status["category"]
    return ""


def _normalize_status(entry):
    """Normalize one status to {id, name, status_id, category}."""
    sid = entry.get("id") or entry.get("statusId") or entry.get("status_id") or ""
    name = entry.get("name") or ""
    return {
        "id": str(sid),
        "name": str(name),
        "status_id": str(entry.get("statusId") or sid),
        "category": _category_name(entry) or entry.get("statusCategoryName") or "",
    }


def _from_public_project_statuses(data):
    """Parse GET project/{key}/statuses (list of {id,name,statusCategory,...})."""
    if isinstance(data, dict):
        for k in ("statuses", "values"):
            if isinstance(data.get(k), list):
                data = data[k]
                break
    if not isinstance(data, list):
        return []
    return [_normalize_status(s) for s in data if isinstance(s, dict)]


def _from_issue_type_statuses(data):
    """Parse GET project/{key} issueTypes[].statuses (per-issue-type shape)."""
    seen = {}
    issue_types = data.get("issueTypes") if isinstance(data, dict) else None
    if not isinstance(issue_types, list):
        return []
    for it in issue_types:
        for s in it.get("statuses") or []:
            if not isinstance(s, dict):
                continue
            row = _normalize_status(s)
            seen.setdefault(row["id"] or row["name"], row)
    return list(seen.values())


def _from_workflow_designer(data):
    """Parse workflowDesigner workflows payload -> (statuses, transitions)."""
    wfs = data if isinstance(data, list) else (data.get("workflows") if isinstance(data, dict) else None)
    if isinstance(data, dict) and not wfs:
        # Single-workflow payload shape.
        wfs = [data] if "statuses" in data else None
    if not wfs:
        return [], []
    statuses, transitions = {}, []
    for wf in wfs:
        if not isinstance(wf, dict):
            continue
        for s in wf.get("statuses") or []:
            if not isinstance(s, dict):
                continue
            row = _normalize_status(s)
            statuses.setdefault(row["id"] or row["name"], row)
        for t in wf.get("transitions") or []:
            if not isinstance(t, dict):
                continue
            transitions.append({"id": str(t.get("id") or ""), "name": str(t.get("name") or ""),
                                "from": str(t.get("from") or t.get("fromStatus") or ""),
                                "to": str(t.get("to") or t.get("toStatus") or "")})
    return list(statuses.values()), transitions


def _enrich_categories(cfg, rows):
    """Fill blank categories via GET statuscategory lookup (id or key match)."""
    if not rows or all(r.get("category") for r in rows):
        return rows
    try:
        cats = jira_get(cfg, "statuscategory")
    except SystemExit:
        return rows
    if isinstance(cats, dict):
        cats = cats.get("values", [])
    by_id = {}
    for c in cats if isinstance(cats, list) else []:
        if not isinstance(c, dict):
            continue
        if c.get("id") is not None:
            by_id[str(c["id"])] = c.get("name") or ""
    for r in rows:
        if r.get("category"):
            continue
        # Status objects sometimes carry the category id/key instead of the name.
        for cand in (str(r.get("id") or ""), str(r.get("status_id") or "")):
            if cand in by_id:
                r["category"] = by_id[cand]
                break
    return rows


def fetch_project_statuses(cfg, project):
    """Return (statuses, transitions, source) for a project key."""
    # 1. Public per-project endpoint (Cloud + newer DC).
    try:
        data = jira_get(cfg, f"project/{project}/statuses")
        rows = _from_public_project_statuses(data)
        if not rows:
            rows = _from_issue_type_statuses(data)
        if rows:
            return _enrich_categories(cfg, rows), [], "project-statuses"
    except SystemExit:
        pass
    # 2. workflowDesigner fallback (private UI endpoint, generalized by name).
    try:
        data = _raw_get(cfg, "rest/workflowDesigner/latest/workflows", {
            "name": f"Software Simplified Workflow for Project {project}",
            "draft": "false",
        })
        rows, transitions = _from_workflow_designer(data)
        if rows:
            return _enrich_categories(cfg, rows), transitions, "workflow-designer"
    except SystemExit:
        pass
    # 3. Global status list (no project scoping possible).
    data = jira_get(cfg, "status")
    items = data if isinstance(data, list) else data.get("values", [])
    rows = [_normalize_status(s) for s in items if isinstance(s, dict)]
    return _enrich_categories(cfg, rows), [], "global-statuses"


def cmd_statuses(cfg, project=None, fmt="table"):
    """List all available statuses for a project. Returns normalized rows."""
    key = resolve_project_key(cfg, project)
    if not key:
        print("Usage: jira-cli statuses [KEY] [--project KEY] [--format json]", file=__import__("sys").stderr)
        print("No project key given and no default (JIRA_PROJECT env or config 'project').", file=__import__("sys").stderr)
        __import__("sys").exit(2)
    rows, transitions, source = fetch_project_statuses(cfg, key)
    if fmt == "json":
        print(json.dumps({"project": key, "source": source, "statuses": rows,
                          "transitions": transitions}, indent=2, ensure_ascii=False))
        return rows
    if not rows:
        print(f"No statuses found for project {key}.")
        return []
    print(f"\nStatuses for {key} ({len(rows)} statuses, via {source})")
    print(f"  {'ID':6}  {'Status':28} {'Status ID':10}  Category")
    print("  " + "-" * 70)
    for r in rows:
        print(f"  {r['id'][:6]:6}  {r['name'][:28]:28} {r['status_id'][:10]:10}  {r['category']}")
    if transitions:
        print(f"\n  Transitions ({len(transitions)}):")
        for t in transitions[:20]:
            arrow = f"{t['from']} -> {t['to']}" if t["from"] or t["to"] else t["name"]
            print(f"    {t['id']:6}  {t['name'][:30]:30}  {arrow}")
        if len(transitions) > 20:
            print(f"    ... and {len(transitions) - 20} more (use --format json)")
    print()
    return rows
