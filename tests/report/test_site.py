"""Tests for report/site.py and report/page.py: building the site (S4.1.1).

The site is built from the scan output file alone: the page
(`index.html`) and the Markdown report (`report.md`), both in
`output/site/`. Tests write made-up scan output (`tests/scan_outputs.py`)
to a temporary folder, or run the whole scan, filter and write on the fake
GitHub with canary values, then build and check the files. Moved here from
`test_markdown.py` with S4.1.1: reading the scan output file, the missing
file, the report's leak test and `python -m report`. No network, no clock.
"""

import logging
import os
import subprocess
import sys
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path

from canaries import CANARIES, PRIVATE_REPO
from fake_github import OWNER, FakeGitHub
from scan_outputs import ROWS, output, private_row, table_rows, write_scan_file

import report.page
import report.site
from privacy.output import write_output
from report.markdown import render_report
from report.page import ENVIRONMENT, render_page
from report.site import build_site
from scan.result import run_scan

NOW = datetime(2026, 12, 1, 6, 0, tzinfo=UTC)
ROOT = Path(__file__).resolve().parents[2]

# NFR7's page weight.
MAX_SITE_BYTES = 500 * 1024

# Elements that make a browser fetch something, and the attribute naming it.
RESOURCE_ATTRIBUTES = {
    "script": "src",
    "link": "href",
    "img": "src",
    "iframe": "src",
    "frame": "src",
    "source": "src",
    "audio": "src",
    "video": "src",
    "track": "src",
    "embed": "src",
    "object": "data",
    "input": "src",
}


class ResourceFinder(HTMLParser):
    """Collects every URL the page would fetch: element sources, and
    `url(...)` or `@import` in styles."""

    def __init__(self):
        super().__init__()
        self.urls = []
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        name = RESOURCE_ATTRIBUTES.get(tag)
        if name and attrs.get(name):
            self.urls.append(attrs[name])
        if tag == "link":
            self.urls.append(f"<link rel={attrs.get('rel')}>")
        if "url(" in (attrs.get("style") or ""):
            self.urls.append(attrs["style"])
        self.in_style = tag == "style"

    def handle_endtag(self, tag):
        self.in_style = False

    def handle_data(self, data):
        if self.in_style and ("url(" in data or "@import" in data):
            self.urls.append(data)


def resources(html):
    finder = ResourceFinder()
    finder.feed(html)
    return finder.urls


def build(tmp_path, scan_output, name="site"):
    """Write `scan_output` as the scan file and build the site from it."""
    scan_file = write_scan_file(tmp_path / "scan.json", scan_output)
    site = tmp_path / name
    assert build_site(scan_file, site) == 0
    return site


def files(site):
    """Every file in the built site, by path relative to it, as bytes."""
    return {
        path.relative_to(site).as_posix(): path.read_bytes()
        for path in sorted(site.rglob("*"))
        if path.is_file()
    }


# --- Built from the scan output file alone ---


def test_build_writes_the_page_and_the_report_from_the_scan_output(tmp_path):
    site = build(tmp_path, output(ROWS))

    assert sorted(files(site)) == ["index.html", "report.md"]
    page = (site / "index.html").read_bytes()
    report_md = (site / "report.md").read_bytes()
    assert page.decode("utf-8") == render_page(output(ROWS))
    assert report_md.decode("utf-8") == render_report(output(ROWS))
    assert not page.startswith(b"\xef\xbb\xbf")
    assert not report_md.startswith(b"\xef\xbb\xbf")


def test_page_links_to_the_markdown_report(tmp_path):
    page = (build(tmp_path, output(ROWS)) / "index.html").read_text(encoding="utf-8")

    assert 'href="report.md"' in page


def test_page_shows_the_scan_time():
    assert "2026-12-01 06:00 UTC" in render_page(output(ROWS))


def test_auto_escaping_is_on():
    assert ENVIRONMENT.autoescape is True


def test_values_from_the_scan_output_are_escaped():
    scan_output = {**output(ROWS), "spec_version": "<script>alert(1)</script>"}

    page = render_page(scan_output)

    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page


def test_site_modules_never_import_the_scan_result():
    for module in (report.page, report.site):
        text = Path(module.__file__).read_text(encoding="utf-8")
        assert "scan.result" not in text, module.__name__
        assert "run_scan" not in text, module.__name__


# --- No third-party code, and light ---


def test_page_loads_nothing_from_another_site(tmp_path):
    page = (build(tmp_path, output(ROWS)) / "index.html").read_text(encoding="utf-8")

    external = [
        url
        for url in resources(page)
        if "//" in url or url.startswith("<link") or "url(" in url or "@import" in url
    ]
    assert external == []


def test_the_resource_check_finds_an_external_script():
    # Guards the check above: it would catch what it is looking for.
    page = (
        '<script src="https://cdn.example/x.js"></script><link rel=stylesheet href=a>'
    )

    assert resources(page) == ["https://cdn.example/x.js", "a", "<link rel=stylesheet>"]


def test_site_for_many_repos_stays_under_500_kb(tmp_path):
    rows = [
        private_row(f"a-fairly-long-repository-name-{n:03d}", health="amber")
        for n in range(300)
    ]

    site = build(tmp_path, output(rows))

    total = sum(len(content) for content in files(site).values())
    assert total < MAX_SITE_BYTES


# --- Same input, same files ---


def test_building_twice_gives_identical_files(tmp_path):
    first = build(tmp_path, output(ROWS), "first")
    second = build(tmp_path, output(ROWS), "second")

    assert files(first) == files(second)


# --- No scan output ---


def test_missing_scan_output_stops_with_a_clear_message(tmp_path, caplog):
    with caplog.at_level(logging.INFO):
        code = build_site(tmp_path / "missing.json", tmp_path / "site")

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

    build_site(scan_file, tmp_path / "output" / "site")

    text = (tmp_path / "output" / "site" / "report.md").read_text(encoding="utf-8")
    assert [c for c in CANARIES.values() if c in text] == []
    assert [row[0] for row in table_rows(text)] == ["private-repo", "public-repo"]


# --- Command line ---


def run_report(cwd):
    return subprocess.run(
        [sys.executable, "-m", "report"],
        check=False,
        cwd=cwd,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
        capture_output=True,
        text=True,
    )


def test_python_m_report_builds_the_site_from_output_scan_json(tmp_path):
    write_scan_file(tmp_path / "output" / "scan.json", output(ROWS))

    done = run_report(tmp_path)

    assert done.returncode == 0
    assert (tmp_path / "output" / "site" / "index.html").exists()
    assert (tmp_path / "output" / "site" / "report.md").exists()


def test_python_m_report_without_scan_output_exits_non_zero(tmp_path):
    done = run_report(tmp_path)

    assert done.returncode == 1
    assert "No scan output" in done.stderr


# --- F4.1 integration: scan, filter, write, build ---


def test_the_page_built_from_a_real_shaped_scan_ranks_and_counts_every_repo(tmp_path):
    repos = {
        "private-repo": PRIVATE_REPO,
        "public-repo": {"files": PRIVATE_REPO["files"]},
    }
    result = run_scan(FakeGitHub(repos), OWNER, NOW)
    scan_file = tmp_path / "output" / "scan.json"
    write_output(result, scan_file)

    assert build_site(scan_file, tmp_path / "output" / "site") == 0

    page = (tmp_path / "output" / "site" / "index.html").read_text(encoding="utf-8")
    attention = page[page.index('id="attention"') : page.index('id="summary"')]
    assert "private-repo" in attention
    assert "public-repo" in attention
    assert '<span class="count">2</span> <span class="label">Repos</span>' in page
    table = page[page.index('<table id="repos"') : page.index("</table>")]
    assert "private-repo" in table
    assert "public-repo" in table
