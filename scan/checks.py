"""Loads the standard's check registry and evaluates its checks on a repo.

Part of `scan/`. At the start of a scan, `load_registry` reads
`spec/compliance-checks.json`, and each schema it names, from
pmo-project-standardization's default branch (docs/decisions.md, 2026-11-14)
through the scan's fetch function. If that fails, the scan stops: there is
no local copy to fall back on (AGENTS.md, "the standard is read, never
copied"). `evaluate_checks` then runs every check against one repo's files
(path -> text, a missing path being a missing file) and returns pass, fail
or n/a per check ID. The compliance level (S1.2.2) and warnings (S1.2.3)
are worked out from those results.

The four kinds follow the spec (`spec/compliance.md` -> Checks) and
`check-compliance.ps1`, the reference implementation, with one exception:
`schema` validates the whole document, where the script checks only the
top level (docs/decisions.md, "Reuse or reimplement the compliance checks").
Built for S1.2.1.
"""

import base64
import json
import logging
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from jsonschema.validators import validator_for

from scan.repos import Fetch

logger = logging.getLogger(__name__)

STANDARD_REPO = "flegaspi700/pmo-project-standardization"
REGISTRY_FILE = "compliance-checks.json"

KINDS = {"exists", "contains", "absent", "schema"}


class RegistryError(Exception):
    """The check registry or a schema couldn't be read: the scan must stop."""


class UnknownCheckKind(Exception):
    """The registry uses a kind this scanner doesn't implement."""


@dataclass(frozen=True)
class Registry:
    """The check registry: the check IDs each level needs, the checks as
    the registry states them, and each schema they name, by file name."""

    levels: dict[str, list[str]]
    checks: list[dict[str, Any]]
    schemas: dict[str, dict[str, Any]]


def load_registry(fetch: Fetch) -> Registry:
    """Read the check registry and its schemas from the standard's repo.

    Raises RegistryError, naming the file and the standard's repo, if any
    of them can't be fetched or parsed, or the registry has no `checks` or
    `levels`.
    """
    document = _read_spec_file(fetch, REGISTRY_FILE)
    if (
        not isinstance(document, dict)
        or "checks" not in document
        or "levels" not in document
    ):
        raise RegistryError(
            f"spec/{REGISTRY_FILE} in {STANDARD_REPO} has no 'checks' or 'levels': "
            "it isn't a check registry. The scan stops."
        )
    checks = document["checks"]
    # Each schema once, in the order the checks first name it.
    names = dict.fromkeys(
        check["schema"] for check in checks if check.get("kind") == "schema"
    )
    schemas = {name: _read_spec_file(fetch, name) for name in names}
    logger.info(
        "Read the check registry: %d checks, %d schemas", len(checks), len(schemas)
    )
    return Registry(levels=document["levels"], checks=checks, schemas=schemas)


def evaluate_checks(
    registry: Registry, files: Mapping[str, str]
) -> dict[str, bool | None]:
    """Evaluate every check on one repo's files: check ID -> True (pass),
    False (fail) or None (n/a). Raises UnknownCheckKind on a kind this
    scanner doesn't know."""
    return {
        check["id"]: evaluate_check(check, files, registry.schemas)
        for check in registry.checks
    }


def evaluate_check(
    check: dict[str, Any],
    files: Mapping[str, str],
    schemas: Mapping[str, dict[str, Any]],
) -> bool | None:
    """Evaluate one check on a repo's files (path -> text; missing paths are
    missing files). Returns True, False, or None when `applies_if` doesn't
    match. An unknown kind raises UnknownCheckKind even when `applies_if`
    wouldn't match: the scanner is out of date either way."""
    kind = check.get("kind")
    if kind not in KINDS:
        raise UnknownCheckKind(
            f"Unknown check kind '{kind}' in {check.get('id')}: the scanner needs "
            "updating for this version of the check registry."
        )

    condition = check.get("applies_if")
    if condition and not _matches(files.get(condition["path"]), condition["pattern"]):
        return None

    if kind == "exists":
        return all(path in files for path in check["paths"])
    if kind == "contains":
        text = files.get(check["path"])
        if text is None:
            return bool(check.get("if_exists"))
        return _matches(text, check["pattern"])
    if kind == "absent":
        # Missing files are skipped: they can't contain the pattern.
        return not any(
            _matches(files.get(path), check["pattern"]) for path in check["paths"]
        )
    return _fits_schema(files.get(check["path"]), schemas[check["schema"]])


def _matches(text: str | None, pattern: str) -> bool:
    """True if `text` exists and the pattern matches anywhere in it.

    Ignores case: check-compliance.ps1 uses PowerShell's -match, which
    does, and the registry's patterns are written for it.
    """
    return text is not None and re.search(pattern, text, re.IGNORECASE) is not None


def _fits_schema(text: str | None, schema: dict[str, Any]) -> bool:
    """True if `text` exists, is JSON, and fits the whole schema (nested
    objects and types included, unlike check-compliance.ps1)."""
    if text is None:
        return False
    try:
        document = json.loads(text)
    except ValueError:
        return False
    return validator_for(schema)(schema).is_valid(document)


def _read_spec_file(fetch: Fetch, name: str) -> Any:
    """Fetch spec/<name> from the standard's default branch through the
    contents API and parse it as JSON. Any failure raises RegistryError."""
    path = f"/repos/{STANDARD_REPO}/contents/spec/{name}"
    try:
        body = fetch(path)
        return json.loads(base64.b64decode(body["content"]))
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise RegistryError(
            f"Could not read spec/{name} from {STANDARD_REPO} ({error}). The scan stops: "
            "compliance comes only from the standard, never from a local copy."
        ) from error
