"""Works out the scan warnings S1, S2 and S3 for one repo.

Part of `scan/`. The scan result (S1.4.1) calls `work_out_warnings` once
per repo with its repo facts (S1.1.2), what its `portfolio.json` reports
(S1.3.1) and its compliance level (S1.2.2). Warning S2 also needs the
adoption date, which `read_adoption_date` reads from the repo's commit
history through the scan's fetch function, but only when S2 could fire
(docs/decisions.md, 2026-11-17), so most repos cost no extra requests.

The rules are `spec/compliance.md` -> Warnings worked out by the scanner.
These are spec warning IDs, not story IDs. Built for S1.2.3.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from scan.facts import FailedRead, RepoFacts, failed_read
from scan.levels import ComplianceLevel
from scan.repos import PAGE_SIZE, Fetch

logger = logging.getLogger(__name__)

# From spec/compliance.md -> Warnings worked out by the scanner.
STALE_AFTER = timedelta(days=30)  # S1: report age, and the push window
NOT_REPORTED_AFTER = timedelta(days=14)  # S2
DUE_SOON_WITHIN = timedelta(days=14)  # S3


@dataclass(frozen=True)
class ScanWarning:
    """One scan warning: "S1", "S2" or "S3". An S3 names the required
    check that comes due and its `required_from` date."""

    id: str
    check_id: str | None = None
    required_from: str | None = None


def work_out_warnings(
    today: date,
    facts: RepoFacts,
    has_portfolio: bool,
    health: str,
    updated: date | None,
    level: ComplianceLevel,
    read_adopted: Callable[[], date | None],
) -> list[ScanWarning] | FailedRead:
    """Work out one repo's scan warnings on `today`, in the order S1, S2, S3.

    `health` and `updated` are what `portfolio.json` reports; with no file
    (`has_portfolio` False) neither S1 nor S2 fires, because Level 0 is
    already the finding. `read_adopted` is called only when S2 could fire;
    if it raises a network or API error (urllib's OSError) the repo is a
    `FailedRead`, so no date is guessed.
    """
    result = []

    if has_portfolio and _stale_report(today, facts.pushed_at, updated):
        result.append(ScanWarning(id="S1"))

    if has_portfolio and _could_be_s2(today, facts.created_at, health):
        try:
            adopted_on = read_adopted()
        except OSError as error:
            return failed_read(facts.name, error, "adoption date")
        # No commit found: fall back to the created date (the spec's
        # "created or adopted"), never a guess.
        start = max(facts.created_at.date(), adopted_on or date.min)
        if today - start > NOT_REPORTED_AFTER:
            result.append(ScanWarning(id="S2"))

    # Grace-period warnings are already limited to Adopted or higher and
    # to checks not yet due (S1.2.2).
    for check_id, required_from in level.grace_warnings:
        if date.fromisoformat(required_from) - today <= DUE_SOON_WITHIN:
            result.append(
                ScanWarning(id="S3", check_id=check_id, required_from=required_from)
            )

    return result


def read_adoption_date(fetch: Fetch, owner: str, name: str) -> date | None:
    """The UTC date of the first commit that touched `portfolio.json`, or
    None if there is none (docs/decisions.md, "S2 adoption date").

    GitHub lists commits newest first, so this reads pages until one comes
    back empty (the same paging as `list_repos`) and takes the last commit.
    Errors from `fetch` propagate; `work_out_warnings` handles them.
    """
    oldest = None
    page = 1
    while True:
        batch = fetch(
            f"/repos/{owner}/{name}/commits?path=portfolio.json"
            f"&per_page={PAGE_SIZE}&page={page}"
        )
        if not batch:
            break
        oldest = batch[-1]
        page += 1
    if oldest is None:
        return None
    committed = datetime.fromisoformat(oldest["commit"]["committer"]["date"])
    return committed.astimezone(UTC).date()


def _stale_report(today: date, pushed_at: datetime, updated: date | None) -> bool:
    """S1: the report is over 30 days old (or never dated) while the repo
    had pushes in the last 30 days."""
    pushed_recently = today - pushed_at.date() <= STALE_AFTER
    report_old = updated is None or today - updated > STALE_AFTER
    return pushed_recently and report_old


def _could_be_s2(today: date, created_at: datetime, health: str) -> bool:
    """True if S2 is possible before reading the adoption date: health is
    `not-reported` and the repo is over 14 days old (adoption can't be
    earlier than creation)."""
    return health == "not-reported" and today - created_at.date() > NOT_REPORTED_AFTER
