"""Checks the development environment matches what the project pins.

Phase 0 setup task: the venv runs the chosen Python, and every package in
requirements.txt and requirements-dev.txt is installed at its pinned
version (docs/architecture.md, Tech stack). Not part of any component.
"""

import sys
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def pinned_packages() -> dict[str, str]:
    """Read `name==version` lines from both requirements files.

    Returns package name -> pinned version. Blank lines and comments are
    skipped; any other line format fails the test, since every dependency
    must be pinned exactly.
    """
    pins = {}
    for file_name in ("requirements.txt", "requirements-dev.txt"):
        for line in (ROOT / file_name).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name, separator, pinned = line.partition("==")
            assert separator, f"{file_name}: '{line}' is not pinned with =="
            pins[name] = pinned
    return pins


def test_python_is_3_13():
    assert sys.version_info[:2] == (3, 13)


def test_installed_packages_match_their_pins():
    pins = pinned_packages()
    assert pins, "no pinned packages found"
    mismatches = {
        name: (pinned, version(name))
        for name, pinned in pins.items()
        if version(name) != pinned
    }
    assert mismatches == {}
