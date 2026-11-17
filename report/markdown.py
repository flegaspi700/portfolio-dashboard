"""Renders the Markdown report from the scan output.

Part of `report/`. Runs as its own step after `main.py`
(`python -m report`, see `__main__.py`): `write_report` reads
`output/scan.json`, the filtered scan output written by
`privacy/output.py`, and writes `output/site/index.md`, which the daily
workflow builds into the Pages site (F3.2; docs/decisions.md, "How the
output gets published"). It never sees the unfiltered scan result.

The report shows names, fixed values, numbers and dates only, never free
text from a repo, because the Pages build renders Markdown as HTML and a
public repo's text could carry markup (threat model T3). Every cell is
escaped anyway, Liquid braces included, since the build also runs Liquid.
Built for S3.1.1.
"""

import json
import logging
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from privacy.output import OUTPUT_FILE
from scan.levels import LEVEL_NAMES

logger = logging.getLogger(__name__)

SITE_DIR = OUTPUT_FILE.parent / "site"
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


def write_report(scan_path: Path = OUTPUT_FILE, site_dir: Path = SITE_DIR) -> int:
    """Read the scan output and write `index.md` in `site_dir`, as UTF-8
    without a BOM. Returns 0, or 1 if there is no scan output to read."""
    if not scan_path.is_file():
        logger.error(
            "No scan output to report on: run main.py first, which writes it. "
            "A failed scan writes none, so there is nothing new to publish."
        )
        return 1
    output = json.loads(scan_path.read_text(encoding="utf-8"))
    site_dir.mkdir(parents=True, exist_ok=True)
    (site_dir / "index.md").write_text(
        render_report(output), encoding="utf-8", newline="\n"
    )
    logger.info("Wrote the report: %d repos", len(output["rows"]))
    return 0


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
