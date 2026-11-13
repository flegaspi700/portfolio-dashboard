"""Lists the owner's repos and selects the in-scope ones.

Part of `scan/`. The scan calls `list_repos` with a fetch function (the
only thing here that touches the network, passed in so tests can fake it),
then `select_in_scope` on the listing. The selected `InScopeRepo`s are what
the rest of the scan reads facts, files and status for.

Scope rule: docs/decisions.md -> "Repo scope: spec exclusions plus a fixed
cut-off". Built for S1.1.1.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

logger = logging.getLogger(__name__)

# Fixed by decision (docs/decisions.md, "Repo scope"), not tuned: repos last
# pushed before this date are out of scope.
SCAN_CUT_OFF = date(2026, 1, 1)

# The topic an owner sets on a repo to keep it off the portfolio
# (the standard's spec/compliance.md).
EXCLUDE_TOPIC = "portfolio-exclude"

# GitHub's maximum page size, so the fewest requests (NFR1).
PAGE_SIZE = 100

# Fetches one GitHub API path, such as "/user/repos?page=1", and returns
# the parsed JSON body.
Fetch = Callable[[str], Any]


@dataclass(frozen=True)
class InScopeRepo:
    """An in-scope repo (docs/architecture.md, Words and names), as far as
    the listing tells us.

    `visibility` is "public" or "private"; anything GitHub sends that
    isn't plainly "public" becomes "private", so an odd value can never
    make a private repo's details public. `pushed_at` is in UTC.
    """

    name: str
    visibility: str
    pushed_at: datetime


def list_repos(fetch: Fetch) -> list[dict[str, Any]]:
    """Return every repo the owner owns, reading all pages of the listing.

    Asks for page 1, 2, 3 ... until a page comes back empty. That costs one
    extra request per scan, but doesn't rely on the server honouring the
    page size or on parsing its Link header. Errors from `fetch` propagate:
    without the full listing there is nothing correct to scan.
    """
    repos = []
    page = 1
    while True:
        batch = fetch(f"/user/repos?affiliation=owner&per_page={PAGE_SIZE}&page={page}")
        if not batch:
            break
        repos.extend(batch)
        page += 1
    logger.info("Listed %d repos in %d pages", len(repos), page - 1)
    return repos


def select_in_scope(listing: list[dict[str, Any]]) -> list[InScopeRepo]:
    """Keep the in-scope repos from a GitHub repo listing, in listing order.

    Leaves out archived repos, forks, repos tagged `portfolio-exclude`, and
    repos last pushed before the scan cut-off (a push on the cut-off date
    counts). A repo GitHub has never seen a push for (`pushed_at` null) has
    no activity since the cut-off, so it's left out too. A listing entry
    missing `name`, `archived` or `fork` raises KeyError: GitHub always
    sends them, so their absence means the data isn't a repo listing.
    """
    selected = [
        InScopeRepo(
            name=repo["name"],
            visibility=_visibility(repo.get("visibility")),
            pushed_at=_parse_time(repo["pushed_at"]),
        )
        for repo in listing
        if _is_in_scope(repo)
    ]
    # Counts only: private repo names stay out of the Action logs (NFR5).
    logger.info("Selected %d of %d repos as in scope", len(selected), len(listing))
    return selected


def _is_in_scope(repo: dict[str, Any]) -> bool:
    if repo["archived"] or repo["fork"]:
        return False
    if EXCLUDE_TOPIC in (repo.get("topics") or []):
        return False
    pushed_at = repo.get("pushed_at")
    return pushed_at is not None and _parse_time(pushed_at).date() >= SCAN_CUT_OFF


def _visibility(value: Any) -> str:
    # Anything but a plain "public" is private: the safe side for NFR5.
    return "public" if value == "public" else "private"


def _parse_time(value: str) -> datetime:
    """Parse GitHub's timestamp, such as "2026-01-01T00:00:00Z", as UTC."""
    return datetime.fromisoformat(value).astimezone(UTC)
