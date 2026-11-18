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
| T2 | The read token | Logs, commits, pull requests from forks, a compromised third-party Action, the local `.env` (git-ignored) | Someone gets read access to the owner's private repos | Low | High |
| T3 | People viewing the page | Text from public repos' `portfolio.json` (summary, risks, call-outs) rendered as HTML | Script injected into the owner's public site | Low | Med |
| T4 | The scan run | A malformed or huge `portfolio.json`, or unexpected API responses | The run crashes, or shows made-up values | Med | Low |
| T5 | Trust in the page | Scheduled workflows switched off after 60 days without activity, an expired token, owners who stop reporting | The page looks current but isn't | Med | Med |
| T6 | Private details in public git history | How the output gets published (`decisions.md`, "How the output gets published") | Committed output stays in the repo's history for good | Med | High |
| T7 | The owner's machine and the Action | Dependencies | A vulnerable or look-alike package runs with our permissions | Low | High |

**3. What are we doing about it?**

- **T1:** the allow-list filter in `privacy/` is the only component that
  writes scan output (S2.1.1, S2.1.2). A leak test plants canary values in
  a fixture private repo and fails if any reach output files or logs, at
  every log level (S2.1.2, S2.1.3), and to every file of the built site,
  the report and the pages alike (S2.2.1). The repo pages also read private
  rows by the allow-list, a second guard behind the filter (S4.3.1). Errors log only a generic reason or the error type, never
  the error's text; the scan logs no repo names at all, which is stricter
  than the allow-list needs (S2.1.3, `privacy/safe_logging.py`). NFR5.
- **T2:** a fine-grained, read-only token (Contents, Metadata and Pull
  requests: read; Pull requests added 2026-11-17 because the scan counts
  open PRs), with access to every repo the scan reads (13 private on
  2026-11-17), sent only to api.github.com (`scan/github.py`), with an expiry date, stored as an
  encrypted Actions secret; it never appears in logs (S2.1.3); a renewal
  reminder (F3.3). New, for F3.2's stories: workflows set minimal
  `permissions:`, never run on `pull_request_target`, and pin third-party
  Actions to a full commit SHA.
- **T3:** pages are rendered with Jinja2 and auto-escaping on (tech stack,
  `architecture.md`), never as raw HTML (S4.1.1); the page is our own HTML
  with its scripts inline and one same-site stylesheet, so no third-party
  code runs on it (S4.1.1, S4.3.1); request links are built from a fixed
  template with URL encoding and carry no repo text (S4.4.1). Tests feed
  markup through every place public text shows.
- **T4:** `portfolio.json` is validated against the schema, files over 1 MB
  aren't parsed, and problems are recorded without quoting the content
  (S1.3.1). A repo that fails shows as "could not scan" while the others
  publish (`decisions.md`, "Scan failure").
- **T5:** the page shows when it was last updated; stale reports are
  flagged (S1, in S1.2.3); a failure alert, a keep-alive and the token
  renewal reminder (F3.3: each run logs the token's expiry date and fails
  within 14 days of it, so the failure email is the reminder). NFR4.
- **T6:** only filtered scan output may ever be committed or deployed.
  Decided 2026-11-17 (`decisions.md`, "How the output gets published"): the
  `publish` workflow builds the report into a Pages artifact and deploys it,
  committing nothing, and `output/` is git-ignored.
- **T7:** pinned requirements, `pip-audit` at each phase end (NFR2),
  Dependabot alerts (a Phase 0 setup task, still off: the owner's call).
  Jinja2 3.1.6 (and MarkupSafe under it) added in S4.1.1, audited clean on
  2026-11-18.

**4. Did it work?** Token test, 2026-11-13 (closes Phase 0, T1 and T2):
the `token-check` workflow read a private repo's `portfolio.json` from an
Action (HTTP 200, valid JSON). The public run log shows the token masked
(`***`), and none of the file's text values appear in it (6 checked, 0
found; the repo's name appears, which the allow-list publishes anyway).
The first run had failed safely because the secret had been stored empty.
The leak test for scan output and logs is in place (S2.1.2, S2.1.3,
2026-11-17), on fixtures: canaries in 19 places of a private repo, and in
the text of API errors, plus a made-up token, reach no output file and no
log line at DEBUG, INFO or WARNING. The first real run (S1.4.2) checks the
real token's logs. First real run, 2026-11-17 (S1.4.2): the log lines
carried counts only, no repo names or token, and the 9 private rows in
`output/scan.json` held only allow-list fields. Phase 2 review, 2026-11-18:
the first scheduled run's public log carried counts only (T1, T2); the
scan output now also carries the standard's check text and the owner's
account name, both public and holding no repo data (S4.3.1, S4.4.1); no
open secret-scanning alerts.

## Personal data

The owner's name (the `owner` and `sponsor` fields) is in public repos'
scan output by the owner's choice, but the repo pages don't show it (S4.3.1
lists the reported fields they show). The owner's GitHub account name is in
the scan output for request links, and is already public in the site's
address. Private rows don't carry it (the
allow-list in `decisions.md`). Nothing else personal is stored: there is no
database, and each scan starts fresh.

## GitHub setup (GitHub only)

Turning these on is the user's call. Record what's on:

- [ ] Dependabot alerts
- [ ] Dependabot security updates
- [x] Secret scanning and push protection (on; checked 2026-11-17, no open alerts 2026-11-18)
- [ ] `main` protected (PR required, no force pushes)
