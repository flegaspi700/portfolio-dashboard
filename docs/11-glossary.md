# Glossary

Project-specific terms, so you, the docs, the code, and AI agents all use
the same word for the same thing. One concept = one term — this is what
keeps names consistent across the codebase (see the naming rules in
`06-coding-conventions.md`).

- Add a term when a new concept appears, in the same change that
  introduces it.
- **Use instead of** lists the synonyms you've ruled out — if one of them
  shows up in code or docs, rename it.
- Keep the table sorted alphabetically.

| Term | Meaning | Use instead of |
|---|---|---|
| allow-list | The fields a private repo may publish: name, visibility, lifecycle, health, compliance level, last activity date, risk count, blocker count, scan status. Anything else is dropped. | "blacklist", "redaction list" |
| canary value | A unique made-up string planted in a fixture private repo. If it shows up in output or logs, something leaked. | "marker", "secret" |
| check registry | `spec/compliance-checks.json` in `pmo-project-standardization`: the machine-readable compliance checks. Read at scan time, never copied here. | "rules file" |
| compliance level | A repo's standing against the standard, worked out by the scan: 0 Not on standard, 1 Reporting, 2 Adopted, 3 Current. | "score", "grade" |
| in-scope repo | A repo the portfolio counts: not archived, not a fork, not tagged `portfolio-exclude`, and pushed since the scan cut-off. | "active repo", "tracked repo" |
| leak test | The automated test that plants canary values in a private repo and fails if any reach output files or logs. | "privacy check" |
| request link | A link on the page that opens a pre-filled GitHub issue for a public repo's owner. It changes nothing by itself. | "action button", "update button" |
| scan | One run that reads all in-scope repos and works out their facts, compliance and status. | "crawl", "sync" |
| scan cut-off | The fixed date 2026-01-01. Repos last pushed before it are out of scope. | "activity window" |
| scan output | The scan result after the allow-list filter: the only form written to disk or published. | "report data" |
| scan result | The in-memory, unfiltered structure a scan assembles, marked complete, partial or failed. Never written to disk. | "raw output" |
| scan warning | A warning that needs GitHub data or dates: S1 stale report, S2 health never reported, S3 required change due soon (`spec/compliance.md`). Not the same as story IDs. | — |
