"""Tests for scan/warnings.py: spec warnings S1, S2 and S3 (S1.2.3).

All data is made up and the date is fixed; no clock. The adoption date is
read through a fake fetch function serving canned commit pages, or raising
the errors urllib raises, so no test touches the network.
"""

import logging
from datetime import UTC, date, datetime, timedelta
from email.message import Message
from urllib.error import HTTPError, URLError

from scan.facts import FailedRead, RepoFacts
from scan.levels import ComplianceLevel
from scan.warnings import ScanWarning, read_adoption_date, work_out_warnings

OWNER = "owner"
TODAY = date(2026, 12, 1)


def days_ago(days):
    """A UTC time `days` days before TODAY, at noon."""
    return datetime(2026, 12, 1, 12, tzinfo=UTC) - timedelta(days=days)


def facts(pushed_days_ago=2, created_days_ago=400, name="secret-repo"):
    return RepoFacts(
        name=name,
        pushed_at=days_ago(pushed_days_ago),
        created_at=days_ago(created_days_ago),
        language=None,
        description=None,
        default_branch="main",
        open_issues=0,
        open_prs=0,
    )


ADOPTED_LEVEL = ComplianceLevel(level=3, version="v2.0.0", grace_warnings=[])


def never_read():
    raise AssertionError("the adoption date was read when S2 couldn't fire")


def adopted(days):
    """A reader for an adoption date `days` days before TODAY."""
    return lambda: TODAY - timedelta(days=days)


def warnings(
    repo=None,
    has_portfolio=True,
    health="green",
    updated=TODAY,
    level=ADOPTED_LEVEL,
    read_adopted=never_read,
):
    return work_out_warnings(
        TODAY,
        repo or facts(),
        has_portfolio,
        health,
        updated,
        level,
        read_adopted,
    )


def ids(result):
    return [warning.id for warning in result]


# --- S1: stale report ---


def test_updated_over_30_days_old_with_recent_pushes_is_s1():
    assert ids(warnings(updated=TODAY - timedelta(days=31))) == ["S1"]


def test_updated_null_with_recent_pushes_is_s1():
    assert ids(warnings(updated=None)) == ["S1"]


def test_updated_exactly_30_days_old_is_not_s1():
    assert warnings(updated=TODAY - timedelta(days=30)) == []


def test_stale_updated_without_pushes_in_the_last_30_days_is_not_s1():
    quiet = facts(pushed_days_ago=31)

    assert warnings(repo=quiet, updated=None) == []


def test_push_exactly_30_days_ago_counts_as_in_the_last_30_days():
    edge = facts(pushed_days_ago=30)

    assert ids(warnings(repo=edge, updated=None)) == ["S1"]


def test_no_portfolio_file_is_not_s1():
    # Level 0 is already the finding; there is no report to be stale.
    assert warnings(has_portfolio=False, health="not-reported", updated=None) == []


# --- S2: health never reported ---


def test_not_reported_more_than_14_days_after_adoption_is_s2():
    result = warnings(health="not-reported", read_adopted=adopted(15))

    assert ids(result) == ["S2"]


def test_not_reported_exactly_14_days_after_adoption_is_not_s2():
    assert warnings(health="not-reported", read_adopted=adopted(14)) == []


def test_old_repo_adopted_recently_is_not_s2():
    old = facts(created_days_ago=400)

    assert warnings(repo=old, health="not-reported", read_adopted=adopted(3)) == []


def test_no_portfolio_file_is_not_s2_and_reads_no_history():
    assert warnings(has_portfolio=False, health="not-reported") == []


def test_reported_health_is_not_s2_and_reads_no_history():
    assert warnings(health="amber") == []


def test_repo_created_14_days_ago_or_less_is_not_s2_and_reads_no_history():
    young = facts(created_days_ago=14)

    assert warnings(repo=young, health="not-reported") == []


def test_no_adoption_commit_found_falls_back_to_the_created_date():
    young = facts(created_days_ago=20)

    result = warnings(repo=young, health="not-reported", read_adopted=lambda: None)

    assert ids(result) == ["S2"]


def test_adoption_date_unreadable_makes_the_repo_a_failed_read(caplog):
    def broken():
        raise HTTPError("url", 403, "rate limited", Message(), None)

    with caplog.at_level(logging.DEBUG):
        result = warnings(health="not-reported", read_adopted=broken)

    assert result == FailedRead(name="secret-repo", reason="HTTP 403")
    assert "secret-repo" not in caplog.text


def test_adoption_date_network_error_makes_the_repo_a_failed_read():
    def offline():
        raise URLError("no route")

    result = warnings(health="not-reported", read_adopted=offline)

    assert result == FailedRead(name="secret-repo", reason="network error")


# --- S3: required change due soon ---


def grace(*pairs):
    return ComplianceLevel(level=3, version="v2.0.0", grace_warnings=list(pairs))


def test_required_check_due_within_14_days_is_s3():
    level = grace(("C8", "2026-12-13"))

    result = warnings(level=level)

    assert result == [ScanWarning(id="S3", check_id="C8", required_from="2026-12-13")]


def test_required_check_due_in_exactly_14_days_is_s3():
    level = grace(("C8", "2026-12-15"))

    assert ids(warnings(level=level)) == ["S3"]


def test_required_check_due_in_15_days_is_not_s3():
    level = grace(("C8", "2026-12-16"))

    assert warnings(level=level) == []


def test_each_check_due_soon_is_its_own_s3():
    level = grace(("C8", "2026-12-13"), ("C9", "2026-12-13"), ("C10", "2027-01-30"))

    result = warnings(level=level)

    assert [w.check_id for w in result] == ["C8", "C9"]


def test_below_adopted_has_no_grace_warnings_so_no_s3():
    # S1.2.2 lists grace-period warnings only at Adopted or higher.
    reporting = ComplianceLevel(level=1, version=None, grace_warnings=[])

    assert warnings(level=reporting) == []


# --- All three together ---


def test_all_three_warnings_in_order():
    result = warnings(
        health="not-reported",
        updated=None,
        level=grace(("C8", "2026-12-13")),
        read_adopted=adopted(60),
    )

    assert ids(result) == ["S1", "S2", "S3"]


# --- Reading the adoption date ---


def commits_path(name, page):
    return f"/repos/{OWNER}/{name}/commits?path=portfolio.json&per_page=100&page={page}"


def fake_commits(dates, name="repo"):
    """A fetch function serving commits touching portfolio.json, newest
    first, 100 per page, with an empty page after the last."""
    commits = [{"commit": {"committer": {"date": d}}} for d in dates]

    def fetch(path):
        fetch.requested.append(path)
        prefix = commits_path(name, "")
        assert path.startswith(prefix), f"unexpected path {path}"
        page = int(path.removeprefix(prefix))
        return commits[(page - 1) * 100 : page * 100]

    fetch.requested = []
    return fetch


def test_adoption_date_is_the_oldest_commit_touching_portfolio_json():
    fetch = fake_commits(["2026-11-10T09:00:00Z", "2026-10-02T23:30:00Z"])

    assert read_adoption_date(fetch, OWNER, "repo") == date(2026, 10, 2)


def test_adoption_date_reads_every_page():
    newest_first = [f"2026-11-{day:02d}T00:00:00Z" for day in range(30, 0, -1)] * 9
    newest_first[-1] = "2025-06-07T00:00:00Z"
    fetch = fake_commits(newest_first)

    assert read_adoption_date(fetch, OWNER, "repo") == date(2025, 6, 7)
    assert fetch.requested == [commits_path("repo", page) for page in (1, 2, 3, 4)]


def test_adoption_date_with_no_commits_is_none():
    assert read_adoption_date(fake_commits([]), OWNER, "repo") is None


def test_adoption_date_is_the_utc_date():
    # 2026-10-02T23:30-05:00 is 2026-10-03 in UTC.
    fetch = fake_commits(["2026-10-02T23:30:00-05:00"])

    assert read_adoption_date(fetch, OWNER, "repo") == date(2026, 10, 3)
