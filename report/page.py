"""Renders the dashboard page, `index.html`, from the scan output.

Part of `report/`. `site.py` reads `output/scan.json` (the filtered scan
output) and passes it to `render_page`, which works out the counts and
fills the Jinja2 template in `templates/`. It never sees the unfiltered
scan result.

Auto-escaping is on for every value, because a public repo's text could
carry markup (threat model T3), and an undefined value fails the build
instead of showing as blank. The page is our own HTML with its style and
script inline: nothing is loaded from another site. Every state has a text
label, never colour alone (accessibility.md). Built for S4.1.1 (the page)
and S4.1.2 (summary tiles, scan time, old-data notice, levels explained).
"""

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

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
    )
