# Security

This project's threat model and security setup. The rules are in the
standard's `security.md`; this file records what applies here. Review it at
the end of each phase, and when a change adds a component or a new way in.

## Threat model (lite)

First pass 2026-11-13 (Phase 0), confirmed by the owner.

**1. What are we building?** A public, read-only GitHub Pages dashboard,
rebuilt daily by a GitHub Action that reads all in-scope repos, private
ones included, with a read-only token.

**2. What can go wrong?**

| # | Asset (worth protecting) | Entry point (how it could be reached) | What could go wrong | Likelihood | Impact |
|---|---|---|---|---|---|
| T1 | Private repo details | Published output, the report, the page, the Action logs (public on a public repo), error messages | A field off the allow-list, or file content in an exception, gets published or logged | Med | High |
| T2 | The read token | Logs, commits, pull requests from forks, a compromised third-party Action | Someone gets read access to the owner's private repos | Low | High |
| T3 | People viewing the page | Text from public repos' `portfolio.json` (summary, risks, call-outs) rendered as HTML | Script injected into the owner's public site | Low | Med |
| T4 | The scan run | A malformed or huge `portfolio.json`, or unexpected API responses | The run crashes, or shows made-up values | Med | Low |
| T5 | Trust in the page | Scheduled workflows switched off after 60 days without activity, an expired token, owners who stop reporting | The page looks current but isn't | Med | Med |
| T6 | Private details in public git history | How the output gets published (`decisions.md`, still open) | Committed output stays in the repo's history for good | Med | High |
| T7 | The owner's machine and the Action | Dependencies | A vulnerable or look-alike package runs with our permissions | Low | High |

**3. What are we doing about it?**

- **T1:** the allow-list filter in `privacy/` is the only component that
  writes scan output (S2.1.1, S2.1.2). A leak test plants canary values in
  a fixture private repo and fails if any reach output files or logs, at
  every log level (S2.1.2, S2.1.3), later extended to the report and the
  page (F2.2). Errors log only the repo name and the error type (S2.1.3).
  NFR5.
- **T2:** a fine-grained, read-only token (Contents and Metadata: read)
  limited to the selected repos, with an expiry date, stored as an
  encrypted Actions secret; it never appears in logs (S2.1.3); a renewal
  reminder (F3.3). New, for F3.2's stories: workflows set minimal
  `permissions:`, never run on `pull_request_target`, and pin third-party
  Actions to a full commit SHA.
- **T3:** pages are rendered with Jinja2 and auto-escaping on (tech stack,
  `architecture.md`), never as raw HTML; request links are built from a
  fixed template with URL encoding (F4.4).
- **T4:** `portfolio.json` is validated against the schema, files over 1 MB
  aren't parsed, and problems are recorded without quoting the content
  (S1.3.1). A repo that fails shows as "could not scan" while the others
  publish (`decisions.md`, "Scan failure").
- **T5:** the page shows when it was last updated; stale reports are
  flagged (S1, in S1.2.3); a failure alert, a keep-alive and the token
  renewal reminder (F3.3). NFR4.
- **T6:** new constraint on the Phase 2 publishing decision: only filtered
  scan output may ever be committed or deployed, and deploying a Pages
  artifact is preferred over committing output (`decisions.md`, "How the
  output gets published").
- **T7:** pinned requirements, `pip-audit` at each phase end (NFR2),
  Dependabot alerts (a Phase 0 setup task).

**4. Did it work?** Not yet: there's no code. The token test closes Phase
0 (an Action reads one private repo and logs nothing); the leak test
arrives in Phase 1.

## Personal data

The owner's name (the `owner` and `sponsor` fields) appears on the page for
public repos, by the owner's choice. Private rows don't carry it (the
allow-list in `decisions.md`). Nothing else personal is stored: there is no
database, and each scan starts fresh.

## GitHub setup (GitHub only)

Turning these on is the user's call. Record what's on:

- [ ] Dependabot alerts
- [ ] Dependabot security updates
- [ ] Secret scanning and push protection
- [ ] `main` protected (PR required, no force pushes)
