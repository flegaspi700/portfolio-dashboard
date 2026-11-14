"""Tests for scan/checks.py: loading the check registry and evaluating the
four check kinds (S1.2.1).

The checks, repos and expected results are in fixtures/check_kinds.json.
Its expected results were confirmed against check-compliance.ps1 on the
same fixtures, apart from the cases listed under `script_differs`, where
the spec wins. Registry tests use a fake fetch function; no network.
"""

import base64
import json
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

from scan.checks import (
    STANDARD_REPO,
    Registry,
    RegistryError,
    UnknownCheckKind,
    evaluate_check,
    evaluate_checks,
    load_registry,
)

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "check_kinds.json").read_text(
        encoding="utf-8"
    )
)
CHECKS = {check["id"]: check for check in FIXTURES["checks"]}
SCHEMAS = FIXTURES["schemas"]
REPOS = FIXTURES["repos"]

REGISTRY_PATH = f"/repos/{STANDARD_REPO}/contents/spec/compliance-checks.json"
SCHEMA_PATH = f"/repos/{STANDARD_REPO}/contents/spec/portfolio.schema.json"


def expected_cases(differs):
    """(repo, check id, expected) for every fixture expectation, either the
    ones check-compliance.ps1 agrees with or the ones it doesn't."""
    return [
        (repo, check_id, expected)
        for repo, results in FIXTURES["expected"].items()
        for check_id, expected in results.items()
        if (check_id in FIXTURES["script_differs"].get(repo, {})) == differs
    ]


# --- The four kinds, matching check-compliance.ps1 ---


@pytest.mark.parametrize(
    ("repo", "check_id", "expected"), expected_cases(differs=False)
)
def test_check_kinds_match_check_compliance_script(repo, check_id, expected):
    assert evaluate_check(CHECKS[check_id], REPOS[repo], SCHEMAS) is expected


def test_contains_ignores_case_like_the_script():
    # PowerShell's -match ignores case, so the script does too.
    agents = {"AGENTS.md": "Text files are UTF-8 WITHOUT A BOM."}

    assert evaluate_check(CHECKS["CT_CASE"], agents, SCHEMAS) is True


def test_absent_ignores_case_like_the_script():
    check = {"id": "X", "kind": "absent", "paths": ["notes.md"], "pattern": "todo"}

    assert evaluate_check(check, {"notes.md": "TODO: finish"}, SCHEMAS) is False


def test_applies_if_ignores_case_like_the_script():
    check = dict(CHECKS["AI_CONTAINS"])
    files = {"AGENTS.md": "TEMPLATE VERSION: V1\n## Doc status\n"}

    assert evaluate_check(check, files, SCHEMAS) is True


# --- Nested schema errors: the spec wins over the script ---


@pytest.mark.parametrize(("repo", "check_id", "expected"), expected_cases(differs=True))
def test_schema_errors_the_script_misses_still_fail(repo, check_id, expected):
    assert evaluate_check(CHECKS[check_id], REPOS[repo], SCHEMAS) is expected


def test_nested_schema_error_fails_the_schema_check():
    assert evaluate_check(CHECKS["SC"], REPOS["schema_nested_error"], SCHEMAS) is False


# --- applies_if and if_exists ---


def test_applies_if_not_matching_gives_n_a():
    files = {"AGENTS.md": "**Standard:** pmo-project-standardization v2.0.0\n"}

    assert evaluate_check(CHECKS["AI_CONTAINS"], files, SCHEMAS) is None


def test_applies_if_with_its_file_missing_gives_n_a():
    assert evaluate_check(CHECKS["AI_EXISTS"], {}, SCHEMAS) is None


def test_if_exists_with_the_file_missing_passes():
    assert evaluate_check(CHECKS["CT_IF_EXISTS"], {}, SCHEMAS) is True


def test_contains_without_if_exists_fails_when_the_file_is_missing():
    assert evaluate_check(CHECKS["CT"], {}, SCHEMAS) is False


# --- Unknown kinds stop the run ---


def test_unknown_check_kind_stops_and_names_the_kind_and_check():
    check = {"id": "C99", "kind": "matches_glob", "path": "x"}

    with pytest.raises(UnknownCheckKind, match="matches_glob") as error:
        evaluate_check(check, {}, SCHEMAS)

    assert "C99" in str(error.value)


def test_unknown_check_kind_stops_a_whole_evaluation():
    registry = Registry(
        levels={},
        checks=[CHECKS["EX"], {"id": "C99", "kind": "matches_glob"}],
        schemas=SCHEMAS,
    )

    with pytest.raises(UnknownCheckKind):
        evaluate_checks(registry, REPOS["full"])


# --- Evaluating a whole registry ---


def test_every_check_in_the_registry_gets_a_result_by_id():
    registry = Registry(levels={}, checks=FIXTURES["checks"], schemas=SCHEMAS)

    assert evaluate_checks(registry, REPOS["full"]) == FIXTURES["expected"]["full"]


def test_registry_with_no_checks_gives_no_results():
    assert (
        evaluate_checks(Registry(levels={}, checks=[], schemas={}), REPOS["full"]) == {}
    )


def test_large_realistic_file_is_evaluated():
    # About 1 MB of requirements text with one placeholder at the very end.
    line = "- [ ] Given a repo, when read, then its facts are returned (`<code>` ok)\n"
    text = line * (1_000_000 // len(line)) + "<One paragraph vision>\n"

    assert (
        evaluate_check(CHECKS["AB"], {"docs/requirements.md": text}, SCHEMAS) is False
    )


# --- Loading the registry from the standard ---


def contents(document):
    """A GitHub contents API response holding `document` as JSON."""
    raw = json.dumps(document).encode("utf-8")
    return {"encoding": "base64", "content": base64.b64encode(raw).decode("ascii")}


REGISTRY_DOCUMENT = {
    "version": 2,
    "levels": {"reporting": ["SC"], "adopted": ["SC", "CT"]},
    "checks": FIXTURES["checks"],
}


def fake_fetch(responses):
    """A fetch serving `responses` (path -> body), recording each path."""

    def fetch(path):
        fetch.requested.append(path)
        response = responses[path]
        if isinstance(response, Exception):
            raise response
        return response

    fetch.requested = []
    return fetch


def test_registry_and_schemas_are_read_from_the_standards_default_branch():
    fetch = fake_fetch(
        {
            REGISTRY_PATH: contents(REGISTRY_DOCUMENT),
            SCHEMA_PATH: contents(SCHEMAS["portfolio.schema.json"]),
        }
    )

    registry = load_registry(fetch)

    assert registry == Registry(
        levels=REGISTRY_DOCUMENT["levels"],
        checks=FIXTURES["checks"],
        schemas=SCHEMAS,
    )
    # No ?ref=: the default branch (docs/decisions.md, 2026-11-14).
    assert fetch.requested == [REGISTRY_PATH, SCHEMA_PATH]


def test_each_schema_is_read_once_however_many_checks_use_it():
    document = dict(
        REGISTRY_DOCUMENT, checks=[CHECKS["SC"], dict(CHECKS["SC"], id="SC2")]
    )
    fetch = fake_fetch(
        {
            REGISTRY_PATH: contents(document),
            SCHEMA_PATH: contents(SCHEMAS["portfolio.schema.json"]),
        }
    )

    load_registry(fetch)

    assert fetch.requested == [REGISTRY_PATH, SCHEMA_PATH]


@pytest.mark.parametrize(
    "failure",
    [
        HTTPError("https://api.github.com/x", 404, "Not Found", None, None),
        HTTPError("https://api.github.com/x", 403, "Forbidden", None, None),
        URLError("timed out"),
    ],
    ids=["not found", "rate limited", "network error"],
)
def test_unreadable_registry_stops_the_run_with_no_fallback(failure):
    fetch = fake_fetch({REGISTRY_PATH: failure})

    with pytest.raises(RegistryError, match="pmo-project-standardization"):
        load_registry(fetch)

    # Nothing else is tried: there is no local copy to fall back on.
    assert fetch.requested == [REGISTRY_PATH]


def test_unreadable_schema_stops_the_run():
    failure = HTTPError("https://api.github.com/x", 404, "Not Found", None, None)
    fetch = fake_fetch(
        {REGISTRY_PATH: contents(REGISTRY_DOCUMENT), SCHEMA_PATH: failure}
    )

    with pytest.raises(RegistryError, match="portfolio.schema.json"):
        load_registry(fetch)


def test_registry_that_is_not_json_stops_the_run():
    not_json = {"encoding": "base64", "content": base64.b64encode(b"{ nope").decode()}

    with pytest.raises(RegistryError):
        load_registry(fake_fetch({REGISTRY_PATH: not_json}))


def test_registry_without_checks_stops_the_run():
    fetch = fake_fetch({REGISTRY_PATH: contents({"version": 2, "levels": {}})})

    with pytest.raises(RegistryError, match="checks"):
        load_registry(fetch)
