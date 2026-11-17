"""Reads the files the check registry names from one repo.

Part of `scan/`. For each repo with readable facts, the scan calls
`read_files` with the same fetch function, the repo's default branch (from
`scan/facts.py`) and the check registry (`scan/checks.py`), and passes the
result to `evaluate_checks`. It makes as few requests as possible (NFR1):
one request for the repo's whole file tree, then one per file whose
content a check actually reads. A path missing from the tree is a missing
file. A path that only `exists` checks name, or a file over 1 MB, is
present with content None (not read); the checks treat that as unverified
(docs/decisions.md, "Unreadable files don't pass content checks").

An API error, rate limit or a tree GitHub cut short gives a `FailedRead`
for the repo, so no file is ever wrongly counted as missing. Built for
S1.2.4.
"""

import base64
import logging
from urllib.error import HTTPError
from urllib.parse import quote

from scan.checks import Registry
from scan.facts import FailedRead, failed_read
from scan.repos import Fetch

logger = logging.getLogger(__name__)

# Files over this aren't downloaded. Matches the 1 MB cap S1.3.1 puts on
# portfolio.json; every file a check names is far smaller in practice.
MAX_FILE_BYTES = 1024 * 1024

# GitHub's answer for the tree of a repo with no commits.
EMPTY_REPO_STATUS = 409

CONTENT_KINDS = {"contains", "absent", "schema"}


def read_files(
    fetch: Fetch,
    owner: str,
    name: str,
    default_branch: str | None,
    registry: Registry,
) -> dict[str, str | None] | FailedRead:
    """Read one repo's named files: path -> text, or None for a file that
    is present but wasn't read. Missing files are left out.

    An empty repo (no default branch, or GitHub says it's empty) has no
    files and isn't an error.
    """
    if default_branch is None:
        return {}

    try:
        tree = fetch(
            f"/repos/{owner}/{name}/git/trees/{quote(default_branch, safe='')}"
            "?recursive=1"
        )
    except HTTPError as error:
        if error.code == EMPTY_REPO_STATUS:
            return {}
        return failed_read(name, error, "files")
    except OSError as error:
        return failed_read(name, error, "files")

    if tree.get("truncated"):
        # GitHub cut the tree short (over ~100k entries): files it left
        # out would count as missing, so report the repo as failed.
        logger.warning("Could not read a repo's files: file tree too large")
        return FailedRead(name=name, reason="file tree too large")

    blobs = {entry["path"]: entry for entry in tree["tree"] if entry["type"] == "blob"}
    named, content_needed = _named_paths(registry)

    files: dict[str, str | None] = {}
    for path in sorted(named & blobs.keys()):
        blob = blobs[path]
        if path not in content_needed or blob["size"] > MAX_FILE_BYTES:
            files[path] = None
            continue
        try:
            body = fetch(f"/repos/{owner}/{name}/git/blobs/{blob['sha']}")
        except OSError as error:
            return failed_read(name, error, "files")
        files[path] = _decode(body["content"])

    logger.debug(
        "Read a repo's files: %d named present, %d read",
        len(files),
        sum(text is not None for text in files.values()),
    )
    return files


def _named_paths(registry: Registry) -> tuple[set[str], set[str]]:
    """Every path the checks and their `applies_if` name, and the subset
    whose content some check reads (everything but `exists` paths)."""
    named: set[str] = set()
    content_needed: set[str] = set()
    for check in registry.checks:
        paths = check.get("paths") or [check["path"]]
        named.update(paths)
        if check["kind"] in CONTENT_KINDS:
            content_needed.update(paths)
        condition = check.get("applies_if")
        if condition:
            named.add(condition["path"])
            content_needed.add(condition["path"])
    return named, content_needed


def _decode(content: str) -> str:
    """Decode a blob's base64 content as UTF-8 text, dropping a BOM.

    Bytes that aren't UTF-8 become U+FFFD instead of stopping the scan:
    the checks look for ASCII patterns, so a stray byte can't make one
    pass that shouldn't.
    """
    return base64.b64decode(content).decode("utf-8-sig", errors="replace")
