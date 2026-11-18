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
repos rank alike).
"""

import math
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from privacy.allow_list import PRIVATE_FIELDS
from report.markdown import COULD_NOT_SCAN, HEALTH_VALUES
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
    )


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
