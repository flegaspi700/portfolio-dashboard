# Requirements

What the project must do, broken down as **Epic → Feature → Story**. The
project plan (`04-project-plan.md`) decides *when* each piece gets built;
this doc decides *what* gets built and how you know it's done.

- **Epic:** a large capability or outcome. Too big to build in one go.
  Usually spans several phases.
- **Feature:** a piece of an epic that is useful on its own. Fits in one
  phase.
- **Story:** the smallest unit of work: one prompt-sized change to one
  component, with acceptance criteria that can be tested. If a story needs
  more than ~a day or touches several components, split it.

## How to work with this doc

- Every epic serves at least one goal from `00-vision.md`. An epic that
  serves none is out of scope until the vision changes.
- A small project can have a single epic with a few features, and stories
  for the current phase only — don't pad it to look complete.
- Break requirements down top-down when starting the project: write the
  epics first, then features, then stories only for the current and next
  phase. Stories for later phases get written when you reach them.
- IDs are stable — never renumber. Removed items get status `Dropped`, not
  deleted.
- Every story's acceptance criteria become its tests (see
  `07-testing-checklist.md`).
- Reference story IDs in the project plan, commit messages and prompts
  (e.g. "Implement S1.2.3").
- A story is done when it meets its acceptance criteria *and* the
  Definition of Done below. Then update its status here and in the summary
  table.

**Statuses:** `Backlog` → `Ready` (acceptance criteria written) →
`In progress` → `Done` · or `Dropped`

## Definition of Done

A story is `Done` only when it meets **its own acceptance criteria** *and*
**every item below**. This list is the same for every story — edit it here
if the project needs more (or fewer) checks, never per story.

- [ ] Each acceptance criterion has a test, written first and seen failing;
      the tests now pass, and the output has been seen (not just reported)
- [ ] No test was deleted, skipped, or weakened to get there
- [ ] The full test suite still passes
- [ ] The code is the simplest version that works — nothing speculative
      (`06-coding-conventions.md` → Simplicity first)
- [ ] New/changed files have a header note; non-obvious functions have a
      doc comment; existing notes still match the code
- [ ] Any new decision is logged in `05-decisions-log.md`; any new term is
      in `11-glossary.md`; diagrams in `02-architecture.md` still match
      the code
- [ ] No non-functional requirement (below) is broken by the change
- [ ] Security checks for the change pass (`14-security.md` → Every
      change); accessibility checks too if the UI changed
      (`15-accessibility.md`)
- [ ] Story status is updated here (story + summary table)
- [ ] A session log entry is written in `10-session-log.md`

A **feature** is done when all its stories are `Done`, its integration
and manual tests pass (`07-testing-checklist.md` → Before marking a feature
done), and its **Done when** line is demonstrated. An **epic** is done when all its features are.

## Non-functional requirements

Qualities the whole system must have, rather than things it does —
how fast, how secure, how accessible, how reliable, how cheap. They apply
to every story, so they're checked by the Definition of Done and verified
at each phase end (`07-testing-checklist.md`).

- Each one must be **measurable** — "fast" isn't a requirement; "≥ 20
  updates/sec on the target machine" is.
- Delete the example rows that don't apply; add your own. Stories that
  exist mainly to meet an NFR reference its ID in **Notes**.

| ID | Category | Requirement (measurable) | How verified | Status |
|---|---|---|---|---|
| NFR1 | Performance | <e.g. main loop runs ≥ 20 times/sec on the target machine> | <e.g. timing test in tests/integration> | Not met yet |
| NFR2 | Security | No known high-severity vulnerabilities in dependencies | Dependency audit + Dependabot, each phase end (`14-security.md`) | Not met yet |
| NFR3 | Accessibility | Meets WCAG 2.2 AA | Manual pass per `15-accessibility.md` | Not met yet |
| NFR4 | Reliability | <e.g. runs a full 30-minute session without crashing> | <e.g. end-to-end test / manual test> | Not met yet |
| NFR5 | Privacy | <e.g. no personal data stored or logged> | <e.g. review of logs and stored files> | Not met yet |
| NFR6 | Cost | $0 per month: free tiers only (`16-budget.md` is not needed) | Any new cost needs a logged decision in `05-decisions-log.md` | Not met yet |

**Statuses:** `Not met yet` · `Met` (with date last verified) · `At risk`

## Summary

| ID | Title | Type | Phase | Status |
|---|---|---|---|---|
| E1 | Portfolio scan | Epic | 1 | Backlog |
| F1.1 | Find in-scope repos | Feature | 1 | Backlog |
| S1.1.1 | Select in-scope repos | Story | 1 | Ready |
| S1.1.2 | Read repo facts | Story | 1 | Ready |
| F1.2 | Work out compliance | Feature | 1 | Backlog |
| S1.2.1 | Evaluate check kinds | Story | 1 | Ready |
| S1.2.2 | Work out the compliance level | Story | 1 | Ready |
| S1.2.3 | Work out scan warnings | Story | 1 | Ready |
| F1.3 | Read reported status | Feature | 1 | Backlog |
| S1.3.1 | Read `portfolio.json` | Story | 1 | Ready |
| F1.4 | Assemble the scan result | Feature | 1 | Backlog |
| S1.4.1 | Assemble the scan result | Story | 1 | Ready |
| E2 | Private data protection | Epic | 1, 3 | Backlog |
| F2.1 | Allow-list and leak test | Feature | 1 | Backlog |
| S2.1.1 | Allow-list filter | Story | 1 | Ready |
| S2.1.2 | Write only filtered output, with a leak test | Story | 1 | Ready |
| S2.1.3 | Keep logs safe | Story | 1 | Ready |
| F2.2 | Leak test covers everything published | Feature | 3 | Backlog |
| E3 | Daily publishing | Epic | 2 | Backlog |
| F3.1 | Markdown report | Feature | 2 | Backlog |
| F3.2 | Scheduled Action | Feature | 2 | Backlog |
| F3.3 | Failure alert and keep-alive | Feature | 2 | Backlog |
| E4 | Dashboard page | Epic | 3 | Backlog |
| F4.1 | Portfolio summary | Feature | 3 | Backlog |
| F4.2 | Sortable table | Feature | 3 | Backlog |
| F4.3 | Per-repo pages | Feature | 3 | Backlog |
| F4.4 | Request links | Feature | 3 | Backlog |

Component folders in the stories below are provisional until `/stack` and
`06-coding-conventions.md` settle the layout. All tests use fixtures, with no
real network or clock. Phases 2 and 3 get their stories when they are next.

---

## E1 — Portfolio scan

**Goal:** Read every in-scope repo and work out its facts, compliance and
reported status, so the owner and a reviewer never have to open each repo.
**Serves:** G2, G3
**Out of scope:** Changing other repos; redefining the standard; publishing
anything (E3, E4).

### F1.1 — Find in-scope repos

**Description:** Decide which repos count, and read what GitHub knows about
each one.
**Phase:** 1
**Depends on:** none
**Done when:** a real run lists the expected 13 repos with their GitHub facts.

#### S1.1.1 — Select in-scope repos

**Story:** Technical — apply the spec's exclusions plus the scan cut-off, so
the same repos are counted every time.

**Component:** `scan/`
**Status:** Ready

**Acceptance criteria:**
- [ ] Given a listing, when selecting, then archived repos, forks, repos tagged `portfolio-exclude` and repos last pushed before 2026-01-01 are left out
- [ ] Given a repo pushed exactly on 2026-01-01, when selecting, then it is included
- [ ] Given an empty listing, when selecting, then the result is an empty list, not an error
- [ ] Given 54 repos across several API pages, when listing, then all pages are read
- [ ] Given a repo with missing or unrecognised visibility, when selecting, then it is treated as private

**Notes:** Scope rule: `05-decisions-log.md` → "Repo scope: spec exclusions plus a fixed cut-off".

#### S1.1.2 — Read repo facts

**Story:** As the owner, I want last activity and open work per repo, so that I don't have to open each one.

**Component:** `scan/`
**Status:** Ready

**Acceptance criteria:**
- [ ] Given a repo, when read, then last push, created date, language, description, default branch and open issue and PR counts are returned
- [ ] Given GitHub's issue count that includes PRs, when read, then issues and PRs are reported separately
- [ ] Given an empty repo with no default branch, when read, then facts are returned and files count as missing
- [ ] Given an API error or rate limit, when read, then that repo is reported as failed, with no made-up values

### F1.2 — Work out compliance

**Description:** Run the standard's checks against each repo and turn the
results into a compliance level and warnings.
**Phase:** 1
**Depends on:** F1.1
**Done when:** levels match `check-compliance.ps1` on the same repos, except
where a nested schema error makes C4 fail here (the spec wins over the script).

#### S1.2.1 — Evaluate check kinds

**Story:** Technical — a pure function of the check registry plus repo files, so results follow the standard and not a separate copy of it.

**Component:** `scan/`
**Status:** Ready

**Acceptance criteria:**
- [ ] Given the four kinds (`exists`, `contains`, `absent`, `schema`), when evaluated on fixtures, then results match `check-compliance.ps1`, except as in the next criterion
- [ ] Given a `portfolio.json` with a nested schema error, when the `schema` kind is evaluated, then C4 fails, even though `check-compliance.ps1` passes it
- [ ] Given `applies_if` that doesn't match, when evaluated, then the result is n/a
- [ ] Given `if_exists` with a missing file, when evaluated, then the check passes
- [ ] Given a check kind the scanner doesn't recognise, when evaluated, then the run stops and names the kind and check
- [ ] Given the check registry can't be read from `pmo-project-standardization`, when the scan starts, then the run stops, with no local copy as a fallback

**Notes:** `check-compliance.ps1` only checks a schema's top level, while `compliance.md` says "fits the schema". The spec wins: `05-decisions-log.md` → "Reuse or reimplement the compliance checks".

#### S1.2.2 — Work out the compliance level

**Story:** As a reviewer, I want one level per repo, so that I can compare them.

**Component:** `scan/`
**Status:** Ready

**Acceptance criteria:**
- [ ] Given C1–C3 pass and all due checks pass, when working out the level, then it is Level 3
- [ ] Given C1–C3 pass and a due required check fails, when working out the level, then it is Level 2
- [ ] Given only C4 passes, when working out the level, then it is Level 1
- [ ] Given nothing passes, when working out the level, then it is Level 0
- [ ] Given a required check fails before its `required_from` date, when working out the level, then it is a warning and the level doesn't drop
- [ ] Given a required check fails on its `required_from` date, when working out the level, then it counts as due
- [ ] Given a template version stamp, when working out the level, then it is reported but never affects the level

#### S1.2.3 — Work out scan warnings

**Story:** As the owner, I want stale reports flagged, so that the page doesn't look confident while wrong.

**Component:** `scan/`
**Status:** Ready

**Acceptance criteria:**
- [ ] Given `updated` is over 30 days old or `null`, and there were pushes in the last 30 days, when scanning, then spec warning S1 fires
- [ ] Given `updated` is exactly 30 days old, when scanning, then spec warning S1 doesn't fire
- [ ] Given `health` is `not-reported` more than 14 days after the repo was created or adopted, when scanning, then spec warning S2 fires
- [ ] Given no `portfolio.json`, when scanning, then spec warning S2 doesn't fire, because Level 0 is already the finding
- [ ] Given a required check fails with `required_from` within 14 days, when scanning, then spec warning S3 fires

**Notes:** These are warnings S1, S2 and S3 in `spec/compliance.md`, not story IDs. The adoption date for S2 isn't recorded anywhere, so it is the date of the first commit that touched `portfolio.json`; this stops a newly adopted old repo being flagged immediately.

### F1.3 — Read reported status

**Description:** Read what each project reports about itself through the
reporting contract.
**Phase:** 1
**Depends on:** F1.1
**Done when:** a missing or broken `portfolio.json` shows as not reported and
doesn't stop the run.

#### S1.3.1 — Read `portfolio.json`

**Story:** As a reviewer, I want each project's reported status, so that I can see how it is doing, and can tell when it hasn't said.

**Component:** `scan/`
**Status:** Ready

**Acceptance criteria:**
- [ ] Given a valid file, when read, then its fields are returned unchanged
- [ ] Given a missing file, when read, then health is `not-reported` and the run continues
- [ ] Given invalid JSON, a schema mismatch or an unknown `schema` version, when read, then health is `not-reported`, and the problem is recorded without quoting the file's content
- [ ] Given a file over 1 MB, when read, then it is treated as invalid and not parsed
- [ ] Given any input, when read, then health, risks and call-outs are never inferred

### F1.4 — Assemble the scan result

**Description:** Combine facts, compliance and status into one structure, and
say whether the run succeeded.
**Phase:** 1
**Depends on:** F1.1, F1.2, F1.3
**Done when:** one failed repo gives a "could not scan" row and the rest are
complete.

#### S1.4.1 — Assemble the scan result

**Story:** Technical — combine the parts into one structure the filter and later the report and page can read.

**Component:** `scan/`
**Status:** Ready

**Acceptance criteria:**
- [ ] Given all repos succeed, when assembling, then there is one row per repo, sorted by name, plus the scan time and spec version
- [ ] Given one repo fails, when assembling, then its row says "could not scan", its other fields are `null`, and the result is marked partial
- [ ] Given a bad token or every repo failing, when assembling, then the result is marked failed
- [ ] Given zero in-scope repos, when assembling, then the result is marked failed, because this repo is always in scope, so zero means something broke
- [ ] Given the same inputs, when assembling twice, then the output is identical apart from the scan time

**Notes:** Failure behaviour: `05-decisions-log.md` → "Scan failure: publish partial and flag it".

---

## E2 — Private data protection

**Goal:** Only allow-listed fields ever leave the scan, with a test that fails
if anything else gets through.
**Serves:** G4
**Out of scope:** Access control on the page (it is public, with no sign-in).

### F2.1 — Allow-list and leak test

**Description:** Cut private rows to the approved fields, write only that
result, and prove it for output files and logs.
**Phase:** 1
**Depends on:** F1.4
**Done when:** canary values planted in a private repo appear in no output file
or log.

#### S2.1.1 — Allow-list filter

**Story:** As the owner, I want private rows cut to approved fields, so that details can't reach the page.

**Component:** `privacy/`
**Status:** Ready

**Acceptance criteria:**
- [ ] Given a private row, when filtered, then only these remain: name, visibility, lifecycle, health, compliance level, last activity date, risk count, blocker count, scan status
- [ ] Given a new field no one has listed, when filtered, then it is dropped
- [ ] Given a failed private row, when filtered, then only name and scan status remain, with no error text
- [ ] Given a public row, when filtered, then it passes unchanged

**Notes:** Allow-list: `05-decisions-log.md` → "Private repos: real name plus signals". Private rows show the level only, not which checks failed.

#### S2.1.2 — Write only filtered output, with a leak test

**Story:** As the owner, I want proof that nothing private gets through, so that I can publish safely.

**Component:** `privacy/`
**Status:** Ready

**Acceptance criteria:**
- [ ] Given a fixture private repo with a unique canary value in every field, when the full scan runs, then no canary appears in any output file
- [ ] Given the filter is bypassed, when the leak test runs, then it fails
- [ ] Given a failed result, when the scan ends, then nothing is written
- [ ] Given a partial or failed result, when the scan ends, then the exit code is non-zero
- [ ] Given any run, when the scan runs, then unfiltered data is never written to disk

#### S2.1.3 — Keep logs safe

**Story:** As the owner, I want safe logs, so that nothing private appears in Action logs, which are public on a public repo.

**Component:** `privacy/`
**Status:** Ready

**Acceptance criteria:**
- [ ] Given the canary fixture, when the scan runs at every log level, then no canary appears in captured logs
- [ ] Given an exception carrying a private file's content or a URL, when logged, then only the repo name and error type are logged
- [ ] Given a run with a token, when the scan runs, then the token appears nowhere in logs

### F2.2 — Leak test covers everything published

**Description:** Extend the leak test to the Markdown report and the built page.
**Phase:** 3
**Depends on:** F2.1, F3.1, F4.3
**Done when:** the same test also runs on the report and the built page.

---

## E3 — Daily publishing

**Goal:** The view rebuilds itself every day, and a failure gets noticed.
**Serves:** G3
**Out of scope:** Automated update PRs to other repos; history and trends.

### F3.1 — Markdown report

**Description:** Generate a Markdown report of the portfolio.
**Phase:** 2
**Depends on:** F2.1
**Done when:** the report is generated from the scan output alone.

### F3.2 — Scheduled Action

**Description:** Run the scan and publish the result daily on GitHub Actions.
**Phase:** 2
**Depends on:** F3.1
**Done when:** it runs daily with no manual steps, and a failed run leaves the
last good version up.

### F3.3 — Failure alert and keep-alive

**Description:** Make failures visible, and keep the schedule and the token alive.
**Phase:** 2
**Depends on:** F3.2
**Done when:** a forced failure sends an alert, the token renewal reminder
exists, and the 60-day workflow shutoff is handled.

---

## E4 — Dashboard page

**Goal:** A reader understands the portfolio from one link and can drill down.
**Serves:** G1, G2
**Out of scope:** Backend, sign-in, editing on the page, history and trends.

### F4.1 — Portfolio summary

**Description:** Tiles, "needs attention first", last-updated time with an
old-data flag, and an explanation of the compliance levels.
**Phase:** 3
**Depends on:** F3.2
**Done when:** a first-time reader can name the project needing attention
within 3 minutes.

### F4.2 — Sortable table

**Description:** All in-scope repos in one table that can be sorted.
**Phase:** 3
**Depends on:** F4.1
**Done when:** all repos can be sorted by keyboard, and status isn't shown by
colour alone.

### F4.3 — Per-repo pages

**Description:** A drill-down page for each repo.
**Phase:** 3
**Depends on:** F4.2
**Done when:** public repos show full detail and private repos show
allow-listed fields only.

### F4.4 — Request links

**Description:** Links that open a pre-filled GitHub issue for the owner.
**Phase:** 3
**Depends on:** F4.3
**Done when:** a link opens a pre-filled issue in public repos, and private
repos have no links.

---

## Bugs

Bugs found in finished work. Each one gets a regression test before it's
fixed (`07-testing-checklist.md` → Bugs). Small bugs found while a story is
still in progress are just part of that story.

| ID | Title | Found in | Severity | Status | Test |
|---|---|---|---|---|---|
| B1 | <what's wrong, in one line> | <story/feature ID> | High / Medium / Low | Open | <test name> |

**Statuses:** `Open` → `In progress` → `Fixed` · or `Won't fix` (with a
reason in Notes)

### B1 — <Bug title>

**Steps to reproduce:**
1. <...>

**Expected:** <what should happen>
**Actual:** <what happens instead>
**Notes:** <cause once found, related decisions>

---

## Template for new items

```
## E<n> — <Epic title>

**Goal:** <outcome>
**Serves:** <G-IDs from 00-vision.md>
**Out of scope:** <exclusions>

### F<n>.<m> — <Feature title>

**Description:** <what it adds>
**Phase:** <n>
**Depends on:** <IDs or "none">
**Done when:** <end-to-end demo>

#### S<n>.<m>.<k> — <Story title>

**Story:** As a <user>, I want <capability>, so that <benefit>.
**Component:** <folder>
**Status:** Backlog

**Acceptance criteria:**
- [ ] Given <state>, when <action>, then <result>

**Notes:** <optional>
```
