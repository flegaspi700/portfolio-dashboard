"""Works out a repo's compliance level from its check results.

Part of `scan/`. Takes the check registry and the results of
`checks.evaluate_checks` (check ID -> True, False or None for n/a), plus
the repo's files for the version line, and returns the level (0-3), the
standard version the repo names, and its grace-period warnings. The scan
result (S1.4.1) calls it once per repo; scan warnings S1-S3 are S1.2.3.

The rules are `spec/compliance.md` -> Levels and Grace period, with the
level sets taken from the registry's `levels`, never a copy of them
(docs/requirements.md, S1.2.2 notes). It follows `check-compliance.ps1`:
a level set needs each of its checks to pass (n/a isn't a pass), a
required check counts from its `required_from` date onwards, and
grace-period warnings are listed only for repos at Adopted or higher.
Built for S1.2.2.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from scan.checks import Registry

LEVEL_NAMES = ("Not on standard", "Reporting", "Adopted", "Current")

# The same patterns as check-compliance.ps1 uses for the version.
STANDARD_LINE = re.compile(r"\*\*Standard:\*\* pmo-project-standardization (v[^*\s]+)")
TEMPLATE_STAMP = re.compile(r"Template version: ([^*\s]+)")


@dataclass(frozen=True)
class ComplianceLevel:
    """A repo's compliance level, the standard version its AGENTS.md names
    (None if none), and the required checks it fails that aren't due yet,
    as (check ID, required_from) pairs."""

    level: int
    version: str | None
    grace_warnings: list[tuple[str, str]]

    @property
    def name(self) -> str:
        return LEVEL_NAMES[self.level]


def work_out_level(
    registry: Registry,
    results: Mapping[str, bool | None],
    files: Mapping[str, str | None],
    today: date,
) -> ComplianceLevel:
    """Work out one repo's level on `today` from its check results.

    A check ID missing from `results` counts as not passing. The version
    is only reported: it never changes the level.
    """
    required_failures = [
        check
        for check in registry.checks
        if results.get(check["id"]) is False and _is_required(check)
    ]

    level = 0
    if _all_pass(registry.levels.get("adopted", []), results):
        due = [c for c in required_failures if _is_due(c, today)]
        level = 2 if due else 3
    elif _all_pass(registry.levels.get("reporting", []), results):
        level = 1

    grace_warnings = []
    if level >= 2:
        grace_warnings = [
            (check["id"], check["required_from"])
            for check in required_failures
            if not _is_due(check, today)
        ]

    return ComplianceLevel(
        level=level,
        version=_version(files.get("AGENTS.md")),
        grace_warnings=grace_warnings,
    )


def _all_pass(check_ids: list[str], results: Mapping[str, bool | None]) -> bool:
    """True if the set isn't empty and every check in it passed."""
    return bool(check_ids) and all(results.get(cid) is True for cid in check_ids)


def _is_required(check: dict) -> bool:
    return check.get("severity") == "required"


def _is_due(check: dict, today: date) -> bool:
    """A required check is due on and after its `required_from` date."""
    return date.fromisoformat(check["required_from"]) <= today


def _version(agents: str | None) -> str | None:
    """The version AGENTS.md names: the v2 Standard line, else a v1
    project's Template version stamp, marked as such, else None."""
    if agents is None:
        return None
    match = STANDARD_LINE.search(agents)
    if match:
        return match.group(1)
    match = TEMPLATE_STAMP.search(agents)
    if match:
        return f"{match.group(1)} (v1 template)"
    return None
