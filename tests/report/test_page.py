"""Tests for report/page.py: what the dashboard page shows (E4).

Each test renders made-up scan output (`tests/scan_outputs.py`) and reads
the HTML. Building and writing the site is in `test_site.py`. The stale
notice's script needs a browser, so its behaviour is a manual test
(`docs/manual-tests.md`, F4.1); here the page is checked to carry it. No
network, no clock.
"""

import html
import re
from urllib.parse import parse_qs, urlsplit

import pytest
from scan_outputs import ROWS, output, private_row, public_row

from report.page import (
    rank_for_attention,
    render_page,
    render_repo_page,
    repo_paths,
)

COULD_NOT = {"name": "broken", "scan_status": "could not scan"}


def tiles(page):
    """Every tile on the page, as label -> count."""
    found = re.findall(
        r'<li class="tile[^"]*"><span class="count">(\d+)</span> '
        r'<span class="label">([^<]*)</span></li>',
        page,
    )
    return {label: int(count) for count, label in found}


# --- S4.1.2: summary tiles ---


def test_tiles_count_repos_health_levels_and_could_not_scan():
    page = render_page(output([*ROWS, COULD_NOT], status="partial"))

    assert tiles(page) == {
        "Repos": 4,
        "Could not scan": 1,
        "Green": 1,
        "Amber": 1,
        "Red": 0,
        "Not reported": 1,
        "Level 3 · Current": 1,
        "Level 2 · Adopted": 0,
        "Level 1 · Reporting": 1,
        "Level 0 · Not on standard": 1,
    }


def test_no_repos_gives_zero_tiles():
    counts = tiles(render_page(output([])))

    assert counts["Repos"] == 0
    assert set(counts.values()) == {0}
    assert len(counts) == 10


def test_many_repos_are_all_counted():
    rows = [private_row(f"r{n}", health="red", level=n % 4) for n in range(300)]

    counts = tiles(render_page(output(rows)))

    assert counts["Repos"] == 300
    assert counts["Red"] == 300
    assert counts["Level 0 · Not on standard"] == 75


# --- S4.1.2: scan time and partial flag ---


def test_page_shows_the_scan_time_in_utc():
    page = render_page(output(ROWS, scanned_at="2026-12-01T01:00:00-05:00"))

    assert '<time id="scanned-at" datetime="2026-12-01T06:00:00Z">' in page
    assert "2026-12-01 06:00 UTC</time>" in page


def test_partial_scan_is_flagged_above_the_summary():
    page = render_page(output([*ROWS, COULD_NOT], status="partial"))

    flag = page.index("Partial scan: 1 of 4 repos could not be scanned.")
    assert flag < page.index('id="summary"')


def test_complete_scan_has_no_partial_flag():
    assert "Partial scan" not in render_page(output(ROWS))


# --- S4.1.2: old-data notice ---


def test_old_data_notice_is_hidden_until_the_script_shows_it():
    page = render_page(output(ROWS))

    notice = re.search(r'<p id="stale-notice"[^>]*>(.*?)</p>', page, re.DOTALL)
    assert notice
    assert " hidden" in notice.group(0)[: notice.group(0).index(">")]
    assert "may be out of date" in notice.group(1)


def test_script_compares_the_scan_time_with_the_readers_clock_at_36_hours():
    page = render_page(output(ROWS))

    script = re.search(r"<script>(.*?)</script>", page, re.DOTALL).group(1)
    assert "36 * 60 * 60 * 1000" in script
    assert "Date.now()" in script
    assert 'getElementById("scanned-at")' in script
    assert 'getElementById("stale-notice")' in script


def test_without_scripts_the_scan_time_is_still_shown():
    page = render_page(output(ROWS))

    # What a reader sees with scripts off: no script, no hidden elements.
    visible = re.sub(r"<script>.*?</script>", "", page, flags=re.DOTALL)
    visible = re.sub(r"<(\w+)[^>]* hidden[^>]*>.*?</\1>", "", visible, flags=re.DOTALL)
    assert "2026-12-01 06:00 UTC" in visible


# --- S4.1.2: the levels explained ---


def test_the_four_levels_are_explained_in_a_sentence_each():
    page = render_page(output(ROWS))

    terms = re.findall(r"<dt>(.*?)</dt>\s*<dd>(.*?)</dd>", page, re.DOTALL)
    assert [term for term, _ in terms] == [
        "Level 0 · Not on standard",
        "Level 1 · Reporting",
        "Level 2 · Adopted",
        "Level 3 · Current",
    ]
    for _, sentence in terms:
        assert sentence.strip().endswith(".")
        assert sentence.count(". ") == 0  # one sentence


def test_levels_link_to_the_standards_compliance_spec():
    page = render_page(output(ROWS))

    assert (
        'href="https://github.com/flegaspi700/pmo-project-standardization'
        '/blob/HEAD/spec/compliance.md"'
    ) in page


# --- S4.1.2: never colour alone ---


def test_every_tile_has_a_text_label():
    page = render_page(output(ROWS))

    tile_tags = re.findall(r'<li class="tile[^"]*">.*?</li>', page, re.DOTALL)
    assert len(tile_tags) == len(tiles(page)) == 10
    assert all(label.strip() for label in tiles(page))


def test_health_tiles_carry_their_value_as_text_not_only_a_colour_class():
    page = render_page(output(ROWS))

    for value, label in (
        ("green", "Green"),
        ("amber", "Amber"),
        ("red", "Red"),
        ("not-reported", "Not reported"),
    ):
        assert re.search(
            rf'<li class="tile health-{value}"><span class="count">\d+</span> '
            rf'<span class="label">{label}</span></li>',
            page,
        ), value


# --- S4.1.3: needs attention first ---

TIER_ROWS = [
    private_row("rest"),
    private_row("low-level", level=1),
    private_row("unreported", health="not-reported"),
    private_row("amber", health="amber"),
    private_row("blocked", blocker_count=2),
    private_row("red", health="red"),
    {"name": "broken", "scan_status": "could not scan"},
]


def ranked_names(rows):
    return [row["name"] for row, _ in rank_for_attention(rows)]


def attention_items(page):
    """The "Needs attention first" list, as (name, reason) pairs."""
    section = page[page.index('id="attention"') : page.index('id="summary"')]
    return re.findall(
        r'<li><span class="name">([^<]*)</span> — <span class="reason">([^<]*)'
        r"</span></li>",
        section,
    )


def test_repos_are_ranked_by_tier():
    ranked = rank_for_attention(list(reversed(TIER_ROWS)))

    assert [(row["name"], reason) for row, reason in ranked] == [
        ("broken", "Could not scan"),
        ("red", "Health red"),
        ("blocked", "Has blockers"),
        ("amber", "Health amber"),
        ("unreported", "Health not reported"),
        ("low-level", "Below Level 2"),
        ("rest", "Nothing flagged"),
    ]


def test_the_first_matching_tier_wins():
    row = private_row("both", health="amber", blocker_count=1, level=0)

    assert rank_for_attention([row])[0][1] == "Has blockers"


def test_missing_health_or_level_counts_as_not_reported_and_below_level_2():
    assert rank_for_attention([private_row("a", health=None)])[0][1] == (
        "Health not reported"
    )
    assert rank_for_attention([private_row("b", level=None)])[0][1] == "Below Level 2"


def test_ties_go_to_active_then_recent_activity_then_name():
    rows = [
        private_row("b-old", health="red", last_activity="2026-10-01"),
        private_row("paused-new", health="red", lifecycle="paused"),
        private_row("a-old", health="red", last_activity="2026-10-01"),
        private_row("new", health="red", last_activity="2026-11-30"),
        private_row("no-date", health="red", last_activity=None),
    ]

    assert ranked_names(rows) == ["new", "a-old", "b-old", "no-date", "paused-new"]


def test_done_and_archived_repos_are_not_ranked():
    rows = [
        private_row("done", lifecycle="done", health="red"),
        private_row("archived", lifecycle="archived", health="red"),
        private_row("kept", lifecycle="paused"),
    ]

    assert ranked_names(rows) == ["kept"]


def test_page_lists_the_top_5_with_their_reason_private_and_public_alike():
    rows = [*TIER_ROWS, private_row("open-red", visibility="public", health="red")]

    items = attention_items(render_page(output(rows, status="partial")))

    assert items == [
        ("broken", "Could not scan"),
        ("open-red", "Health red"),
        ("red", "Health red"),
        ("blocked", "Has blockers"),
        ("amber", "Health amber"),
    ]


def test_needs_attention_comes_before_the_summary():
    page = render_page(output(ROWS))

    assert page.index('id="attention"') < page.index('id="summary"')
    assert "Needs attention first</h2>" in page


def test_no_rankable_repos_says_so():
    page = render_page(output([private_row("done", lifecycle="done")]))

    assert attention_items(page) == []
    assert "No repos to rank." in page


def test_many_repos_still_list_only_5():
    rows = [private_row(f"r{n:03d}", health="red") for n in range(300)]

    items = attention_items(render_page(output(rows)))

    assert [name for name, _ in items] == ["r000", "r001", "r002", "r003", "r004"]


def test_a_public_row_ranks_exactly_as_it_would_if_private():
    private = private_row("open", health="green", level=3, blocker_count=0)
    # Fields only a public row carries, all pointing at trouble.
    public = {
        **private,
        "visibility": "public",
        "warnings": [{"id": "S1", "check_id": None, "required_from": None}],
        "reported": {"health": "red", "blockers": [{"description": "x"}]},
        "checks": {"C4": False},
        "description": "red",
    }
    others = [private_row("amber", health="amber"), private_row("rest")]

    def names_and_reasons(rows):
        return [(row["name"], reason) for row, reason in rank_for_attention(rows)]

    assert names_and_reasons([public, *others]) == names_and_reasons([private, *others])
    assert ("open", "Nothing flagged") in names_and_reasons([public, *others])


# --- S4.2.1: the repo table ---

COLUMN_TITLES = [
    "Repo",
    "Visibility",
    "Level",
    "Health",
    "Lifecycle",
    "Last activity",
    "Risks",
    "Blockers",
    "Scan",
]


def repo_table(page):
    """The repo table's HTML."""
    return page[page.index('<table id="repos"') : page.index("</table>") + 8]


def body_rows(page):
    """The table body's rows, as lists of cell texts (links unwrapped)."""
    body = repo_table(page).split("<tbody>", 1)[1]
    rows = re.findall(r"<tr>(.*?)</tr>", body, re.DOTALL)
    return [
        [
            re.sub(r"<[^>]+>", "", cell)
            for cell in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row)
        ]
        for row in rows
    ]


def test_table_lists_every_repo_in_attention_order_then_done_and_archived():
    rows = [
        *TIER_ROWS,
        private_row("finished", lifecycle="done", health="red"),
        private_row("Archived", lifecycle="archived"),
    ]

    table = body_rows(render_page(output(rows, status="partial")))

    assert [row[0] for row in table] == [
        "broken",
        "red",
        "blocked",
        "amber",
        "unreported",
        "low-level",
        "rest",
        "Archived",
        "finished",
    ]


def test_table_row_has_the_listed_columns_with_text_labels():
    row = private_row("Alpha", health="not-reported", level=2, risk_count=None)

    table = body_rows(render_page(output([row])))

    assert table == [
        [
            "Alpha",
            "private",
            "2 · Adopted",
            "Not reported",
            "active",
            "2026-11-28",
            "—",
            "0",
            "ok",
        ]
    ]


def test_a_repo_that_could_not_scan_shows_dashes_and_says_so():
    table = body_rows(render_page(output([COULD_NOT], status="partial")))

    assert table == [["broken", *["—"] * 7, "could not scan"]]


def test_table_has_a_caption_and_real_column_headers():
    table = repo_table(render_page(output(ROWS)))

    assert "<caption>" in table
    head = table[table.index("<thead>") : table.index("</thead>")]
    titles = re.findall(r'<th scope="col"[^>]*>([^<]*)</th>', head)
    assert titles == COLUMN_TITLES


def test_row_headers_name_each_repo():
    table = repo_table(render_page(output(ROWS)))

    names = [
        re.sub(r"<[^>]+>", "", cell)
        for cell in re.findall(r'<th scope="row"[^>]*>(.*?)</th>', table)
    ]
    assert names == ["beta", "zeta", "Alpha"]  # amber, not reported, the rest


def test_cells_carry_a_sort_value_and_missing_values_carry_none():
    row = private_row("Alpha", health="red", level=0, risk_count=None)

    table = repo_table(render_page(output([row])))

    body = table.split("<tbody>", 1)[1]
    values = re.findall(r'<t[hd][^>]*?(?: data-value="([^"]*)")?>', body)
    # Repo, visibility, level, health (red sorts first), lifecycle,
    # last activity, risks (missing), blockers, scan.
    assert values == [
        "alpha",
        "private",
        "0",
        "0",
        "active",
        "2026-11-28",
        "",
        "0",
        "ok",
    ]


def test_number_columns_are_marked_for_number_sorting():
    table = repo_table(render_page(output(ROWS)))

    numbers = re.findall(r'<th scope="col" data-type="number">([^<]*)</th>', table)
    assert numbers == ["Level", "Health", "Risks", "Blockers"]


def test_script_makes_each_header_a_button_and_sets_aria_sort():
    page = render_page(output(ROWS))

    script = page[page.rindex("<script>") :]
    assert 'getElementById("repos")' in script
    assert 'createElement("button")' in script
    assert '"aria-sort"' in script
    assert '"ascending"' in script
    assert '"descending"' in script


def test_names_in_the_table_are_escaped():
    page = render_page(output([private_row("<img src=x onerror=alert(1)>")]))

    assert "<img src=x" not in page
    assert "&lt;img src=x onerror=alert(1)&gt;" in repo_table(page)


# --- S4.3.1: a page per repo ---


def visible_text(page):
    """The page's text with tags, the style and the scripts removed."""
    page = re.sub(r"<(style|script)>.*?</\1>", "", page, flags=re.DOTALL)
    return " ".join(re.sub(r"<[^>]+>", " ", page).split())


def test_each_repo_gets_a_path_made_of_safe_characters():
    rows = [
        private_row("My.Repo"),
        private_row("my_repo-2"),
        private_row("../../etc/passwd"),
        private_row("<script>"),
        private_row(""),
    ]

    paths = repo_paths(rows)

    assert paths == {
        "My.Repo": "repos/my-repo.html",
        "my_repo-2": "repos/my_repo-2.html",
        "../../etc/passwd": "repos/------etc-passwd.html",
        "<script>": "repos/-script-.html",
        "": "repos/repo.html",
    }
    for path in paths.values():
        assert re.fullmatch(r"repos/[a-z0-9_-]+\.html", path)


def test_names_that_clash_after_cleaning_get_distinct_paths():
    paths = repo_paths([private_row("a.b"), private_row("A-B"), private_row("a_b")])

    assert sorted(paths.values()) == [
        "repos/a-b-2.html",
        "repos/a-b.html",
        "repos/a_b.html",
    ]
    assert paths["A-B"] == "repos/a-b.html"  # by name order: "A-B" before "a.b"


def test_each_table_row_links_to_its_repo_page():
    rows = [private_row("Alpha"), public_row("beta")]

    table = repo_table(render_page(output(rows)))

    assert '<a href="repos/alpha.html">Alpha</a>' in table
    assert '<a href="repos/beta.html">beta</a>' in table


def test_public_repo_page_shows_facts_level_checks_warnings_and_status():
    row = public_row("beta")

    text = visible_text(render_repo_page(row, output([row])))

    for expected in (
        "beta",
        "A made-up public project",
        "Python",
        "2025-03-01",
        "2026-11-28",
        "main",
        "Open issues 3",
        "Open pull requests 1",
        "2 · Adopted",
        "v2.0.0",
        "Amber",
        "Tracks the made-up things.",
        "Behind on the made-up milestone.",
        "Made-up risk",
        "high",
        "Watch it.",
        "Made-up blocker",
        "A yes.",
        "A made-up call-out.",
        "Made-up release",
        "2026-12-20",
        "2026-11-20",
    ):
        assert expected in text, expected


def test_public_repo_page_lists_each_check_with_the_fix_for_failures():
    row = public_row("beta")

    page = render_repo_page(row, output([row]))

    checks = re.findall(
        r"<tr><th scope=\"row\">([^<]*)</th><td>([^<]*)</td><td>([^<]*)</td>"
        r"<td>([^<]*)</td></tr>",
        page,
    )
    assert checks == [
        ("C8", "Names the standard", "Pass", ""),
        ("C2", "Has the Hosting line", "Pass", ""),
        ("C4", "portfolio.json fits", "Pass", ""),
        ("C10", "Names v2", "Fail", "Move to v2."),
        ("C5", "UTF-8 rule", "Not applicable", ""),
    ]


def test_public_repo_page_explains_each_scan_warning():
    row = public_row(
        "beta",
        warnings=[
            {"id": "S1", "check_id": None, "required_from": None},
            {"id": "S2", "check_id": None, "required_from": None},
            {"id": "S3", "check_id": "C10", "required_from": "2026-12-13"},
        ],
    )

    text = visible_text(render_repo_page(row, output([row])))

    assert "S1 Stale report" in text
    assert "S2 Health never reported" in text
    assert "S3 Required change due soon: C10 is required from 2026-12-13" in text


def test_public_repo_without_a_valid_report_says_so():
    row = public_row("beta", reported=None, has_portfolio=False, warnings=[])

    text = visible_text(render_repo_page(row, output([row])))

    assert "No valid portfolio.json, so no reported status." in text
    assert "No scan warnings." in text


def test_private_repo_page_shows_the_allow_list_fields_only():
    # Extra fields as if the filter had been bypassed: none may show.
    row = {
        **private_row("secret", risk_count=4, blocker_count=1),
        "description": "CANARY-description",
        "reported": {"summary": "CANARY-summary"},
        "checks": {"CANARY-check": False},
        "warnings": [{"id": "CANARY-warning"}],
        "language": "CANARY-language",
    }

    page = render_repo_page(row, output([row]))

    assert "CANARY" not in page
    labels = re.findall(r"<dt>([^<]*)</dt>", page)
    assert labels == [
        "Visibility",
        "Lifecycle",
        "Health",
        "Level",
        "Last activity",
        "Risks",
        "Blockers",
        "Scan",
    ]
    text = visible_text(page)
    assert "secret" in text
    assert "Private repo: only these signals are published." in text


def test_a_repo_that_could_not_scan_has_a_page_that_says_so_and_nothing_else():
    row = {
        "name": "broken",
        "visibility": "public",
        "scan_status": "could not scan",
        "scan_error": "HTTP 500",
    }

    page = render_repo_page(row, output([row], status="partial"))

    assert "This repo could not be scanned in the latest run" in page
    assert "HTTP 500" not in page
    assert "public" not in visible_text(page)
    assert "<dl" not in page


def test_markup_in_public_text_is_escaped():
    row = public_row(
        "beta",
        description="<script>alert('d')</script>",
        reported={
            **public_row("beta")["reported"],
            "summary": "<img src=x onerror=alert(1)>",
            "callouts": ["<b>bold</b>"],
        },
    )

    page = render_repo_page(row, output([row]))

    assert "<script>alert" not in page
    assert "<img src=x" not in page
    assert "<b>bold</b>" not in page
    assert "&lt;img src=x onerror=alert(1)&gt;" in page
    assert "&lt;b&gt;bold&lt;/b&gt;" in page


def test_repo_page_links_back_to_the_dashboard():
    row = private_row("Alpha")

    assert 'href="../index.html"' in render_repo_page(row, output([row]))


def test_missing_level_and_health_show_a_dash_in_the_table():
    row = private_row("Alpha", level=None, health=None)

    assert body_rows(render_page(output([row])))[0][2:4] == ["—", "—"]


def test_public_repo_with_no_next_milestone_shows_a_dash():
    row = public_row("beta")
    row["reported"] = {**row["reported"], "next_milestone": None}

    assert "Next milestone — " in visible_text(render_repo_page(row, output([row])))


# --- S4.4.1: request links ---


def request_links(page):
    """The page's request links, as (text, URL) with the URL unescaped."""
    return [
        (text, html.unescape(href))
        for href, text in re.findall(
            r'<a class="request" href="([^"]*)">([^<]*)</a>', page
        )
    ]


def link_parts(url):
    parts = urlsplit(url)
    return parts, parse_qs(parts.query)


@pytest.mark.parametrize(
    "overrides",
    [
        {"health": "not-reported", "warnings": []},
        {"health": None, "reported": None, "warnings": []},
        {"warnings": [{"id": "S1", "check_id": None, "required_from": None}]},
        {"warnings": [{"id": "S2", "check_id": None, "required_from": None}]},
    ],
    ids=["not-reported", "no-report", "S1-stale", "S2-never-reported"],
)
def test_public_repo_needing_a_status_update_gets_that_link(overrides):
    row = public_row("beta", **overrides)

    links = request_links(render_repo_page(row, output([row])))

    assert [text for text, _ in links] == ["Request a status update"]


def test_public_repo_below_level_2_gets_an_adoption_link():
    row = public_row("beta", level=1, warnings=[])

    links = request_links(render_repo_page(row, output([row])))

    assert [text for text, _ in links] == ["Request standard adoption"]


def test_a_repo_can_need_both_requests():
    row = public_row("beta", level=0, health="not-reported", warnings=[])

    links = request_links(render_repo_page(row, output([row])))

    assert [text for text, _ in links] == [
        "Request a status update",
        "Request standard adoption",
    ]


def test_a_reporting_adopted_repo_gets_no_links():
    row = public_row("beta", warnings=[])  # amber, Level 2, no S1 or S2

    assert request_links(render_repo_page(row, output([row]))) == []


def test_a_link_opens_githubs_new_issue_form_with_a_fixed_title_and_body():
    row = public_row("beta", level=1, health="not-reported", warnings=[])

    links = dict(request_links(render_repo_page(row, output([row]))))

    for text in ("Request a status update", "Request standard adoption"):
        parts, query = link_parts(links[text])
        assert (parts.scheme, parts.netloc) == ("https", "github.com")
        assert parts.path == "/someone/beta/issues/new"
        assert set(query) == {"title", "body"}
        assert query["title"][0]
        assert query["body"][0]
    _, status = link_parts(links["Request a status update"])
    assert "/report" in status["body"][0]
    _, adoption = link_parts(links["Request standard adoption"])
    assert "/new-project" in adoption["body"][0]


def test_the_title_and_body_are_the_same_whatever_the_repo_says():
    # Fixed template: nothing from the repo's own text goes into the issue.
    plain = public_row("beta", level=1, warnings=[])
    loud = public_row(
        "beta",
        level=1,
        warnings=[],
        description="CANARY & <x>",
        reported={**plain["reported"], "summary": "CANARY summary"},
    )

    def query(row):
        links = request_links(render_repo_page(row, output([row])))
        return link_parts(links[0][1])[1]

    assert query(plain) == query(loud)
    assert "CANARY" not in str(query(loud))


def test_link_parts_are_url_encoded():
    row = public_row("beta", level=1, warnings=[])

    page = render_repo_page(row, output([row]))

    href = re.search(r'<a class="request" href="([^"]*)"', page).group(1)
    url = html.unescape(href)
    query = url.split("?", 1)[1]
    assert " " not in query
    assert "\n" not in query
    assert "%20" in query or "+" in query


def test_a_private_repo_has_no_request_links():
    row = private_row("secret", level=0, health="not-reported")

    page = render_repo_page(row, output([row]))

    assert request_links(page) == []
    assert "issues/new" not in page


def test_a_repo_that_could_not_scan_has_no_request_links():
    row = {"name": "broken", "visibility": "public", "scan_status": "could not scan"}

    assert "issues/new" not in render_repo_page(row, output([row], status="partial"))


def test_no_owner_in_the_scan_output_means_no_links():
    row = public_row("beta", level=0, health="not-reported", warnings=[])
    scan_output = {**output([row]), "owner": None}

    assert request_links(render_repo_page(row, scan_output)) == []
