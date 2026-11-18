"""Renders the dashboard page, `index.html`, and a page per repo.

Part of `report/`. `site.py` reads `output/scan.json` (the filtered scan
output) and passes it to `render_page`, which works out the counts and
fills the Jinja2 template in `templates/`. It never sees the unfiltered
scan result.

Auto-escaping is on for every value, because a public repo's text could
carry markup (threat model T3), and an undefined value fails the build
instead of showing as blank. The page is our own HTML with its style and
script inline: nothing is loaded from another site. Every state has a text
label, never colour alone (accessibility.md). Built for S4.1.1 (the page),
S4.1.2 (summary tiles, scan time, old-data notice, levels explained) and
S4.1.3 (needs attention first, docs/decisions.md, "'Needs attention
first' ranking": it reads the allow-list fields only, so public and private
repos rank alike), S4.2.1 (the repo table: every repo in attention order,
each cell with a sort value for the page's sorting script) and S4.3.1 (a
page per repo at `repos/<safe name>.html`: public repos in full, with each
check's fix from the scan output's `checks`; private repos with the
allow-list fields only, read by name; could not scan with nothing else)
and S4.4.1 (request links on public pages: a GitHub new-issue link, filled
from a fixed template and URL-encoded, which changes nothing until the
reader submits it).
"""

import math
import re
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from privacy.allow_list import PRIVATE_FIELDS
from report.markdown import COULD_NOT_SCAN, HEALTH_VALUES, MISSING
from scan.levels import LEVEL_NAMES

TEMPLATES = Path(__file__).parent / "templates"
STYLESHEET = TEMPLATES / "style.css"

ENVIRONMENT = Environment(
    loader=FileSystemLoader(TEMPLATES),
    autoescape=True,
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
)

HEALTH_LABELS = {
    "green": "Green",
    "amber": "Amber",
    "red": "Red",
    "not-reported": "Not reported",
}

# One sentence per level, from the Meaning column of the standard's
# spec/compliance.md -> Levels (spec version 2).
LEVEL_SENTENCES = (
    "Nothing the portfolio can read: no valid portfolio.json.",
    "Reports its status in a valid portfolio.json, but hasn't adopted the standard.",
    (
        "On the standard: it reports its status and names the standard's version, "
        "its hosting and its planning docs."
    ),
    (
        "Adopted, on the current major version of the standard, with every "
        "required check that is due passing."
    ),
)

# The tiers of "needs attention first", in order; the first match wins.
# Each is (reason shown on the page, test on the allow-list fields).
ATTENTION_TIERS = (
    ("Could not scan", lambda row: row["scan_status"] == COULD_NOT_SCAN),
    ("Health red", lambda row: row["health"] == "red"),
    ("Has blockers", lambda row: (row["blocker_count"] or 0) > 0),
    ("Health amber", lambda row: row["health"] == "amber"),
    ("Health not reported", lambda row: row["health"] in ("not-reported", None)),
    ("Below Level 2", lambda row: row["level"] is None or row["level"] < 2),
    ("Nothing flagged", lambda row: True),
)
NOT_RANKED = ("done", "archived")
ATTENTION_LIST_LENGTH = 5  # From S4.1.3's criteria.

# The repo table's columns: (title, sorts as a number).
TABLE_COLUMNS = (
    ("Repo", False),
    ("Visibility", False),
    ("Level", True),
    ("Health", True),
    ("Lifecycle", False),
    ("Last activity", False),
    ("Risks", True),
    ("Blockers", True),
    ("Scan", False),
)
# Health sorts by how much attention it needs, red first.
HEALTH_SORT = {"red": 0, "amber": 1, "not-reported": 2, "green": 3}

COMPLIANCE_SPEC_URL = (
    "https://github.com/flegaspi700/pmo-project-standardization"
    "/blob/HEAD/spec/compliance.md"
)


def render_page(output: dict[str, Any]) -> str:
    """The page for one scan output, as HTML. The same output always gives
    the same text."""
    rows = output["rows"]
    scanned = [row for row in rows if row.get("scan_status") != COULD_NOT_SCAN]
    scanned_at = datetime.fromisoformat(output["scanned_at"]).astimezone(UTC)
    paths = repo_paths(rows)
    health = Counter(row.get("health") for row in scanned)
    levels = Counter(row.get("level") for row in scanned)
    return ENVIRONMENT.get_template("index.html").render(
        root="",
        scanned_at=f"{scanned_at:%Y-%m-%d %H:%M}",
        scanned_at_iso=f"{scanned_at:%Y-%m-%dT%H:%M:%SZ}",
        spec_version=output["spec_version"],
        partial=output["status"] == "partial",
        repo_count=len(rows),
        could_not_scan=len(rows) - len(scanned),
        health_tiles=[
            (value, HEALTH_LABELS[value], health[value]) for value in HEALTH_VALUES
        ],
        level_tiles=[
            (f"Level {level} · {name}", levels[level])
            for level, name in reversed(list(enumerate(LEVEL_NAMES)))
        ],
        levels=[
            (f"Level {level} · {name}", sentence)
            for level, (name, sentence) in enumerate(
                zip(LEVEL_NAMES, LEVEL_SENTENCES, strict=True)
            )
        ],
        compliance_spec_url=COMPLIANCE_SPEC_URL,
        attention=[
            (row["name"], reason)
            for row, reason in rank_for_attention(rows)[:ATTENTION_LIST_LENGTH]
        ],
        columns=TABLE_COLUMNS,
        table=[(paths[row["name"]], _table_cells(row)) for row in table_order(rows)],
    )


def table_order(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every row: the ranked ones in "needs attention first" order, then
    the done and archived ones, which aren't ranked, by name."""
    ranked = [row for row, _ in rank_for_attention(rows)]
    not_ranked = [row for row in rows if row.get("lifecycle") in NOT_RANKED]
    return ranked + sorted(
        not_ranked, key=lambda row: (row["name"].lower(), row["name"])
    )


def _table_cells(row: dict[str, Any]) -> list[tuple[str, str | None]]:
    """One repo's cells, in TABLE_COLUMNS order, as (text shown, sort
    value). A missing value shows a dash and has no sort value, so the
    script sorts it last."""
    name = (row["name"], row["name"].lower())
    if row.get("scan_status") == COULD_NOT_SCAN:
        return [name, *[(MISSING, None)] * 7, (COULD_NOT_SCAN, COULD_NOT_SCAN)]
    level = row.get("level")
    health = row.get("health")
    if isinstance(level, int) and 0 <= level < len(LEVEL_NAMES):
        level_cell = (f"{level} · {LEVEL_NAMES[level]}", str(level))
    else:
        level_cell = _plain(level)
    if health in HEALTH_LABELS:
        health_cell = (HEALTH_LABELS[health], str(HEALTH_SORT[health]))
    else:
        health_cell = _plain(health)
    return [
        name,
        _plain(row.get("visibility")),
        level_cell,
        health_cell,
        _plain(row.get("lifecycle")),
        _plain(row.get("last_activity")),
        _plain(row.get("risk_count")),
        _plain(row.get("blocker_count")),
        _plain(row.get("scan_status")),
    ]


def _plain(value: Any) -> tuple[str, str | None]:
    """A value shown as it is and sorted by its text, or a dash if missing."""
    if value is None:
        return (MISSING, None)
    return (str(value), str(value))


def rank_for_attention(
    rows: list[dict[str, Any]],
) -> list[tuple[dict[str, Any], str]]:
    """Rows in "needs attention first" order, each with its tier's reason.

    Order: tier, then lifecycle `active` first, then the most recent
    activity (none last), then the name. Rows whose lifecycle is `done` or
    `archived` are left out. Only the allow-list fields are read, so a
    public row ranks exactly as it would if it were private.
    """
    ranked = []
    for row in rows:
        fields = {name: row.get(name) for name in PRIVATE_FIELDS}
        if fields["lifecycle"] in NOT_RANKED:
            continue
        tier, reason = next(
            (number, reason)
            for number, (reason, matches) in enumerate(ATTENTION_TIERS)
            if matches(fields)
        )
        key = (
            tier,
            fields["lifecycle"] != "active",
            -_day_number(fields["last_activity"]),
            fields["name"].lower(),
            fields["name"],
        )
        ranked.append((key, row, reason))
    ranked.sort(key=lambda item: item[0])
    return [(row, reason) for _, row, reason in ranked]


def _day_number(day: str | None) -> float:
    """A date as a number for sorting, with no date as the oldest."""
    return date.fromisoformat(day).toordinal() if day else -math.inf


# Request links (S4.4.1): (link text, issue title, issue body). Fixed text
# only, so nothing from a repo's own content goes into the issue.
STATUS_REQUEST = (
    "Request a status update",
    "Status update requested by the portfolio dashboard",
    (
        "The portfolio dashboard shows this repo's health as not reported, or its "
        "report as out of date.\n\n"
        "Please update `portfolio.json`: run `/report` in this repo, or edit the "
        "file by hand and set `updated` to today.\n\n"
        "Opened from a request link on the portfolio dashboard."
    ),
)
ADOPTION_REQUEST = (
    "Request standard adoption",
    "Adopt the project standard",
    (
        "The portfolio dashboard shows this repo below Level 2 (Adopted) of "
        "pmo-project-standardization.\n\n"
        "To adopt it, run `/new-project` and choose the option for an existing "
        "repo. To report status only for now (Level 1), add a `portfolio.json`.\n\n"
        f"What each level needs: {COMPLIANCE_SPEC_URL}\n\n"
        "Opened from a request link on the portfolio dashboard."
    ),
)


def repo_paths(rows: list[dict[str, Any]]) -> dict[str, str]:
    """Each repo's page path, `repos/<slug>.html`, by name. The slug is the
    name in lower case with anything but a-z, 0-9, `_` and `-` turned into
    `-`, so a name can't reach outside `repos/`. Names that clean to the
    same slug get `-2`, `-3` and so on, in name order."""
    paths: dict[str, str] = {}
    taken: set[str] = set()
    for name in sorted({row["name"] for row in rows}, key=lambda n: (n.lower(), n)):
        slug = re.sub(r"[^a-z0-9_-]", "-", name.lower()) or "repo"
        candidate, number = slug, 1
        while candidate in taken:
            number += 1
            candidate = f"{slug}-{number}"
        taken.add(candidate)
        paths[name] = f"repos/{candidate}.html"
    return paths


def render_repo_page(row: dict[str, Any], output: dict[str, Any]) -> str:
    """One repo's page, as HTML: in full for a public row, the allow-list
    fields only for a private one, and only its name for a row that could
    not be scanned."""
    scanned_at = datetime.fromisoformat(output["scanned_at"]).astimezone(UTC)
    context: dict[str, Any] = {
        "root": "../",
        "name": row["name"],
        "scanned_at": f"{scanned_at:%Y-%m-%d %H:%M}",
        "scanned_at_iso": f"{scanned_at:%Y-%m-%dT%H:%M:%SZ}",
    }
    if row.get("scan_status") == COULD_NOT_SCAN:
        context["kind"] = "failed"
    elif row.get("visibility") == "public":
        context.update(_public_details(row, output.get("checks", [])))
        context["requests"] = _request_links(row, output.get("owner"))
    else:
        # Read by name from the allow-list, so nothing else can show.
        fields = {name: row.get(name) for name in PRIVATE_FIELDS}
        context.update(kind="private", status=_status(fields))
    return ENVIRONMENT.get_template("repo.html").render(**context)


def _status(fields: dict[str, Any]) -> list[tuple[str, str]]:
    """The allow-list fields as (label, text), for every kind of page."""
    return [
        ("Visibility", _text(fields.get("visibility"))),
        ("Lifecycle", _text(fields.get("lifecycle"))),
        ("Health", _table_cells_text(fields)[3]),
        ("Level", _table_cells_text(fields)[2]),
        ("Last activity", _text(fields.get("last_activity"))),
        ("Risks", _text(fields.get("risk_count"))),
        ("Blockers", _text(fields.get("blocker_count"))),
        ("Scan", _text(fields.get("scan_status"))),
    ]


def _table_cells_text(fields: dict[str, Any]) -> list[str]:
    return [text for text, _ in _table_cells(fields)]


def _public_details(
    row: dict[str, Any], checks: list[dict[str, Any]]
) -> dict[str, Any]:
    """Everything a public repo's page shows."""
    status = _status(row)
    status.insert(4, ("Standard version", _text(row.get("standard_version"))))
    return {
        "kind": "public",
        "description": row.get("description"),
        "status": status,
        "facts": [
            ("Language", _text(row.get("language"))),
            ("Created", _date(row.get("created_at"))),
            ("Last push", _date(row.get("pushed_at"))),
            ("Default branch", _text(row.get("default_branch"))),
            ("Open issues", _text(row.get("open_issues"))),
            ("Open pull requests", _text(row.get("open_prs"))),
        ],
        "reported": _reported(row.get("reported")),
        "checks": _check_rows(row.get("checks") or {}, checks),
        "warnings": [_warning_text(warning) for warning in row.get("warnings") or []],
    }


def _request_links(row: dict[str, Any], owner: str | None) -> list[tuple[str, str]]:
    """A public repo's request links, as (text, URL): a status update when
    its health isn't reported or its report is stale (S1, S2), and adoption
    when it is below Level 2. None without an owner to address them to."""
    if not owner:
        return []
    warning_ids = {warning.get("id") for warning in row.get("warnings") or []}
    wanted = []
    if row.get("health") in ("not-reported", None) or warning_ids & {"S1", "S2"}:
        wanted.append(STATUS_REQUEST)
    if row.get("level") is not None and row["level"] < 2:
        wanted.append(ADOPTION_REQUEST)
    base = f"https://github.com/{quote(owner, safe='')}/{quote(row['name'], safe='')}"
    return [
        (
            text,
            f"{base}/issues/new?"
            + urlencode({"title": title, "body": body}, quote_via=quote),
        )
        for text, title, body in wanted
    ]


def _reported(reported: dict[str, Any] | None) -> dict[str, Any] | None:
    """A valid portfolio.json as the page shows it, or None."""
    if not reported:
        return None
    return {
        "fields": [
            ("Summary", _text(reported.get("summary"))),
            ("Health reason", _text(reported.get("health_reason"))),
            ("Next milestone", _milestone(reported.get("next_milestone"))),
            ("Updated", _text(reported.get("updated"))),
        ],
        "risks": [
            _joined(risk["title"], risk.get("severity"), risk.get("mitigation"))
            for risk in reported.get("risks") or []
        ],
        "blockers": [
            _joined(
                blocker["title"],
                f"since {blocker['since']}" if blocker.get("since") else None,
                f"needs: {blocker['needs']}" if blocker.get("needs") else None,
            )
            for blocker in reported.get("blockers") or []
        ],
        "callouts": list(reported.get("callouts") or []),
    }


def _check_rows(
    results: dict[str, bool | None], checks: list[dict[str, Any]]
) -> list[tuple[str, str, str, str]]:
    """(ID, title, result, fix) for each check in registry order; the fix
    only for a failure."""
    rows = []
    for check in checks:
        if check["id"] not in results:
            continue
        passed = results[check["id"]]
        result = {True: "Pass", False: "Fail", None: "Not applicable"}[passed]
        fix = (check.get("fix") or "") if passed is False else ""
        rows.append((check["id"], check.get("title") or "", result, fix))
    return rows


WARNING_TEXT = {
    "S1": "S1 Stale report: portfolio.json is more than 30 days old while the "
    "repo had pushes in the last 30 days.",
    "S2": "S2 Health never reported: still not reported 14 days after the repo "
    "was created or adopted the standard.",
}


def _warning_text(warning: dict[str, Any]) -> str:
    """A scan warning in words (spec/compliance.md, Warnings worked out by
    the scanner)."""
    if warning.get("id") == "S3":
        return (
            f"S3 Required change due soon: {warning.get('check_id')} is required "
            f"from {warning.get('required_from')}."
        )
    return WARNING_TEXT.get(warning.get("id"), str(warning.get("id")))


def _milestone(milestone: dict[str, Any] | None) -> str:
    """The next milestone as "name, date"; either part may be missing."""
    if not milestone:
        return MISSING
    return ", ".join(
        str(part) for part in (milestone.get("name"), milestone.get("date")) if part
    )


def _joined(*parts: str | None) -> str:
    return " — ".join(part for part in parts if part)


def _date(value: str | None) -> str:
    """The date part of an ISO date and time, or a dash."""
    return value[:10] if value else MISSING


def _text(value: Any) -> str:
    return MISSING if value is None else str(value)
