"""Builds the published site from the scan output: the page and the report.

Part of `report/`. Runs as its own step after `main.py`
(`python -m report`, see `__main__.py`): `build_site` reads
`output/scan.json`, the filtered scan output written by
`privacy/output.py`, and writes `output/site/index.html` (`page.py`), a page per repo
in `output/site/repos/` (S4.3.1), the shared `style.css`, and
`output/site/report.md` (`markdown.py`). The daily workflow uploads that
folder as it is, with no other build step (F3.2;
docs/decisions.md, "How the output gets published"). It never sees the
unfiltered scan result. Built for S3.1.1; the page added in S4.1.1.
"""

import json
import logging
from pathlib import Path

from privacy.output import OUTPUT_FILE
from report.markdown import render_report
from report.page import STYLESHEET, render_page, render_repo_page, repo_paths

logger = logging.getLogger(__name__)

SITE_DIR = OUTPUT_FILE.parent / "site"


def build_site(scan_path: Path = OUTPUT_FILE, site_dir: Path = SITE_DIR) -> int:
    """Read the scan output and write the site's files in `site_dir`, as
    UTF-8 without a BOM. Returns 0, or 1 if there is no scan output."""
    if not scan_path.is_file():
        logger.error(
            "No scan output to build the site from: run main.py first, which "
            "writes it. A failed scan writes none, so there is nothing new to publish."
        )
        return 1
    output = json.loads(scan_path.read_text(encoding="utf-8"))
    site_dir.mkdir(parents=True, exist_ok=True)
    _write(site_dir / "index.html", render_page(output))
    _write(site_dir / "style.css", STYLESHEET.read_text(encoding="utf-8"))
    _write(site_dir / "report.md", render_report(output))
    paths = repo_paths(output["rows"])
    for row in output["rows"]:
        path = site_dir / paths[row["name"]]
        path.parent.mkdir(exist_ok=True)
        _write(path, render_repo_page(row, output))
    logger.info("Built the site: %d repos", len(output["rows"]))
    return 0


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")
