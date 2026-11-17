"""Tests for scan/files.py: reading the files the check registry names
from one repo (S1.2.4).

All data is made up. A fake fetch function serves a canned file tree and
blobs, or raises the errors urllib raises, so no test touches the network.
Every request is recorded, because the point of the reader is to make as
few as possible (NFR1).
"""

import base64
import logging
from email.message import Message
from urllib.error import HTTPError, URLError

import pytest

from scan.checks import Registry
from scan.facts import FailedRead
from scan.files import MAX_FILE_BYTES, read_files

OWNER = "owner"
NAME = "secret-repo"

REGISTRY = Registry(
    levels={},
    checks=[
        {"id": "CT", "kind": "contains", "path": "AGENTS.md", "pattern": "x"},
        {"id": "SC", "kind": "schema", "path": "portfolio.json", "schema": "s"},
        {"id": "EX", "kind": "exists", "paths": ["docs/decisions.md", "docs/log.md"]},
        {
            "id": "AB",
            "kind": "absent",
            "paths": ["docs/requirements.md"],
            "pattern": "x",
            "applies_if": {"path": "AGENTS.md", "pattern": "y"},
        },
        {
            "id": "IF",
            "kind": "exists",
            "paths": ["extra.md"],
            "applies_if": {"path": "NOTES.md", "pattern": "y"},
        },
    ],
    schemas={},
)


def tree_path(branch="main"):
    return f"/repos/{OWNER}/{NAME}/git/trees/{branch}?recursive=1"


def blob_path(sha):
    return f"/repos/{OWNER}/{NAME}/git/blobs/{sha}"


def fake_repo(files, truncated=False, branch="main", sizes=None):
    """A fetch function for a repo holding `files` (path -> text), plus a
    file no check names. `sizes` overrides a file's size in the tree."""
    files = {**files, "src/unrelated.py": "print('hi')\n"}
    sizes = sizes or {}
    tree = [{"path": "docs", "type": "tree", "sha": "t-docs"}]
    blobs = {}
    for number, (path, text) in enumerate(files.items()):
        sha = f"sha{number}"
        data = text.encode("utf-8")
        tree.append(
            {
                "path": path,
                "type": "blob",
                "sha": sha,
                "size": sizes.get(path, len(data)),
            }
        )
        blobs[blob_path(sha)] = {
            "encoding": "base64",
            # GitHub wraps base64 at 60 characters.
            "content": "\n".join(
                base64.b64encode(data).decode()[i : i + 60]
                for i in range(0, max(len(data), 1) * 2, 60)
            ),
        }

    def fetch(path):
        fetch.requested.append(path)
        if path == tree_path(branch):
            return {"sha": "root", "tree": tree, "truncated": truncated}
        if path in blobs:
            return blobs[path]
        raise AssertionError(f"unexpected path {path}")

    fetch.requested = []
    return fetch


def http_error(code):
    return HTTPError("url", code, "error", Message(), None)


def raising(error):
    def fetch(path):
        fetch.requested.append(path)
        raise error

    fetch.requested = []
    return fetch


# --- Only the named files, with one tree request ---


def test_reads_named_files_with_one_tree_request():
    fetch = fake_repo(
        {
            "AGENTS.md": "# Project\n",
            "portfolio.json": '{"schema": 1}',
            "docs/requirements.md": "# Requirements\n",
        }
    )

    files = read_files(fetch, OWNER, NAME, "main", REGISTRY)

    assert files == {
        "AGENTS.md": "# Project\n",
        "portfolio.json": '{"schema": 1}',
        "docs/requirements.md": "# Requirements\n",
    }
    assert fetch.requested[0] == tree_path()
    assert fetch.requested.count(tree_path()) == 1
    assert len(fetch.requested) == 4


def test_files_no_check_names_are_never_fetched():
    fetch = fake_repo({"AGENTS.md": "a"})

    files = read_files(fetch, OWNER, NAME, "main", REGISTRY)

    assert "src/unrelated.py" not in files
    assert len(fetch.requested) == 2


def test_applies_if_paths_are_read():
    fetch = fake_repo({"NOTES.md": "apply"})

    assert read_files(fetch, OWNER, NAME, "main", REGISTRY) == {"NOTES.md": "apply"}


# --- Missing paths ---


def test_path_not_in_the_tree_is_missing_with_no_request():
    fetch = fake_repo({})

    files = read_files(fetch, OWNER, NAME, "main", REGISTRY)

    assert files == {}
    assert fetch.requested == [tree_path()]


def test_directories_in_the_tree_are_not_files():
    registry = Registry(
        levels={}, checks=[{"id": "D", "kind": "exists", "paths": ["docs"]}], schemas={}
    )

    assert read_files(fake_repo({}), OWNER, NAME, "main", registry) == {}


# --- exists-only paths ---


def test_exists_only_path_is_present_from_the_tree_alone():
    fetch = fake_repo({"docs/decisions.md": "# Decisions\n", "extra.md": "x"})

    files = read_files(fetch, OWNER, NAME, "main", REGISTRY)

    assert files == {"docs/decisions.md": None, "extra.md": None}
    assert fetch.requested == [tree_path()]


def test_path_named_by_exists_and_a_content_check_is_read():
    registry = Registry(
        levels={},
        checks=[
            {"id": "EX", "kind": "exists", "paths": ["AGENTS.md"]},
            {"id": "CT", "kind": "contains", "path": "AGENTS.md", "pattern": "x"},
        ],
        schemas={},
    )

    files = read_files(fake_repo({"AGENTS.md": "x"}), OWNER, NAME, "main", registry)

    assert files == {"AGENTS.md": "x"}


# --- Empty repos ---


def test_repo_with_no_default_branch_has_no_files_and_makes_no_request():
    fetch = raising(AssertionError("no request expected"))

    assert read_files(fetch, OWNER, NAME, None, REGISTRY) == {}
    assert fetch.requested == []


def test_repo_github_calls_empty_has_no_files():
    # GitHub answers 409 "Git Repository is empty" for an empty repo's tree.
    fetch = raising(http_error(409))

    assert read_files(fetch, OWNER, NAME, "main", REGISTRY) == {}


# --- Large files ---


def test_file_over_1_mb_is_present_but_unread():
    fetch = fake_repo({"AGENTS.md": "huge"}, sizes={"AGENTS.md": MAX_FILE_BYTES + 1})

    files = read_files(fetch, OWNER, NAME, "main", REGISTRY)

    assert files == {"AGENTS.md": None}
    assert fetch.requested == [tree_path()]


def test_file_of_exactly_1_mb_is_read():
    fetch = fake_repo({"AGENTS.md": "big"}, sizes={"AGENTS.md": MAX_FILE_BYTES})

    assert read_files(fetch, OWNER, NAME, "main", REGISTRY) == {"AGENTS.md": "big"}


def test_1_mb_is_1024_squared_bytes():
    assert MAX_FILE_BYTES == 1024 * 1024


# --- Errors ---


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (http_error(403), "HTTP 403"),
        (http_error(404), "HTTP 404"),
        (http_error(500), "HTTP 500"),
        (URLError("no route"), "network error"),
    ],
)
def test_tree_error_makes_the_repo_a_failed_read(error, reason, caplog):
    with caplog.at_level(logging.DEBUG):
        result = read_files(raising(error), OWNER, NAME, "main", REGISTRY)

    assert result == FailedRead(name=NAME, reason=reason)
    assert NAME not in caplog.text


def test_blob_error_makes_the_repo_a_failed_read():
    good = fake_repo({"AGENTS.md": "a"})

    def fetch(path):
        if "/git/blobs/" in path:
            raise http_error(403)
        return good(path)

    result = read_files(fetch, OWNER, NAME, "main", REGISTRY)

    assert result == FailedRead(name=NAME, reason="HTTP 403")


def test_truncated_tree_makes_the_repo_a_failed_read(caplog):
    fetch = fake_repo({"AGENTS.md": "a"}, truncated=True)

    with caplog.at_level(logging.DEBUG):
        result = read_files(fetch, OWNER, NAME, "main", REGISTRY)

    assert result == FailedRead(name=NAME, reason="file tree too large")
    assert fetch.requested == [tree_path()]
    assert NAME not in caplog.text


# --- Text ---


def test_utf8_bom_is_dropped():
    fetch = fake_repo({"AGENTS.md": "﻿**Standard:** x\n"})

    files = read_files(fetch, OWNER, NAME, "main", REGISTRY)

    assert files == {"AGENTS.md": "**Standard:** x\n"}


def test_text_that_is_not_utf8_does_not_crash():
    fetch = fake_repo({"AGENTS.md": "placeholder"})
    blob = blob_path("sha0")
    good = fetch

    def latin1(path):
        if path == blob:
            good.requested.append(path)
            raw = "café".encode("latin-1")
            return {"encoding": "base64", "content": base64.b64encode(raw).decode()}
        return good(path)

    files = read_files(latin1, OWNER, NAME, "main", REGISTRY)

    assert files["AGENTS.md"].startswith("caf")


def test_branch_name_with_a_slash_is_encoded():
    fetch = fake_repo({"AGENTS.md": "a"}, branch="release%2F2026")

    files = read_files(fetch, OWNER, NAME, "release/2026", REGISTRY)

    assert files == {"AGENTS.md": "a"}


# --- Worst case ---


def test_v1_sized_registry_on_a_large_tree():
    exists_only = [f"docs/{n:02d}-doc.md" for n in range(17)]
    registry = Registry(
        levels={},
        checks=[
            {"id": "C3", "kind": "exists", "paths": exists_only},
            {"id": "CT", "kind": "contains", "path": "AGENTS.md", "pattern": "x"},
        ],
        schemas={},
    )
    repo = {f"src/file{n}.py": "" for n in range(5000)}
    repo.update({path: "# doc\n" for path in exists_only})
    repo["AGENTS.md"] = "x"
    fetch = fake_repo(repo)

    files = read_files(fetch, OWNER, NAME, "main", registry)

    assert len(files) == 18
    assert len(fetch.requested) == 2
