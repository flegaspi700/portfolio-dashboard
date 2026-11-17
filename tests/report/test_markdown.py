"""Tests for report/markdown.py: the Markdown report (S3.1.1).

The report is built from the scan output file alone. Tests write made-up
scan output to a temporary folder, or run the whole scan, filter and write
on the fake GitHub with canary values in a private and a public repo, then
render the report and check it. No network, no clock.
"""

import json
import logging
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from canaries import CANARIES, PRIVATE_REPO
from fake_github import OWNER, FakeGitHub

import report.markdown
from privacy.output import write_output
from report.markdown import render_report, write_report
from scan.result import run_scan

NOW = datetime(2026, 12, 1, 6, 0, tzinfo=UTC)


def private_row(name, **overrides):
    row = {
        "name": name,
        "visibility": "private",
        "lifecycle": "active",
        "health": "green",
        "level": 3,
        "last_activity": "2026-11-28",
        "risk_count": 2,
        "blocker_count": 0,
        "scan_status": "ok",
    }
    row.update(overrides)
    return row


def output(rows, status="complete"):
    return {
        "status": status,
        "scanned_at": "2026-12-01T06:00:00+00:00",
        "spec_version": 2,
        "failure": None,
        "rows": rows,
    }


ROWS = [
    private_row("zeta", level=0, health="not-reported", lifecycle=None),
    private_row("Alpha"),
    {**private_row("beta", visibility="public", level=1, health="amber")},
]


def table_rows(text):
    """The repo table's body rows, as lists of cells."""
    lines = text[text.index("## Repos") :].splitlines()
    # Lines starting "| " are the header and the body; the separator
    # ("|---|") doesn't match, so only the header is skipped.
    rows = [line for line in lines if line.startswith("| ")][1:]
    return [[cell.strip() for cell in line.strip("|").split("|")] for line in rows]


# --- Content ---


def test_report_has_scan_time_spec_version_and_counts():
    text = render_report(output(ROWS))

    assert "2026-12-01 06:00 UTC" in text
    assert "spec version 2" in text
    assert "3 repos" in text
    assert "| 3 Current | 1 |" in text
    assert "| 1 Reporting | 1 |" in text
    assert "| 0 Not on standard | 1 |" in text
    assert "| 2 Adopted | 0 |" in text
    assert "| green | 1 |" in text
    assert "| amber | 1 |" in text
    assert "| not-reported | 1 |" in text
    assert "Could not scan: 0" in text


def test_one_row_per_repo_sorted_by_name_with_the_listed_columns():
    rows = table_rows(render_report(output(ROWS)))

    assert [row[0] for row in rows] == ["Alpha", "beta", "zeta"]
    assert rows[0] == [
        "Alpha",
        "private",
        "3 Current",
        "green",
        "active",
        "2026-11-28",
        "2",
        "0",
        "ok",
    ]


def test_missing_values_show_a_dash_not_a_guess():
    rows = table_rows(render_report(output(ROWS)))

    assert rows[2][4] == "—"


def test_report_has_front_matter_for_the_pages_build():
    assert render_report(output(ROWS)).startswith("---\ntitle: Portfolio report\n---\n")


# --- Partial ---


def test_partial_result_is_flagged_at_the_top_with_could_not_scan_rows():
    rows = [*ROWS, {"name": "broken", "scan_status": "could not scan"}]

    text = render_report(output(rows, status="partial"))

    body = text.split("---\n", 2)[2]
    assert body.lstrip().startswith("# Portfolio report")
    assert "**Partial scan:** 1 of 4 repos could not be scanned." in text
    assert "Could not scan: 1" in text
    broken = next(row for row in table_rows(text) if row[0] == "broken")
    assert broken == ["broken", "—", "—", "—", "—", "—", "—", "—", "could not scan"]


def test_complete_result_has_no_partial_line():
    assert "Partial scan" not in render_report(output(ROWS))


# --- No free text, escaping ---


def test_public_repo_free_text_never_appears():
    public = {
        **private_row("open", visibility="public"),
        "description": "CANARY-description",
        "language": "CANARY-language",
        "reported": {"summary": "CANARY-summary", "callouts": ["CANARY-callout"]},
        "warnings": [{"id": "S1", "check_id": None, "required_from": None}],
        "portfolio_problem": "CANARY-problem",
        "scan_error": "CANARY-error",
    }

    text = render_report(output([public]))

    assert "CANARY" not in text


@pytest.mark.parametrize(
    ("name", "escaped"),
    [
        ("my_repo", r"my\_repo"),
        ("a|b", r"a\|b"),
        ("<script>", "&lt;script&gt;"),
        ("{{ site }}", "&#123;&#123; site &#125;&#125;"),
        ("a*b`c[d]e\\f", r"a\*b\`c\[d\]e\\f"),
        ("x&y", "x&amp;y"),
    ],
)
def test_names_with_markdown_or_html_characters_are_escaped(name, escaped):
    text = render_report(output([private_row(name)]))

    assert f"| {escaped} |" in text
    if name != escaped:
        assert f"| {name} |" not in text


def test_a_value_outside_the_known_set_is_escaped_too():
    text = render_report(output([private_row("a", health="<b>", lifecycle="x|y")]))

    assert "&lt;b&gt;" in text
    assert r"x\|y" in text


# --- Same input, same report ---


def test_same_scan_output_gives_the_same_report():
    assert render_report(output(ROWS)) == render_report(output(list(reversed(ROWS))))


# --- Reading only the scan output file ---


def test_write_report_reads_the_scan_output_file_and_writes_index_md(tmp_path):
    scan_file = tmp_path / "scan.json"
    scan_file.write_text(json.dumps(output(ROWS)), encoding="utf-8")
    site = tmp_path / "site"

    code = write_report(scan_file, site)

    assert code == 0
    written = (site / "index.md").read_bytes()
    assert written.decode("utf-8") == render_report(output(ROWS))
    assert not written.startswith(b"\xef\xbb\xbf")


def test_report_module_never_imports_the_scan_result():
    # F3.1's Done when: the report comes from the scan output alone.
    text = Path(report.markdown.__file__).read_text(encoding="utf-8")

    assert "scan.result" not in text
    assert "run_scan" not in text


def test_missing_scan_output_stops_with_a_clear_message(tmp_path, caplog):
    with caplog.at_level(logging.INFO):
        code = write_report(tmp_path / "missing.json", tmp_path / "site")

    assert code != 0
    assert "scan output" in caplog.text
    assert "main.py" in caplog.text
    assert not (tmp_path / "site").exists()


# --- The leak test, through the whole scan ---


def test_no_canary_reaches_the_report(tmp_path):
    public = {
        "description": CANARIES["description"],
        "files": PRIVATE_REPO["files"],
    }
    repos = {"private-repo": PRIVATE_REPO, "public-repo": public}
    result = run_scan(FakeGitHub(repos), OWNER, NOW)
    scan_file = tmp_path / "output" / "scan.json"
    write_output(result, scan_file)

    write_report(scan_file, tmp_path / "output" / "site")

    text = (tmp_path / "output" / "site" / "index.md").read_text(encoding="utf-8")
    assert [c for c in CANARIES.values() if c in text] == []
    assert [row[0] for row in table_rows(text)] == ["private-repo", "public-repo"]


# --- Worst case ---


def test_many_repos_render_in_order():
    rows = [private_row(f"repo-{n:03d}") for n in reversed(range(300))]

    table = table_rows(render_report(output(rows)))

    assert len(table) == 300
    assert table[0][0] == "repo-000"


# --- Command line ---


def test_python_m_report_renders_from_output_scan_json(tmp_path):
    root = Path(__file__).resolve().parents[2]
    (tmp_path / "output").mkdir()
    (tmp_path / "output" / "scan.json").write_text(
        json.dumps(output(ROWS)), encoding="utf-8"
    )

    done = subprocess.run(
        [sys.executable, "-m", "report"],
        check=False,
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(root)},
        capture_output=True,
        text=True,
    )

    assert done.returncode == 0
    assert (tmp_path / "output" / "site" / "index.md").exists()


def test_python_m_report_without_scan_output_exits_non_zero(tmp_path):
    root = Path(__file__).resolve().parents[2]

    done = subprocess.run(
        [sys.executable, "-m", "report"],
        check=False,
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(root)},
        capture_output=True,
        text=True,
    )

    assert done.returncode == 1
    assert "No scan output" in done.stderr
