"""Tests for scan/result.py: running the scan and assembling its result
(S1.4.1).

All data is made up. `FakeGitHub` answers every API path the scan uses
(the standard's registry, the repo listing, and each repo's facts, PRs,
file tree, blobs and commit history) from plain Python data, so these
tests also run the scan's parts together through their real interfaces:
the integration test for F1.2 and F1.3. No network, no clock.
"""

import base64
import json
import logging
from dataclasses import fields, replace
from datetime import UTC, datetime
from email.message import Message
from urllib.error import HTTPError

from scan.checks import STANDARD_REPO
from scan.result import COULD_NOT_SCAN, SCAN_OK, RepoRow, run_scan

OWNER = "owner"
NOW = datetime(2026, 12, 1, 6, 0, tzinfo=UTC)

SCHEMA = {
    "type": "object",
    "required": ["schema", "name", "health"],
    "properties": {
        "schema": {"const": 1},
        "name": {"type": "string"},
        "health": {"enum": ["green", "amber", "red", "not-reported"]},
        "updated": {"type": ["string", "null"]},
    },
}

REGISTRY = {
    "version": 2,
    "levels": {"reporting": ["C4"], "adopted": ["C4", "C2", "C8"]},
    "checks": [
        {
            "id": "C8",
            "severity": "required",
            "required_from": "2026-12-13",
            "kind": "contains",
            "path": "AGENTS.md",
            "pattern": r"\*\*Standard:\*\* pmo-project-standardization v\d",
        },
        {
            "id": "C2",
            "severity": "required",
            "required_from": "2026-11-09",
            "kind": "contains",
            "path": "AGENTS.md",
            "pattern": r"\*\*Hosting: (local|github)\*\*",
        },
        {
            "id": "C4",
            "severity": "required",
            "required_from": "2026-11-24",
            "kind": "schema",
            "path": "portfolio.json",
            "schema": "portfolio.schema.json",
        },
        {
            "id": "C10",
            "severity": "required",
            "required_from": "2026-12-13",
            "kind": "contains",
            "path": "AGENTS.md",
            "pattern": r"\*\*Standard:\*\* pmo-project-standardization v2\.",
        },
    ],
}

AGENTS = "**Standard:** pmo-project-standardization v2.0.0\n**Hosting: github**\n"


def portfolio(health="green", updated="2026-11-20"):
    return json.dumps({"schema": 1, "name": "x", "health": health, "updated": updated})


CURRENT = {"AGENTS.md": AGENTS, "portfolio.json": portfolio()}


def http_error(code):
    return HTTPError("url", code, "error", Message(), None)


def encoded(text):
    return base64.b64encode(text.encode("utf-8")).decode()


class FakeGitHub:
    """A fetch function over made-up repos.

    `repos` maps a name to a dict with any of: `files` (path -> text),
    `visibility`, `pushed`, `created`, `adopted` (first portfolio.json
    commit), `empty` (no default branch) and `fail` (a path fragment whose
    requests raise HTTP 403). `fail_listing` and `fail_registry` raise on
    those requests. Every path asked for is kept in `requested`.
    """

    def __init__(self, repos, fail_listing=None, fail_registry=False):
        self.repos = repos
        self.fail_listing = fail_listing
        self.fail_registry = fail_registry
        self.requested = []

    def __call__(self, path):
        self.requested.append(path)
        standard = f"/repos/{STANDARD_REPO}/contents/spec/"
        if path.startswith(standard):
            if self.fail_registry:
                raise http_error(401)
            name = path.removeprefix(standard)
            document = REGISTRY if name == "compliance-checks.json" else SCHEMA
            return {"content": encoded(json.dumps(document))}
        if path.startswith("/user/repos"):
            if self.fail_listing:
                raise self.fail_listing
            return self._listing() if path.endswith("&page=1") else []

        name, rest = path.removeprefix(f"/repos/{OWNER}/").partition("/")[::2]
        repo = self.repos[name]
        if repo.get("fail") and repo["fail"] in path:
            raise http_error(403)
        files = repo.get("files", {})
        if rest == "":
            return {
                "name": name,
                "pushed_at": repo.get("pushed", "2026-11-28T10:00:00Z"),
                "created_at": repo.get("created", "2025-03-01T10:00:00Z"),
                "language": "Python",
                "description": "made up",
                "default_branch": None if repo.get("empty") else "main",
                "open_issues_count": 2,
            }
        if rest.startswith("pulls"):
            return []
        if rest.startswith("git/trees/"):
            return {
                "tree": [
                    {"path": p, "type": "blob", "sha": p, "size": len(t)}
                    for p, t in files.items()
                ],
                "truncated": False,
            }
        if rest.startswith("git/blobs/"):
            return {"content": encoded(files[rest.removeprefix("git/blobs/")])}
        if rest.startswith("commits"):
            if not path.endswith("&page=1") or "adopted" not in repo:
                return []
            return [{"commit": {"committer": {"date": repo["adopted"]}}}]
        raise AssertionError(f"unexpected path {path}")

    def _listing(self):
        return [
            {
                "name": name,
                "visibility": repo.get("visibility", "public"),
                "archived": False,
                "fork": False,
                "topics": [],
                "pushed_at": repo.get("pushed", "2026-11-28T10:00:00Z"),
            }
            for name, repo in self.repos.items()
        ]


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
