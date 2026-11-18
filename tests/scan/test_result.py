"""Tests for scan/result.py: running the scan and assembling its result
(S1.4.1).

All data is made up. `FakeGitHub` answers every API path the scan uses
(the standard's registry, the repo listing, and each repo's facts, PRs,
file tree, blobs and commit history) from plain Python data, so these
tests also run the scan's parts together through their real interfaces:
the integration test for F1.2 and F1.3. No network, no clock.
"""

import json
import logging
from dataclasses import fields, replace
from datetime import UTC, datetime

from fake_github import OWNER, REGISTRY, FakeGitHub, http_error

from scan.result import COULD_NOT_SCAN, SCAN_OK, RepoRow, run_scan

NOW = datetime(2026, 12, 1, 6, 0, tzinfo=UTC)

AGENTS = "**Standard:** pmo-project-standardization v2.0.0\n**Hosting: github**\n"


def portfolio(health="green", updated="2026-11-20"):
    return json.dumps({"schema": 1, "name": "x", "health": health, "updated": updated})


CURRENT = {"AGENTS.md": AGENTS, "portfolio.json": portfolio()}


def scan(repos, **options):
    github = FakeGitHub(repos, **options)
    return run_scan(github, OWNER, NOW), github


NULL_WHEN_FAILED = {f.name for f in fields(RepoRow)} - {
    "name",
    "visibility",
    "scan_status",
    "scan_error",
}


# --- All repos succeed ---


def test_all_repos_succeed_one_row_each_sorted_by_name():
    result, _ = scan(
        {"zeta": {"files": CURRENT}, "Alpha": {"files": CURRENT}, "beta": {}}
    )

    assert result.status == "complete"
    assert [row.name for row in result.rows] == ["Alpha", "beta", "zeta"]
    assert result.scanned_at == NOW
    assert result.spec_version == 2
    assert result.failure is None


def test_a_row_carries_facts_compliance_and_status():
    result, _ = scan({"tidy": {"files": CURRENT, "visibility": "private"}})

    row = result.rows[0]
    assert row.scan_status == SCAN_OK
    assert row.visibility == "private"
    assert row.pushed_at == datetime(2026, 11, 28, 10, 0, tzinfo=UTC)
    assert row.open_issues == 2
    assert row.open_prs == 0
    assert row.level == 3
    assert row.level_name == "Current"
    assert row.standard_version == "v2.0.0"
    assert row.checks == {"C8": True, "C2": True, "C4": True, "C10": True}
    assert row.has_portfolio is True
    assert row.health == "green"
    assert row.reported["updated"] == "2026-11-20"
    assert row.portfolio_problem is None
    assert row.warnings == []


# --- The parts working together (F1.2, F1.3) ---


def test_reporting_repo_with_no_health_and_old_adoption_gets_s2():
    files = {"portfolio.json": portfolio(health="not-reported", updated=None)}
    repos = {"quiet": {"files": files, "adopted": "2026-10-01T09:00:00Z"}}

    row = scan(repos)[0].rows[0]

    assert row.level == 1
    assert row.health == "not-reported"
    assert [w.id for w in row.warnings] == ["S1", "S2"]


def test_adopted_repo_with_a_check_due_soon_gets_s3_and_keeps_level_3():
    # C10 (Standard line names v2) fails, but isn't due until 2026-12-13.
    agents = "**Standard:** pmo-project-standardization v1.9.0\n**Hosting: local**\n"
    files = {"AGENTS.md": agents, "portfolio.json": portfolio()}

    row = scan({"soon": {"files": files}})[0].rows[0]

    assert row.level == 3
    assert row.checks["C10"] is False
    assert [(w.id, w.check_id) for w in row.warnings] == [("S3", "C10")]


def test_broken_portfolio_json_is_not_reported_and_the_scan_goes_on():
    files = {"AGENTS.md": AGENTS, "portfolio.json": "{ not json"}

    result, _ = scan({"broken": {"files": files}, "fine": {"files": CURRENT}})

    broken = result.rows[0]
    assert result.status == "complete"
    assert broken.health == "not-reported"
    assert broken.reported is None
    assert broken.portfolio_problem == "not valid JSON"
    assert broken.level == 0


def test_empty_repo_is_scanned_at_level_0():
    row = scan({"blank": {"empty": True}})[0].rows[0]

    assert row.scan_status == SCAN_OK
    assert row.level == 0
    assert row.has_portfolio is False
    assert row.health == "not-reported"


def test_adoption_date_is_only_read_when_s2_could_fire():
    _, github = scan({"tidy": {"files": CURRENT}})

    assert not any("/commits" in path for path in github.requested)


# --- One repo fails ---


def test_one_failed_repo_could_not_scan_with_null_fields_and_partial_result():
    result, _ = scan({"good": {"files": CURRENT}, "bad": {"fail": "pulls"}})

    bad = result.rows[0]
    assert result.status == "partial"
    assert bad.name == "bad"
    assert bad.scan_status == COULD_NOT_SCAN
    assert bad.scan_error == "HTTP 403"
    assert all(getattr(bad, name) is None for name in NULL_WHEN_FAILED)
    assert result.rows[1].scan_status == SCAN_OK


def test_failed_file_read_could_not_scan():
    result, _ = scan({"good": {"files": CURRENT}, "bad": {"fail": "git/trees"}})

    assert result.rows[0].scan_status == COULD_NOT_SCAN
    assert result.status == "partial"


def test_failed_adoption_date_read_could_not_scan():
    files = {"portfolio.json": portfolio(health="not-reported")}
    repos = {"good": {"files": CURRENT}, "bad": {"files": files, "fail": "commits"}}

    result, _ = scan(repos)

    assert result.rows[0].scan_status == COULD_NOT_SCAN
    assert result.status == "partial"


def test_failed_row_keeps_its_visibility_for_the_filter():
    result, _ = scan({"good": {}, "hidden": {"fail": "pulls", "visibility": "private"}})

    assert result.rows[1].visibility == "private"


# --- The whole run fails ---


def test_result_carries_the_registry_checks_as_stated():
    # S4.3.1: the page shows each check's title and fix from the registry.
    result, _ = scan({"repo": {"files": CURRENT}})

    assert result.checks == REGISTRY["checks"]


def test_unreadable_registry_gives_no_checks():
    result, _ = scan({"repo": {"files": CURRENT}}, fail_registry=True)

    assert result.status == "failed"
    assert result.checks == []


def test_bad_token_fails_the_result_with_no_rows():
    result, _ = scan({"good": {}}, fail_listing=http_error(401))

    assert result.status == "failed"
    assert result.rows == []
    assert result.failure == "could not list repos: HTTP 401"


def test_every_repo_failing_fails_the_result():
    result, _ = scan({"a": {"fail": "pulls"}, "b": {"fail": "pulls"}})

    assert result.status == "failed"
    assert result.failure == "every repo failed"
    assert len(result.rows) == 2


def test_zero_in_scope_repos_fails_the_result():
    result, _ = scan({})

    assert result.status == "failed"
    assert result.failure == "no in-scope repos"


def test_unreadable_registry_fails_the_result_before_any_repo_is_read():
    result, github = scan({"good": {}}, fail_registry=True)

    assert result.status == "failed"
    assert result.failure.startswith("could not read the check registry")
    assert not any(path.startswith(f"/repos/{OWNER}/") for path in github.requested)


# --- Same inputs, same output ---


def test_same_inputs_give_identical_results_apart_from_the_scan_time():
    repos = {
        "b": {"files": CURRENT},
        "a": {"files": {"portfolio.json": portfolio(health="not-reported")}},
        "c": {"fail": "pulls"},
    }
    first = run_scan(FakeGitHub(repos), OWNER, NOW)
    later = datetime(2026, 12, 1, 7, 30, tzinfo=UTC)

    second = run_scan(FakeGitHub(repos), OWNER, later)

    assert replace(first, scanned_at=later) == second


# --- Logs ---


def test_logs_carry_counts_but_no_repo_names(caplog):
    with caplog.at_level(logging.DEBUG):
        scan({"secret-one": {"files": CURRENT}, "secret-two": {"fail": "pulls"}})

    assert "secret" not in caplog.text
    assert "2 repos" in caplog.text


# --- Worst case ---


def test_sixty_repos_with_a_few_failures():
    repos = {f"repo-{n:02d}": {"files": CURRENT} for n in range(60)}
    for n in (3, 30, 59):
        repos[f"repo-{n:02d}"] = {"fail": "pulls"}

    result, _ = scan(repos)

    assert result.status == "partial"
    assert len(result.rows) == 60
    assert sum(row.scan_status == COULD_NOT_SCAN for row in result.rows) == 3


def test_registry_that_is_not_json_fails_with_a_generic_reason():
    class Garbled(FakeGitHub):
        def __call__(self, path):
            if path.endswith("compliance-checks.json"):
                self.requested.append(path)
                return {"content": "bm90IGpzb24="}  # base64 of "not json"
            return super().__call__(path)

    result = run_scan(Garbled({"good": {}}), OWNER, NOW)

    assert result.status == "failed"
    assert result.failure == "could not read the check registry: invalid"
