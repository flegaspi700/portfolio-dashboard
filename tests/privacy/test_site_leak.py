"""The leak test on the built site (S2.2.1).

Runs everything that publishes, the way the daily workflow does: the whole
scan on a fake GitHub, the allow-list filter and write (`privacy/output.py`),
then the site build (`report/site.py`), and searches every file of the built
site, HTML and Markdown alike, for the canary values planted in a private
repo (`tests/canaries.py`). Canaries are letters, digits and dashes, so
HTML escaping and URL encoding leave them as they are and can't hide a hit.

A bypass test proves the leak test can see a leak: a filter that passes
private rows through whole and labelled public, the worst filter bug and
one the page can't guard against, must make it fail. A plain bypass (rows
whole but still labelled private) leaks nothing, because the page reads
private rows by the allow-list too; a test pins that second guard. The
owner chose this reading of the story's second criterion on 2026-11-18.
No network, no clock.
"""

import json
import re
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from canaries import CANARIES, PRIVATE_REPO, PUBLIC_REPO
from fake_github import OWNER, FakeGitHub

import privacy.output
from privacy.output import write_output
from report.site import build_site
from scan.result import run_scan

NOW = datetime(2026, 12, 1, 6, 0, tzinfo=UTC)

# The labels a private repo's page shows, one per allow-list field (the
# name is the page's heading).
PRIVATE_PAGE_LABELS = [
    "Visibility",
    "Lifecycle",
    "Health",
    "Level",
    "Last activity",
    "Risks",
    "Blockers",
    "Scan",
]
# Sections only a public repo's page has.
PUBLIC_ONLY_SECTIONS = ("Facts", "Reported status", "Compliance checks", "Requests")


def canaries_in(folder: Path) -> list[str]:
    """The leak test: every canary found in any file under `folder`."""
    found = []
    for path in sorted(folder.rglob("*")):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            found += [canary for canary in CANARIES.values() if canary in text]
    return found


def publish(tmp_path: Path, repos: dict) -> Path:
    """Scan, filter, write and build the site, as the workflow does; return
    the built site's folder."""
    result = run_scan(FakeGitHub(repos), OWNER, NOW)
    scan_file = tmp_path / "output" / "scan.json"
    write_output(result, scan_file)
    site = tmp_path / "output" / "site"
    assert build_site(scan_file, site) == 0
    return site


REPOS = {
    "private-repo": PRIVATE_REPO,
    "broken-private": {**PRIVATE_REPO, "fail": "git/trees"},
    "public-repo": PUBLIC_REPO,
}


# --- No canary anywhere in the built site ---


def test_no_canary_reaches_any_file_of_the_built_site(tmp_path):
    site = publish(tmp_path, REPOS)

    built = sorted(
        p.relative_to(site).as_posix() for p in site.rglob("*") if p.is_file()
    )
    assert built == [
        "index.html",
        "report.md",
        "repos/broken-private.html",
        "repos/private-repo.html",
        "repos/public-repo.html",
        "style.css",
    ]
    assert canaries_in(site) == []
    # The private repo was really scanned and published, canaries and all.
    page = (site / "repos" / "private-repo.html").read_text(encoding="utf-8")
    assert "Red" in page
    assert "3 · Current" in page


def test_sixty_repos_half_private_leak_nothing_into_the_site(tmp_path):
    repos = {f"repo-{n:02d}": PRIVATE_REPO for n in range(30)}
    repos.update({f"open-{n:02d}": PUBLIC_REPO for n in range(30)})

    site = publish(tmp_path, repos)

    assert canaries_in(site) == []
    assert len(list((site / "repos").glob("*.html"))) == 60


# --- The leak test can see a leak ---


def test_leak_test_fails_when_the_filter_passes_private_rows_as_public(
    tmp_path, monkeypatch
):
    def everything_public(result):
        output = asdict(result)
        output["rows"] = [
            {**asdict(row), "visibility": "public"} for row in result.rows
        ]
        return output

    monkeypatch.setattr(privacy.output, "filter_result", everything_public)

    site = publish(tmp_path, {"private-repo": PRIVATE_REPO})

    assert canaries_in(site) != []


def test_a_plain_filter_bypass_is_still_stopped_by_the_page(tmp_path, monkeypatch):
    # Rows whole but still labelled private: the page reads them by the
    # allow-list, a second guard behind the filter.
    def no_filter(result):
        return {**asdict(result), "rows": [asdict(row) for row in result.rows]}

    monkeypatch.setattr(privacy.output, "filter_result", no_filter)

    site = publish(tmp_path, {"private-repo": PRIVATE_REPO})

    assert canaries_in(site) == []


# --- Private pages and rows hold the allow-list only ---


def test_a_private_repos_page_holds_the_allow_list_fields_only(tmp_path):
    site = publish(tmp_path, REPOS)

    page = (site / "repos" / "private-repo.html").read_text(encoding="utf-8")

    assert re.findall(r"<dt>([^<]*)</dt>", page) == PRIVATE_PAGE_LABELS
    headings = re.findall(r"<h2[^>]*>([^<]*)</h2>", page)
    assert headings == ["Status"]
    assert not set(headings) & set(PUBLIC_ONLY_SECTIONS)
    assert "issues/new" not in page


def test_a_private_repo_that_could_not_scan_shows_its_name_only(tmp_path):
    site = publish(tmp_path, REPOS)

    page = (site / "repos" / "broken-private.html").read_text(encoding="utf-8")

    assert "<dl" not in page
    assert "<h2" not in page
    assert "could not be scanned" in page


def test_private_rows_in_the_page_and_report_hold_the_allow_list_only(tmp_path):
    site = publish(tmp_path, REPOS)
    scan = json.loads((tmp_path / "output" / "scan.json").read_text(encoding="utf-8"))
    private = next(row for row in scan["rows"] if row["name"] == "private-repo")

    index = (site / "index.html").read_text(encoding="utf-8")
    table = index[index.index('<table id="repos"') : index.index("</table>")]
    rows = re.findall(r"<tr>(.*?)</tr>", table.split("<tbody>", 1)[1], re.DOTALL)
    row = next(row for row in rows if 'href="repos/private-repo.html"' in row)
    cells = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row, re.DOTALL)
    texts = [re.sub(r"<[^>]+>", "", cell) for cell in cells]
    assert texts == [
        "private-repo",
        "private",
        "3 · Current",
        "Red",
        private["lifecycle"] or "—",
        private["last_activity"],
        str(private["risk_count"]),
        str(private["blocker_count"]),
        "ok",
    ]

    report_md = (site / "report.md").read_text(encoding="utf-8")
    line = next(
        line for line in report_md.splitlines() if line.startswith("| private-repo |")
    )
    assert len(line.strip("|").split("|")) == 9
