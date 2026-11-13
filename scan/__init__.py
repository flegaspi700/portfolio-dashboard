"""The scan component: reads the in-scope repos over the GitHub API and
works out their facts, compliance and reported status.

Never writes to disk; only `privacy/` writes scan output
(docs/architecture.md, Layout). Package created for S1.1.1.
"""
