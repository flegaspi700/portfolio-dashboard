# Vision

Why this project exists. Keep it to one page — if it needs more, the
project is probably two projects. Everything in `01-requirements.md` should
trace back to a goal here; if something doesn't, question whether it
belongs.

## Problem

Nobody can see the state of my GitHub projects in one place. To find out
what a project is, who owns it, how healthy it is, what its risks are, or
whether it follows my project standard, you have to open each repo and read
its docs. So gaps stay hidden, and someone reviewing my work, such as a
hiring manager, has no quick way to see how I run a portfolio of projects.

## Who it's for

- **Primary (showcase):** a hiring manager or senior reviewer looking at my
  work. They have a few minutes, want the overall picture first, and today
  have to read through individual repos to judge how I work.
- **Also:** me, as owner of the portfolio. I need to see which projects need
  attention and which are behind the standard, and today I'd have to check
  each repo by hand.
- **Designed as if** a portfolio manager or executive uses it: it reads at a
  glance and lets you drill down when you want more.

## Why build it

Mainly as a portfolio piece: to show a hiring manager that I can define a
project management standard and also apply it and report on it across real
projects, using AI-assisted development. The second reason is practical: I
want a real view of my own projects, and building it will push me to move
more of them onto the standard.

"Good enough" means a page I'd be happy to send a hiring manager, built on
real data and refreshed automatically, and one I actually check myself. It
doesn't need to be a full PMO product.

## Goals

Numbered so epics can reference them (`01-requirements.md` → "Serves: G1").

- **G1:** A reviewer can understand the state of my portfolio within a few
  minutes, starting from one link: what the projects are, how healthy they
  are, and what needs attention.
- **G2:** I can see each week which projects need my attention and which are
  behind the standard, without opening each repo.
- **G3:** The view stays current with no manual upkeep beyond the status each
  project's owner reports.
- **G4:** Publishing it publicly never exposes details of my private repos.

## Success looks like

How you'll know it worked. Measurable where possible.

- A first-time reader can say, within 3 minutes and without help, how healthy
  the portfolio is and which project needs attention first.
- All 12 active repos appear on the page, and at least 4 are on the standard
  (Level 2 or higher) with real status data.
- The page rebuilds daily with no manual steps for 30 days straight, and
  shows when it was last updated.
- An automated test confirms that nothing beyond the allowed fields for
  private repos reaches the published page or the Action logs.
- I check it at least weekly for a month instead of going repo by repo.
- I'm happy to put the link on my resume or send it to a hiring manager.

## Non-goals

What this project deliberately won't do — saying it upfront stops scope
creep, including from AI agents.

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
- **No coverage of older repos in v1.** Forks and repos not pushed to in 2026
  are left out, or counted in a single summary line.

## Constraints

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

## Assumptions and risks

- **Assumption:** the page will look worthwhile with real data, even though
  few repos are on the standard yet. → Check first: run
  `check-compliance.ps1` on all 12 repos and hand-build one static mock. If
  it doesn't look good enough to send, move more repos onto the standard
  before building further.
- **Assumption:** `check-compliance.ps1` can run inside a GitHub Action, since
  it was built as a local tool. → Check in the first scan story.
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
