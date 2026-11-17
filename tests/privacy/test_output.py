"""Tests for privacy/output.py: writing only the scan output, and the leak
test (S2.1.2).

The leak test runs the whole scan on a fake GitHub with a private repo
whose every field holds a unique canary value (except its name, which the
allow-list publishes), writes the output, then searches every file in the
output folder for any canary. A second test bypasses the filter and checks
the leak test catches it, so the leak test can't pass by accident.
"""

import builtins
import io
import json
import os
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import pytest
from canaries import CANARIES, PRIVATE_REPO, PUBLIC_REPO
from fake_github import OWNER, FakeGitHub, http_error

import privacy.output
from privacy.output import write_output
from scan.result import ScanResult, run_scan

NOW = datetime(2026, 12, 1, 6, 0, tzinfo=UTC)


def canaries_in(folder: Path) -> list[str]:
    """The leak test: every canary found in any file under `folder`."""
    found = []
    for path in folder.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            found += [canary for canary in CANARIES.values() if canary in text]
    return found


def full_scan(repos):
    return run_scan(FakeGitHub(repos), OWNER, NOW)


@pytest.fixture
def out(tmp_path):
    return tmp_path / "output" / "scan.json"


# --- The leak test ---


def test_no_canary_from_a_private_repo_reaches_any_output_file(out):
    result = full_scan({"private-repo": PRIVATE_REPO, "public-repo": PUBLIC_REPO})

    write_output(result, out)

    assert out.exists()
    assert canaries_in(out.parent.parent) == []
    rows = json.loads(out.read_text(encoding="utf-8"))["rows"]
    assert [row["name"] for row in rows] == ["private-repo", "public-repo"]
    # The private repo was really scanned, canaries and all, not skipped.
    assert rows[0]["scan_status"] == "ok"
    assert rows[0]["health"] == "red"
    assert rows[0]["risk_count"] == 1
    assert rows[0]["level"] == 3


def test_failed_private_repo_leaks_nothing_either(out):
    failing = {**PRIVATE_REPO, "fail": "git/trees"}
    result = full_scan({"private-repo": failing, "public-repo": PUBLIC_REPO})

    write_output(result, out)

    assert canaries_in(out.parent) == []


def test_leak_test_fails_when_the_filter_is_bypassed(out, monkeypatch):
    # Swap the filter for one that lets everything through.
    def no_filter(result):
        return {**asdict(result), "rows": [asdict(row) for row in result.rows]}

    monkeypatch.setattr(privacy.output, "filter_result", no_filter)
    result = full_scan({"private-repo": PRIVATE_REPO})

    write_output(result, out)

    assert canaries_in(out.parent) != []


# --- What gets written ---


def test_complete_result_is_written_as_json_and_exits_0(out):
    result = full_scan({"public-repo": PUBLIC_REPO})

    code = write_output(result, out)

    written = json.loads(out.read_text(encoding="utf-8"))
    assert code == 0
    assert written["status"] == "complete"
    assert written["scanned_at"] == "2026-12-01T06:00:00+00:00"
    assert written["rows"][0]["last_activity"] == "2026-11-28"


def test_partial_result_is_written_and_exits_non_zero(out):
    result = full_scan({"good": PUBLIC_REPO, "bad": {"fail": "pulls"}})

    code = write_output(result, out)

    assert code != 0
    assert json.loads(out.read_text(encoding="utf-8"))["status"] == "partial"


def test_failed_result_writes_nothing_and_exits_non_zero(out):
    result = run_scan(FakeGitHub({}, fail_listing=http_error(401)), OWNER, NOW)

    code = write_output(result, out)

    assert code != 0
    assert not out.parent.exists()


def test_failed_result_keeps_the_last_good_file(out):
    write_output(full_scan({"public-repo": PUBLIC_REPO}), out)
    last_good = out.read_text(encoding="utf-8")

    write_output(full_scan({}), out)

    assert out.read_text(encoding="utf-8") == last_good


def test_output_file_is_utf8_without_a_bom(out):
    write_output(full_scan({"public-repo": PUBLIC_REPO}), out)

    assert not out.read_bytes().startswith(b"\xef\xbb\xbf")


def test_a_failed_write_leaves_the_last_good_file_whole(out, monkeypatch):
    write_output(full_scan({"public-repo": PUBLIC_REPO}), out)
    last_good = out.read_text(encoding="utf-8")

    def broken_replace(source, target):
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", broken_replace)
    with pytest.raises(OSError):
        write_output(full_scan({"other": PUBLIC_REPO}), out)

    assert out.read_text(encoding="utf-8") == last_good
    assert [p.name for p in out.parent.iterdir()] == ["scan.json"]


def test_only_the_scan_output_file_is_written(out):
    write_output(full_scan({"private-repo": PRIVATE_REPO}), out)

    assert [p.name for p in out.parent.iterdir()] == ["scan.json"]


# --- Unfiltered data is never written ---


def test_the_scan_itself_never_opens_a_file(monkeypatch):
    def no_files(*args, **kwargs):
        raise AssertionError("the scan opened a file")

    monkeypatch.setattr(builtins, "open", no_files)
    monkeypatch.setattr(io, "open", no_files)
    monkeypatch.setattr(Path, "write_text", no_files)
    monkeypatch.setattr(Path, "write_bytes", no_files)

    result = full_scan({"private-repo": PRIVATE_REPO, "public-repo": PUBLIC_REPO})

    assert isinstance(result, ScanResult)


def test_write_output_takes_the_scan_result_not_a_prefiltered_dict(out):
    # The filter runs inside write_output, so there is no way to hand it
    # unfiltered data in another shape.
    with pytest.raises(AttributeError):
        write_output({"rows": [{"description": "x"}]}, out)


# --- Worst case ---


def test_sixty_repos_half_private_leak_nothing(out):
    repos = {f"repo-{n:02d}": PRIVATE_REPO for n in range(30)}
    repos.update({f"open-{n:02d}": PUBLIC_REPO for n in range(30)})

    write_output(full_scan(repos), out)

    assert canaries_in(out.parent) == []
    assert len(json.loads(out.read_text(encoding="utf-8"))["rows"]) == 60


def test_a_value_json_cannot_hold_is_refused_not_written_as_text():
    # Only dates and times are converted; anything else is a bug upstream.
    with pytest.raises(TypeError, match="set"):
        privacy.output._json_value({1, 2})
