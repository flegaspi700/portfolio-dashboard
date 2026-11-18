"""Renders the dashboard page, `index.html`, from the scan output.

Part of `report/`. `site.py` reads `output/scan.json` (the filtered scan
output) and passes it to `render_page`, which works out the counts and
fills the Jinja2 template in `templates/`. It never sees the unfiltered
scan result.

Auto-escaping is on for every value, because a public repo's text could
carry markup (threat model T3), and an undefined value fails the build
instead of showing as blank. The page is our own HTML with its style and
script inline: nothing is loaded from another site. Every state has a text
label, never colour alone (accessibility.md). Built for S4.1.1 (the page),
S4.1.2 (summary tiles, scan time, old-data notice, levels explained) and
S4.1.3 (needs attention first, docs/decisions.md, "'Needs attention
first' ranking": it reads the allow-list fields only, so public and private
repos rank alike) and S4.2.1 (the repo table: every repo in attention order,
each cell with a sort value for the page's sorting script).
"""

import math
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from privacy.allow_list import PRIVATE_FIELDS
from report.markdown import COULD_NOT_SCAN, HEALTH_VALUES, MISSING
from scan.levels import LEVEL_NAMES

ENVIRONMENT = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=True,
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
)

HEALTH_LABELS = {
    "green": "Green",
    "amber": "Amber",
    "red": "Red",
    "not-reported": "Not reported",
}

# One sentence per level, from the Meaning column of the standard's
# spec/compliance.md -> Levels (spec version 2).
LEVEL_SENTENCES = (
    "Nothing the portfolio can read: no valid portfolio.json.",
    "Reports its status in a valid portfolio.json, but hasn't adopted the standard.",
    (
        "On the standard: it reports its status and names the standard's version, "
        "its hosting and its planning docs."
    ),
    (
        "Adopted, on the current major version of the standard, with every "
        "required check that is due passing."
    ),
)

# The tiers of "needs attention first", in order; the first match wins.
# Each is (reason shown on the page, test on the allow-list fields).
ATTENTION_TIERS = (
    ("Could not scan", lambda row: row["scan_status"] == COULD_NOT_SCAN),
    ("Health red", lambda row: row["health"] == "red"),
    ("Has blockers", lambda row: (row["blocker_count"] or 0) > 0),
    ("Health amber", lambda row: row["health"] == "amber"),
    ("Health not reported", lambda row: row["health"] in ("not-reported", None)),
    ("Below Level 2", lambda row: row["level"] is None or row["level"] < 2),
    ("Nothing flagged", lambda row: True),
)
NOT_RANKED = ("done", "archived")
ATTENTION_LIST_LENGTH = 5  # From S4.1.3's criteria.

# The repo table's columns: (title, sorts as a number).
TABLE_COLUMNS = (
    ("Repo", False),
    ("Visibility", False),
    ("Level", True),
    ("Health", True),
    ("Lifecycle", False),
    ("Last activity", False),
    ("Risks", True),
    ("Blockers", True),
    ("Scan", False),
)
# Health sorts by how much attention it needs, red first.
HEALTH_SORT = {"red": 0, "amber": 1, "not-reported": 2, "green": 3}

COMPLIANCE_SPEC_URL = (
    "https://github.com/flegaspi700/pmo-project-standardization"
    "/blob/HEAD/spec/compliance.md"
)


def render_page(output: dict[str, Any]) -> str:
    """The page for one scan output, as HTML. The same output always gives
    the same text."""
    rows = output["rows"]
    scanned = [row for row in rows if row.get("scan_status") != COULD_NOT_SCAN]
    scanned_at = datetime.fromisoformat(output["scanned_at"]).astimezone(UTC)
    health = Counter(row.get("health") for row in scanned)
    levels = Counter(row.get("level") for row in scanned)
    return ENVIRONMENT.get_template("index.html").render(
        scanned_at=f"{scanned_at:%Y-%m-%d %H:%M}",
        scanned_at_iso=f"{scanned_at:%Y-%m-%dT%H:%M:%SZ}",
        spec_version=output["spec_version"],
        partial=output["status"] == "partial",
        repo_count=len(rows),
        could_not_scan=len(rows) - len(scanned),
        health_tiles=[
            (value, HEALTH_LABELS[value], health[value]) for value in HEALTH_VALUES
        ],
        level_tiles=[
            (f"Level {level} · {name}", levels[level])
            for level, name in reversed(list(enumerate(LEVEL_NAMES)))
        ],
        levels=[
            (f"Level {level} · {name}", sentence)
            for level, (name, sentence) in enumerate(
                zip(LEVEL_NAMES, LEVEL_SENTENCES, strict=True)
            )
        ],
        compliance_spec_url=COMPLIANCE_SPEC_URL,
        attention=[
            (row["name"], reason)
            for row, reason in rank_for_attention(rows)[:ATTENTION_LIST_LENGTH]
        ],
        columns=TABLE_COLUMNS,
        table=[_table_cells(row) for row in table_order(rows)],
    )


def table_order(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every row: the ranked ones in "needs attention first" order, then
    the done and archived ones, which aren't ranked, by name."""
    ranked = [row for row, _ in rank_for_attention(rows)]
    not_ranked = [row for row in rows if row.get("lifecycle") in NOT_RANKED]
    return ranked + sorted(
        not_ranked, key=lambda row: (row["name"].lower(), row["name"])
    )


def _table_cells(row: dict[str, Any]) -> list[tuple[str, str | None]]:
    """One repo's cells, in TABLE_COLUMNS order, as (text shown, sort
    value). A missing value shows a dash and has no sort value, so the
    script sorts it last."""
    name = (row["name"], row["name"].lower())
    if row.get("scan_status") == COULD_NOT_SCAN:
        return [name, *[(MISSING, None)] * 7, (COULD_NOT_SCAN, COULD_NOT_SCAN)]
    level = row.get("level")
    health = row.get("health")
    if isinstance(level, int) and 0 <= level < len(LEVEL_NAMES):
        level_cell = (f"{level} · {LEVEL_NAMES[level]}", str(level))
    else:
        level_cell = _plain(level)
    if health in HEALTH_LABELS:
        health_cell = (HEALTH_LABELS[health], str(HEALTH_SORT[health]))
    else:
        health_cell = _plain(health)
    return [
        name,
        _plain(row.get("visibility")),
        level_cell,
        health_cell,
        _plain(row.get("lifecycle")),
        _plain(row.get("last_activity")),
        _plain(row.get("risk_count")),
        _plain(row.get("blocker_count")),
        _plain(row.get("scan_status")),
    ]


def _plain(value: Any) -> tuple[str, str | None]:
    """A value shown as it is and sorted by its text, or a dash if missing."""
    if value is None:
        return (MISSING, None)
    return (str(value), str(value))


def rank_for_attention(
    rows: list[dict[str, Any]],
) -> list[tuple[dict[str, Any], str]]:
    """Rows in "needs attention first" order, each with its tier's reason.

    Order: tier, then lifecycle `active` first, then the most recent
    activity (none last), then the name. Rows whose lifecycle is `done` or
    `archived` are left out. Only the allow-list fields are read, so a
    public row ranks exactly as it would if it were private.
    """
    ranked = []
    for row in rows:
        fields = {name: row.get(name) for name in PRIVATE_FIELDS}
        if fields["lifecycle"] in NOT_RANKED:
            continue
        tier, reason = next(
            (number, reason)
            for number, (reason, matches) in enumerate(ATTENTION_TIERS)
            if matches(fields)
        )
        key = (
            tier,
            fields["lifecycle"] != "active",
            -_day_number(fields["last_activity"]),
            fields["name"].lower(),
            fields["name"],
        )
        ranked.append((key, row, reason))
    ranked.sort(key=lambda item: item[0])
    return [(row, reason) for _, row, reason in ranked]


def _day_number(day: str | None) -> float:
    """A date as a number for sorting, with no date as the oldest."""
    return date.fromisoformat(day).toordinal() if day else -math.inf
