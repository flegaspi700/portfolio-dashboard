# Decisions

Design and technology decisions for this project, newest first. When to log
one, and the entry format: the standard's `decisions.md`. Never rewrite an
accepted entry: add a new one and mark the old one `Superseded by`.

Entries before 2026-11-13 were written under the v1 template and refer to
its numbered docs. Where they live now: `00`, `01`, `04` → `requirements.md`;
`02`, `03`, `06` (layout, naming), `11` → `architecture.md`; `05` →
`decisions.md`; `10` → `session-log.md`; `14`, `15` → `security.md`,
`accessibility.md`; `06`, `07`, `13` (the rules) → the standard's
`coding.md`, `testing.md`, `git.md`.

---

## 2026-11-14 — Read the check registry from the standard's default branch

**Status:** Accepted

**Context:** The scan reads `spec/compliance-checks.json` and
`spec/portfolio.schema.json` from `pmo-project-standardization` at run time
(S1.2.1), never a local copy. That repo is public, publishes versions as git
tags (no GitHub releases), and its `main` was the same as `v2.1.0` on
2026-11-14.

**Options considered:**

| Option | Pros | Cons | Cost |
|---|---|---|---|
| A. The default branch (`main`) | One request per file; always the newest rules; no version parsing | A change merged before it's tagged applies at once | $0 |
| B. The newest version tag | Only released rules count | Needs semver parsing of the tag list, and one more request | $0 |
| C. A version pinned in this repo | Fully predictable | Has to be bumped after every standard release, or "current" goes stale | $0 |

**Decision:** A.

**Why:** The simplest option, and the standard's own process puts each
registry change and its CHANGELOG entry in one PR, so `main` holds rules
the owner has already accepted.

**Trade-offs accepted:** Levels can shift the day a registry change merges,
before its tag exists.

**Revisit if:** the standard starts merging work in progress to `main`.

---

## 2026-11-13 — Go: build the dashboard

**Status:** Accepted

**Context:** Phase 0 asked whether the page would look worthwhile on real
data. On 2026-11-02 the answer was no for now: 13 repos were in scope, 2
were at Level 3, 11 at Level 0, and 1 reported real health, so most rows
of the mock were empty. The recommendation was to move the rollout ahead
of Phase 1. Since then the standard went to v2.0.0 (a five-file footprint
per repo) and was rolled out.

Counts on 2026-11-13, with the scope rule in this log (2026-11-02, "Repo
scope"):

| | Repos |
|---|---|
| In scope | 17 (new repos were pushed this month) |
| Level 3 (Current) | 5 |
| Level 1 (Reporting) | 3 |
| Level 0 (Not on standard) | 9 |
| Reporting real health | 0 (all eight reporting repos are `not-reported` until their first `/report`) |

**Options considered:**

| Option | Pros | Cons | Cost |
|---|---|---|---|
| Go: start Phase 1 now | The success bar of at least 4 repos at Level 2 or higher is met (5); 8 of 17 rows have real data | Health is still empty until the owners run `/report` | $0 |
| Wait until health is reported everywhere | The first real page looks fuller | Delays the build for data Phase 1 doesn't need: the scan works on any data | $0 |

**Decision:** Go. Finish the rest of Phase 0 (token test, threat model,
NFRs, environment), then start Phase 1.

**Why:** The reason for the earlier no-go, too few repos on the standard,
is gone. Health data can come in during Phase 1, since the scan doesn't
depend on it.

**Trade-offs accepted:** The first page will show health as not reported
for most repos until their owners run `/report`.

**Revisit if:** the first real scan output looks empty or misleading.

**Open question:** the vision's success criteria, Phase 1's exit criteria
and F1.1's "Done when" say "13 repos", a snapshot of the scope rule on
2026-11-02. The rule now gives 17. Changing those criteria is the owner's
call; "all in-scope repos" would stop them going stale.

## 2026-11-02 — Repo scope: spec exclusions plus a fixed cut-off

**Status:** Accepted

**Context:** The vision said "non-fork, pushed in 2026". `spec/compliance.md`
says every repo except archived, forks and repos tagged `portfolio-exclude`.
They disagree, and "in 2026" needed a fixed meaning before January. Today this
account has 54 repos, 10 of them forks, and none tagged.

**Options considered:**

| Option | Pros | Cons | Cost |
|---|---|---|---|
| A. Spec exclusions plus "pushed since 2026-01-01" | 13 repos with no tagging; still works in 2027; quiet repos stay listed and look stale, which is honest | One rule on top of the spec | $0 |
| B. Spec exclusions plus "pushed in the last 12 months" | Quiet repos drop off by themselves | 14 repos today; totals change with no action from the owner | $0 |
| C. Spec rule only | Follows the standard exactly and is explicit | Tag about 31 old repos by hand; new experiments appear by default | $0 |

**Decision:** A. The scan cut-off is a single constant, 2026-01-01. Excluded
repos don't count in totals.

**Why:** Simplest rule that gives the intended set and doesn't go stale.

**Trade-offs accepted:** The in-scope count is 13 (the original 12 plus this
dashboard), and repos never age out unless archived or tagged.

**Revisit if:** too many quiet repos pile up and dilute the page.

---

## 2026-11-02 — Private repos: real name plus signals

**Status:** Accepted

**Context:** G4 says publishing never exposes details of private repos. The
page is public, so this list is what the leak test enforces.

**Options considered:**

| Option | Pros | Cons | Cost |
|---|---|---|---|
| A. Real name plus signals | Reads as a real portfolio; no free text gets through | Owner opens the repo for the detail behind a red health | $0 |
| B. Masked name plus signals | Strongest protection | Looks less real to a reviewer; numbering must stay stable between runs | $0 |
| C. Real name plus owner-written summary | Most useful to a reviewer | Free text gets through, so it relies on owners writing safe summaries | $0 |

**Decision:** A. Private rows carry only: name, visibility, lifecycle, health,
compliance level, last activity date, risk count, blocker count, scan status.
Anything not on the list is dropped. No free text, links or budget.

**Why:** An allow-list with no free text can be tested and can't leak by
accident, and the page still looks like a real portfolio.

**Trade-offs accepted:** Private rows show the level but not which checks
failed, so the page says there's a problem but not what it is (a limit on G2).

**Revisit if:** the owner keeps needing private detail that the page can't give.

---

## 2026-11-02 — Scan failure: publish partial and flag it

**Status:** Accepted

**Context:** There is no database, so there is no earlier data to fall back on
row by row.

**Options considered:**

| Option | Pros | Cons | Cost |
|---|---|---|---|
| A. Publish partial and flag it | Stays fresh; the failure is visible and alerts | A row can look broken to a reviewer that day | $0 |
| B. All or nothing | The page never looks broken | One flaky repo freezes everything; only the last-updated time shows it | $0 |

**Decision:** A. A failed repo shows as "could not scan" with no guessed data,
the others publish, and the run is marked failed so an alert fires. A bad
token, total failure or zero in-scope repos publishes nothing, so the last good
page stays up.

**Why:** G3 wants the view current, and a visible gap is more honest than a
frozen page.

**Trade-offs accepted:** A reviewer may occasionally see a "could not scan" row.

**Revisit if:** partial runs become common.

---

## 2026-11-02 — Rollout tracked as plan tasks

**Status:** Accepted

**Decision:** Moving repos onto the standard is tracked as non-story tasks in
`04-project-plan.md`, not as stories.

**Why:** The work is done by hand in other repos and has no code here, but this
plan needs to show what launch is waiting on.

---

## 2026-11-02 — S2 adoption date: first commit touching portfolio.json

**Status:** Accepted

**Decision:** For spec warning S2, a repo's adoption date is the date of the
first commit that touched `portfolio.json`.

**Why:** The standard records no adoption date, and using the created date would
flag a newly adopted old repo immediately.

---

## 2026-11-02 — Reuse or reimplement the compliance checks

**Status:** Accepted

**Context:** The vision assumed `check-compliance.ps1` could run in an Action, but
it reads a local folder, so every repo would have to be cloned. It also only
checks a schema's top level, while `compliance.md` says "fits the schema".

**Options considered:**

| Option | Pros | Cons | Cost |
|---|---|---|---|
| A. Reimplement the check kinds in Python, with full schema validation | Follows the written spec; no cloning; nested mistakes can't reach the page | A repo can pass locally yet fail C4 on the page until the script is fixed | $0 |
| B. Reimplement in Python, validating the top level only | Matches the script exactly | Nested mistakes, such as a malformed `progress` block, pass C4 and can reach the page | $0 |
| C. Run the script itself in the Action | No second copy of the logic | Clones private repos onto the runner; needs PowerShell in the stack | $0 |

**Decision:** A. The scan reads the check registry at run time and applies the
kinds in Python over the GitHub API. On nested schema errors, the spec wins over
the script.

**Why:** The written spec is the source of truth, and the script's own comment
describes its top-level check as a limit of Windows PowerShell.

**Trade-offs accepted:** The scan and `check-compliance.ps1` can disagree on C4
until the script is fixed in `pmo-project-standardization`. S1.2.1 and F1.2 state
this exception.

**Revisit if:** the script gains full validation, which removes the exception.

---

## 2026-11-02 — How the output gets published

**Status:** Proposed

**Context:** Output committed to the repo stays in public history, and the
publishing method also affects GitHub's 60-day shutoff of scheduled workflows.

**Decision:** _Pending. Settle at the start of Phase 2._

**Constraint (threat model T6, added 2026-11-13):** only filtered scan
output may ever be committed or deployed. Deploying a Pages artifact is
preferred over committing output, because anything committed stays in the
public history.

---

## 2026-11-02 — "Needs attention first" ranking

**Status:** Proposed

**Context:** The page must name which project needs attention first, using only
reported and scanned data, never a guessed judgment.

**Decision:** _Pending. Settle at the start of Phase 3._

---

## 2026-11-02 — Public repo, so GitHub Pages works on a free plan

**Status:** Accepted

**Decision:** The repo `flegaspi700/portfolio-dashboard` is public.

**Why:** Free GitHub accounts can only publish Pages from a public repo, and
a public repo also suits the showcase goal. Consequence: code, history and
Action logs are visible to anyone, so the scan must not log private repo
details.

---

## 2026-11-02 — Product direction: static dashboard on real data

**Status:** Accepted

**Context:** Brainstorm from `pmo-project-standardization`'s
`ideas/portfolio-reporting.md`. Main job: both a showcase and a working tool,
showcase first. Scope: the 12 non-fork repos pushed to in 2026. Public page,
with limited detail for the 5 private repos. Rebuilt daily.

**Options considered:**

| Option | Pros | Cons | Cost |
|---|---|---|---|
| A. Markdown report (`PORTFOLIO.md`, regenerated daily) | Nothing to host; the scan is reusable later | Doesn't look like an executive tool; no drill-down | $0 |
| B. Static dashboard on real data (GitHub Pages: summary tiles, sortable table, per-repo pages, "Request update" links) | Fits all the answers above; free hosting; real governance behind it | Needs a token, and a filter to keep private data off the page | $0 |
| C. Static dashboard on demo data | Looks great from day one; no token or privacy risk | Proves little to a hiring manager and isn't useful to the owner | $0 |
| D. Issues and Projects board (one issue per compliance gap) | Gaps become tracked work where the work happens | Noisy; puts issues in public repos; not readable at a glance | $0 |

**Decision:** B, hosted on GitHub Pages, built in stages: the scan and its
JSON output first, then the Markdown report (which is A), then the page. Move
more repos onto the standard along the way.

**Why:** It is the only direction that serves both the showcase and real use.

**Trade-offs accepted:** More work than C, and a token to look after.

**Riskiest assumption:** the page looks worthwhile with real data while few
repos are on the standard. **Cheap test:** run `check-compliance.ps1` on all
12 repos and hand-build one static HTML mock from the results before building
further.

**Revisit if:** the mock isn't good enough to send a hiring manager (move more
repos onto the standard first), or hosting on Pages stops fitting.

---

## 2026-11-02 — Language and stack

**Status:** Accepted

**Context:** The template doesn't assume a language. The scan is a batch job and
the page is generated HTML with a little vanilla JS, so nothing needs a browser
framework. Free tools only, and G4 favours the least code handling private data.

**Options considered:**

| Option | Pros | Cons | Cost |
|---|---|---|---|
| A. Python 3.13: `urllib`, `jsonschema`, `Jinja2` from Phase 3 | Few dependencies, no build step; `Jinja2` can auto-escape untrusted text | Must reimplement the 4 check kinds | $0 |
| B. TypeScript on Node 24: `fetch`, `ajv`, `eta` | Same language as the page's JS; `ajv` is a strong validator | Build step and many more dev dependencies, for a page that barely needs JS | $0 |
| C. PowerShell 7: reuse `check-compliance.ps1` | No second copy of the check logic; levels match the local tool exactly | Reads a local folder, so private repos get cloned onto the runner; `pwsh` isn't installed here; weak for HTML generation | $0 |

**Decision:** A.

**Why:** Simplest fit that meets the constraints, with the least code and
dependencies around private data.

**Trade-offs accepted:** The 4 check kinds exist in Python as well as PowerShell.
The rules themselves stay in the standard's check registry, read at run time.

**Revisit if:** the page grows real client-side needs that vanilla JS can't meet.

---

## 2026-11-02 — Formatter, linter and test runner

**Status:** Accepted

**Context:** Tooling needs to be fixed early so AI-generated code stays
consistent between sessions. Follows from the language choice above.

**Decision:** `ruff` for formatting and linting, `pytest` with `pytest-cov` for
tests and coverage, `pip-audit` for dependency audits. `mypy` is deferred.

**Why:** `ruff` covers both formatting and linting with one tool, and these are
the standard choices for Python.

---
