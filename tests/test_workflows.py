"""Tests for the GitHub Actions workflows (S3.2.1).

Actions can't run here, so these read the workflow files as text and check
the rules that keep them safe (threat model T2, docs/security.md) and the
shape of the daily publish run. What only a real run can show is in
docs/manual-tests.md. No YAML library: plain text checks are enough for
the few lines that matter.
"""

import re
from pathlib import Path

import pytest

WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"
PUBLISH = WORKFLOWS / "publish.yml"
ALL = sorted(WORKFLOWS.glob("*.yml"))


def text(path=PUBLISH):
    return path.read_text(encoding="utf-8")


def job(name):
    """The text of one job in publish.yml, up to the next job."""
    body = text()
    start = body.index(f"\n  {name}:\n")
    following = re.search(r"\n  [a-z][a-z-]*:\n", body[start + 1 :])
    return body[start : start + 1 + following.start()] if following else body[start:]


# --- Security rules, every workflow ---


@pytest.mark.parametrize("path", ALL, ids=lambda p: p.name)
def test_every_action_is_pinned_to_a_full_commit_sha(path):
    for line in text(path).splitlines():
        if "uses:" in line:
            assert re.search(r"uses: [\w.-]+/[\w./-]+@[0-9a-f]{40} # v\d", line), line


@pytest.mark.parametrize("path", ALL, ids=lambda p: p.name)
def test_no_pull_request_target_trigger(path):
    assert "pull_request_target" not in text(path)


@pytest.mark.parametrize("path", ALL, ids=lambda p: p.name)
def test_workflow_grants_nothing_by_default(path):
    assert "\npermissions: {}\n" in text(path)


def test_every_publish_job_sets_its_own_permissions():
    jobs = re.findall(r"\n  ([a-z][a-z-]*):\n", text().split("\njobs:\n", 1)[1])
    assert jobs
    for name in jobs:
        assert "\n    permissions:" in job(name), name


def test_the_token_reaches_only_the_scan_step():
    body = text()
    assert body.count("secrets.PORTFOLIO_READ_TOKEN") == 1
    step = body[body.index("- name: Scan") : body.index("secrets.PORTFOLIO_READ_TOKEN")]
    assert "\n      - " not in step[1:]  # no other step starts in between


def test_checkout_keeps_no_credentials():
    assert "persist-credentials: false" in job("scan")


# --- The daily run ---


def test_runs_daily_at_06_00_utc_and_by_hand():
    body = text()
    assert 'cron: "0 6 * * *"' in body
    assert "workflow_dispatch:" in body


def test_scan_runs_main_then_the_report():
    scan = job("scan")
    assert scan.index("python main.py") < scan.index("python -m report")
    assert 'python-version: "3.13"' in scan


def test_report_and_build_only_run_when_there_is_scan_output():
    scan = job("scan")
    for step in ("Render the report", "Build the site", "Upload the site"):
        part = scan[scan.index(step) :]
        part = part[: part.find("\n      - ", 1) if "\n      - " in part[1:] else None]
        assert "steps.scan.outputs.has_output == 'true'" in part, step


def test_deploy_only_when_there_is_scan_output_with_pages_permissions():
    deploy = job("deploy")
    assert "needs: scan" in deploy
    assert "if: needs.scan.outputs.has_output == 'true'" in deploy
    assert "pages: write" in deploy
    assert "id-token: write" in deploy
    assert "actions/deploy-pages@" in deploy


def test_run_fails_unless_the_scan_was_complete_and_deployed():
    result = job("result")
    assert "if: always()" in result
    assert "needs: [scan, deploy]" in result
    assert "needs.scan.outputs.exit_code" in result
    assert "needs.deploy.result" in result


def test_only_one_publish_run_at_a_time():
    body = text()
    assert "concurrency:" in body
    assert "cancel-in-progress: false" in body
