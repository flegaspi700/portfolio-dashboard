"""Tests for scan/status.py: reading a repo's `portfolio.json` (S1.3.1).

All data is made up. The schema is a cut-down copy of the reporting
contract's, given to the reader through a made-up registry, the way the
scan gets the real one from the standard. A canary value is planted in
broken files to prove the reader never quotes them.
"""

import json
import logging
from datetime import date

import pytest

from scan.checks import Registry, RegistryError
from scan.files import MAX_FILE_BYTES
from scan.status import NOT_REPORTED, read_status

CANARY = "CANARY-7f3e-private-detail"

SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["schema", "name", "lifecycle", "health"],
    "additionalProperties": False,
    "properties": {
        "schema": {"const": 1},
        "name": {"type": "string", "minLength": 1},
        "lifecycle": {"enum": ["planning", "active", "on-hold", "done", "archived"]},
        "health": {"enum": ["green", "amber", "red", "not-reported"]},
        "risks": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["title", "severity"],
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "severity": {"enum": ["high", "medium", "low"]},
                },
            },
        },
        "callouts": {"type": "array", "items": {"type": "string"}},
        "updated": {
            "oneOf": [
                {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                {"type": "null"},
            ]
        },
    },
}

REGISTRY = Registry(
    levels={},
    checks=[
        {"id": "C4", "kind": "schema", "path": "portfolio.json", "schema": "p.json"},
        {"id": "C8", "kind": "contains", "path": "AGENTS.md", "pattern": "x"},
    ],
    schemas={"p.json": SCHEMA},
)

VALID = {
    "schema": 1,
    "name": "made-up",
    "lifecycle": "active",
    "health": "amber",
    "risks": [{"title": "Slow API", "severity": "medium"}],
    "callouts": ["Needs a decision on hosting"],
    "updated": "2026-11-10",
}


def read(document=None, text=None):
    """Read a portfolio.json holding `document` (as JSON) or raw `text`."""
    content = text if text is not None else json.dumps(document)
    return read_status({"portfolio.json": content}, REGISTRY)


# --- Valid ---


def test_valid_file_fields_are_returned_unchanged():
    status = read(VALID)

    assert status.has_portfolio is True
    assert status.fields == VALID
    assert status.problem is None
    assert status.health == "amber"
    assert status.updated == date(2026, 11, 10)


def test_valid_file_with_updated_null():
    status = read({**VALID, "updated": None})

    assert status.updated is None
    assert status.problem is None


# --- Missing ---


def test_missing_file_is_not_reported_and_does_not_fail():
    status = read_status({"AGENTS.md": "x"}, REGISTRY)

    assert status.has_portfolio is False
    assert status.health == NOT_REPORTED
    assert status.fields is None
    assert status.updated is None


def test_empty_repo_is_not_reported():
    assert read_status({}, REGISTRY).health == NOT_REPORTED


# --- Invalid ---


@pytest.mark.parametrize(
    ("text", "problem"),
    [
        ('{"name": "' + CANARY + '", ', "not valid JSON"),
        ("", "not valid JSON"),
        ('"' + CANARY + '"', "does not fit the schema"),
        ("[1, 2]", "does not fit the schema"),
    ],
)
def test_broken_file_is_not_reported_without_quoting_it(text, problem, caplog):
    with caplog.at_level(logging.DEBUG):
        status = read(text=text)

    assert status.has_portfolio is True
    assert status.health == NOT_REPORTED
    assert status.fields is None
    assert status.problem.startswith(problem)
    assert CANARY not in status.problem
    assert CANARY not in caplog.text


@pytest.mark.parametrize(
    "broken",
    [
        {**VALID, "health": CANARY},
        {**VALID, CANARY: "extra field"},
        {k: v for k, v in VALID.items() if k != "lifecycle"},
        {**VALID, "risks": [{"title": CANARY, "severity": CANARY}]},
        {**VALID, "name": 5},
    ],
    ids=["bad-enum", "unknown-field", "missing-field", "nested", "top-level-type"],
)
def test_schema_mismatch_is_not_reported_without_quoting_it(broken, caplog):
    with caplog.at_level(logging.DEBUG):
        status = read(broken)

    assert status.health == NOT_REPORTED
    assert status.fields is None
    assert status.problem.startswith("does not fit the schema")
    assert CANARY not in status.problem
    assert CANARY not in caplog.text


def test_schema_problem_says_where():
    status = read({**VALID, "risks": [{"title": "t", "severity": "huge"}]})

    assert status.problem == "does not fit the schema (enum at $.risks[0].severity)"


def test_unknown_schema_version_is_not_reported():
    status = read({**VALID, "schema": 2})

    assert status.health == NOT_REPORTED
    assert status.fields is None
    assert status.problem == "unknown schema version"


def test_updated_that_is_not_a_real_date_is_invalid():
    status = read({**VALID, "updated": "2026-13-45"})

    assert status.health == NOT_REPORTED
    assert status.problem == "'updated' is not a real date"


def test_invalid_file_is_logged_without_a_repo_name(caplog):
    with caplog.at_level(logging.DEBUG):
        read(text="not json")

    assert "not valid JSON" in caplog.text


# --- Large files ---


def test_file_too_large_to_read_is_invalid():
    # scan/files.py leaves a file over 1 MB unread (None).
    status = read_status({"portfolio.json": None}, REGISTRY)

    assert status.has_portfolio is True
    assert status.health == NOT_REPORTED
    assert status.problem == "over 1 MB, not read"


def test_text_over_1_mb_is_invalid_and_not_parsed():
    huge = json.dumps({**VALID, "callouts": ["x" * MAX_FILE_BYTES]})

    status = read(text=huge)

    assert status.health == NOT_REPORTED
    assert status.problem == "over 1 MB, not read"


# --- Never inferred ---


def test_absent_risks_and_callouts_stay_absent():
    minimal = {k: VALID[k] for k in ("schema", "name", "lifecycle", "health")}

    status = read(minimal)

    assert status.fields == minimal
    assert "risks" not in status.fields
    assert "callouts" not in status.fields
    assert status.updated is None


def test_health_from_an_invalid_file_is_never_used():
    status = read({**VALID, "health": "green", "lifecycle": "unknown"})

    assert status.health == NOT_REPORTED


def test_reported_not_reported_is_kept_as_is():
    status = read({**VALID, "health": "not-reported"})

    assert status.health == NOT_REPORTED
    assert status.problem is None


# --- The schema comes from the registry ---


def test_registry_without_a_portfolio_schema_check_stops_the_run():
    registry = Registry(levels={}, checks=[], schemas={})

    with pytest.raises(RegistryError, match="portfolio.json"):
        read_status({"portfolio.json": json.dumps(VALID)}, registry)
