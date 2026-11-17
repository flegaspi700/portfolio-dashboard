"""A fake GitHub for tests that run the whole scan (S1.4.1, S2.1.2).

`FakeGitHub` is a fetch function: it answers every API path the scan uses
(the standard's check registry and schema, the token's user, the repo
listing, and each
repo's facts, PRs, file tree, blobs and commit history) from plain Python
data. No network. The registry is made up but shaped like spec version 2.
"""

import base64
import json
from email.message import Message
from urllib.error import HTTPError
from urllib.parse import quote

from scan.checks import STANDARD_REPO

OWNER = "owner"


SCHEMA = {
    "type": "object",
    "required": ["schema", "name", "health"],
    "properties": {
        "schema": {"const": 1},
        "name": {"type": "string"},
        "health": {"enum": ["green", "amber", "red", "not-reported"]},
        "updated": {"type": ["string", "null"]},
    },
}


REGISTRY = {
    "version": 2,
    "levels": {"reporting": ["C4"], "adopted": ["C4", "C2", "C8"]},
    "checks": [
        {
            "id": "C8",
            "severity": "required",
            "required_from": "2026-12-13",
            "kind": "contains",
            "path": "AGENTS.md",
            "pattern": r"\*\*Standard:\*\* pmo-project-standardization v\d",
        },
        {
            "id": "C2",
            "severity": "required",
            "required_from": "2026-11-09",
            "kind": "contains",
            "path": "AGENTS.md",
            "pattern": r"\*\*Hosting: (local|github)\*\*",
        },
        {
            "id": "C4",
            "severity": "required",
            "required_from": "2026-11-24",
            "kind": "schema",
            "path": "portfolio.json",
            "schema": "portfolio.schema.json",
        },
        {
            "id": "C10",
            "severity": "required",
            "required_from": "2026-12-13",
            "kind": "contains",
            "path": "AGENTS.md",
            "pattern": r"\*\*Standard:\*\* pmo-project-standardization v2\.",
        },
    ],
}


def http_error(code):
    return HTTPError("url", code, "error", Message(), None)


def encoded(text):
    return base64.b64encode(text.encode("utf-8")).decode()


class FakeGitHub:
    """A fetch function over made-up repos.

    `repos` maps a name to a dict with any of: `files` (path -> text),
    `visibility`, `pushed`, `created`, `adopted` (first portfolio.json
    commit), `description`, `language`, `branch`, `topics`, `empty` (no
    default branch) and `fail` (a path fragment whose
    requests raise HTTP 403). `fail_listing` and `fail_registry` raise on
    those requests. Every path asked for is kept in `requested`.
    """

    def __init__(self, repos, fail_listing=None, fail_registry=False):
        self.repos = repos
        self.fail_listing = fail_listing
        self.fail_registry = fail_registry
        self.requested = []

    def __call__(self, path):
        self.requested.append(path)
        standard = f"/repos/{STANDARD_REPO}/contents/spec/"
        if path.startswith(standard):
            if self.fail_registry:
                raise http_error(401)
            name = path.removeprefix(standard)
            document = REGISTRY if name == "compliance-checks.json" else SCHEMA
            return {"content": encoded(json.dumps(document))}
        if path == "/user":
            return {"login": OWNER}
        if path.startswith("/user/repos"):
            if self.fail_listing:
                raise self.fail_listing
            return self._listing() if path.endswith("&page=1") else []

        name, rest = path.removeprefix(f"/repos/{OWNER}/").partition("/")[::2]
        repo = self.repos[name]
        if repo.get("fail") and repo["fail"] in path:
            raise http_error(403)
        files = repo.get("files", {})
        if rest == "":
            return {
                "name": name,
                "pushed_at": repo.get("pushed", "2026-11-28T10:00:00Z"),
                "created_at": repo.get("created", "2025-03-01T10:00:00Z"),
                "language": repo.get("language", "Python"),
                "description": repo.get("description", "made up"),
                "default_branch": None if repo.get("empty") else self._branch(repo),
                "open_issues_count": 2,
            }
        if rest.startswith("pulls"):
            return []
        if rest.startswith(f"git/trees/{quote(self._branch(repo), safe='')}"):
            return {
                "tree": [
                    {"path": p, "type": "blob", "sha": p, "size": len(t)}
                    for p, t in files.items()
                ],
                "truncated": False,
            }
        if rest.startswith("git/blobs/"):
            return {"content": encoded(files[rest.removeprefix("git/blobs/")])}
        if rest.startswith("commits"):
            if not path.endswith("&page=1") or "adopted" not in repo:
                return []
            return [{"commit": {"committer": {"date": repo["adopted"]}}}]
        raise AssertionError(f"unexpected path {path}")

    @staticmethod
    def _branch(repo):
        return repo.get("branch", "main")

    def _listing(self):
        return [
            {
                "name": name,
                "visibility": repo.get("visibility", "public"),
                "archived": False,
                "fork": False,
                "topics": repo.get("topics", []),
                "pushed_at": repo.get("pushed", "2026-11-28T10:00:00Z"),
            }
            for name, repo in self.repos.items()
        ]
