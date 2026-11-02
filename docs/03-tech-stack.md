# Tech stack

Every dependency in the project should appear here with a reason. If an AI
agent wants to add one that isn't listed, it logs the decision in
`05-decisions-log.md` first.

This doc shows what was *chosen*. For significant choices (language,
framework, storage, anything hard to swap out), the options that were
compared and why the others lost are in the matching
`05-decisions-log.md` entry — link it in the Rationale column.

## Core

| Layer | Choice | Rationale |
|---|---|---|
| Language | Python 3.13 | Default for a batch job with no browser framework. See `05-decisions-log.md` → "Language and stack" |
| GitHub API | Standard library `urllib` | Enough for the calls and paging the scan needs, with no dependency. Tests pass in a fake fetch function. Switch only if a story proves it isn't enough |
| Schema validation | `jsonschema` | Full validation of `portfolio.json` against the standard's schema (check C4). See `05-decisions-log.md` → "Reuse or reimplement the compliance checks" |
| Page | Generated static HTML with a little vanilla JS | Sorting needs no framework. The HTML templating library is added in Phase 3 (see Deferred) |
| Persistence | None between runs | No database (`00-vision.md` → Non-goals). Each scan starts fresh |

## Dev environment

| Tool | Purpose |
|---|---|
| VS Code | Primary editor |
| `ruff format` | Formatting |
| `ruff check` | Linting |
| `pytest` | Tests |
| `pytest-cov` | Coverage report (a hint, no target %) |
| `pip-audit` | Known vulnerabilities in dependencies (`14-security.md`) |
| `venv` | Dependency isolation, in `.venv/` |

## Starting dependencies

Versions confirmed on PyPI on 2026-11-02. Packages these pull in, including the
compiled `rpds-py` under `jsonschema`, get checked when they are first installed.

`requirements.txt`:

```
jsonschema==4.26.0
```

`requirements-dev.txt`:

```
pytest==9.2.0
pytest-cov==7.1.0
ruff==0.17.3
pip-audit==2.10.1
```

## Deferred / not needed yet

- `Jinja2` — add in Phase 3 for the page, because it can auto-escape untrusted text. 3.1.6 is the latest on PyPI, released 2025-03, so run `pip-audit` on it again then.
- `mypy` — `ruff` doesn't check types, so signatures are typed but not enforced. Revisit if type mistakes reach review.
- `requests` and HTTP mocking libraries — not needed while `urllib` and a fake fetch function are enough.
