"""Command-line entry for the report: `python -m report`.

Sets up safe logging (`privacy/safe_logging.py`), then renders
`output/site/index.md` from `output/scan.json` and exits with
`write_report`'s code. The daily workflow runs it after `main.py` (F3.2).
Built for S3.1.1.
"""

import sys

from privacy.safe_logging import configure_logging
from report.markdown import write_report

configure_logging()
sys.exit(write_report())
