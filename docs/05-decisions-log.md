# Decisions log

Running log of design and technology decisions, in ADR-style (Architecture
Decision Record). Add new entries at the top. Copy the template at the
bottom for new entries.

- Log open questions too, as `Proposed` entries with the decision left
  pending and a note on what result will settle it — that way they don't
  get decided silently.
- For significant choices (see `02-architecture.md` → Design options and
  trade-offs), fill in **Options considered** with every serious option,
  not just the winner. Knowing what was rejected and why stops the same
  debate from restarting later.
- Small choices can skip the options table — a one-line Decision and Why
  is enough.
- Never delete or rewrite an accepted entry. If a decision changes, add a
  new entry and mark the old one `Superseded by <new entry>`.

---

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

**Status:** Proposed

**Context:** The vision assumes `check-compliance.ps1` can run in an Action, but
its header says the dashboard runs the same checks over the GitHub API. It also
only checks a schema's top level, while `compliance.md` says "fits the schema",
so a stricter validator could give different levels.

**Decision:** _Pending. Settle in Phase 0 alongside `/stack`, before S1.2.1._

---

## 2026-11-02 — How the output gets published

**Status:** Proposed

**Context:** Output committed to the repo stays in public history, and the
publishing method also affects GitHub's 60-day shutoff of scheduled workflows.

**Decision:** _Pending. Settle at the start of Phase 2._

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

## YYYY-MM-DD — Language and stack

**Status:** Proposed

**Context:** The template doesn't assume a language. The stack is chosen
per project in Phase 0 (see `AGENTS.md` → Choosing the stack).

**Options considered:**

| Option | Pros | Cons | Cost |
|---|---|---|---|
| _<language + key libraries>_ | | | |
| _<alternative>_ | | | |

**Decision:** _Pending — fill in during Phase 0._

**Why:** _What the project needs (from `00-vision.md`) and why this option
fits best._

**Trade-offs accepted:** _What we give up by not choosing the
alternatives._

**Revisit if:** _The condition that would make this worth reconsidering._

---

## YYYY-MM-DD — Formatter, linter and test runner

**Status:** Proposed

**Context:** Tooling needs to be fixed early so AI-generated code stays
consistent between sessions. Follows from the language choice above.

**Decision:** _Pending — fill in during Phase 0._

**Why:** _Fill in once chosen._

---

## Template for new entries

```
## YYYY-MM-DD — <short decision title>

**Status:** Proposed | Accepted | Superseded by <link>

**Context:** What prompted this decision? What constraints or goals
(from 00-vision.md) apply?

**Options considered:**   (skip for small choices)

| Option | Pros | Cons | Cost |
|---|---|---|---|
| <simplest option that could work> | | | <$0 / $X per month / usage-based> |
| <option B> | | | |
| <option C, if any> | | | |

**Decision:** What was decided?

**Why:** Which criteria decided it — e.g. simplicity, effort, performance,
cost, security, ease of changing later.

**Trade-offs accepted:** What we give up with this choice.

**Revisit if:** The condition or measurement that would make this worth
reconsidering (e.g. "capture rate drops below 20 fps").
```
