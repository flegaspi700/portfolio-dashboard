"""Renders the Markdown report from the scan output.

Part of `report/`. `site.py` reads `output/scan.json`, the filtered scan
output written by `privacy/output.py`, and passes it to `render_report`;
the result is published next to the page as `output/site/report.md`. It
never sees the unfiltered scan result.

The report shows names, fixed values, numbers and dates only, never free
text from a repo, because a viewer may render the Markdown as HTML and a
public repo's text could carry markup (threat model T3). Every cell is
escaped anyway, Liquid braces included: Jekyll built the report into the
page until S4.1.1, and the front matter still gives it a title on GitHub.
Built for S3.1.1; writing the file moved to `site.py` in S4.1.1.
"""

from collections import Counter
from datetime import UTC, datetime
from typing import Any

from scan.levels import LEVEL_NAMES

HEALTH_VALUES = ("green", "amber", "red", "not-reported")
COULD_NOT_SCAN = "could not scan"
MISSING = "—"

COLUMNS = (
    ("Repo", "name"),
    ("Visibility", "visibility"),
    ("Level", "level"),
    ("Health", "health"),
    ("Lifecycle", "lifecycle"),
    ("Last activity", "last_activity"),
    ("Risks", "risk_count"),
    ("Blockers", "blocker_count"),
    ("Scan", "scan_status"),
)

# HTML entities for what HTML or Liquid would act on, backslashes for
# what Markdown would.
ENTITIES = {"&": "&amp;", "<": "&lt;", ">": "&gt;", "{": "&#123;", "}": "&#125;"}
MARKDOWN_SPECIAL = set("\\`*_[]|")


def render_report(output: dict[str, Any]) -> str:
    """The report for one scan output, as Markdown with front matter.
    The same output always gives the same text."""
    rows = sorted(output["rows"], key=lambda row: (row["name"].lower(), row["name"]))
    scanned = [row for row in rows if row.get("scan_status") != COULD_NOT_SCAN]
    failed = len(rows) - len(scanned)
    scanned_at = datetime.fromisoformat(output["scanned_at"]).astimezone(UTC)

    lines = ["---", "title: Portfolio report", "---", "", "# Portfolio report", ""]
    if output["status"] == "partial":
        lines += [
            f"> **Partial scan:** {failed} of {len(rows)} repos could not be scanned.",
            "",
        ]
    lines += [
        (
            f"Scanned {scanned_at:%Y-%m-%d %H:%M} UTC · spec version "
            f"{_cell(output['spec_version'])} · {len(rows)} repos"
        ),
        "",
        "## Summary",
        "",
        "| Level | Repos |",
        "|---|---|",
    ]
    levels = Counter(row.get("level") for row in scanned)
    lines += [f"| {level} {name} | {levels[level]} |" for level, name in _levels()]
    health = Counter(row.get("health") for row in scanned)
    lines += ["", "| Health | Repos |", "|---|---|"]
    lines += [f"| {value} | {health[value]} |" for value in HEALTH_VALUES]
    lines += ["", f"Could not scan: {failed}", "", "## Repos", ""]
    lines.append("| " + " | ".join(title for title, _ in COLUMNS) + " |")
    lines.append("|" + "---|" * len(COLUMNS))
    lines += [_table_row(row) for row in rows]
    return "\n".join(lines) + "\n"


def _levels() -> list[tuple[int, str]]:
    """(level, name) from highest to lowest."""
    return sorted(enumerate(LEVEL_NAMES), reverse=True)


def _table_row(row: dict[str, Any]) -> str:
    """One repo's row: only the listed columns, never any other field."""
    if row.get("scan_status") == COULD_NOT_SCAN:
        cells = [_cell(row["name"])] + [MISSING] * (len(COLUMNS) - 2) + [COULD_NOT_SCAN]
    else:
        cells = [_column(row, key) for _, key in COLUMNS]
    return "| " + " | ".join(cells) + " |"


def _column(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if key == "level" and isinstance(value, int) and 0 <= value < len(LEVEL_NAMES):
        return f"{value} {LEVEL_NAMES[value]}"
    return _cell(value)


def _cell(value: Any) -> str:
    """A value as safe table text: a dash for a missing value, otherwise
    escaped so Markdown, HTML and Liquid treat it as plain text."""
    if value is None:
        return MISSING
    text = " ".join(str(value).split())
    return "".join(
        ENTITIES.get(char, "\\" + char if char in MARKDOWN_SPECIAL else char)
        for char in text
    )
