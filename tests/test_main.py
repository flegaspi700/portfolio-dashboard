"""Tests for main.py: running a whole scan from the command line (S1.4.2).

`main` takes the environment, the `.env` path, the output path, the clock
and the function that makes the fetch function, so these run it on the
fake GitHub with no network and no real token. Logs are read from stderr,
where `configure_logging` sends them.
"""

import logging
from datetime import UTC, datetime
from email.message import Message
from urllib.error import HTTPError

import pytest
from fake_github import FakeGitHub

import main
from privacy.safe_logging import SafeFormatter

TOKEN = "github_pat_FAKE0TOKEN0FOR0TESTS0ONLY"
NOW = datetime(2026, 12, 1, 6, 0, tzinfo=UTC)
GOOD_REPO = {"files": {"AGENTS.md": "**Hosting: github**\n"}}


@pytest.fixture
def paths(tmp_path):
    """A missing .env and an output path, both in a fresh folder."""
    return tmp_path / ".env", tmp_path / "output" / "scan.json"


@pytest.fixture(autouse=True)
def reset_logging():
    yield
    logging.getLogger().handlers.clear()


def run(paths, github, environ=None, tokens=None):
    """Run main with `github` as the fake API; record the tokens it got."""
    env_file, output = paths
    seen = tokens if tokens is not None else []

    def factory(token):
        seen.append(token)
        return github

    environ = {"PORTFOLIO_READ_TOKEN": TOKEN} if environ is None else environ
    return main.main(environ, env_file, output, factory, NOW)


# --- A run with a token ---


def test_run_scans_writes_the_output_and_logs_counts(paths, capsys):
    github = FakeGitHub({"a": GOOD_REPO, "b": GOOD_REPO})

    code = run(paths, github)

    logged = capsys.readouterr().err
    assert code == 0
    assert paths[1].exists()
    assert github.requested[0] == "/user"
    assert "2 repos in scope, 0 could not be scanned" in logged
    assert f"{len(github.requested)} API requests" in logged
    assert "seconds" in logged


def test_token_from_env_file_is_used(paths):
    paths[0].write_text(
        "# local secrets\n\nPORTFOLIO_READ_TOKEN=from-file\n", encoding="utf-8"
    )
    tokens = []

    run(paths, FakeGitHub({"a": GOOD_REPO}), environ={}, tokens=tokens)

    assert tokens == ["from-file"]


def test_environment_wins_over_env_file(paths):
    paths[0].write_text("PORTFOLIO_READ_TOKEN=from-file\n", encoding="utf-8")
    tokens = []

    run(paths, FakeGitHub({"a": GOOD_REPO}), tokens=tokens)

    assert tokens == [TOKEN]


@pytest.mark.parametrize(
    "line",
    [
        'PORTFOLIO_READ_TOKEN="quoted"',
        "PORTFOLIO_READ_TOKEN='quoted'",
        "  PORTFOLIO_READ_TOKEN = quoted  ",
        "﻿PORTFOLIO_READ_TOKEN=quoted",
    ],
    ids=["double-quotes", "single-quotes", "spaces", "bom"],
)
def test_env_file_value_is_cleaned_up(paths, line):
    paths[0].write_text(line + "\n", encoding="utf-8")
    tokens = []

    run(paths, FakeGitHub({"a": GOOD_REPO}), environ={}, tokens=tokens)

    assert tokens == ["quoted"]


# --- No token ---


@pytest.mark.parametrize("environ", [{}, {"PORTFOLIO_READ_TOKEN": "  "}])
def test_missing_token_stops_before_any_request(paths, capsys, environ):
    tokens = []

    code = run(paths, FakeGitHub({}), environ=environ, tokens=tokens)

    logged = capsys.readouterr().err
    assert code != 0
    assert tokens == []
    assert "PORTFOLIO_READ_TOKEN" in logged
    assert ".env.example" in logged
    assert not paths[1].exists()


def test_env_file_without_the_token_counts_as_missing(paths):
    paths[0].write_text("OTHER=1\nnot a setting\n", encoding="utf-8")
    tokens = []

    code = run(paths, FakeGitHub({}), environ={}, tokens=tokens)

    assert code != 0
    assert tokens == []


# --- Exit codes ---


def test_partial_result_exits_non_zero_and_writes(paths):
    github = FakeGitHub({"a": GOOD_REPO, "b": {"fail": "pulls"}})

    assert run(paths, github) == 1
    assert paths[1].exists()


def test_bad_token_exits_non_zero_and_writes_nothing(paths, capsys):
    class Rejected(FakeGitHub):
        def __call__(self, path):
            self.requested.append(path)
            raise HTTPError("url", 401, "Bad credentials", Message(), None)

    code = run(paths, Rejected({}))

    assert code == 1
    assert not paths[1].exists()
    assert "HTTP 401" in capsys.readouterr().err


def test_unexpected_crash_exits_non_zero_and_logs_only_its_type(paths, capsys):
    class Broken(FakeGitHub):
        def __call__(self, path):
            if path.startswith("/user/repos"):
                raise KeyError(f"CANARY-crash {TOKEN}")
            return super().__call__(path)

    code = run(paths, Broken({"a": GOOD_REPO}))

    logged = capsys.readouterr().err
    assert code == 1
    assert "KeyError" in logged
    assert "CANARY-crash" not in logged
    assert TOKEN not in logged


# --- Logs and files ---


def test_logging_goes_through_the_safe_formatter(paths):
    run(paths, FakeGitHub({"a": GOOD_REPO}))

    handlers = logging.getLogger().handlers
    assert [type(h.formatter) for h in handlers] == [SafeFormatter]


def test_token_appears_in_no_log_line(paths, capsys):
    github = FakeGitHub({"a": GOOD_REPO, "b": {"fail": "git/trees"}})

    run(paths, github)

    assert TOKEN not in capsys.readouterr().err


def test_only_the_scan_output_file_is_written(paths):
    env_file, _ = paths

    run(paths, FakeGitHub({"a": GOOD_REPO}))

    written = sorted(
        p.relative_to(env_file.parent).as_posix() for p in env_file.parent.rglob("*")
    )
    assert written == ["output", "output/scan.json"]
