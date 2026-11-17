"""Reads what a repo reports about itself in its `portfolio.json`.

Part of `scan/`. The scan calls `read_status` with the repo's files (from
`scan/files.py`) and the check registry. The file is validated against the
schema the registry's `portfolio.json` check names (the reporting contract,
read from the standard, never copied). A valid file's fields come back
unchanged; anything else (missing, too big, not JSON, not fitting the
schema, an unknown contract version) gives health `not-reported` and no
fields at all, so health, risks and call-outs are never inferred
(reporting contract: "Unknown is null, not a guess"). Scan warnings
(S1.2.3) use `has_portfolio`, `health` and `updated`.

A rejected file's problem names what is wrong and where, never the file's
content. Built for S1.3.1.
"""

import json
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

from jsonschema.exceptions import best_match
from jsonschema.validators import validator_for

from scan.checks import Registry, RegistryError
from scan.files import MAX_FILE_BYTES

logger = logging.getLogger(__name__)

PORTFOLIO_FILE = "portfolio.json"
NOT_REPORTED = "not-reported"


@dataclass(frozen=True)
class ReportedStatus:
    """What one repo reports. `fields` is the whole valid file, unchanged,
    or None when there is no valid file; `problem` says why a present file
    was rejected (None when valid or missing)."""

    has_portfolio: bool
    fields: dict[str, Any] | None
    problem: str | None

    @property
    def health(self) -> str:
        return self.fields["health"] if self.fields else NOT_REPORTED

    @property
    def updated(self) -> date | None:
        """The date a person last reviewed the status, or None."""
        value = self.fields.get("updated") if self.fields else None
        return date.fromisoformat(value) if value else None


def read_status(files: Mapping[str, str | None], registry: Registry) -> ReportedStatus:
    """Read and validate one repo's `portfolio.json`.

    Raises RegistryError if the registry has no schema check for the file:
    without the contract's schema nothing can be validated.
    """
    schema = _portfolio_schema(registry)
    if PORTFOLIO_FILE not in files:
        return ReportedStatus(has_portfolio=False, fields=None, problem=None)

    problem, document = _validate(files[PORTFOLIO_FILE], schema)
    if problem:
        # No repo name or content: both may be private (NFR5).
        logger.warning("A repo's portfolio.json was rejected: %s", problem)
        return ReportedStatus(has_portfolio=True, fields=None, problem=problem)
    return ReportedStatus(has_portfolio=True, fields=document, problem=None)


def _validate(
    text: str | None, schema: dict[str, Any]
) -> tuple[str | None, dict[str, Any] | None]:
    """Return (problem, None) for a file to reject, or (None, document)."""
    # None: scan/files.py didn't download it because it is over 1 MB.
    if text is None or len(text.encode("utf-8")) > MAX_FILE_BYTES:
        return "over 1 MB, not read", None
    try:
        document = json.loads(text)
    except ValueError:
        return "not valid JSON", None

    known_version = schema.get("properties", {}).get("schema", {}).get("const")
    if (
        isinstance(document, dict)
        and "schema" in document
        and known_version is not None
        and document["schema"] != known_version
    ):
        return "unknown schema version", None

    error = best_match(validator_for(schema)(schema).iter_errors(document))
    if error is not None:
        # The validator name and path only: an error's message quotes values.
        return f"does not fit the schema ({error.validator} at {error.json_path})", None

    try:
        if document.get("updated"):
            date.fromisoformat(document["updated"])
    except ValueError:
        return "'updated' is not a real date", None
    return None, document


def _portfolio_schema(registry: Registry) -> dict[str, Any]:
    """The schema the registry's schema check for portfolio.json uses."""
    for check in registry.checks:
        if check.get("kind") == "schema" and check.get("path") == PORTFOLIO_FILE:
            return registry.schemas[check["schema"]]
    raise RegistryError(
        "The check registry has no schema check for portfolio.json, so reported "
        "status can't be validated. The scan stops: the scanner needs updating."
    )
