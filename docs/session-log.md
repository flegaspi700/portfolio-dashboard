# Session log

A handoff note at the end of every working session, so the next one can
pick up without rereading everything. Newest first. Entry format: the
standard's `sessions.md`.

Entries before 2026-11-13 were written under the v1 template and refer to
its numbered docs. Where they live now: `00`, `01`, `04` → `requirements.md`;
`02`, `03`, `06` (layout, naming), `11` → `architecture.md`; `05` →
`decisions.md`; `10` → `session-log.md`; `14`, `15` → `security.md`,
`accessibility.md`; `06`, `07`, `13` (the rules) → the standard's
`coding.md`, `testing.md`, `git.md`.

---

## 2026-11-18 — Phases 2 and 3 closed; E4 and E2 built; rollout done

**Worked on:** S4.1.1, S4.1.2, S4.1.3, S4.2.1, S4.3.1, S4.4.1, S2.2.1, B1, Phase 2 and Phase 3 close, Phase 4 rollout

**Time spent:** about 3.5h, estimated from the first check (09:30 local) to this entry (13:00). Correct it if that's off.

**Changed:**
- `report/` — S4.1.1: `python -m report` builds the whole site in `output/site/` (our own `index.html` with Jinja2 3.1.6, auto-escaping on; the report renamed `report.md`); the workflow uploads it as it is, no Jekyll. Built in `report/`, not `site/`: `site` is a standard-library module. PR #34
- `report/page.py`, `templates/` — S4.1.2 tiles, scan time, partial flag, 36-hour old-data notice, levels explained; S4.1.3 "Needs attention first" (logged tiers, allow-list fields only). PR #34
- `report/` — S4.2.1: sortable repo table (header buttons added by script, `aria-sort`, missing values last). PR #35
- `report/`, `scan/result.py`, `privacy/allow_list.py` — S4.3.1: a page per repo at `repos/<slug>.html`; the scan output now carries the registry's checks (decision logged: "Check titles and fixes in the scan output"); one same-site `style.css` keeps a 300-repo site under 500 KB (the owner's choice). PR #36
- same — S4.4.1: request links on public repo pages; the scan output carries the owner's account name. PR #37
- `docs/` — Phase 2 closed: the first scheduled run (44333809359) ran unattended, though GitHub started it 9 h late. PR #38
- `tests/privacy/test_site_leak.py` — S2.2.1: leak test on every built file; AC2 read as a filter passing private rows as public (the owner's choice). F2.2 and E2 done; NFR5 met. PR #39
- `docs/accessibility.md` — the page's WCAG 2.2 AA checklist and pass; found B1 (reflow at 320 px), fixed in `style.css` (`fit-content(40%)`). PR #41 (it carried #40's commit, so #40 was closed)
- `docs/` — Phase 3 closed: Lighthouse Accessibility 100 and Performance 99, the owner's Narrator pass, F4.4 and F4.1 steps 1-4 pass; NFR3 and NFR7 met; Phase 4 active. PR #42
- Rollout (in other repos, by the owner): `/report` in 3 private Level 3 repos; with one other public repo and this one, 5 repos are at Level 3 with real health. Run 44363519631 put it live.
- `docs/requirements.md` — rollout task ticked; this entry.

**Stopped at:** All 24 stories done, 0 open bugs, 409 tests pass, Ruff clean, `pip-audit` clean. NFR1-3 and NFR5-7 met. Phase 4 is active: the rollout is done; the 30-day unattended count runs from 2026-11-18 to 2026-12-17 at the earliest. F4.1 and E4 stay In progress until the first-reader test.

**Next step:** Run the first-reader test (`docs/manual-tests.md`, F4.1, step 5) with someone who hasn't seen the page; on a pass, mark F4.1 and E4 Done. Meanwhile check the page weekly and let the daily runs count; a failure email means a run to look at.

**Open questions:**
- Dependabot alerts are still off; turning them on is the owner's call.
- Protect `main` (PR required, no force pushes)? Optional, the owner's call.
- The scheduled run started 9 h late on 2026-11-18; if it keeps happening, move the cron off the hour (`17 6 * * *`).
- Lighthouse's Best Practices 96 (no favicon, so a 404) and SEO 90 (no meta description) aren't NFRs; fix them as a small change?
- Carried over: `check-compliance.ps1` also passes top-level type errors, so C4 differs from it in a second way. Widen the logged exception, or raise a fix in `pmo-project-standardization`?
- Merged branches (9, listed by `git branch --no-merged` because of squash merges) can be deleted locally and on GitHub.

---

## 2026-11-17 — Phase 1 closed; E3 built and live; Phase 3 prepared

**Worked on:** S1.4.2, Phase 1 close, Phase 2 (S3.1.1, S3.2.1, S3.3.1, S3.3.2, S3.3.3), Phase 3 prep

**Time spent:** about 1h, estimated from commit times (after the earlier entry today). Correct it if that's off.

**Changed:**
- `scan/github.py`, `main.py`, `.env.example` — S1.4.2: the real fetch function and `main.py`; `.env` read with the standard library. The token needed Pull requests: read (GitHub refused all 13 private PR lists without it); the owner added it. First real run: 17 of 58 repos in scope, none failed, 86 requests, 28 s; levels matched `check-compliance.ps1` on 12 of 12 local clones. E1 done. PR #24
- `docs/requirements.md`, `portfolio.json` — Phase 1 closed (exit criteria met on real data; NFR2, NFR5 for output and logs, NFR6 met); `portfolio.json` set to active, phase 2, health green by the owner. PR #25
- `docs/decisions.md` — "How the output gets published": deploy a Pages artifact, nothing committed. Phase 2 stories written and approved. PR #26
- `report/` — S3.1.1: Markdown report from `output/scan.json` only, no free text, everything escaped; `python -m report`. PR #27
- `.github/workflows/publish.yml`, `tests/test_workflows.py`, `docs/manual-tests.md` — S3.2.1: daily 06:00 UTC scan, report and Pages deploy; partial deploys then fails, failed deploys nothing. PR #28
- `publish.yml`, `scan/github.py`, `main.py` — S3.3.1 forced-failure input; S3.3.2 keep-alive job (re-enables the workflow through the API); S3.3.3 token-expiry reminder (fails the run within 14 days of expiry). PR #29 merged into F3.2's branch by mistake (I said GitHub would retarget it; it only does when the base branch is deleted); the same commit was cherry-picked to `main` as PR #30
- `docs/manual-tests.md` — live checks passed: run 44142627009 deployed https://flegaspi700.github.io/portfolio-dashboard/ with counts-only logs (84 requests, 20.6 s: NFR1 met on Actions); forced-failure run 44142953144 skipped the deploy, kept the last good page, and the owner got the email. E3 done. PR #31
- `docs/decisions.md`, `docs/requirements.md` — "Needs attention first" ranking: fixed tiers on allow-list fields, with the reason shown. Seven Phase 3 stories approved and Ready; Phase 4 timing notes. PR #32
- `portfolio.json` — progress 17 of 24 stories

**Stopped at:** E1, E2's F2.1 and E3 done and live; 319 tests pass, Ruff clean. Phase 2 is still Active: its last exit criterion ("the daily run needs no manual steps") waits for the first scheduled run, 2026-11-18 06:00 UTC. Phase 3 is ready to build (S4.1.1 to S4.4.1, S2.2.1).

**Next step:** check the 2026-11-18 06:00 UTC scheduled `publish` run passed on its own (`gh run list --workflow publish.yml`); if so, close Phase 2 (NFR statuses, `pip-audit`, Phases table, `portfolio.json` phase 3). Then `/story E4` (Jinja2 gets pinned and audited at S4.1.1), then F2.2.

**Open questions:**
- Phase 4 rollout can start now and is the owner's: run `/report` in four of the five Level 3 repos so they report real health (also gives the Phase 3 page real data).
- Dependabot alerts are still off (secret scanning is on); turning them on is the owner's call.
- Risks, blockers and call-outs in `portfolio.json` are empty; say if any should be listed.
- Carried over: `check-compliance.ps1` also passes top-level type errors, so C4 differs from it in a second way. Widen the logged exception, or raise a fix in `pmo-project-standardization`?

---

## 2026-11-17 — S1.2.2 to S2.1.3 done: scan, filter, output and safe logs

**Worked on:** S1.2.2, S1.2.3, S1.2.4, S1.3.1, S1.4.1, S2.1.1, S2.1.2, S2.1.3; added S1.4.2

**Time spent:** about 1h, estimated from commit times. Correct it if that's off.

**Changed:**
- `scan/levels.py` — S1.2.2: compliance level from check results, using the registry's `levels` sets (criteria reworded from v1 IDs, owner's choice). Matched `check-compliance.ps1` in 22 of 22 local comparisons. PR #15
- `scan/warnings.py` — S1.2.3: scan warnings S1-S3; the S2 adoption date is read only when S2 could fire (decision logged). PR #16
- `scan/files.py`, `scan/checks.py` — S1.2.4: one tree request plus one per content-checked file; unread files pass `exists` only (decision logged); two criteria added by the owner. Live read-only check on 2 public repos matched the script. PR #17
- `scan/status.py` — S1.3.1: validated `portfolio.json` or `not-reported`, problems without content. Agreed with C4 on 9 local files. PR #18
- `scan/result.py` — S1.4.1: `run_scan` and the scan result (complete, partial, failed); F1.2 and F1.3 marked Done. PR #19
- `privacy/allow_list.py` — S2.1.1: private rows cut to the nine allow-list fields. PR #20
- `privacy/output.py`, `tests/fake_github.py` — S2.1.2: `output/scan.json` (git-ignored, decision logged), exit code, leak test with canaries in 19 places. PR #21
- `privacy/safe_logging.py` — S2.1.3: exceptions log only their type; fixed a registry error's text reaching the logs; F2.1 marked Done. PR #22
- `docs/requirements.md` — new story S1.4.2 (real fetch function and `main.py`), draft criteria; its exit-code criterion defers to S2.1.2
- `docs/decisions.md` — four entries: S2 adoption date read only when needed; unreadable files don't pass content checks; scan output as one JSON file (plus the S1.4.2/S2.1.2 split)
- `docs/security.md`, `docs/architecture.md` — kept in step with the code
- `portfolio.json` — progress 11 of 12 stories

**Stopped at:** all eight stories merged on `main`; 233 tests pass, coverage 100% for `scan/` and `privacy/`, Ruff clean. Nothing has run against real GitHub yet: there is no real fetch function and no `main.py`. Phase 1's only open story is S1.4.2.

**Next step:** the owner reviews S1.4.2's draft criteria (`docs/requirements.md` -> S1.4.2), puts `PORTFOLIO_READ_TOKEN` in `.env`, and decides on Pull requests: read for the token; then `/story S1.4.2` and the first real run. After that, close Phase 1 (exit criteria, `pip-audit`, NFR statuses), then the Phase 2 publishing decision, E3's stories, and `/story E3`.

**Open questions:**
- Does the token need Pull requests: read? `read_facts` lists open PRs, and `security.md` lists Contents and Metadata only; without it, private repos would likely be "could not scan".
- S1.4.2's criteria are an agent draft: review before it starts. Also open: where the owner login comes from (config or `GET /user`).
- Carried over: `check-compliance.ps1` also passes top-level type errors, so C4 differs from it in a second way. Widen the logged exception, or raise a fix in `pmo-project-standardization`?

---

## 2026-11-14 — S1.1.2 and S1.2.1 done: repo facts and check kinds

**Worked on:** S1.1.2, S1.2.1

**Time spent:** about 0.75h, estimated from commit and file timestamps. Correct it if that's off.

**Changed:**
- `scan/facts.py`, `tests/scan/test_facts.py` — S1.1.2: `read_facts`
  returns last push, created date, language, description, default branch,
  and open issues and PRs counted separately (GitHub's issue count includes
  PRs). Any API error, rate limit or network failure gives a `FailedRead`
  with no values guessed; logs carry no repo names. PR #12, merged
- `scan/checks.py`, `tests/scan/test_checks.py`,
  `tests/scan/fixtures/check_kinds.json` — S1.2.1: `load_registry` reads the
  check registry and its schemas from the standard's default branch and
  stops the run if it can't; the four check kinds give pass, fail or n/a.
  Matching ignores case, like the script's `-match`. Cross-checked with
  `check-compliance.ps1`: 28 of 28 shared fixture results, and all 14 real
  checks on this repo. PR #13, merged
- `docs/decisions.md` — "Read the check registry from the standard's
  default branch" (chosen over the newest tag or a pinned version)
- `docs/requirements.md` — S1.1.2 and S1.2.1 Done; new story S1.2.4 (read
  repo files), because no story fetched repo files
- `docs/architecture.md` — component note; "repo facts" in the glossary
- `portfolio.json` — progress 3 of 11 stories

**Stopped at:** S1.1.1, S1.1.2 and S1.2.1 merged on `main`; 80 tests pass,
`scan/` coverage 100%, Ruff clean. Nothing runs against real GitHub yet:
there is no real fetch function and no `main.py`. The owner chose to keep
the original plan (no early dry-run story), so the first real run comes
with S1.4.1 / F2.1.

**Next step:** `/story S1.2.2` (work out the compliance level from
`evaluate_checks` results and the registry's `levels`, `severity` and
`required_from`).

**Open questions:**
- `check-compliance.ps1` also passes top-level type errors (`"name": 5`),
  not only nested ones, so C4 differs from it in a second way. Widen the
  exception with a new decision entry, or raise a fix in
  `pmo-project-standardization`?
- S1.2.4's acceptance criteria were drafted by the agent: review them
  before it starts.
- Which story builds the real fetch function (with `PORTFOLIO_READ_TOKEN`)
  and `main.py`? Probably S1.4.1 or S2.1.2; decide when it comes up.
- The local `.env` needs `PORTFOLIO_READ_TOKEN` (the read-only GitHub
  token) before the first real run; list the name in `.env.example` then.

---

## 2026-11-13 — S1.1.1 done: select in-scope repos

**Worked on:** S1.1.1

**Time spent:** about 0.3h, estimated. Correct it if that's off.

**Changed:**
- `scan/repos.py` — `list_repos(fetch)` reads every page of
  `/user/repos?affiliation=owner` through a fetch function passed in;
  `select_in_scope` keeps repos that aren't archived, forks or tagged
  `portfolio-exclude` and were pushed on or after 2026-01-01, as
  `InScopeRepo` records. Odd visibility counts as private; logs hold counts
  only (NFR5)
- `scan/__init__.py` — package header note
- `tests/scan/test_repos.py` — 12 tests, seen failing on stubs first, then
  passing; fake fetch, no network
- `docs/requirements.md` — S1.1.1 Done; `docs/architecture.md` — diagram
  note says `scan/repos.py` exists
- PR #10, squash-merged by the agent at the owner's request (an exception
  to "the user merges"); branch deleted locally and on GitHub

**Stopped at:** S1.1.1 merged on `main`. 14 tests pass, `scan/` coverage
100%, Ruff clean. Two small calls in the code: a repo with no push date is
out of scope, and paging stops at the first empty page (one extra request).
Not verified yet: how the fine-grained token answers
`/user/repos?affiliation=owner` (all public repos, or only the ones it was
given). The first real call shows it.

**Next step:** `/story S1.1.2` (read repo facts). Check the real listing's
counts against the 17 in scope once a real fetch function exists (S1.4.1 at
the latest).

**Open questions:** None

---

## 2026-11-13 — Token test passed; Phase 0 done

**Worked on:** Phase 0, the token test

**Time spent:** about 0.3h

**Changed:**
- `.github/workflows/token-check.yml` (PR #8) — manual workflow that reads
  one repo's `portfolio.json` with the read token and logs no content
- `docs/requirements.md` — token task ticked; Phase 0 marked Done
- `docs/security.md` — "Did it work?" records the token test

**Stopped at:** Phase 0 done. The owner created a fine-grained, read-only
token (one private repo, Contents read, 90 days) and stored it as
`PORTFOLIO_READ_TOKEN`. The first run failed safely: the secret had been
saved empty, because `gh secret set` can't prompt without a terminal; it
was stored again through the website. The second run passed, and the
public log shows the token masked and none of the file's content.

**Next step:** Phase 1, `/story S1.1.1` (select in-scope repos). Give the
token access to the other in-scope private repos when the scan needs them.

**Open questions:** None

---

## 2026-11-13 — Environment set up

**Worked on:** Phase 0, the environment and test-folder tasks

**Time spent:** about 0.2h

**Changed:**
- `requirements.txt`, `requirements-dev.txt` — the pins from
  `docs/architecture.md` → Tech stack (jsonschema 4.26.0; pytest 9.2.0,
  pytest-cov 7.1.0, ruff 0.17.3, pip-audit 2.10.1)
- `tests/test_environment.py` — checks the venv runs Python 3.13 and every
  installed package matches its pin; seen failing with a wrong pin first
- `docs/requirements.md` — the two Phase 0 tasks ticked

**Stopped at:** the AGENTS.md commands work: tests 2 passed, Ruff lint and
format clean, `pip-audit` found no known vulnerabilities. Coverage reports
"no data" until `scan/` and `privacy/` exist; `main.py` comes with the
first story that wires components (S1.4.1), so the Run command has nothing
to run yet.

**Next step:** the token test (the owner creates a fine-grained read-only
token and stores it as a repo secret; then a workflow reads one private
repo and logs nothing).

**Open questions:** None

---

## 2026-11-13 — Threat model, first pass

**Worked on:** Phase 0, the threat model task

**Time spent:** about 0.2h

**Changed:**
- `docs/security.md` — threat model T1–T7 with mitigations mapped to
  stories, NFRs and decisions; personal data section
- `docs/decisions.md` — a constraint added to the open "How the output gets
  published" decision (T6: only filtered output may be committed or
  deployed)
- `docs/requirements.md` — F3.2 notes the workflow rules for T2; threat
  model task ticked

**Stopped at:** compliance level 3, no warnings. Phase 0 still needs the
environment and test folders, and the token test.

**Next step:** set up the environment and one passing test.

**Open questions:** None

---

## 2026-11-13 — NFRs filled in; scope wording no longer counts repos

**Worked on:** Phase 0, the NFR task

**Time spent:** about 0.1h

**Changed:**
- `docs/requirements.md` — NFR1 (scan under 5 minutes, under 1,000 API
  requests), NFR4 (30 days unattended; a failed run never replaces the last
  good page), NFR5 (allow-list only; 0 canary values or token in output and
  logs), and a new NFR7 (page under 2 s and 500 KB); NFR task ticked.
  "13 repos" became "all in-scope repos" in the success criteria, Phase 1
  exit criteria and F1.1, as the owner chose (the scope rule gives 17 now)
- `README.md` — the same change in Project target

**Stopped at:** compliance level 3, no warnings. Phase 0 still needs the
threat model, the environment and test folders, and the token test.

**Next step:** the threat model in `docs/security.md`.

**Open questions:** None

---

## 2026-11-13 — Go decision

**Worked on:** Phase 0, the go/no-go task

**Time spent:** about 0.1h

**Changed:**
- `docs/decisions.md` — "Go: build the dashboard", with the counts behind it
  (17 in scope; 5 at Level 3, 3 at Level 1, 9 at Level 0)
- `docs/requirements.md` — Phase 0 tasks: compliance run and go/no-go ticked

**Stopped at:** go decided and logged. Phase 0 still needs the token test
(an Action reads one private repo and logs nothing), the threat model, the
NFRs, the environment and test folders.

**Next step:** fill in NFR1, NFR4 and NFR5 in `docs/requirements.md`, then
the threat model in `docs/security.md`.

**Open questions:** change "13 repos" in the success criteria, Phase 1 exit
criteria and F1.1 to "all in-scope repos"? (The scope rule now gives 17.)

---

## 2026-11-13 — Moved to standard v2.0.0

**Worked on:** no story — moving the project from the v1 template to the
shared standard v2.0.0

**Time spent:** not counted toward Phase 0 (standard work)

**Changed:**
- `AGENTS.md` — the v2 file: standard version, commands, core rules, and
  the project's own notes (public repo, hard boundaries, layout)
- `docs/requirements.md` — vision (`00`), requirements (`01`) and plan
  (`04`, now a Phases table plus the open phase tasks) in one file
- `docs/architecture.md` — key decisions and open questions (`02`), layout
  and naming (`06`), tech stack (`03`) and glossary (`11`), plus a planned
  components diagram
- `docs/decisions.md`, `docs/session-log.md` — renamed from `05`, `10`;
  entries unchanged
- `docs/security.md`, `docs/accessibility.md` — the extras for the Phase 0
  threat model and the Phase 3 page; the security doc is still the blank
  template, as `14` was
- Removed: the rest of the numbered docs (the prompt log and status report
  had no entries), `.claude/skills/`, `.github/pull_request_template.md`
- Also committed the 2026-11-02 handoff note and progress counts, left
  uncommitted then

**Stopped at:** compliance level 3 (Current) on v2.0.0; one warning (W3):
NFR1, NFR4 and NFR5 are still template placeholders, an open Phase 0 task.
No code yet, so no tests to run.

**Next step:** unchanged — decide go or no-go. The v2 rollout of other
repos is now under way, which is what the no-go recommendation asked for.

**Open questions:** Go or no-go? Is "most projects predate the standard",
a draft line on the mock, still accurate?

---

## 2026-11-02 — Breakdown, stack choice, and the go/no-go check (paused undecided)

**Worked on:** Phase 0 planning; no stories started.

**Time spent:** about 0.5h, estimated from file timestamps. Correct it if that's off.

**Changed:**
- `docs/01`, `02`, `04`, `05`, `11`, `00`, `AGENTS.md`, `README.md` — epics, features, Phase 1 stories, five-phase plan, scope decisions (PR #1, merged)
- `docs/03`, `05`, `06`, `.gitignore`, `AGENTS.md` — Python 3.13 stack, tools and commands; full schema validation for C4 (PR #2, merged)
- `docs/10-session-log.md`, `portfolio.json` — this entry and refreshed progress (uncommitted)

**Stopped at:** the Phase 0 go/no-go is **undecided**. `check-compliance.ps1` ran on all 13 repos: 2 at Level 3, 11 at Level 0, and 1 of 13 reports real health. A mock page was built outside this repo, because it holds private data. The layout works, but most rows are empty. Recommendation given: no-go for now, moving the rollout ahead of Phase 1. The commands in `AGENTS.md` haven't been run yet, because the environment isn't set up.

**Next step:** decide go or no-go, after looking at the mock (rebuild it if the temp copy is gone). If no-go, pick two repos to move onto the standard, run `/report` here, then rebuild the mock. Log the decision in `05-decisions-log.md` with counts only, because that file is public.

**Open questions:** Go or no-go? If no-go, which two repos go first? Is "most projects predate the standard", a draft line on the mock, accurate? `check-compliance.ps1` still needs full validation in `pmo-project-standardization`.

---
