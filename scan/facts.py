"""Reads the facts GitHub knows about one in-scope repo.

Part of `scan/`. For each `InScopeRepo` from `scan/repos.py`, the scan calls
`read_facts` with the same fetch function (passed in so tests can fake it).
It reads the repo and counts its open PRs, and returns either `RepoFacts`
or, when GitHub can't be read, a `FailedRead` with no made-up values. The
scan result (S1.4.1) turns a `FailedRead` into a "could not scan" row
(docs/decisions.md -> "Scan failure: publish partial and flag it").

Built for S1.1.2.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.error import HTTPError

from scan.repos import PAGE_SIZE, Fetch

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RepoFacts:
    """Repo facts (docs/architecture.md, Words and names) for one repo.

    Times are in UTC. `language`, `description` and `default_branch` are
    None when GitHub has none. `open_issues` excludes PRs, unlike GitHub's
    own count.
    """

    name: str
    pushed_at: datetime
    created_at: datetime
    language: str | None
    description: str | None
    default_branch: str | None
    open_issues: int
    open_prs: int

    @property
    def has_files(self) -> bool:
        """False for an empty repo (no default branch): its files all count
        as missing."""
        return self.default_branch is not None


@dataclass(frozen=True)
class FailedRead:
    """A repo whose facts couldn't be read. `reason` is short and generic,
    such as "HTTP 403" or "network error", with nothing from the repo."""

    name: str
    reason: str


def read_facts(fetch: Fetch, owner: str, name: str) -> RepoFacts | FailedRead:
    """Read one repo's facts: two API paths, the PR list paged.

    An API error, rate limit or network failure (urllib raises all of them
    as OSError) on any request gives a `FailedRead` for the whole repo, so
    no count is ever a guess. Other errors propagate: a response missing a
    field GitHub always sends, such as `created_at`, raises KeyError.
    """
    try:
        repo = fetch(f"/repos/{owner}/{name}")
        open_prs = _count_open_prs(fetch, owner, name)
    except OSError as error:
        reason = (
            f"HTTP {error.code}" if isinstance(error, HTTPError) else "network error"
        )
        # No repo name: private names stay out of the Action logs (NFR5).
        logger.warning("Could not read a repo's facts: %s", reason)
        return FailedRead(name=name, reason=reason)

    return RepoFacts(
        name=name,
        pushed_at=_parse_time(repo["pushed_at"]),
        created_at=_parse_time(repo["created_at"]),
        language=repo.get("language"),
        description=repo.get("description"),
        default_branch=repo.get("default_branch") or None,
        # GitHub's count includes open PRs. A PR opened between the two
        # requests could push this below zero, so it stops at zero.
        open_issues=max(repo["open_issues_count"] - open_prs, 0),
        open_prs=open_prs,
    )


def _count_open_prs(fetch: Fetch, owner: str, name: str) -> int:
    """Count open PRs, reading pages until one comes back empty (the same
    paging as `list_repos`: one extra request, no Link header parsing)."""
    count = 0
    page = 1
    while True:
        batch = fetch(
            f"/repos/{owner}/{name}/pulls?state=open&per_page={PAGE_SIZE}&page={page}"
        )
        if not batch:
            return count
        count += len(batch)
        page += 1


def _parse_time(value: str) -> datetime:
    """Parse GitHub's timestamp, such as "2026-01-01T00:00:00Z", as UTC."""
    return datetime.fromisoformat(value).astimezone(UTC)
