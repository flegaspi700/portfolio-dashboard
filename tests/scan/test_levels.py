"""Tests for scan/levels.py: the compliance level from check results (S1.2.2).

The registry here is made up but shaped like spec version 2: `levels`
names the reporting and adopted sets, and each check has a severity and,
if required, a `required_from` date. Check results are given directly
(check ID -> True, False or None for n/a), so no files are evaluated. The
date is fixed; no clock.
"""

from datetime import date

from scan.checks import Registry
from scan.levels import LEVEL_NAMES, work_out_level

TODAY = date(2026, 12, 1)

REGISTRY = Registry(
    levels={"reporting": ["C4"], "adopted": ["C4", "C2", "C8", "C9"]},
    checks=[
        {"id": "C8", "severity": "required", "required_from": "2026-11-20"},
        {"id": "C2", "severity": "required", "required_from": "2026-11-09"},
        {"id": "C9", "severity": "required", "required_from": "2026-11-20"},
        {"id": "C4", "severity": "required", "required_from": "2026-11-24"},
        {"id": "C10", "severity": "required", "required_from": "2026-12-01"},
        {"id": "C11", "severity": "required", "required_from": "2026-12-13"},
        {"id": "C5", "severity": "optional"},
        {"id": "W1", "severity": "warning"},
    ],
    schemas={},
)

ALL_PASS = {check["id"]: True for check in REGISTRY.checks}

STANDARD_AGENTS = {"AGENTS.md": "**Standard:** pmo-project-standardization v2.0.0\n"}


def results(**changes):
    """Every check passing, except the given check IDs."""
    return {**ALL_PASS, **changes}


# --- Levels ---


def test_adopted_set_and_all_due_checks_pass_is_level_3():
    level = work_out_level(REGISTRY, ALL_PASS, STANDARD_AGENTS, TODAY)

    assert level.level == 3
    assert level.name == "Current"


def test_adopted_set_passes_but_a_due_required_check_fails_is_level_2():
    level = work_out_level(REGISTRY, results(C10=False), STANDARD_AGENTS, TODAY)

    assert level.level == 2
    assert level.name == "Adopted"


def test_only_the_reporting_set_passing_is_level_1():
    only_c4 = {check_id: check_id == "C4" for check_id in ALL_PASS}

    level = work_out_level(REGISTRY, only_c4, {}, TODAY)

    assert level.level == 1
    assert level.name == "Reporting"


def test_nothing_passing_is_level_0():
    nothing = {check_id: False for check_id in ALL_PASS}

    level = work_out_level(REGISTRY, nothing, {}, TODAY)

    assert level.level == 0
    assert level.name == "Not on standard"


def test_no_results_and_no_files_is_level_0_not_an_error():
    level = work_out_level(REGISTRY, {}, {}, TODAY)

    assert level.level == 0
    assert level.version is None
    assert level.grace_warnings == []


def test_n_a_does_not_count_as_a_pass_for_a_level_set():
    # As in check-compliance.ps1: a level needs each of its checks to pass.
    level = work_out_level(REGISTRY, results(C9=None), STANDARD_AGENTS, TODAY)

    assert level.level == 1


def test_n_a_on_a_due_required_check_does_not_drop_the_level():
    level = work_out_level(REGISTRY, results(C10=None), STANDARD_AGENTS, TODAY)

    assert level.level == 3


def test_optional_and_warning_failures_never_lower_the_level():
    level = work_out_level(
        REGISTRY, results(C5=False, W1=False), STANDARD_AGENTS, TODAY
    )

    assert level.level == 3


def test_level_names_follow_the_spec():
    assert LEVEL_NAMES == ("Not on standard", "Reporting", "Adopted", "Current")


# --- Grace period ---


def test_required_check_failing_before_its_date_is_a_warning_and_level_holds():
    level = work_out_level(REGISTRY, results(C11=False), STANDARD_AGENTS, TODAY)

    assert level.level == 3
    assert level.grace_warnings == [("C11", "2026-12-13")]


def test_required_check_failing_on_its_date_counts_as_due():
    # C10 is required from 2026-12-01, which is TODAY.
    level = work_out_level(REGISTRY, results(C10=False), STANDARD_AGENTS, TODAY)

    assert level.level == 2
    assert level.grace_warnings == []


def test_no_grace_warnings_below_adopted():
    # spec/compliance.md -> Grace period (since v2.1.0): for a Reporting
    # repo, failing required checks are the step to Adopted, not warnings.
    only_c4 = {check_id: check_id == "C4" for check_id in ALL_PASS}

    level = work_out_level(REGISTRY, only_c4, {}, TODAY)

    assert level.grace_warnings == []


def test_level_set_check_still_in_grace_period_is_still_needed_for_the_level():
    # The level sets don't wait for a grace period: C8 is in `adopted`.
    early = date(2026, 11, 10)

    level = work_out_level(REGISTRY, results(C8=False), STANDARD_AGENTS, early)

    assert level.level == 1


# --- Version ---


def test_standard_line_version_is_reported():
    level = work_out_level(REGISTRY, ALL_PASS, STANDARD_AGENTS, TODAY)

    assert level.version == "v2.0.0"


def test_agents_file_without_a_version_line_reports_no_version():
    level = work_out_level(REGISTRY, ALL_PASS, {"AGENTS.md": "# A project\n"}, TODAY)

    assert level.version is None


def test_template_version_stamp_is_reported_but_never_affects_the_level():
    v1_agents = {"AGENTS.md": "Template version: v1.5.0\n"}
    only_c4 = {check_id: check_id == "C4" for check_id in ALL_PASS}

    with_stamp = work_out_level(REGISTRY, only_c4, v1_agents, TODAY)
    without_stamp = work_out_level(REGISTRY, only_c4, {}, TODAY)

    assert with_stamp.version == "v1.5.0 (v1 template)"
    assert with_stamp.level == without_stamp.level == 1


def test_template_version_stamp_does_not_raise_a_level_3_repo_or_lower_it():
    both = {
        "AGENTS.md": "**Standard:** pmo-project-standardization v2.1.0\n"
        "Template version: v1.5.0\n"
    }

    level = work_out_level(REGISTRY, ALL_PASS, both, TODAY)

    assert level.level == 3
    assert level.version == "v2.1.0"


# --- Worst case ---


def test_every_check_failing_in_a_large_registry_is_level_0():
    many = [
        {"id": f"R{n}", "severity": "required", "required_from": "2026-11-01"}
        for n in range(500)
    ]
    registry = Registry(
        levels={"reporting": ["R0"], "adopted": ["R0", "R1"]},
        checks=many,
        schemas={},
    )
    failing = {check["id"]: False for check in many}

    level = work_out_level(registry, failing, {}, TODAY)

    assert level.level == 0
    assert level.grace_warnings == []
