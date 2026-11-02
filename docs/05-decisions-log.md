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
