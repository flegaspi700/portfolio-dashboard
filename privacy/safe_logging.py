"""Sets up logging so nothing private reaches the logs.

Part of `privacy/`. `main.py` (S1.4.2) calls `configure_logging` once, at
the start of a run. The Action logs are public on a public repo (NFR5), so
every record goes through `SafeFormatter`: a logged exception shows only
its type (and the types it was raised from), never its message or
traceback, because an error's text can hold a URL, a response reason or a
file's content. Stack info is dropped for the same reason.

The scan's own log messages already carry only counts and generic reasons
(such as "HTTP 403"), never repo names, file content or the token. This
module is the safety net for exceptions nobody planned for. Built for
S2.1.3.
"""

import logging
import sys
from typing import TextIO

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


class SafeFormatter(logging.Formatter):
    """A formatter that withholds exception text and stack info."""

    def format(self, record: logging.LogRecord) -> str:
        # Work on a copy: another handler may have cached the full
        # traceback in `exc_text`, and later handlers mustn't see ours.
        safe = logging.makeLogRecord(record.__dict__)
        safe.exc_text = None
        safe.stack_info = None
        return super().format(safe)

    def formatException(self, ei) -> str:
        """Only the exception's type and the types it was raised from."""
        names = []
        error = ei[1]
        while error is not None and len(names) < 10:
            names.append(type(error).__name__)
            error = error.__cause__ or error.__context__
        return (
            f"Error type: {' <- '.join(names)} "
            "(details withheld: error text can hold private data)"
        )


def configure_logging(level: int = logging.INFO, stream: TextIO | None = None) -> None:
    """Send all logging at `level` and above to `stream` (stderr by
    default) through `SafeFormatter`, replacing any earlier handlers."""
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(SafeFormatter(LOG_FORMAT))
    root.addHandler(handler)
    root.setLevel(level)
