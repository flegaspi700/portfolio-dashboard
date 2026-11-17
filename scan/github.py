"""The real fetch function: the one place the scan talks to GitHub.

Part of `scan/`. `main.py` calls `make_fetch` with the read-only token
(`PORTFOLIO_READ_TOKEN`, docs/security.md T2) and passes the result to
`scan/result.py`, which hands it to every reader. Tests pass fakes instead
(docs/architecture.md: logic in `scan/` takes a fetch function, so only
this module touches the network).

Each call is one GET to the GitHub REST API, returning the parsed JSON
body. Errors aren't retried here: an API error or rate limit is raised as
urllib's HTTPError, and a timeout or network failure as another OSError,
so the reader turns it into a failed repo or the run fails
(S1.1.2, S1.4.1). `token_expiry` reads the token's expiry date from the
last response's headers, for the renewal reminder. Built for S1.4.2;
expiry for S3.3.3.
"""

import json
import urllib.request
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any

from scan.repos import Fetch

API_ROOT = "https://api.github.com"
API_VERSION = "2022-11-28"
EXPIRY_HEADER = "github-authentication-token-expiration"

# Guessed, not measured: GitHub normally answers in well under a second, so
# 30 s only cuts off a request that has hung. The token-check workflow
# (Phase 0) used the same value.
TIMEOUT_SECONDS = 30

Opener = Callable[..., Any]


def make_fetch(token: str, opener: Opener = urllib.request.urlopen) -> Fetch:
    """A fetch function that GETs an API path, such as "/user", from
    GitHub with `token` and returns the parsed JSON.

    Only paths starting with a single "/" are fetched, so the token is
    never sent anywhere but api.github.com; anything else raises
    ValueError. Raises ValueError if `token` is empty.
    """
    if not token:
        raise ValueError("PORTFOLIO_READ_TOKEN is empty: the scan needs the token.")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
    }

    def fetch(path: str) -> Any:
        if not path.startswith("/") or path.startswith("//"):
            raise ValueError("Only GitHub API paths starting with '/' are fetched.")
        request = urllib.request.Request(API_ROOT + path, headers=headers)
        with opener(request, timeout=TIMEOUT_SECONDS) as response:
            fetch.last_headers = response.headers
            return json.loads(response.read())

    # The last response's headers, for the token's expiry date (S3.3.3).
    fetch.last_headers = {}
    return fetch


def token_expiry(headers: Mapping[str, str] | None) -> datetime | None:
    """When the token expires, from the header GitHub adds to answers to a
    personal access token, such as "2027-02-11 21:50:00 UTC", in UTC.

    None when there is no such header (a token that never expires) or it
    can't be read: a wrong date is worse than none.
    """
    value = (headers or {}).get(EXPIRY_HEADER)
    if not value:
        return None
    try:
        expires = datetime.strptime(
            value.replace(" UTC", " +0000"), "%Y-%m-%d %H:%M:%S %z"
        )
    except ValueError:
        return None
    return expires.astimezone(UTC)
