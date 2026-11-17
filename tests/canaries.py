"""Canary values for leak tests (S2.1.2, S2.1.3, S3.1.1).

A made-up private repo for `tests/fake_github.py` with a different canary
value in each place private text could come from: its description,
language, branch, topic, files, and every free-text `portfolio.json`
field. Its name has no canary, because the allow-list publishes names.
"""

import json

# One canary per field, so a hit says exactly what leaked.
CANARIES = {
    field: f"CANARY-{field}-9d2c"
    for field in (
        "description",
        "language",
        "branch",
        "topic",
        "agents",
        "summary",
        "owner",
        "sponsor",
        "program",
        "health_reason",
        "phase",
        "risk",
        "mitigation",
        "blocker",
        "needs",
        "callout",
        "milestone",
        "requirements",
        "claude",
    )
}


def leaky_portfolio():
    return json.dumps(
        {
            "schema": 1,
            "name": "private-repo",
            "summary": CANARIES["summary"],
            "owner": CANARIES["owner"],
            "sponsor": CANARIES["sponsor"],
            "program": CANARIES["program"],
            "health": "red",
            "health_reason": CANARIES["health_reason"],
            "phase": {"name": CANARIES["phase"]},
            "risks": [
                {"title": CANARIES["risk"], "mitigation": CANARIES["mitigation"]}
            ],
            "blockers": [{"title": CANARIES["blocker"], "needs": CANARIES["needs"]}],
            "callouts": [CANARIES["callout"]],
            "next_milestone": {"name": CANARIES["milestone"]},
            "updated": "2026-11-20",
        }
    )


AGENTS = (
    "**Standard:** pmo-project-standardization v2.0.0\n**Hosting: github**\n"
    + CANARIES["agents"]
)

PRIVATE_REPO = {
    "visibility": "private",
    "description": CANARIES["description"],
    "language": CANARIES["language"],
    "branch": CANARIES["branch"],
    "topics": [CANARIES["topic"]],
    "files": {
        "AGENTS.md": AGENTS,
        "portfolio.json": leaky_portfolio(),
        "docs/requirements.md": CANARIES["requirements"],
        "CLAUDE.md": CANARIES["claude"],
    },
}

PUBLIC_REPO = {"files": {"AGENTS.md": "**Hosting: github**\n"}}
