"""Tests for scan/github.py: the real fetch function (S1.4.2).

No network: `make_fetch` takes the function that opens a request, so these
pass in a fake one that records the request and returns canned bytes or
raises the errors urllib raises.
"""

import io
import json
from email.message import Message
from urllib.error import HTTPError, URLError

import pytest

from scan.facts import error_reason
from scan.github import API_ROOT, TIMEOUT_SECONDS, make_fetch

TOKEN = "github_pat_FAKE0TOKEN0FOR0TESTS0ONLY"


class FakeOpener:
    """Stands in for urllib.request.urlopen: answers `body` (JSON) or
    raises `error`, and records every call."""

    def __init__(self, body=None, error=None):
        self.body = body
        self.error = error
        self.calls = []

    def __call__(self, request, timeout):
        self.calls.append((request, timeout))
        if self.error:
            raise self.error
        return io.BytesIO(json.dumps(self.body).encode("utf-8"))


def test_fetch_asks_github_with_the_token_and_returns_json():
    opener = FakeOpener(body={"login": "owner"})

    result = make_fetch(TOKEN, opener)("/user")

    request, timeout = opener.calls[0]
    assert result == {"login": "owner"}
    assert request.full_url == f"{API_ROOT}/user"
    assert request.get_header("Authorization") == f"Bearer {TOKEN}"
    assert request.get_header("Accept") == "application/vnd.github+json"
    assert request.get_header("X-github-api-version") == "2022-11-28"
    assert timeout == TIMEOUT_SECONDS


def test_timeout_is_30_seconds():
    assert TIMEOUT_SECONDS == 30


@pytest.mark.parametrize(
    "error",
    [TimeoutError("timed out"), URLError(TimeoutError("timed out"))],
    ids=["timeout", "urlopen-timeout"],
)
def test_slow_request_times_out_as_a_network_error(error):
    fetch = make_fetch(TOKEN, FakeOpener(error=error))

    with pytest.raises(OSError) as raised:
        fetch("/user/repos?page=1")

    assert error_reason(raised.value) == "network error"


@pytest.mark.parametrize("code", [401, 403, 404, 429, 500])
def test_api_error_is_raised_once_with_no_retry(code):
    opener = FakeOpener(error=HTTPError("url", code, "error", Message(), None))
    fetch = make_fetch(TOKEN, opener)

    with pytest.raises(HTTPError) as raised:
        fetch("/repos/owner/repo")

    assert raised.value.code == code
    assert len(opener.calls) == 1


@pytest.mark.parametrize(
    "path", ["https://evil.example/steal", "user", "//evil.example/x"]
)
def test_only_api_paths_are_fetched_so_the_token_stays_with_github(path):
    opener = FakeOpener(body={})

    with pytest.raises(ValueError):
        make_fetch(TOKEN, opener)(path)

    assert opener.calls == []


def test_missing_token_is_refused():
    with pytest.raises(ValueError, match="PORTFOLIO_READ_TOKEN"):
        make_fetch("", FakeOpener(body={}))
