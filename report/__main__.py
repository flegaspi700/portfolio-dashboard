"""Command-line entry for the site: `python -m report`.

Sets up safe logging (`privacy/safe_logging.py`), then builds
`output/site/` (the page and the Markdown report) from `output/scan.json`
and exits with `build_site`'s code. The daily workflow runs it after
`main.py` (F3.2). Built for S3.1.1; the page added in S4.1.1.
"""

import sys

from privacy.safe_logging import configure_logging
from report.site import build_site

configure_logging()
sys.exit(build_site())
