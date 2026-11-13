"""Tests for scan/repos.py: listing the owner's repos and selecting the
in-scope ones (S1.1.1).

All data is made up. Listing tests pass in a fake fetch function that
serves pages from memory, so no test touches the network.
"""

import logging
from datetime import UTC, datetime

from scan.repos import InScopeRepo, list_repos, select_in_scope


def listed(name="repo", **overrides):
    """One repo as GitHub's listing returns it, in scope unless overridden."""
    repo = {
        "name": name,
        "visibility": "public",
        "archived": False,
        "fork": False,
        "topics": [],
        "pushed_at": "2026-06-15T12:00:00Z",
    }
    repo.update(overrides)
    return repo


def fake_fetch_serving(all_repos, page_size):
    """A fetch function that serves `all_repos` in pages of `page_size`.

    It reads only the `page` query parameter, the way GitHub numbers pages,
    and records every path it was asked for in `.requested`.
    """

    def fetch(path):
        fetch.requested.append(path)
        page = int(path.split("page=")[-1].split("&")[0])
        start = (page - 1) * page_size
        return all_repos[start : start + page_size]

    fetch.requested = []
    return fetch


def names(repos):
    return [repo.name for repo in repos]


# --- Selecting ---


def test_archived_forks_tagged_and_stale_repos_are_left_out():
    listing = [
        listed("kept"),
        listed("archived", archived=True),
        listed("forked", fork=True),
        listed("tagged", topics=["python", "portfolio-exclude"]),
        listed("stale", pushed_at="2025-12-31T23:59:59Z"),
    ]

    assert names(select_in_scope(listing)) == ["kept"]


def test_repo_pushed_exactly_on_the_cut_off_date_is_included():
    listing = [
        listed("midnight", pushed_at="2026-01-01T00:00:00Z"),
        listed("late_that_day", pushed_at="2026-01-01T23:59:59Z"),
    ]

    assert names(select_in_scope(listing)) == ["midnight", "late_that_day"]


def test_empty_listing_selects_an_empty_list():
    assert select_in_scope([]) == []


def test_missing_or_unrecognised_visibility_is_treated_as_private():
    listing = [
        listed("public_repo", visibility="public"),
        listed("private_repo", visibility="private"),
        listed("internal_repo", visibility="internal"),
        listed("blank_repo", visibility=""),
        listed("null_repo", visibility=None),
        listed("missing_repo"),
    ]
    del listing[-1]["visibility"]

    visibility = {repo.name: repo.visibility for repo in select_in_scope(listing)}

    assert visibility == {
        "public_repo": "public",
        "private_repo": "private",
        "internal_repo": "private",
        "blank_repo": "private",
        "null_repo": "private",
        "missing_repo": "private",
    }


def test_selected_repo_carries_name_visibility_and_last_push():
    [repo] = select_in_scope([listed("one", pushed_at="2026-03-04T05:06:07Z")])

    assert repo == InScopeRepo(
        name="one",
        visibility="public",
        pushed_at=datetime(2026, 3, 4, 5, 6, 7, tzinfo=UTC),
    )


def test_repo_never_pushed_is_left_out():
    # GitHub sends pushed_at as null for a repo with no pushes; it has no
    # activity since the cut-off, so it is out of scope.
    listing = [listed("kept"), listed("never_pushed", pushed_at=None)]

    assert names(select_in_scope(listing)) == ["kept"]


def test_missing_topics_means_not_tagged():
    repo = listed("no_topics_field")
    del repo["topics"]

    assert names(select_in_scope([repo])) == ["no_topics_field"]


def test_selection_logs_counts_but_no_repo_names(caplog):
    listing = [listed("secret_name_kept"), listed("secret_name_gone", fork=True)]

    with caplog.at_level(logging.DEBUG, logger="scan.repos"):
        select_in_scope(listing)

    assert "1 of 2" in caplog.text
    assert "secret_name" not in caplog.text


# --- Listing ---


def test_all_pages_are_read_for_54_repos():
    all_repos = [listed(f"repo{number}") for number in range(54)]
    fetch = fake_fetch_serving(all_repos, page_size=20)

    assert list_repos(fetch) == all_repos


def test_listing_asks_for_the_owners_repos_page_by_page():
    fetch = fake_fetch_serving([listed("a"), listed("b"), listed("c")], page_size=2)

    list_repos(fetch)

    assert fetch.requested == [
        "/user/repos?affiliation=owner&per_page=100&page=1",
        "/user/repos?affiliation=owner&per_page=100&page=2",
        "/user/repos?affiliation=owner&per_page=100&page=3",
    ]


def test_listing_with_no_repos_returns_an_empty_list():
    fetch = fake_fetch_serving([], page_size=100)

    assert list_repos(fetch) == []


def test_listing_stops_at_the_first_empty_page():
    # Exactly one full page: the next page is empty, and nothing after it
    # is asked for.
    fetch = fake_fetch_serving([listed(f"r{n}") for n in range(100)], page_size=100)

    assert len(list_repos(fetch)) == 100
    assert len(fetch.requested) == 2
