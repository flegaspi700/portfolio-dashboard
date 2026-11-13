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
