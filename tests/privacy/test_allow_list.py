"""Tests for privacy/allow_list.py: cutting private rows to the allow-list
(S2.1.1).

All data is made up. Private rows are filled with canary values in every
field that isn't on the allow-list, so a test fails if any of them gets
through. The allow-list is docs/decisions.md, "Private repos: real name
plus signals".
"""

from dataclasses import asdict, field, fields, make_dataclass
from datetime import UTC, date, datetime

from privacy.allow_list import PRIVATE_FIELDS, filter_result, filter_row
from scan.result import COULD_NOT_SCAN, SCAN_OK, RepoRow, ScanResult
from scan.warnings import ScanWarning

CANARY = "CANARY-41b9"
NOW = datetime(2026, 12, 1, 6, 0, tzinfo=UTC)


# A row type with one field the allow-list has never heard of, as if a
# later story added it to RepoRow.
ExtendedRow = make_dataclass(
    "ExtendedRow",
    [("secret_field", str, field(default=CANARY))],
    bases=(RepoRow,),
    frozen=True,
)


def reported(**overrides):
    document = {
        "schema": 1,
        "name": f"{CANARY}-reported-name",
        "summary": f"{CANARY} summary",
        "owner": f"{CANARY} owner",
        "lifecycle": "active",
        "health": "amber",
        "health_reason": f"{CANARY} reason",
        "risks": [
            {"title": f"{CANARY} risk 1", "severity": "high"},
            {"title": f"{CANARY} risk 2", "severity": "low"},
        ],
        "blockers": [{"title": f"{CANARY} blocker", "needs": CANARY}],
        "callouts": [f"{CANARY} callout"],
        "budget": {"month": "2026-11", "currency": "USD", "spend": 12.5},
        "updated": "2026-11-20",
    }
    document.update(overrides)
    return document


def row(visibility="private", **overrides):
    values = {
        "name": "secret-repo",
        "visibility": visibility,
        "scan_status": SCAN_OK,
        "pushed_at": datetime(2026, 11, 28, 22, 30, tzinfo=UTC),
        "created_at": datetime(2025, 3, 1, tzinfo=UTC),
        "language": f"{CANARY}-lang",
        "description": f"{CANARY} description",
        "default_branch": f"{CANARY}-branch",
        "open_issues": 7,
        "open_prs": 3,
        "level": 2,
        "level_name": "Adopted",
        "standard_version": "v2.0.0",
        "checks": {"C8": True, "C10": False},
        "warnings": [ScanWarning(id="S3", check_id="C10", required_from="2026-12-13")],
        "has_portfolio": True,
        "health": "amber",
        "reported": reported(),
        "portfolio_problem": None,
    }
    values.update(overrides)
    return RepoRow(**values)


# --- Private rows ---


def test_private_row_keeps_only_the_allow_list():
    output = filter_row(row())

    assert output == {
        "name": "secret-repo",
        "visibility": "private",
        "lifecycle": "active",
        "health": "amber",
        "level": 2,
        "last_activity": date(2026, 11, 28),
        "risk_count": 2,
        "blocker_count": 1,
        "scan_status": SCAN_OK,
    }
    assert CANARY not in repr(output)


def test_allow_list_matches_the_decision():
    assert PRIVATE_FIELDS == (
        "name",
        "visibility",
        "lifecycle",
        "health",
        "level",
        "last_activity",
        "risk_count",
        "blocker_count",
        "scan_status",
    )


def test_a_new_field_no_one_has_listed_is_dropped():
    base = row()
    extended = ExtendedRow(**{f.name: getattr(base, f.name) for f in fields(RepoRow)})

    output = filter_row(extended)

    assert set(output) == set(PRIVATE_FIELDS)
    assert CANARY not in repr(output)


def test_unlisted_reported_fields_never_get_through():
    document = reported(new_field=CANARY, program=CANARY)

    output = filter_row(row(reported=document))

    assert CANARY not in repr(output)


def test_private_row_without_a_valid_portfolio_has_no_counts():
    output = filter_row(row(has_portfolio=False, health="not-reported", reported=None))

    assert output["health"] == "not-reported"
    assert output["lifecycle"] is None
    assert output["risk_count"] is None
    assert output["blocker_count"] is None


def test_counts_are_null_when_not_reported_and_zero_when_empty():
    document = reported(risks=[])
    del document["blockers"]

    output = filter_row(row(reported=document))

    assert output["risk_count"] == 0
    assert output["blocker_count"] is None


def test_odd_visibility_is_treated_as_private():
    output = filter_row(row(visibility="internal"))

    assert set(output) == set(PRIVATE_FIELDS)


# --- Failed private rows ---


def test_failed_private_row_keeps_only_name_and_scan_status():
    failed = RepoRow(
        name="secret-repo",
        visibility="private",
        scan_status=COULD_NOT_SCAN,
        scan_error="HTTP 403",
    )

    assert filter_row(failed) == {
        "name": "secret-repo",
        "scan_status": COULD_NOT_SCAN,
    }


# --- Public rows ---


def test_public_row_passes_unchanged():
    public = row(visibility="public", name="open-repo")

    output = filter_row(public)

    assert {name: output[name] for name in asdict(public)} == asdict(public)


def test_public_row_also_gets_the_signal_fields():
    output = filter_row(row(visibility="public"))

    assert output["last_activity"] == date(2026, 11, 28)
    assert output["risk_count"] == 2
    assert output["lifecycle"] == "active"


def test_failed_public_row_passes_unchanged():
    failed = RepoRow(
        name="open-repo",
        visibility="public",
        scan_status=COULD_NOT_SCAN,
        scan_error="HTTP 500",
    )

    output = filter_row(failed)

    assert output["scan_error"] == "HTTP 500"
    assert output["level"] is None


# --- The whole result ---


def test_result_is_filtered_row_by_row_with_its_header_kept():
    result = ScanResult(
        status="partial",
        scanned_at=NOW,
        spec_version=2,
        rows=[row(visibility="public", name="a"), row(name="b")],
    )

    output = filter_result(result)

    assert output["status"] == "partial"
    assert output["scanned_at"] == NOW
    assert output["spec_version"] == 2
    assert output["failure"] is None
    assert [r["name"] for r in output["rows"]] == ["a", "b"]
    assert set(output["rows"][1]) == set(PRIVATE_FIELDS)


def test_failed_result_has_no_rows_to_leak():
    result = ScanResult(
        status="failed",
        scanned_at=NOW,
        spec_version=None,
        rows=[],
        failure="could not list repos: HTTP 401",
    )

    output = filter_result(result)

    assert output["rows"] == []
    assert output["failure"] == "could not list repos: HTTP 401"


# --- The standard's checks (S4.3.1) ---


def test_checks_keep_only_id_title_severity_and_fix():
    result = ScanResult(
        status="complete",
        scanned_at=NOW,
        spec_version=2,
        rows=[],
        checks=[
            {
                "id": "C8",
                "title": "Names the standard",
                "severity": "required",
                "fix": "Add the line.",
                "kind": "contains",
                "pattern": CANARY,
                "secret_field": CANARY,
            }
        ],
    )

    output = filter_result(result)

    assert output["checks"] == [
        {
            "id": "C8",
            "title": "Names the standard",
            "severity": "required",
            "fix": "Add the line.",
        }
    ]
    assert CANARY not in str(output)


def test_a_check_without_a_title_or_fix_gets_null():
    result = ScanResult(
        status="complete",
        scanned_at=NOW,
        spec_version=2,
        rows=[],
        checks=[{"id": "C5", "severity": "optional"}],
    )

    assert filter_result(result)["checks"] == [
        {"id": "C5", "title": None, "severity": "optional", "fix": None}
    ]


def test_a_result_without_checks_has_an_empty_list():
    result = ScanResult(status="failed", scanned_at=NOW, spec_version=None, rows=[])

    assert filter_result(result)["checks"] == []


# --- Worst case ---


def test_many_private_rows_none_leak():
    rows = [row(name=f"repo-{n}") for n in range(200)]
    result = ScanResult(status="complete", scanned_at=NOW, spec_version=2, rows=rows)

    output = filter_result(result)

    assert CANARY not in repr(output)
    assert all(set(r) == set(PRIVATE_FIELDS) for r in output["rows"])
