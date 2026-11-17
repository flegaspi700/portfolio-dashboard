"""Runs the scan and assembles the scan result.

Part of `scan/`, and the one place its parts meet. `run_scan` reads the
check registry, lists and selects the in-scope repos (`repos.py`), then
for each repo reads its facts (`facts.py`) and files (`files.py`),
evaluates the checks (`checks.py`), works out its level (`levels.py`),
reads its `portfolio.json` (`status.py`) and works out its scan warnings
(`warnings.py`). Every read goes through one fetch function, passed in
so tests can fake GitHub; the real one and `main.py` are S1.4.2.

The result is the scan result (docs/architecture.md, Words and names):
in memory, unfiltered, never written to disk. The allow-list filter
(`privacy/`, S2.1.1) is the only way out. It is marked complete, partial
(some repos "could not scan") or failed (nothing worth publishing), as
docs/decisions.md, "Scan failure: publish partial and flag it", says.
Built for S1.4.1.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from scan.checks import Registry, RegistryError, evaluate_checks, load_registry
from scan.facts import FailedRead, error_reason, read_facts
from scan.files import read_files
from scan.levels import work_out_level
from scan.repos import Fetch, InScopeRepo, list_repos, select_in_scope
from scan.status import read_status
from scan.warnings import ScanWarning, read_adoption_date, work_out_warnings

logger = logging.getLogger(__name__)

SCAN_OK = "ok"
COULD_NOT_SCAN = "could not scan"

COMPLETE = "complete"
PARTIAL = "partial"
FAILED = "failed"


@dataclass(frozen=True)
class RepoRow:
    """One in-scope repo in the scan result. A row that could not be
    scanned has only its name, visibility, `scan_status` and a generic
    `scan_error` (such as "HTTP 403"); every other field is None.

    `checks` is check ID -> True, False or None (n/a); `reported` is the
    valid `portfolio.json`, unchanged, or None.
    """

    name: str
    visibility: str
    scan_status: str
    scan_error: str | None = None
    pushed_at: datetime | None = None
    created_at: datetime | None = None
    language: str | None = None
    description: str | None = None
    default_branch: str | None = None
    open_issues: int | None = None
    open_prs: int | None = None
    level: int | None = None
    level_name: str | None = None
    standard_version: str | None = None
    checks: dict[str, bool | None] | None = None
    warnings: list[ScanWarning] | None = None
    has_portfolio: bool | None = None
    health: str | None = None
    reported: dict[str, Any] | None = None
    portfolio_problem: str | None = None


@dataclass(frozen=True)
class ScanResult:
    """One scan: its status (complete, partial or failed), when it ran,
    the spec version of the check registry, the rows sorted by name, and
    why it failed, if it did."""

    status: str
    scanned_at: datetime
    spec_version: int | None
    rows: list[RepoRow]
    failure: str | None = None


def run_scan(fetch: Fetch, owner: str, now: datetime) -> ScanResult:
    """Scan every in-scope repo of `owner`, as of `now` (UTC).

    A registry or listing that can't be read (a bad token, say) gives a
    failed result with no rows, before any repo is read. Errors that
    aren't about reading GitHub, such as an unknown check kind, propagate:
    the scanner needs fixing, and nothing should be published.
    """
    try:
        registry = load_registry(fetch)
    except RegistryError as error:
        logger.error("Scan failed: could not read the check registry")
        return _failed(now, None, f"could not read the check registry ({error})")

    try:
        repos = select_in_scope(list_repos(fetch))
    except OSError as error:
        reason = f"could not list repos: {error_reason(error)}"
        logger.error("Scan failed: %s", reason)
        return _failed(now, registry.version, reason)

    rows = sorted(
        (_scan_repo(fetch, owner, repo, registry, now) for repo in repos),
        key=lambda row: (row.name.lower(), row.name),
    )
    failed = sum(row.scan_status == COULD_NOT_SCAN for row in rows)
    # Counts only: private repo names stay out of the Action logs (NFR5).
    logger.info("Scanned %d repos: %d could not be scanned", len(rows), failed)

    if not rows:
        # This repo is always in scope, so zero means something broke.
        return _failed(now, registry.version, "no in-scope repos")
    if failed == len(rows):
        return _failed(now, registry.version, "every repo failed", rows)
    return ScanResult(
        status=PARTIAL if failed else COMPLETE,
        scanned_at=now,
        spec_version=registry.version,
        rows=rows,
    )


def _scan_repo(
    fetch: Fetch, owner: str, repo: InScopeRepo, registry: Registry, now: datetime
) -> RepoRow:
    """Read and work out one repo's row, or a "could not scan" row."""
    facts = read_facts(fetch, owner, repo.name)
    if isinstance(facts, FailedRead):
        return _could_not_scan(repo, facts)
    files = read_files(fetch, owner, repo.name, facts.default_branch, registry)
    if isinstance(files, FailedRead):
        return _could_not_scan(repo, files)

    today = now.date()
    results = evaluate_checks(registry, files)
    level = work_out_level(registry, results, files, today)
    status = read_status(files, registry)
    warnings = work_out_warnings(
        today,
        facts,
        status.has_portfolio,
        status.health,
        status.updated,
        level,
        lambda: read_adoption_date(fetch, owner, repo.name),
    )
    if isinstance(warnings, FailedRead):
        return _could_not_scan(repo, warnings)

    return RepoRow(
        name=repo.name,
        visibility=repo.visibility,
        scan_status=SCAN_OK,
        pushed_at=facts.pushed_at,
        created_at=facts.created_at,
        language=facts.language,
        description=facts.description,
        default_branch=facts.default_branch,
        open_issues=facts.open_issues,
        open_prs=facts.open_prs,
        level=level.level,
        level_name=level.name,
        standard_version=level.version,
        checks=results,
        warnings=warnings,
        has_portfolio=status.has_portfolio,
        health=status.health,
        reported=status.fields,
        portfolio_problem=status.problem,
    )


def _could_not_scan(repo: InScopeRepo, failure: FailedRead) -> RepoRow:
    return RepoRow(
        name=repo.name,
        visibility=repo.visibility,
        scan_status=COULD_NOT_SCAN,
        scan_error=failure.reason,
    )


def _failed(
    now: datetime,
    spec_version: int | None,
    failure: str,
    rows: list[RepoRow] | None = None,
) -> ScanResult:
    return ScanResult(
        status=FAILED,
        scanned_at=now,
        spec_version=spec_version,
        rows=rows or [],
        failure=failure,
    )
