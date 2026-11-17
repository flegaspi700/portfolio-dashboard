"""Writes the scan output to disk, and gives the run's exit code.

Part of `privacy/`, the only component that writes scan output
(docs/architecture.md, Layout). `main.py` (S1.4.2) passes the scan result
from `scan/result.py` to `write_output`, which runs the allow-list filter
(`allow_list.py`) itself, so unfiltered data has no way onto disk, and
writes the filtered result as one JSON file, `output/scan.json`
(docs/decisions.md, "Scan output: one JSON file").

A failed result writes nothing, so the last good file stays (decisions.md,
"Scan failure: publish partial and flag it"). The file is replaced in one
step, so a crash mid-write never leaves half a file. The exit code is 0
for a complete result and 1 for a partial or failed one, so the scheduled
Action can alert (F3.3). Built for S2.1.2.
"""

import json
import logging
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any

from privacy.allow_list import filter_result
from scan.result import COMPLETE, FAILED, ScanResult

logger = logging.getLogger(__name__)

OUTPUT_FILE = Path("output") / "scan.json"


def write_output(result: ScanResult, path: Path = OUTPUT_FILE) -> int:
    """Filter `result` and write it to `path` as UTF-8 JSON (no BOM), unless
    the result failed. Returns the exit code: 0 complete, 1 otherwise.

    An error while writing propagates, and the previous file is left whole.
    """
    if result.status == FAILED:
        logger.error("Scan failed, so nothing was written: %s", result.failure)
        return 1

    text = json.dumps(filter_result(result), default=_json_value, indent=2)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write a temporary file next to the target, then swap it in.
    handle, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as file:
            file.write(text + "\n")
        os.replace(temporary, path)
    except BaseException:
        os.remove(temporary)
        raise

    logger.info(
        "Wrote the scan output: %d rows, status %s", len(result.rows), result.status
    )
    return 0 if result.status == COMPLETE else 1


def _json_value(value: Any) -> str:
    """Dates and times as ISO 8601 text; anything else is a bug."""
    if isinstance(value, datetime | date):
        return value.isoformat()
    raise TypeError(f"Can't write a {type(value).__name__} to the scan output")
