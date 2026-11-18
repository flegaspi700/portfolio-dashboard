"""Renders the dashboard page, `index.html`, from the scan output.

Part of `report/`. `site.py` reads `output/scan.json` (the filtered scan
output) and passes it to `render_page`, which fills the Jinja2 template in
`templates/`. It never sees the unfiltered scan result.

Auto-escaping is on for every value, because a public repo's text could
carry markup (threat model T3), and an undefined value fails the build
instead of showing as blank. The page is our own HTML with its style and
script inline: nothing is loaded from another site. Built for S4.1.1.
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

ENVIRONMENT = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=True,
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_page(output: dict[str, Any]) -> str:
    """The page for one scan output, as HTML. The same output always gives
    the same text."""
    scanned_at = datetime.fromisoformat(output["scanned_at"]).astimezone(UTC)
    return ENVIRONMENT.get_template("index.html").render(
        scanned_at=f"{scanned_at:%Y-%m-%d %H:%M}",
        spec_version=output["spec_version"],
        repo_count=len(output["rows"]),
    )
