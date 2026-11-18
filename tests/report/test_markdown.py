"""Tests for report/markdown.py: the Markdown report (S3.1.1).

Tests render made-up scan output (`tests/scan_outputs.py`) and check the
text. Reading the scan output file, writing the site and the leak test
through the whole scan are in `test_site.py`. No network, no clock.
"""

from pathlib import Path

import pytest
from scan_outputs import ROWS, output, private_row, table_rows

import report.markdown
from report.markdown import render_report

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


# --- Reading only the scan output ---


def test_report_module_never_imports_the_scan_result():
    # F3.1's Done when: the report comes from the scan output alone.
    text = Path(report.markdown.__file__).read_text(encoding="utf-8")

    assert "scan.result" not in text
    assert "run_scan" not in text


# --- Worst case ---


def test_many_repos_render_in_order():
    rows = [private_row(f"repo-{n:03d}") for n in reversed(range(300))]

    table = table_rows(render_report(output(rows)))

    assert len(table) == 300
    assert table[0][0] == "repo-000"
