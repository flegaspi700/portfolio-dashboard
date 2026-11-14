"""Tests for scan/facts.py: reading one in-scope repo's facts (S1.1.2).

All data is made up. A fake fetch function serves canned API responses by
path, or raises the errors urllib raises, so no test touches the network.
"""

import logging
from datetime import UTC, datetime
from email.message import Message
from urllib.error import HTTPError, URLError

from scan.facts import FailedRead, RepoFacts, read_facts

OWNER = "owner"


def repo_body(name="repo", **overrides):
    """One repo as GitHub's /repos/{owner}/{name} returns it."""
    body = {
        "name": name,
        "pushed_at": "2026-10-20T08:30:00Z",
        "created_at": "2025-04-01T12:00:00Z",
        "language": "Python",
        "description": "A made-up repo",
        "default_branch": "main",
        "open_issues_count": 0,
    }
    body.update(overrides)
    return body


def pulls_path(name, page):
    return f"/repos/{OWNER}/{name}/pulls?state=open&per_page=100&page={page}"


def fake_fetch(repo, open_prs=0, page_size=100):
    """A fetch function serving `repo` and `open_prs` made-up open PRs.

    PRs come in pages of `page_size`; any page past the last is empty, as
    on GitHub. Every path asked for is recorded in `.requested`.
    """
    name = repo["name"]
    prs = [{"number": number} for number in range(1, open_prs + 1)]

    def fetch(path):
        fetch.requested.append(path)
        if path == f"/repos/{OWNER}/{name}":
            return repo
        prefix = f"/repos/{OWNER}/{name}/pulls?state=open&per_page=100&page="
        if path.startswith(prefix):
            page = int(path.removeprefix(prefix))
            return prs[(page - 1) * page_size : page * page_size]
        raise AssertionError(f"unexpected path {path}")

    fetch.requested = []
    return fetch


def http_error(code, reason, headers=None):
    message = Message()
    for key, value in (headers or {}).items():
        message[key] = value
    return HTTPError("https://api.github.com/x", code, reason, message, None)


def failing_fetch(error, fail_on="/repos/"):
    """A fetch that serves a normal repo but raises `error` on any path
    starting with `fail_on`."""
    working = fake_fetch(repo_body("repo", open_issues_count=2), open_prs=1)

    def fetch(path):
        if path.startswith(fail_on):
            raise error
        return working(path)

    return fetch


# --- Reading facts ---


def test_facts_are_read_from_the_repo_and_its_open_prs():
    repo = repo_body(
        "tool",
        pushed_at="2026-10-20T08:30:00Z",
        created_at="2025-04-01T12:00:00Z",
        language="Python",
        description="A made-up tool",
        default_branch="main",
        open_issues_count=5,
    )

    facts = read_facts(fake_fetch(repo, open_prs=2), OWNER, "tool")

    assert facts == RepoFacts(
        name="tool",
        pushed_at=datetime(2026, 10, 20, 8, 30, tzinfo=UTC),
        created_at=datetime(2025, 4, 1, 12, 0, tzinfo=UTC),
        language="Python",
        description="A made-up tool",
        default_branch="main",
        open_issues=3,
        open_prs=2,
    )
    assert facts.has_files


def test_github_issue_count_is_split_into_issues_and_prs():
    # GitHub's open_issues_count includes open PRs.
    repo = repo_body("busy", open_issues_count=7)

    facts = read_facts(fake_fetch(repo, open_prs=3), OWNER, "busy")

    assert (facts.open_issues, facts.open_prs) == (4, 3)


def test_repo_with_no_open_work_has_zero_counts():
    facts = read_facts(fake_fetch(repo_body("quiet")), OWNER, "quiet")

    assert (facts.open_issues, facts.open_prs) == (0, 0)


def test_open_prs_on_several_pages_are_all_counted():
    repo = repo_body("huge", open_issues_count=260)

    facts = read_facts(fake_fetch(repo, open_prs=230), OWNER, "huge")

    assert (facts.open_issues, facts.open_prs) == (30, 230)


def test_open_prs_are_asked_for_page_by_page():
    fetch = fake_fetch(repo_body("paged", open_issues_count=150), open_prs=150)

    read_facts(fetch, OWNER, "paged")

    assert fetch.requested == [
        f"/repos/{OWNER}/paged",
        pulls_path("paged", 1),
        pulls_path("paged", 2),
        pulls_path("paged", 3),
    ]


def test_issue_count_never_goes_below_zero():
    # A PR opened between the two requests can make the PR count larger
    # than GitHub's combined count.
    repo = repo_body("racy", open_issues_count=1)

    facts = read_facts(fake_fetch(repo, open_prs=2), OWNER, "racy")

    assert (facts.open_issues, facts.open_prs) == (0, 2)


def test_missing_language_and_description_are_none():
    repo = repo_body("bare", language=None)
    del repo["description"]

    facts = read_facts(fake_fetch(repo), OWNER, "bare")

    assert (facts.language, facts.description) == (None, None)


# --- Empty repo ---


def test_empty_repo_with_null_default_branch_returns_facts_with_files_missing():
    repo = repo_body("empty", default_branch=None, language=None)

    facts = read_facts(fake_fetch(repo), OWNER, "empty")

    assert isinstance(facts, RepoFacts)
    assert facts.default_branch is None
    assert not facts.has_files


def test_empty_repo_with_no_default_branch_field_returns_facts_with_files_missing():
    repo = repo_body("empty")
    del repo["default_branch"]

    facts = read_facts(fake_fetch(repo), OWNER, "empty")

    assert isinstance(facts, RepoFacts)
    assert facts.default_branch is None
    assert not facts.has_files


# --- Failures ---


def test_api_error_reports_the_repo_as_failed():
    fetch = failing_fetch(http_error(500, "Server Error"))

    assert read_facts(fetch, OWNER, "repo") == FailedRead(
        name="repo", reason="HTTP 500"
    )


def test_rate_limit_reports_the_repo_as_failed():
    limited = http_error(403, "Forbidden", {"x-ratelimit-remaining": "0"})

    result = read_facts(failing_fetch(limited), OWNER, "repo")

    assert result == FailedRead(name="repo", reason="HTTP 403")


def test_secondary_rate_limit_reports_the_repo_as_failed():
    result = read_facts(
        failing_fetch(http_error(429, "Too Many Requests")), OWNER, "repo"
    )

    assert result == FailedRead(name="repo", reason="HTTP 429")


def test_network_error_reports_the_repo_as_failed():
    result = read_facts(failing_fetch(URLError("timed out")), OWNER, "repo")

    assert result == FailedRead(name="repo", reason="network error")


def test_failure_while_counting_prs_gives_no_partial_facts():
    # The repo itself was read, but without the PR count the issue count
    # would be made up, so the whole read fails.
    fetch = failing_fetch(
        http_error(502, "Bad Gateway"), fail_on=f"/repos/{OWNER}/repo/pulls"
    )

    assert read_facts(fetch, OWNER, "repo") == FailedRead(
        name="repo", reason="HTTP 502"
    )


def test_failure_is_logged_without_the_repo_name(caplog):
    fetch = failing_fetch(http_error(500, "Server Error"))

    with caplog.at_level(logging.DEBUG, logger="scan.facts"):
        read_facts(fetch, OWNER, "secret_repo_name")

    assert "HTTP 500" in caplog.text
    assert "secret_repo_name" not in caplog.text
