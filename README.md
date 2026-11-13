# portfolio-dashboard

A public, read-only dashboard of my GitHub project portfolio: what each active
project is, how healthy it is, what needs attention, and whether it follows my
[project standard](https://github.com/flegaspi700/pmo-project-standardization).
It is rebuilt daily as a static GitHub Pages site.

## Project target (current)

**In:** the 13 non-fork repos pushed to since 2026-01-01, with limited detail for private
ones; a daily scan with JSON output, a Markdown report, and a static page with
summary tiles, a sortable table and per-repo pages; link buttons that open a
pre-filled GitHub issue for the owner.

**Out:** changing other repos, automated update PRs, a backend or sign-in,
history and trends, and older repos. See `docs/requirements.md` → Non-goals.

## How this project is run

It follows the
[PMO project standard](https://github.com/flegaspi700/pmo-project-standardization/tree/v2.0.0/standard):

- [`docs/requirements.md`](docs/requirements.md): the vision, phases,
  epics, features and stories
- [`docs/architecture.md`](docs/architecture.md): design, layout, tech
  stack and terms
- [`docs/decisions.md`](docs/decisions.md): design decisions and why
- [`docs/session-log.md`](docs/session-log.md): notes from each working
  session
- [`portfolio.json`](portfolio.json): current status, for the portfolio
  dashboard
- [`AGENTS.md`](AGENTS.md): instructions for AI coding agents, including
  the commands to set up, run and test
