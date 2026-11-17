"""Runs one scan: read the token, scan GitHub, write the filtered output.

Wires the components together (docs/architecture.md, Layout): logging
through `privacy/safe_logging.py`, the token from the environment or
`.env`, the real fetch function (`scan/github.py`), the scan
(`scan/result.py`), and the write step (`privacy/output.py`), whose exit
code this returns. Run it with `.venv\\Scripts\\python main.py`; the
scheduled Action will run it the same way (Phase 2).

Logs carry counts only. The token goes nowhere but the fetch function,
and an unexpected crash is logged as its type only (S2.1.3). The token's
expiry date is logged, and within 14 days of it the run exits 1 after
writing, as a renewal reminder (S3.3.3). Built for S1.4.2.
"""

import logging
import sys
import time
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from os import environ as os_environ
from pathlib import Path

from privacy.output import OUTPUT_FILE, write_output
from privacy.safe_logging import configure_logging
from scan.facts import error_reason
from scan.github import make_fetch, token_expiry
from scan.repos import Fetch
from scan.result import COULD_NOT_SCAN, run_scan

logger = logging.getLogger("main")

TOKEN_VARIABLE = "PORTFOLIO_READ_TOKEN"

# From the story (S3.3.3): two weeks is time enough to renew the token.
RENEW_WITHIN_DAYS = 14
ENV_FILE = Path(".env")


def main(
    environ: Mapping[str, str] | None = None,
    env_file: Path = ENV_FILE,
    output: Path = OUTPUT_FILE,
    fetch_factory: Callable[[str], Fetch] = make_fetch,
    now: datetime | None = None,
) -> int:
    """Run one scan and return the exit code: 0 when the scan was complete
    and written, 1 otherwise. Every argument defaults to the real thing."""
    configure_logging()
    try:
        return _run(
            os_environ if environ is None else environ,
            env_file,
            output,
            fetch_factory,
            now or datetime.now(UTC),
        )
    except Exception:
        # Logged as its type only: an error's text can hold private data.
        logger.exception("The scan stopped unexpectedly")
        return 1


def _run(
    environ: Mapping[str, str],
    env_file: Path,
    output: Path,
    fetch_factory: Callable[[str], Fetch],
    now: datetime,
) -> int:
    token = (environ.get(TOKEN_VARIABLE) or "").strip() or _read_env_file(env_file).get(
        TOKEN_VARIABLE, ""
    )
    if not token:
        logger.error(
            "%s is not set: copy .env.example to .env and put the read-only "
            "token in it (docs/security.md, T2). Nothing was scanned.",
            TOKEN_VARIABLE,
        )
        return 1

    started = time.monotonic()
    real_fetch = fetch_factory(token)
    requests = 0

    def fetch(path: str):
        nonlocal requests
        requests += 1
        return real_fetch(path)

    try:
        owner = fetch("/user")["login"]
    except OSError as error:
        logger.error("Could not read the token's user: %s", error_reason(error))
        return 1
    days_left = _log_token_expiry(getattr(real_fetch, "last_headers", None), now)

    result = run_scan(fetch, owner, now)
    code = write_output(result, output)
    failed = sum(row.scan_status == COULD_NOT_SCAN for row in result.rows)
    logger.info(
        "Scan %s: %d repos in scope, %d could not be scanned, %d API requests, "
        "%.1f seconds",
        result.status,
        len(result.rows),
        failed,
        requests,
        time.monotonic() - started,
    )
    if days_left is not None and days_left <= RENEW_WITHIN_DAYS:
        # The output is written and will be deployed; failing the run now
        # makes GitHub's failure email the reminder (S3.3.3, T5).
        logger.warning(
            "Renew the read token: it expires in %d days. The run is marked "
            "failed so the alert reminds you (docs/security.md, T2).",
            days_left,
        )
        return 1
    return code


def _log_token_expiry(headers, now: datetime) -> int | None:
    """Log when the read token expires; return the whole days left, or
    None when it has no expiry date."""
    expires = token_expiry(headers)
    if expires is None:
        logger.info("The read token has no expiry date")
        return None
    days_left = (expires.date() - now.date()).days
    logger.info(
        "The read token expires on %s (%d days left)", f"{expires:%Y-%m-%d}", days_left
    )
    return days_left


def _read_env_file(path: Path) -> dict[str, str]:
    """Read `KEY=VALUE` lines from a `.env` file, if there is one. Blank
    lines, comments and other lines are skipped; quotes around a value are
    dropped. Standard library only (docs/requirements.md, S1.4.2 notes)."""
    if not path.is_file():
        return {}
    values = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or not key or key.startswith("#"):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key] = value
    return values


if __name__ == "__main__":
    sys.exit(main())
