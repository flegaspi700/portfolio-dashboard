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
| 1 — Scan and JSON | A correct, filtered scan output on real repos, run locally, with nothing published (F1.1–F1.4, F2.1) | A local run on the real repos lists all in-scope repos, levels match `check-compliance.ps1` (apart from the nested schema exception in F1.2), and the leak test passes for output files and logs | Done | 10 days at most (10 stories) | 2026-11-13 | 2026-11-17 |
| 2 — Report and daily run | The scan runs itself every day and publishes a Markdown report (F3.1–F3.3) | The daily run needs no manual steps, a failed run leaves the last good version up, and a forced failure sends an alert | Active | 5 days at most (5 stories) | 2026-11-17 | |
| 3 — Dashboard page | A reader gets the whole picture from one link and can drill down (F4.1–F4.4, F2.2) | The page is live on GitHub Pages, meets the checks in `accessibility.md`, and the leak test covers the report and the built page | Active | 7 days at most (7 stories) | 2026-11-18 | |
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
- [ ] Turn on Dependabot and secret scanning (`security.md` → GitHub setup). Secret scanning and push protection are on; Dependabot alerts are off (checked 2026-11-17)
- [x] Copy `.env.example` to `.env` for the local token (2026-11-17)
- [x] First pass of the threat model (`security.md`) (2026-11-13)
- [ ] Record what applies to this page in `accessibility.md`
- [x] Fill in the non-functional requirements (`requirements.md`) (2026-11-13)

Phase 0 closed 2026-11-13 with its exit criteria met. The open tasks above
are optional or the owner's call (protect `main`, Dependabot and secret
scanning), or wait until they're needed (a local `.env` for the token in
Phase 1; recording the page's checklist in Phase 3).

**Phase 1:** closed 2026-11-17 with its exit criteria met on real data
(S1.4.2's first real run): all 17 in-scope repos listed, levels matching
`check-compliance.ps1` on all 12 local clones, and the leak tests passing for
output files and logs. Phase checklist: 262 tests pass, coverage 100% for
`scan/` and `privacy/` (no untested logic to add), NFRs updated below,
`pip-audit` clean, no open secret-scanning alerts, threat model still
accurate (T2 now names the local `.env`). No manual tests and no UI yet, so
no accessibility pass.

**Phase 2:**
- [x] Decide how the output gets published (`decisions.md`), since committed output stays in public history (2026-11-17: deploy to Pages, nothing committed)
- [x] Write the stories for F3.1, F3.2, F3.3 (2026-11-17, approved by the owner)

**Phase 3:**
- [x] Decide the "needs attention first" ranking (`decisions.md`) (2026-11-17: fixed tiers, with the reason shown)
- [x] Write the stories for F4.1, F4.2, F4.3, F4.4, F2.2 (2026-11-17, approved by the owner)
- [ ] Record what applies to the page in `accessibility.md`, then run the accessibility pass and a Lighthouse check (NFR3, NFR7) before closing the phase

**Phase 4:**
- [ ] Rollout: get at least 4 repos to Level 2 or higher with real status data (done by hand in those repos, not by the dashboard). Can start any time: on 2026-11-17, 5 repos were at Level 3 but only this one reported health, so `/report` in 4 of them meets it
- [ ] Run the daily rebuild for 30 days straight with no manual steps (the count can start with the first scheduled run, 2026-11-18, while Phase 3 is built)
- [ ] First-reader test: someone new says, within 3 minutes and without help, how healthy the portfolio is and which project needs attention first
- [ ] Check the page at least weekly for a month

## Epics, features and stories

| ID | Title | Type | Phase | Status |
|---|---|---|---|---|
| E1 | Portfolio scan | Epic | 1 | Done |
| F1.1 | Find in-scope repos | Feature | 1 | Done |
| S1.1.1 | Select in-scope repos | Story | 1 | Done |
| S1.1.2 | Read repo facts | Story | 1 | Done |
| F1.2 | Work out compliance | Feature | 1 | Done |
| S1.2.1 | Evaluate check kinds | Story | 1 | Done |
| S1.2.2 | Work out the compliance level | Story | 1 | Done |
| S1.2.3 | Work out scan warnings | Story | 1 | Done |
| S1.2.4 | Read repo files | Story | 1 | Done |
| F1.3 | Read reported status | Feature | 1 | Done |
| S1.3.1 | Read `portfolio.json` | Story | 1 | Done |
| F1.4 | Assemble the scan result | Feature | 1 | Done |
| S1.4.1 | Assemble the scan result | Story | 1 | Done |
| S1.4.2 | Run a real scan | Story | 1 | Done |
| E2 | Private data protection | Epic | 1, 3 | Backlog |
| F2.1 | Allow-list and leak test | Feature | 1 | Done |
| S2.1.1 | Allow-list filter | Story | 1 | Done |
| S2.1.2 | Write only filtered output, with a leak test | Story | 1 | Done |
| S2.1.3 | Keep logs safe | Story | 1 | Done |
| F2.2 | Leak test covers everything published | Feature | 3 | Backlog |
| S2.2.1 | Leak test on the built site | Story | 3 | Ready |
| E3 | Daily publishing | Epic | 2 | Done |
| F3.1 | Markdown report | Feature | 2 | Done |
| S3.1.1 | Render the Markdown report | Story | 2 | Done |
| F3.2 | Scheduled Action | Feature | 2 | Done |
| S3.2.1 | Daily workflow: scan, report, deploy | Story | 2 | Done |
| F3.3 | Failure alert and keep-alive | Feature | 2 | Done |
| S3.3.1 | Failure alert, with a forced-failure test | Story | 2 | Done |
| S3.3.2 | Keep the schedule alive | Story | 2 | Done |
| S3.3.3 | Token renewal reminder | Story | 2 | Done |
| E4 | Dashboard page | Epic | 3 | In progress |
| F4.1 | Portfolio summary | Feature | 3 | In progress |
| S4.1.1 | Build the page from the scan output | Story | 3 | Done |
| S4.1.2 | Summary tiles, freshness and levels | Story | 3 | Done |
| S4.1.3 | Needs attention first | Story | 3 | Ready |
| F4.2 | Sortable table | Feature | 3 | Backlog |
| S4.2.1 | Sortable, accessible repo table | Story | 3 | Ready |
| F4.3 | Per-repo pages | Feature | 3 | Backlog |
| S4.3.1 | A page per repo | Story | 3 | Ready |
| F4.4 | Request links | Feature | 3 | Backlog |
| S4.4.1 | Request links for public repos | Story | 3 | Ready |

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
**Status:** Done 2026-11-17: the first real run (S1.4.2) listed all 17 in-scope repos with their facts.

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
**Status:** Done 2026-11-17: all four stories done; integration test in `tests/scan/test_result.py`; the Done when line shown by the `check-compliance.ps1` cross-checks in S1.2.2 and S1.2.4.

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
**Status:** Done

**Acceptance criteria:**
- [x] Given every check in the registry's `levels.adopted` passes and all due checks pass, when working out the level, then it is Level 3
- [x] Given every check in `levels.adopted` passes and a due required check fails, when working out the level, then it is Level 2
- [x] Given only `levels.reporting` (C4) passes, when working out the level, then it is Level 1
- [x] Given nothing passes, when working out the level, then it is Level 0
- [x] Given a required check fails before its `required_from` date, when working out the level, then it is a warning and the level doesn't drop
- [x] Given a required check fails on its `required_from` date, when working out the level, then it counts as due
- [x] Given a template version stamp, when working out the level, then it is reported but never affects the level

**Notes:** The criteria first named spec v1 IDs ("C1–C3"); on 2026-11-17 the owner changed them to the registry's `levels` sets, which spec v2 defines as reporting = C4 and adopted = C4, C2, C8, C9, so the level follows the registry and not a copy of it. As in `check-compliance.ps1`, n/a doesn't count as a pass for a level set, and grace-period warnings are listed only for repos at Adopted or higher (`spec/compliance.md` → Grace period, since v2.1.0). Built in `scan/levels.py`, which also reports the version from the Standard line or a v1 Template version stamp. Cross-checked with `check-compliance.ps1` on 2026-11-17: 11 local repos, each as of 2026-11-17 and 2026-12-20, matched on level and grace-period warnings in all 22 comparisons.

#### S1.2.3 — Work out scan warnings

**Story:** As the owner, I want stale reports flagged, so that the page doesn't look confident while wrong.

**Component:** `scan/`
**Status:** Done

**Acceptance criteria:**
- [x] Given `updated` is over 30 days old or `null`, and there were pushes in the last 30 days, when scanning, then spec warning S1 fires
- [x] Given `updated` is exactly 30 days old, when scanning, then spec warning S1 doesn't fire
- [x] Given `health` is `not-reported` more than 14 days after the repo was created or adopted, when scanning, then spec warning S2 fires
- [x] Given no `portfolio.json`, when scanning, then spec warning S2 doesn't fire, because Level 0 is already the finding
- [x] Given a required check fails with `required_from` within 14 days, when scanning, then spec warning S3 fires

**Notes:** These are warnings S1, S2 and S3 in `spec/compliance.md`, not story IDs. The adoption date for S2 isn't recorded anywhere, so it is the date of the first commit that touched `portfolio.json`; this stops a newly adopted old repo being flagged immediately. Built in `scan/warnings.py`. The adoption date is read only when S2 could fire (`decisions.md`, 2026-11-17); if it can't be read, the repo is a failed read. Beyond the criteria, following `spec/compliance.md`: S1 doesn't fire without a `portfolio.json` either, and S3 applies only at Adopted or higher, since it is built from S1.2.2's grace-period warnings. Boundaries chosen while building: a push exactly 30 days ago counts as recent for S1, and a check due in exactly 14 days counts as due soon for S3.

#### S1.2.4 — Read repo files

**Story:** Technical — fetch the files the check registry names from each repo, so the checks (S1.2.1) get their input with as few requests as possible (NFR1).

**Component:** `scan/`
**Status:** Done

**Acceptance criteria:**
- [x] Given the check registry, when reading a repo, then only the paths the checks and their `applies_if` name are fetched, and only those that exist in the repo's file tree (one tree request per repo)
- [x] Given a path not in the tree, when read, then it counts as missing, with no request for it
- [x] Given an empty repo (no default branch, or GitHub says the repository is empty), when read, then every file counts as missing and the read doesn't fail
- [x] Given a file over 1 MB, when read, then its content isn't fetched and it counts as present but unreadable
- [x] Given an API error or rate limit, when read, then that repo is reported as failed, with no made-up values
- [x] Given a path that only `exists` checks name, when read, then it counts as present from the tree alone, with no request for its content
- [x] Given GitHub returns a truncated file tree, when read, then that repo is reported as failed, rather than counting files as missing
- [x] Given a present but unreadable file, when the checks run, then `exists` passes, `contains`, `schema` and `absent` fail, and an `applies_if` on it gives n/a

**Notes:** Split out of S1.2.1 on 2026-11-14, which stays a pure function of the registry plus files. The owner reviewed the criteria on 2026-11-17 and added the `exists`-only and truncated-tree ones. A present but unreadable file counts as not passing: `decisions.md`, "Unreadable files don't pass content checks" (2026-11-17). Built in `scan/files.py`, with the unread-file rule in `scan/checks.py`; file content comes from the blob the tree names, so files and tree are the same snapshot. A live read-only check on 2026-11-17 against two public repos gave the same level and check results as `check-compliance.ps1`; this repo took 4 requests.

### F1.3 — Read reported status

**Description:** Read what each project reports about itself through the
reporting contract.
**Phase:** 1
**Depends on:** F1.1
**Done when:** a missing or broken `portfolio.json` shows as not reported and
doesn't stop the run.
**Status:** Done 2026-11-17: S1.3.1 done; `test_broken_portfolio_json_is_not_reported_and_the_scan_goes_on` shows the Done when line through the whole scan.

#### S1.3.1 — Read `portfolio.json`

**Story:** As a reviewer, I want each project's reported status, so that I can see how it is doing, and can tell when it hasn't said.

**Component:** `scan/`
**Status:** Done

**Acceptance criteria:**
- [x] Given a valid file, when read, then its fields are returned unchanged
- [x] Given a missing file, when read, then health is `not-reported` and the run continues
- [x] Given invalid JSON, a schema mismatch or an unknown `schema` version, when read, then health is `not-reported`, and the problem is recorded without quoting the file's content
- [x] Given a file over 1 MB, when read, then it is treated as invalid and not parsed
- [x] Given any input, when read, then health, risks and call-outs are never inferred

**Notes:** Built in `scan/status.py`. The schema is the one the registry's `portfolio.json` schema check names, so it comes from the standard like C4's. A rejected file's problem gives the validator and JSON path only (such as `enum at $.risks[0].severity`), never values. Beyond the criteria: an `updated` that fits the pattern but isn't a real date (`2026-13-45`) is invalid too. On 2026-11-17 the reader accepted exactly the files C4 passes on all 9 local `portfolio.json` files.

### F1.4 — Assemble the scan result

**Description:** Combine facts, compliance and status into one structure, and
say whether the run succeeded.
**Phase:** 1
**Depends on:** F1.1, F1.2, F1.3
**Done when:** one failed repo gives a "could not scan" row and the rest are
complete.
**Status:** Done 2026-11-17: S1.4.1 and S1.4.2 done. The Done when line is shown on fixtures (`test_one_failed_repo_could_not_scan_with_null_fields_and_partial_result`); the first real run had no failed repo.

#### S1.4.1 — Assemble the scan result

**Story:** Technical — combine the parts into one structure the filter and later the report and page can read.

**Component:** `scan/`
**Status:** Done

**Acceptance criteria:**
- [x] Given all repos succeed, when assembling, then there is one row per repo, sorted by name, plus the scan time and spec version
- [x] Given one repo fails, when assembling, then its row says "could not scan", its other fields are `null`, and the result is marked partial
- [x] Given a bad token or every repo failing, when assembling, then the result is marked failed
- [x] Given zero in-scope repos, when assembling, then the result is marked failed, because this repo is always in scope, so zero means something broke
- [x] Given the same inputs, when assembling twice, then the output is identical apart from the scan time

**Notes:** Failure behaviour: `decisions.md` → "Scan failure: publish partial and flag it". Built in `scan/result.py`: `run_scan` reads the registry, lists the repos, and for each in-scope repo runs facts, files, checks, level, status and warnings, so `tests/scan/test_result.py` is also the integration test for F1.2 and F1.3. The spec version is the registry's `version`. Rows sort by name ignoring case. An unreadable registry also gives a failed result, before any repo is read, which is how S1.2.1's "the run stops" shows up in the result. `work_out_warnings` (S1.2.3) can return a `FailedRead` when the adoption date can't be read; pass it `lambda: read_adoption_date(fetch, owner, name)` so the read happens only when needed.

#### S1.4.2 — Run a real scan

**Story:** Technical — a real fetch function and `main.py`, so the scan runs against GitHub with the read-only token and the assembled result (S1.4.1) is built from real data.

**Component:** `scan/`, `main.py`
**Status:** Done

**Acceptance criteria:**
- [x] Given `PORTFOLIO_READ_TOKEN` is set (in the environment or `.env`), when `main.py` runs, then it scans the token owner's repos (login from `GET /user`), writes `output/scan.json` through the write step (S2.1.2), and logs only counts: repos in scope, could not scan, API requests, time taken
- [x] Given the token is missing, when `main.py` runs, then it stops before any request, with a message naming the variable and `.env.example`, and a non-zero exit code
- [x] Given a request takes over 30 seconds, when fetching, then it times out and counts as a network error
- [x] Given a rate-limit or other API error, when fetching, then it is raised as an HTTP error, with no retry loop, so the repo or run fails as S1.1.2 and S1.4.1 say
- [x] Given any result, when `main.py` ends, then it exits with the code the write step returns
- [x] Given any run, when `main.py` runs, then logging goes through `configure_logging` (S2.1.3), only `output/scan.json` is written, and the real token appears in no log line
- [x] Given a real local run, when it ends, then every in-scope repo is listed, and levels match `check-compliance.ps1` on the repos cloned locally

**Notes:** Added 2026-11-17: the owner chose a separate story for the real run over folding it into S1.4.1 or S2.1.2. The owner approved these criteria on 2026-11-17, with `.env` read by the standard library (no new dependency; a variable already in the environment wins). The exit-code rule itself is S2.1.2's. Checked before building, 2026-11-17: the token lists 58 repos (13 private) and reads all 13 private file trees, but GitHub refused its PR lists on all 13 (HTTP 403); the owner chose to add Pull requests: read to the token rather than drop the PR count. Built in `scan/github.py` (the fetch function: one GET per call, 30 s timeout, API paths only so the token goes nowhere else) and `main.py`.

**First real run, 2026-11-17:** after the owner added Pull requests: read, `main.py` listed 58 repos, selected 17 in scope (the same 17 the scope rule gives on an independent `gh` listing), scanned all 17 with none failed, in 86 API requests and 28.4 seconds, exit code 0. Levels: 5 at Level 3, 3 at Level 1, 9 at Level 0; all 12 locally cloned repos matched `check-compliance.ps1`. The 9 private rows held only allow-list fields, and the log lines carried counts only.

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
**Status:** Done 2026-11-17: all three stories done; the leak tests run the whole scan, filter, write and logging together on `tests/fake_github.py`, which is the integration test, and show the Done when line on fixtures.

#### S2.1.1 — Allow-list filter

**Story:** As the owner, I want private rows cut to approved fields, so that details can't reach the page.

**Component:** `privacy/`
**Status:** Done

**Acceptance criteria:**
- [x] Given a private row, when filtered, then only these remain: name, visibility, lifecycle, health, compliance level, last activity date, risk count, blocker count, scan status
- [x] Given a new field no one has listed, when filtered, then it is dropped
- [x] Given a failed private row, when filtered, then only name and scan status remain, with no error text
- [x] Given a public row, when filtered, then it passes unchanged

**Notes:** Allow-list: `decisions.md` → "Private repos: real name plus signals". Private rows show the level only, not which checks failed. Built in `privacy/allow_list.py`. Each allow-listed field is built by name (`last_activity` is the last push date; `risk_count` and `blocker_count` are `null` when a repo didn't report the list, 0 when the list is empty), so a new field can't get through. A visibility other than exactly `public` counts as private. Beyond the criteria: a public row also gets the same signal fields, so the report and page read one shape.

#### S2.1.2 — Write only filtered output, with a leak test

**Story:** As the owner, I want proof that nothing private gets through, so that I can publish safely.

**Component:** `privacy/`
**Status:** Done

**Acceptance criteria:**
- [x] Given a fixture private repo with a unique canary value in every field, when the full scan runs, then no canary appears in any output file
- [x] Given the filter is bypassed, when the leak test runs, then it fails
- [x] Given a failed result, when the scan ends, then nothing is written
- [x] Given a partial or failed result, when the scan ends, then the exit code is non-zero
- [x] Given any run, when the scan runs, then unfiltered data is never written to disk

**Notes:** Output is one JSON file, `output/scan.json`, git-ignored: `decisions.md`, "Scan output: one JSON file" (2026-11-17). The write step returns the exit code; `main.py` (S1.4.2) exits with it. Built in `privacy/output.py`: `write_output` takes the scan result and runs the filter itself, so there is no path for unfiltered data to disk, and swaps the file in one step. The leak test is `tests/privacy/test_output.py`: a private repo with a different canary in each of 19 places (repo description, language, branch, topic, AGENTS.md, CLAUDE.md, requirements and every free-text `portfolio.json` field) runs through the whole scan on `tests/fake_github.py`, shared with S1.4.1's tests. A second test swaps in a filter that lets everything through and checks the leak test catches it.

#### S2.1.3 — Keep logs safe

**Story:** As the owner, I want safe logs, so that nothing private appears in Action logs, which are public on a public repo.

**Component:** `privacy/`
**Status:** Done

**Acceptance criteria:**
- [x] Given the canary fixture, when the scan runs at every log level, then no canary appears in captured logs
- [x] Given an exception carrying a private file's content or a URL, when logged, then only the repo name and error type are logged
- [x] Given a run with a token, when the scan runs, then the token appears nowhere in logs

**Notes:** Built in `privacy/safe_logging.py`: `configure_logging` (for `main.py`, S1.4.2) routes every record through a formatter that shows a logged exception's type and the types it was raised from, never its text or traceback, and drops stack info. The scan logs no repo names at all, which meets "only the repo name and error type" with room to spare. Found while building: an unreadable registry put the error's own text into the result's failure reason, which `write_output` logs; it is now a generic reason (`could not read the check registry: HTTP 401`). The token check uses a made-up token in error text and headers; S1.4.2 checks the real one.

### F2.2 — Leak test covers everything published

**Description:** Extend the leak test to the Markdown report and the built page.
**Phase:** 3
**Depends on:** F2.1, F3.1, F4.3
**Done when:** the same test also runs on the report and the built page.


#### S2.2.1 — Leak test on the built site

**Story:** As the owner, I want proof that nothing private reaches the published site, so that I can share the link safely.

**Component:** `tests/`
**Status:** Ready

**Acceptance criteria:**
- [ ] Given the canary fixture, when the whole scan, filter, report and site build run, then no canary appears in any file of the built site, HTML and Markdown alike
- [ ] Given the filter is bypassed, when the leak test runs, then it fails
- [ ] Given the built site, when checked, then private repos' pages and rows contain the allow-list fields only
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
**Status:** Done 2026-11-17: S3.1.1 done; the leak test runs scan, filter, write and report together on the fake GitHub, and the report reads only `output/scan.json`.

#### S3.1.1 — Render the Markdown report

**Story:** As a reviewer, I want one readable report of the portfolio, so that I can see every project's state without opening each repo.

**Component:** `report/` (new)
**Status:** Done

**Acceptance criteria:**
- [x] Given `output/scan.json`, when rendering, then `output/site/index.md` has the scan time (UTC), the spec version, summary counts (repos per level, per health, could not scan), and one table row per repo, sorted by name: name, visibility, level, health, lifecycle, last activity, risks, blockers, scan status
- [x] Given a partial result, when rendering, then a line at the top says the scan was partial and how many repos could not be scanned, and those rows say "could not scan"
- [x] Given any run, when rendering, then the report reads only the scan output file, never the scan result (F3.1's Done when)
- [x] Given repo text, when rendering, then no free text from any repo appears (names, fixed values, numbers and dates only), and a name with Markdown or HTML characters is escaped (T3)
- [x] Given the canary fixture, when the report is rendered, then no canary appears in it (NFR5, ahead of F2.2)
- [x] Given the same scan output, when rendering twice, then the reports are identical
- [x] Given no `output/scan.json`, when rendering, then it stops with a clear message and a non-zero exit code

**Notes:** Criteria approved by the owner on 2026-11-17. Free text is left out on purpose: the scan output is already filtered, but public repos' text would be rendered as HTML by the Pages build (T3). Ranking by "needs attention first" is Phase 3. Built in `report/markdown.py`, run as `python -m report`. Every cell is escaped: HTML entities for `& < > { }` (the braces stop Jekyll's Liquid), a backslash before Markdown's backslash, backtick, `*`, `_`, `[`, `]` and `|`. The canary fixture moved to `tests/canaries.py` so the report's leak test can share it. On the real scan output of 2026-11-17 it rendered all 17 repos.

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
**Status:** Done 2026-11-17: S3.2.1 done; the live run deployed the report with no manual step beyond starting it, and the forced failure left the last good page up. The first scheduled run is the next 06:00 UTC.

#### S3.2.1 — Daily workflow: scan, report, deploy

**Story:** As the owner, I want the report rebuilt every day by itself, so that it stays current with no manual steps.

**Component:** `.github/workflows/` (new workflow)
**Status:** Done

**Acceptance criteria:**
- [x] Given the daily schedule (06:00 UTC) or a manual run, when the workflow runs, then it runs `main.py` with `PORTFOLIO_READ_TOKEN` from the repo secret, renders the report (S3.1.1), builds it with GitHub's Pages actions and deploys it
- [x] Given a complete or partial result, when the run ends, then the report is deployed; a partial run then fails the job, after deploying (`decisions.md`, "Scan failure")
- [x] Given a failed result (no scan output), when the run ends, then nothing is deployed, the last good page stays, and the job fails
- [x] Given the workflow file, when checked by a test, then it sets minimal `permissions:` per job, has no `pull_request_target` trigger, pins every action to a full commit SHA, and passes the token only to the scan step (T2)
- [x] Given the first Action run, when the owner reads its public log, then it shows counts only, with the token masked, and the run time and request count meet NFR1 (manual check, recorded in `docs/manual-tests.md`)

**Notes:** Owner setup, once: Settings → Pages → Source: GitHub Actions. Adds `docs/manual-tests.md` (the standard's extra doc for checks only a person can do). A test reads the workflow file as text, so no YAML library is added. Built as `.github/workflows/publish.yml`: a `scan` job (checkout, Python 3.13, `main.py`, `python -m report`, Jekyll build, upload), a `deploy` job with the Pages permissions only, and a `result` job that fails the run unless the scan was complete and deployed. GitHub's own actions are pinned to the commit SHAs of their latest releases on 2026-11-17. The workflow also parsed as valid YAML (checked with a throwaway PyYAML outside the project). The last criterion needs the workflow on `main`, so it is run after the merge. Live run 2026-11-17 (run 44142627009) passed: see `docs/manual-tests.md`, F3.2.

### F3.3 — Failure alert and keep-alive

**Description:** Make failures visible, and keep the schedule and the token alive.
**Phase:** 2
**Depends on:** F3.2
**Done when:** a forced failure sends an alert, the token renewal reminder
exists, and the 60-day workflow shutoff is handled.
**Status:** Done 2026-11-17: a forced failure sent the alert email; the token reminder logs the expiry (2027-02-11) and fails within 14 days of it; the keep-alive call passed on both live runs.

#### S3.3.1 — Failure alert, with a forced-failure test

**Story:** As the owner, I want to hear when the daily run fails, so that a broken page doesn't go unnoticed.

**Component:** `.github/workflows/`
**Status:** Done

**Acceptance criteria:**
- [x] Given a failed or partial run, when it ends, then the job fails, so GitHub sends the owner its failed-workflow email
- [x] Given a manual run with `force_failure` set, when it runs, then it fails before deploying, and the last good page stays
- [x] Given the forced failure, when it runs, then the owner receives the alert (manual check, recorded in `docs/manual-tests.md`; NFR4's forced-failure test)

**Notes:** Uses GitHub's own notifications, so no new permission or service. The owner's notification settings must send failed-workflow emails. Built in `publish.yml`: a `force_failure` input (off by default; scheduled runs never set it) and a first step in the `scan` job that exits 1 when it's on, so the scan job fails and the deploy is skipped. The alert check is a live run after the merge (`docs/manual-tests.md`, F3.3). Forced-failure run 2026-11-17 (run 44142953144) passed, and the owner received the email: see `docs/manual-tests.md`, F3.3.

#### S3.3.2 — Keep the schedule alive

**Story:** Technical — stop GitHub switching off the daily schedule after 60 days without a commit, since publishing commits nothing.

**Component:** `.github/workflows/`
**Status:** Done

**Acceptance criteria:**
- [x] Given a run, when it ends, then it re-enables its own workflow through the GitHub API with the workflow's own token (`actions: write` on that job only), which resets the 60-day timer
- [x] Given the keep-alive call fails, when the run ends, then the job fails, so the alert fires before the schedule can lapse
- [x] Given the workflow file, when checked by a test, then the keep-alive uses no third-party action

**Notes:** Checked 2026-11-17: the common keep-alive actions (liskin/gh-workflow-keepalive, gautamkrishnar/keepalive-workflow v2) work this way, calling the enable API with `actions: write` and no dummy commits, and users report it resets the 60-day counter. GitHub doesn't document the reset directly, so it rests on that report; if the schedule is ever switched off anyway, GitHub's warning email and the missing daily runs show it. Built as the `keep-alive` job in `publish.yml`, using the runner's `gh` CLI. Whether the call succeeds on a real run is checked live (`docs/manual-tests.md`, F3.3, step 5).

#### S3.3.3 — Token renewal reminder

**Story:** As the owner, I want a warning before the read token expires, so that the page doesn't silently stop updating (T5).

**Component:** `scan/`, `main.py`
**Status:** Done

**Acceptance criteria:**
- [x] Given GitHub's token-expiry header on the `GET /user` answer, when the scan runs, then it logs the expiry date (a date, never the token)
- [x] Given the token expires within 14 days, when the run ends, then the report is still deployed and the job then fails, so the alert reminds the owner
- [x] Given no expiry header (a token that never expires), when the scan runs, then it logs that and carries on

**Notes:** The read token was renewed on 2026-11-17 and now expires on 2027-02-11 (read from GitHub's header through the new code that day: 86 days left). Built in `scan/github.py` (`token_expiry`, and the fetch function keeps the last response's headers) and `main.py` (logs the date; with 14 days or fewer left, exits 1 after writing, so the report still deploys and the run fails). The header's two formats, `UTC` and a numeric offset, are both read; an unreadable value counts as no expiry rather than a guess.

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

#### S4.1.1 — Build the page from the scan output

**Story:** Technical — generate the site as our own static HTML from the scan output, replacing the Jekyll build and its default theme, so the page has no third-party code and every value is escaped.

**Component:** `report/` (`site.py`, `page.py`, `templates/`), `.github/workflows/publish.yml`
**Status:** Done

**Acceptance criteria:**
- [x] Given `output/scan.json`, when the site is built, then `output/site/index.html` is written from that file alone, with Jinja2 auto-escaping on, and the Markdown report stays at `output/site/report.md`
- [x] Given the workflow, when it runs, then it uploads `output/site` as it is, with no Jekyll step
- [x] Given the built site, when checked, then it loads no script, style or font from another site, and its total size is under 500 KB (NFR7's weight)
- [x] Given the same scan output, when built twice, then the files are identical
- [x] Given no scan output, when building, then it stops with a clear message and a non-zero exit code

**Notes:** Jinja2 was chosen in "Language and stack" for Phase 3; it is pinned and audited (`pip-audit`) when this story starts. Removes `actions/jekyll-build-pages` and the default theme's anchor-js script seen on 2026-11-17. Built in `report/`, not `site/`: `site` is a standard-library module, so a package of that name can't be imported (`architecture.md` → Layout). `python -m report` now builds the whole site. Jinja2 3.1.6 pinned, `pip-audit` clean on 2026-11-18. The page shows the scan time and links to the report; S4.1.2 onwards fill it in. Moving the report from `index.md` to `report.md` dropped one test's step name in `test_workflows.py` ("Render the report", a step that no longer exists); the remaining steps keep the same check.

#### S4.1.2 — Summary tiles, freshness and levels

**Story:** As a reviewer, I want the portfolio's state at a glance, so that I understand it within a few minutes.

**Component:** `report/` (`page.py`, `templates/index.html`)
**Status:** Done

**Acceptance criteria:**
- [x] Given the scan output, when the page is built, then tiles show the number of repos, the count per health value, per compliance level, and could not scan
- [x] Given the page, when read, then it shows when the data was scanned (UTC), and a partial scan is flagged at the top
- [x] Given data more than 36 hours old when the page is opened, when it loads, then a notice says the data may be out of date (a small script compares the scan time with the reader's clock; without scripts, the scan time is still shown)
- [x] Given the page, when read, then the four compliance levels are explained in a sentence each, with a link to the standard's compliance spec
- [x] Given counts and states, when shown, then none rely on colour alone (text labels on every state)

**Notes:** The counts leave out repos that could not be scanned, as the report does. The levels' sentences come from the Meaning column of the standard's `spec/compliance.md`, and the link goes to it on the default branch, where the scan reads the check registry. The old-data notice is a hidden paragraph that an inline script shows; its logic was run against fake clocks with Node (hidden at 35 h 59 min, shown at 36 h 1 min), and the in-browser check is in `docs/manual-tests.md` (F4.1). Health tiles carry a coloured edge as well as their label.

#### S4.1.3 — Needs attention first

**Story:** As the owner, I want the repos that need attention listed first, with the reason, so that I know where to look this week.

**Component:** `site/`
**Status:** Ready

**Acceptance criteria:**
- [ ] Given the scan output, when ranking, then repos are ordered by tier, first match wins: could not scan, health red, has blockers, health amber, health not reported, below Level 2, the rest
- [ ] Given repos in the same tier, when ranking, then lifecycle `active` comes first, then the most recent activity, then the name
- [ ] Given a repo whose lifecycle is `done` or `archived`, when ranking, then it isn't listed
- [ ] Given the page, when read, then a "Needs attention first" section lists the top 5 with their reason, private and public alike
- [ ] Given a public row, when ranking, then only the allow-list fields count, so it ranks exactly as it would if it were private

**Notes:** Criteria approved by the owner on 2026-11-17, with the rest of Phase 3's stories. `decisions.md`, "Needs attention first" ranking (2026-11-17).

### F4.2 — Sortable table

**Description:** All in-scope repos in one table that can be sorted.
**Phase:** 3
**Depends on:** F4.1
**Done when:** all repos can be sorted by keyboard, and status isn't shown by
colour alone.

#### S4.2.1 — Sortable, accessible repo table

**Story:** As a reviewer, I want every in-scope repo in one table I can sort, so that I can compare them my way.

**Component:** `site/`
**Status:** Ready

**Acceptance criteria:**
- [ ] Given the page, when read without scripts, then the table lists every repo in attention order, with name, visibility, level, health, lifecycle, last activity, risks, blockers and scan status
- [ ] Given a column header, when activated by mouse or keyboard (Tab, then Enter or Space), then the table sorts by it, toggling ascending and descending, and `aria-sort` says which
- [ ] Given a state such as health or level, when shown, then it has a text label, never colour alone
- [ ] Given the table, when checked, then headers are real table headers and the page meets the table checks in `accessibility.md`

### F4.3 — Per-repo pages

**Description:** A drill-down page for each repo.
**Phase:** 3
**Depends on:** F4.2
**Done when:** public repos show full detail and private repos show
allow-listed fields only.

#### S4.3.1 — A page per repo

**Story:** As a reviewer, I want to drill into one repo, so that I can see the detail behind its row.

**Component:** `site/`
**Status:** Ready

**Acceptance criteria:**
- [ ] Given a repo, when the site is built, then it has its own page, linked from its table row, at a path made from its name with only safe characters
- [ ] Given a public repo, when its page is built, then it shows its facts, level, each check's result with the standard's fix for failures, scan warnings, and its reported status: summary, health reason, risks, blockers, call-outs, next milestone
- [ ] Given a private repo, when its page is built, then it shows the allow-list fields only
- [ ] Given a repo that could not be scanned, when its page is built, then it says so, with no other values
- [ ] Given text from a public repo containing markup, when shown, then it is escaped and displayed as text (T3)

### F4.4 — Request links

**Description:** Links that open a pre-filled GitHub issue for the owner.
**Phase:** 3
**Depends on:** F4.3
**Done when:** a link opens a pre-filled issue in public repos, and private
repos have no links.


#### S4.4.1 — Request links for public repos

**Story:** As the owner, I want a link that asks a project's owner for what's missing, so that gaps get fixed without me writing each request.

**Component:** `site/`
**Status:** Ready

**Acceptance criteria:**
- [ ] Given a public repo whose health isn't reported or whose report is stale (S1, S2), when its page is built, then it has a "Request a status update" link
- [ ] Given a public repo below Level 2, when its page is built, then it has a "Request standard adoption" link
- [ ] Given a link, when followed, then it opens GitHub's new-issue form in that repo with a title and body from a fixed template, URL-encoded, and changes nothing by itself
- [ ] Given a private repo, when its page is built, then it has no request links

**Notes:** Non-goals: the dashboard never changes other repos; a link only opens a pre-filled issue that the reader submits.
---

## Non-functional requirements

| ID | Category | Requirement (measurable) | How verified | Status |
|---|---|---|---|---|
| NFR1 | Performance | A full scan of all in-scope repos finishes in under 5 minutes on GitHub Actions and makes fewer than 1,000 GitHub API requests | Timed run and a request count in the run log, each phase end | Met (2026-11-17, on GitHub Actions: 84 requests, 20.6 s for 17 repos) |
| NFR2 | Security | No known high-severity vulnerabilities in dependencies | Dependency audit + Dependabot, each phase end (`security.md`) | Met (2026-11-17: `pip-audit` clean; Dependabot alerts are off, the owner's call) |
| NFR3 | Accessibility | Meets WCAG 2.2 AA | Manual pass per `accessibility.md` | Not met yet |
| NFR4 | Reliability | The page rebuilds daily with no manual steps for 30 days in a row; a failed run never replaces the last good page, and a partial run is published with the failed repos flagged | Forced-failure test (F3.3) in Phase 2; 30-day run log in Phase 4 | Not met yet (forced-failure test passed 2026-11-17; the 30-day run log is Phase 4) |
| NFR5 | Privacy | For private repos, only the allow-list fields reach anything published or the Action logs: the leak test's canary values appear in 0 output files and 0 log lines, and the token appears in none | Leak test (S2.1.2, S2.1.3, then F2.2) on every test run | Met for scan output and logs (2026-11-17: leak tests pass; first real run's logs and private rows checked); the report and page come with F2.2 |
| NFR6 | Cost | $0 per month: free tiers only (the standard's `cost.md` is not needed) | Any new cost needs a logged decision in `decisions.md` | Met (2026-11-17: no paid service or dependency; no cost decisions logged) |
| NFR7 | Performance | The dashboard page loads in under 2 seconds on a typical connection, with a total page weight under 500 KB | Lighthouse run on the published page, Phase 3 end | Not met yet |

**Statuses:** `Not met yet` · `Met` (with date last verified) · `At risk`

## Bugs

None logged yet.

| ID | Title | Found in | Severity | Status | Test |
|---|---|---|---|---|---|
