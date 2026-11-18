"""Cuts the scan result down to what may be published: the allow-list filter.

Part of `privacy/`. Takes the scan result from `scan/result.py` (in memory,
unfiltered) and returns the scan output, the only form that may be written
or published (docs/architecture.md, Words and names). Writing it is S2.1.2.

A private row keeps only the allow-list: name, visibility, lifecycle,
health, compliance level, last activity date, risk count, blocker count and
scan status (docs/decisions.md, "Private repos: real name plus signals").
Each is built here by name from the row, so a field no one has listed can't
get through, and none of them is free text. A private row that could not be
scanned keeps only its name and scan status, with no error text. Anything
whose visibility isn't exactly "public" counts as private. A public row
keeps every field, plus the same signal fields, so the report and page
read one shape. Built for S2.1.1.

The standard's checks pass too, cut to their ID, title, severity and fix:
the standard's own public text, the same for every repo, with no repo data
(S4.3.1; docs/decisions.md, "Check titles and fixes in the scan output").
So does the owner's account name, which is already public in the site's
address, for request links (S4.4.1).
"""

from dataclasses import asdict
from typing import Any

from scan.result import COULD_NOT_SCAN, RepoRow, ScanResult

PRIVATE_FIELDS = (
    "name",
    "visibility",
    "lifecycle",
    "health",
    "level",
    "last_activity",
    "risk_count",
    "blocker_count",
    "scan_status",
)

CHECK_FIELDS = ("id", "title", "severity", "fix")


def filter_result(result: ScanResult) -> dict[str, Any]:
    """The scan output: the result's status, scan time, spec version and
    failure reason (all generic, never repo data), the standard's checks
    (CHECK_FIELDS only), the owner's account name, and each row filtered."""
    return {
        "status": result.status,
        "scanned_at": result.scanned_at,
        "spec_version": result.spec_version,
        "failure": result.failure,
        "checks": [
            {name: check.get(name) for name in CHECK_FIELDS} for check in result.checks
        ],
        "owner": result.owner,
        "rows": [filter_row(row) for row in result.rows],
    }


def filter_row(row: RepoRow) -> dict[str, Any]:
    """One row as it may be published: cut to the allow-list if private,
    whole (plus the signal fields) if public."""
    if row.visibility == "public":
        return {**asdict(row), **_signals(row)}
    if row.scan_status == COULD_NOT_SCAN:
        return {"name": row.name, "scan_status": row.scan_status}
    output = _signals(row)
    return {name: output[name] for name in PRIVATE_FIELDS}


def _signals(row: RepoRow) -> dict[str, Any]:
    """The allow-listed fields, worked out from a row by name. Values a
    repo didn't report (no valid portfolio.json, no `risks` list) are None,
    never a guess."""
    reported = row.reported or {}
    return {
        "name": row.name,
        "visibility": "public" if row.visibility == "public" else "private",
        "lifecycle": reported.get("lifecycle"),
        "health": row.health,
        "level": row.level,
        "last_activity": row.pushed_at.date() if row.pushed_at else None,
        "risk_count": _count(reported, "risks"),
        "blocker_count": _count(reported, "blockers"),
        "scan_status": row.scan_status,
    }


def _count(reported: dict[str, Any], key: str) -> int | None:
    items = reported.get(key)
    return len(items) if isinstance(items, list) else None
