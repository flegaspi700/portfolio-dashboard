# Requirements

What this project builds, and how you know each piece is done. Format and
rules: the standard's `requirements.md`.

## Vision

A public, read-only dashboard of my GitHub project portfolio, rebuilt
daily as a static GitHub Pages site from real data: what each active project
is, how healthy it is, what needs attention, and whether it follows the
project standard. A showcase for hiring managers first, my working view
second.

### Problem

Nobody can see the state of my GitHub projects in one place. To find out
what a project is, who owns it, how healthy it is, what its risks are, or
whether it follows my project standard, you have to open each repo and read
its docs. So gaps stay hidden, and someone reviewing my work, such as a
hiring manager, has no quick way to see how I run a portfolio of projects.

### Who it's for

- **Primary (showcase):** a hiring manager or senior reviewer looking at my
  work. They have a few minutes, want the overall picture first, and today
  have to read through individual repos to judge how I work.
- **Also:** me, as owner of the portfolio. I need to see which projects need
  attention and which are behind the standard, and today I'd have to check
  each repo by hand.
- **Designed as if** a portfolio manager or executive uses it: it reads at a
  glance and lets you drill down when you want more.

### Why build it

Mainly as a portfolio piece: to show a hiring manager that I can define a
project management standard and also apply it and report on it across real
projects, using AI-assisted development. The second reason is practical: I
want a real view of my own projects, and building it will push me to move
more of them onto the standard.

"Good enough" means a page I'd be happy to send a hiring manager, built on
real data and refreshed automatically, and one I actually check myself. It
doesn't need to be a full PMO product.

### Goals

- **G1:** A reviewer can understand the state of my portfolio within a few
  minutes, starting from one link: what the projects are, how healthy they
  are, and what needs attention.
- **G2:** I can see each week which projects need my attention and which are
  behind the standard, without opening each repo.
- **G3:** The view stays current with no manual upkeep beyond the status each
  project's owner reports.
- **G4:** Publishing it publicly never exposes details of my private repos.

### Success looks like

- A first-time reader can say, within 3 minutes and without help, how healthy
  the portfolio is and which project needs attention first.
- All in-scope repos appear on the page, and at least 4 are on the standard
  (Level 2 or higher) with real status data.
- The page rebuilds daily with no manual steps for 30 days straight, and
  shows when it was last updated.
- An automated test confirms that nothing beyond the allowed fields for
  private repos reaches the published page or the Action logs.
- I check it at least weekly for a month instead of going repo by repo.
- I'm happy to put the link on my resume or send it to a hiring manager.

### Non-goals

- **No changes to other repos from the dashboard.** It only reads. Buttons
  are links that open a pre-filled GitHub issue for the owner.
- **No automated updates in v1.** Having GitHub Actions or Claude Code open
  draft PRs waits for a later release.
- **No backend, sign-in or database.** It's a static page, so it isn't a live
  app with permissions or an audit trail.
- **No history or trends in v1.** It shows the current state only.
- **No editing health, risks or call-outs on the page.** Those judgments come
  from each project's owner through `portfolio.json`.
- **No redefining the standard here.** The reporting contract and compliance
  rules stay in `pmo-project-standardization`, and this project only uses
  them.
- **No coverage of older repos in v1.** Forks and repos not pushed to since 2026-01-01
  are left out, or counted in a single summary line.

### Constraints

- **Time:** no fixed deadline. Built in small stories, one at a time.
- **Budget:** free tools and tiers only: GitHub Pages and GitHub Actions,
  with no paid services.
- **Platform / environment:** runs on GitHub Actions and is served as a
  static site from GitHub Pages. Developed on Windows 11.
- **Other:**
  - The repo is public, so its code, history and Action logs are visible to
    anyone.
  - Reading private repos needs a read-only token, stored as an encrypted
    Actions secret.
  - Compliance results must follow the rules in
    `pmo-project-standardization` and not a separate copy of them.

### Assumptions and risks

- **Assumption:** the page will look worthwhile with real data, even though
  few repos are on the standard yet. → Check first: run
  `check-compliance.ps1` on all 13 repos and hand-build one static mock. If
  it doesn't look good enough to send, move more repos onto the standard
  before building further.
- **Settled:** the scan doesn't run `check-compliance.ps1` in the Action. It
  applies the same check registry in Python over the GitHub API (see
  `decisions.md`).
- **Risk:** a bug publishes private repo details to the public page or logs.
  → Publish private repos from an explicit list of allowed fields, with a
  test that fails if anything else gets through, and keep those details out
  of the logs.
- **Risk:** the daily rebuild stops without anyone noticing. GitHub turns off
  scheduled workflows in public repos after 60 days without repo activity,
  and the token can expire. → Show the last-updated time prominently and flag
  it when old. Add a failure alert and a token renewal reminder.
- **Risk:** owners stop reporting, so health data goes stale and the page
  looks confident while being wrong. → Show how old each status is and flag
  stale reports.
- **Risk:** the numbers mislead a reader, for example if most repos show as
  behind the standard with no context. → Explain the compliance levels on the
  page and present the gap as a finding.

## Phases

There's no fixed deadline (`requirements.md` → Constraints), so estimates
show the size of the work, not dates.

| Phase | Goal | Exit criteria | Status | Estimate | Started | Finished |
|---|---|---|---|---|---|---|
| 0 — Setup and go/no-go | Prove the toolchain and the riskiest assumptions, with no real logic yet | The go/no-go is decided and logged, and an Action has read a private repo with nothing private in its logs. If the mock is a no-go, the Phase 4 rollout tasks move ahead of Phase 1 | Done | 2-3 days | 2026-11-02 | 2026-11-13 |
| 1 — Scan and JSON | A correct, filtered scan output on real repos, run locally, with nothing published (F1.1–F1.4, F2.1) | A local run on the real repos lists all in-scope repos, levels match `check-compliance.ps1` (apart from the nested schema exception in F1.2), and the leak test passes for output files and logs | Planned | 10 days at most (10 stories) | | |
| 2 — Report and daily run | The scan runs itself every day and publishes a Markdown report (F3.1–F3.3) | The daily run needs no manual steps, a failed run leaves the last good version up, and a forced failure sends an alert | Planned | Set when its stories are written | | |
| 3 — Dashboard page | A reader gets the whole picture from one link and can drill down (F4.1–F4.4, F2.2) | The page is live on GitHub Pages, meets the checks in `accessibility.md`, and the leak test covers the report and the built page | Planned | Set when its stories are written | | |
| 4 — Launch and tuning | Meet the success criteria in the Vision on real data | Every item under "Success looks like" is met, and the link is good enough to send to a hiring manager | Planned | At least 30 days (the unattended run) | | |

### Phase tasks

Work that isn't a story. Tick it here when done.

**Phase 0:**
- [x] Choose and record the stack with `/stack` (the standard's `decisions.md` → Choosing the stack)
- [x] Decide whether to reuse `check-compliance.ps1` or reimplement its checks, including how strict the `schema` check is (`decisions.md`)
- [x] Run `check-compliance.ps1` on all 13 repos (2026-11-02; again on 2026-11-13)
- [x] Hand-build one mock page from the results and decide go or no-go. **The mock contains private data, so it stays outside this repo.** (Mock 2026-11-02; decided **go** on 2026-11-13, see `decisions.md`)
- [x] Create a read-only token and read one private repo from an Action, logging nothing (2026-11-13: `token-check` workflow, run 43514961329; see `security.md`)
- [x] Set up the environment and dependencies (2026-11-13: Python 3.13 venv, pinned `requirements.txt` and `requirements-dev.txt`)
- [x] Create the test folders (the standard's `testing.md` → Kinds of tests)
      and run one passing test from the test runner (2026-11-13: `tests/test_environment.py`;
      `tests/scan/` and `tests/privacy/` arrive with their first stories)
- [x] Fill in `AGENTS.md` → Commands (run, test, coverage, lint, format)
- [x] Make the first commit on `main` (the standard's `git.md`)
- [x] Create the GitHub repo and push `main`
- [ ] (Optional) protect `main` (the standard's `git.md`)
- [ ] Turn on Dependabot and secret scanning (`security.md` → GitHub setup)
- [ ] Copy `.env.example` to `.env` for the local token
- [x] First pass of the threat model (`security.md`) (2026-11-13)
- [ ] Record what applies to this page in `accessibility.md`
- [x] Fill in the non-functional requirements (`requirements.md`) (2026-11-13)

Phase 0 closed 2026-11-13 with its exit criteria met. The open tasks above
are optional or the owner's call (protect `main`, Dependabot and secret
scanning), or wait until they're needed (a local `.env` for the token in
Phase 1; recording the page's checklist in Phase 3).

**Phase 2:**
- [ ] Decide how the output gets published (`decisions.md`), since committed output stays in public history
- [ ] Write the stories for F3.1, F3.2, F3.3

**Phase 3:**
- [ ] Decide the "needs attention first" ranking (`decisions.md`)
- [ ] Write the stories for F4.1, F4.2, F4.3, F4.4, F2.2

**Phase 4:**
- [ ] Rollout: get at least 4 repos to Level 2 or higher with real status data (done by hand in those repos, not by the dashboard)
- [ ] Run the daily rebuild for 30 days straight with no manual steps
- [ ] First-reader test: someone new says, within 3 minutes and without help, how healthy the portfolio is and which project needs attention first
- [ ] Check the page at least weekly for a month

## Epics, features and stories

| ID | Title | Type | Phase | Status |
|---|---|---|---|---|
| E1 | Portfolio scan | Epic | 1 | Backlog |
| F1.1 | Find in-scope repos | Feature | 1 | Backlog |
| S1.1.1 | Select in-scope repos | Story | 1 | Done |
| S1.1.2 | Read repo facts | Story | 1 | Done |
| F1.2 | Work out compliance | Feature | 1 | Backlog |
| S1.2.1 | Evaluate check kinds | Story | 1 | Done |
| S1.2.2 | Work out the compliance level | Story | 1 | Ready |
| S1.2.3 | Work out scan warnings | Story | 1 | Ready |
| S1.2.4 | Read repo files | Story | 1 | Ready |
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
the standard's `coding.md` settle the layout. All tests use fixtures, with no
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
**Done when:** a real run lists all in-scope repos with their GitHub facts.

#### S1.1.1 — Select in-scope repos

**Story:** Technical — apply the spec's exclusions plus the scan cut-off, so
the same repos are counted every time.

**Component:** `scan/`
**Status:** Done

**Acceptance criteria:**
- [x] Given a listing, when selecting, then archived repos, forks, repos tagged `portfolio-exclude` and repos last pushed before 2026-01-01 are left out
- [x] Given a repo pushed exactly on 2026-01-01, when selecting, then it is included
- [x] Given an empty listing, when selecting, then the result is an empty list, not an error
- [x] Given 54 repos across several API pages, when listing, then all pages are read
- [x] Given a repo with missing or unrecognised visibility, when selecting, then it is treated as private

**Notes:** Scope rule: `decisions.md` → "Repo scope: spec exclusions plus a fixed cut-off".

#### S1.1.2 — Read repo facts

**Story:** As the owner, I want last activity and open work per repo, so that I don't have to open each one.

**Component:** `scan/`
**Status:** Done

**Acceptance criteria:**
- [x] Given a repo, when read, then last push, created date, language, description, default branch and open issue and PR counts are returned
- [x] Given GitHub's issue count that includes PRs, when read, then issues and PRs are reported separately
- [x] Given an empty repo with no default branch, when read, then facts are returned and files count as missing
- [x] Given an API error or rate limit, when read, then that repo is reported as failed, with no made-up values

**Notes:** `scan/facts.py`. About 3 API requests per repo (the repo, then open PRs paged until an empty page). On a real empty repo GitHub may still name a default branch, so file reads (S1.2.4) should also treat an empty-repository answer as files missing.

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
**Status:** Done

**Acceptance criteria:**
- [x] Given the four kinds (`exists`, `contains`, `absent`, `schema`), when evaluated on fixtures, then results match `check-compliance.ps1`, except as in the next criterion
- [x] Given a `portfolio.json` with a nested schema error, when the `schema` kind is evaluated, then C4 fails, even though `check-compliance.ps1` passes it
- [x] Given `applies_if` that doesn't match, when evaluated, then the result is n/a
- [x] Given `if_exists` with a missing file, when evaluated, then the check passes
- [x] Given a check kind the scanner doesn't recognise, when evaluated, then the run stops and names the kind and check
- [x] Given the check registry can't be read from `pmo-project-standardization`, when the scan starts, then the run stops, with no local copy as a fallback

**Notes:** `check-compliance.ps1` only checks a schema's top level, while `compliance.md` says "fits the schema". The spec wins: `decisions.md` → "Reuse or reimplement the compliance checks". Built in `scan/checks.py`; the registry is read from the standard's default branch (`decisions.md`, 2026-11-14), and fetching repo files is S1.2.4. Matching, as in the script, ignores case. The fixtures' expected results were confirmed by running `check-compliance.ps1` on them (2026-11-14), and on this repo with the real v2.1.0 registry all 14 checks agreed. Found while building: the script doesn't check top-level types either (`"name": 5` passes it), so C4 also differs there; the spec wins for the same reason.

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

#### S1.2.4 — Read repo files

**Story:** Technical — fetch the files the check registry names from each repo, so the checks (S1.2.1) get their input with as few requests as possible (NFR1).

**Component:** `scan/`
**Status:** Ready

**Acceptance criteria:**
- [ ] Given the check registry, when reading a repo, then only the paths the checks and their `applies_if` name are fetched, and only those that exist in the repo's file tree (one tree request per repo)
- [ ] Given a path not in the tree, when read, then it counts as missing, with no request for it
- [ ] Given an empty repo (no default branch, or GitHub says the repository is empty), when read, then every file counts as missing and the read doesn't fail
- [ ] Given a file over 1 MB, when read, then its content isn't fetched and it counts as present but unreadable
- [ ] Given an API error or rate limit, when read, then that repo is reported as failed, with no made-up values

**Notes:** Split out of S1.2.1 on 2026-11-14, which stays a pure function of the registry plus files. How a present-but-unreadable file affects each check kind is decided when this story starts.

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

**Notes:** Failure behaviour: `decisions.md` → "Scan failure: publish partial and flag it".

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

**Notes:** Allow-list: `decisions.md` → "Private repos: real name plus signals". Private rows show the level only, not which checks failed.

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
**Notes:** security (threat model T2, `security.md`): the workflows set
minimal `permissions:`, never run on `pull_request_target`, and pin
third-party Actions to a full commit SHA. These become acceptance criteria
when the stories are written.

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

## Non-functional requirements

| ID | Category | Requirement (measurable) | How verified | Status |
|---|---|---|---|---|
| NFR1 | Performance | A full scan of all in-scope repos finishes in under 5 minutes on GitHub Actions and makes fewer than 1,000 GitHub API requests | Timed run and a request count in the run log, each phase end | Not met yet |
| NFR2 | Security | No known high-severity vulnerabilities in dependencies | Dependency audit + Dependabot, each phase end (`security.md`) | Not met yet |
| NFR3 | Accessibility | Meets WCAG 2.2 AA | Manual pass per `accessibility.md` | Not met yet |
| NFR4 | Reliability | The page rebuilds daily with no manual steps for 30 days in a row; a failed run never replaces the last good page, and a partial run is published with the failed repos flagged | Forced-failure test (F3.3) in Phase 2; 30-day run log in Phase 4 | Not met yet |
| NFR5 | Privacy | For private repos, only the allow-list fields reach anything published or the Action logs: the leak test's canary values appear in 0 output files and 0 log lines, and the token appears in none | Leak test (S2.1.2, S2.1.3, then F2.2) on every test run | Not met yet |
| NFR6 | Cost | $0 per month: free tiers only (the standard's `cost.md` is not needed) | Any new cost needs a logged decision in `decisions.md` | Not met yet |
| NFR7 | Performance | The dashboard page loads in under 2 seconds on a typical connection, with a total page weight under 500 KB | Lighthouse run on the published page, Phase 3 end | Not met yet |

**Statuses:** `Not met yet` · `Met` (with date last verified) · `At risk`

## Bugs

None logged yet.

| ID | Title | Found in | Severity | Status | Test |
|---|---|---|---|---|---|
