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
