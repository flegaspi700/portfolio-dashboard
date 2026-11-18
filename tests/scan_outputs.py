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


def output(rows, status="complete", scanned_at="2026-12-01T06:00:00+00:00"):
    """A scan output holding `rows`."""
    return {
        "status": status,
        "scanned_at": scanned_at,
        "spec_version": 2,
        "failure": None,
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
