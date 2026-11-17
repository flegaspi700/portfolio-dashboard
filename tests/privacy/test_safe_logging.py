"""Tests for privacy/safe_logging.py and the scan's logs (S2.1.3).

The Action logs are public on a public repo, so these run the whole scan,
filter and write with logging set up the way `main.py` will set it up
(`configure_logging`), at every level, and search what was logged for
canary values and a made-up token. The canaries sit in a private repo's
fields and in the text of the errors GitHub's API raises: error messages,
URLs and response reasons are the usual way content reaches a log.
"""

import io
import logging
from email.message import Message
from urllib.error import HTTPError, URLError

import pytest
from fake_github import OWNER, FakeGitHub
from test_output import CANARIES, NOW, PRIVATE_REPO, PUBLIC_REPO

from privacy.output import write_output
from privacy.safe_logging import configure_logging
from scan.result import run_scan

TOKEN = "github_pat_FAKE0TOKEN0FOR0TESTS0ONLY"
SECRETS = [*CANARIES.values(), TOKEN]
URL_CANARY = f"https://api.github.com/repos/{OWNER}/{CANARIES['description']}"


def leaky_http_error(code=403):
    """An HTTPError whose URL, reason and headers carry private text."""
    headers = Message()
    headers["Authorization"] = f"token {TOKEN}"
    return HTTPError(URL_CANARY, code, f"{CANARIES['summary']} {TOKEN}", headers, None)


class LeakyErrors(FakeGitHub):
    """A fake GitHub whose errors carry private text and the token."""

    def __call__(self, path):
        try:
            return super().__call__(path)
        except HTTPError:
            raise leaky_http_error() from None


@pytest.fixture
def log():
    """Logging set up as main.py does it, writing to a string."""
    stream = io.StringIO()
    yield stream
    logging.getLogger().handlers.clear()


def secrets_in(text):
    return [secret for secret in SECRETS if secret in text]


# --- The whole scan, at every level ---


@pytest.mark.parametrize("level", [logging.DEBUG, logging.INFO, logging.WARNING])
def test_canary_scan_logs_nothing_private_at_every_level(level, log, tmp_path):
    configure_logging(level, stream=log)
    repos = {
        "private-repo": PRIVATE_REPO,
        "private-broken": {**PRIVATE_REPO, "fail": "git/trees"},
        "public-repo": PUBLIC_REPO,
    }

    result = run_scan(LeakyErrors(repos), OWNER, NOW)
    write_output(result, tmp_path / "scan.json")

    logged = log.getvalue()
    assert "Could not read a repo's files: HTTP 403" in logged
    assert secrets_in(logged) == []


def test_network_error_text_is_not_logged(log, tmp_path):
    configure_logging(logging.DEBUG, stream=log)

    class Offline(FakeGitHub):
        def __call__(self, path):
            if "/pulls" in path:
                raise URLError(f"{URL_CANARY} {TOKEN}")
            return super().__call__(path)

    result = run_scan(Offline({"a": PRIVATE_REPO, "b": PUBLIC_REPO}), OWNER, NOW)
    write_output(result, tmp_path / "scan.json")

    assert "network error" in log.getvalue()
    assert secrets_in(log.getvalue()) == []


def test_unreadable_registry_error_text_is_not_logged_or_kept(log, tmp_path):
    configure_logging(logging.DEBUG, stream=log)

    class RegistryDown(FakeGitHub):
        def __call__(self, path):
            if "/contents/spec/" in path:
                raise leaky_http_error(401)
            return super().__call__(path)

    result = run_scan(RegistryDown({"a": PRIVATE_REPO}), OWNER, NOW)
    write_output(result, tmp_path / "scan.json")

    assert result.failure == "could not read the check registry: HTTP 401"
    assert secrets_in(log.getvalue()) == []


# --- Exceptions ---


def test_logged_exception_shows_only_its_type(log):
    configure_logging(logging.DEBUG, stream=log)
    try:
        raise ValueError(f"{CANARIES['agents']} at {URL_CANARY}")
    except ValueError:
        logging.getLogger("scan").exception("The scan stopped")

    logged = log.getvalue()
    assert "The scan stopped" in logged
    assert "ValueError" in logged
    assert secrets_in(logged) == []


def test_chained_exception_shows_only_the_types(log):
    configure_logging(logging.DEBUG, stream=log)
    try:
        try:
            raise KeyError(CANARIES["risk"])
        except KeyError as inner:
            raise RuntimeError(TOKEN) from inner
    except RuntimeError:
        logging.getLogger("scan").exception("The scan stopped")

    logged = log.getvalue()
    assert "RuntimeError" in logged
    assert "KeyError" in logged
    assert secrets_in(logged) == []


def test_exception_already_formatted_by_another_handler_stays_safe(log):
    # A handler with a plain formatter caches the full traceback text on
    # the record; the safe formatter must not reuse it.
    configure_logging(logging.DEBUG, stream=log)
    plain = io.StringIO()
    # The plain handler goes first, so it formats the record first.
    logging.getLogger().handlers.insert(0, logging.StreamHandler(plain))
    try:
        raise ValueError(TOKEN)
    except ValueError:
        logging.getLogger("scan").exception("The scan stopped")

    assert TOKEN in plain.getvalue()
    assert secrets_in(log.getvalue()) == []


def test_stack_info_is_not_logged(log):
    configure_logging(logging.DEBUG, stream=log)

    logging.getLogger("scan").info("Checkpoint", stack_info=True)

    assert "Checkpoint" in log.getvalue()
    assert "Stack (most recent call last)" not in log.getvalue()


# --- Set-up ---


def test_configure_logging_replaces_earlier_handlers(log):
    earlier = io.StringIO()
    logging.getLogger().addHandler(logging.StreamHandler(earlier))

    configure_logging(logging.INFO, stream=log)
    logging.getLogger("scan").info("Scanned 3 repos")

    assert earlier.getvalue() == ""
    assert "Scanned 3 repos" in log.getvalue()


def test_level_is_applied(log):
    configure_logging(logging.WARNING, stream=log)

    logging.getLogger("scan").info("not shown")
    logging.getLogger("scan").warning("shown")

    assert "not shown" not in log.getvalue()
    assert "shown" in log.getvalue()
