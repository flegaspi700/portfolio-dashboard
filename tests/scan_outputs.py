"""Made-up scan output for the report and page tests (S3.1.1, E4).

The same shape `privacy/output.py` writes to `output/scan.json`: the
filtered scan output, never the scan result. Names and values are invented.
"""

import json


def private_row(name, **overrides):
    """A private row with every allow-list field set, plus overrides."""
    row = {
        "name": name,
        "visibility": "private",
        "lifecycle": "active",
        "health": "green",
        "level": 3,
        "last_activity": "2026-11-28",
        "risk_count": 2,
        "blocker_count": 0,
        "scan_status": "ok",
    }
    row.update(overrides)
    return row


def public_row(name, **overrides):
    """A public row in the full shape the filter passes: every scan field,
    plus the signal fields, plus overrides."""
    row = {
        "name": name,
        "visibility": "public",
        "scan_status": "ok",
        "scan_error": None,
        "pushed_at": "2026-11-28T22:30:00+00:00",
        "created_at": "2025-03-01T00:00:00+00:00",
        "language": "Python",
        "description": "A made-up public project",
        "default_branch": "main",
        "open_issues": 3,
        "open_prs": 1,
        "level": 2,
        "level_name": "Adopted",
        "standard_version": "v2.0.0",
        "checks": {"C8": True, "C2": True, "C4": True, "C10": False, "C5": None},
        "warnings": [{"id": "S3", "check_id": "C10", "required_from": "2026-12-13"}],
        "has_portfolio": True,
        "health": "amber",
        "reported": {
            "schema": 1,
            "name": name,
            "summary": "Tracks the made-up things.",
            "lifecycle": "active",
            "health": "amber",
            "health_reason": "Behind on the made-up milestone.",
            "risks": [
                {"title": "Made-up risk", "severity": "high", "mitigation": "Watch it."}
            ],
            "blockers": [
                {"title": "Made-up blocker", "since": "2026-11-01", "needs": "A yes."}
            ],
            "callouts": ["A made-up call-out."],
            "next_milestone": {"name": "Made-up release", "date": "2026-12-20"},
            "updated": "2026-11-20",
        },
        "portfolio_problem": None,
        "lifecycle": "active",
        "last_activity": "2026-11-28",
        "risk_count": 1,
        "blocker_count": 1,
    }
    row.update(overrides)
    return row


# The standard's checks as the scan output carries them (S4.3.1).
CHECKS = [
    {
        "id": "C8",
        "title": "Names the standard",
        "severity": "required",
        "fix": "Add C8.",
    },
    {
        "id": "C2",
        "title": "Has the Hosting line",
        "severity": "required",
        "fix": "Add C2.",
    },
    {
        "id": "C4",
        "title": "portfolio.json fits",
        "severity": "required",
        "fix": "Fix C4.",
    },
    {"id": "C10", "title": "Names v2", "severity": "required", "fix": "Move to v2."},
    {"id": "C5", "title": "UTF-8 rule", "severity": "optional", "fix": "Add C5."},
]


def output(rows, status="complete", scanned_at="2026-12-01T06:00:00+00:00"):
    """A scan output holding `rows`."""
    return {
        "status": status,
        "scanned_at": scanned_at,
        "spec_version": 2,
        "failure": None,
        "checks": CHECKS,
        "rows": rows,
    }


ROWS = [
    private_row("zeta", level=0, health="not-reported", lifecycle=None),
    private_row("Alpha"),
    {**private_row("beta", visibility="public", level=1, health="amber")},
]


def write_scan_file(path, scan_output):
    """Write `scan_output` as the scan output file at `path`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(scan_output), encoding="utf-8")
    return path


def table_rows(text):
    """The Markdown report's repo table body rows, as lists of cells."""
    lines = text[text.index("## Repos") :].splitlines()
    # Lines starting "| " are the header and the body; the separator
    # ("|---|") doesn't match, so only the header is skipped.
    rows = [line for line in lines if line.startswith("| ")][1:]
    return [[cell.strip() for cell in line.strip("|").split("|")] for line in rows]
