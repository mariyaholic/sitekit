# SPDX-License-Identifier: Apache-2.0
"""Shared fixtures for the Python audit tests."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRATCH_BASE = REPO_ROOT / "tests" / "tmp"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def example_catalog(repo_root: Path) -> dict:
    return json.loads(
        (repo_root / "examples" / "room-catalog" / "catalog.json").read_text(encoding="utf-8")
    )


@pytest.fixture(scope="session")
def scratch_factory():
    """Create scratch directories inside the repository and clean them up."""
    SCRATCH_BASE.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []

    def make(prefix: str = "py-") -> Path:
        directory = Path(tempfile.mkdtemp(prefix=prefix, dir=SCRATCH_BASE))
        created.append(directory)
        return directory

    yield make

    for directory in created:
        shutil.rmtree(directory, ignore_errors=True)


@pytest.fixture(scope="session")
def built_site(repo_root: Path, scratch_factory) -> Path:
    """Build the example site once with the real Node builder."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is required to build the audit fixture")
    out = scratch_factory("site-") / "dist"
    result = subprocess.run(
        [node, str(repo_root / "build.mjs"), "--out", str(out)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return out


@pytest.fixture
def site_copy(built_site: Path, scratch_factory) -> Path:
    target = scratch_factory("copy-") / "dist"
    shutil.copytree(built_site, target)
    return target


@pytest.fixture(scope="session")
def browser_available() -> str:
    """Skip browser tests when Playwright or a browser is unavailable."""
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import Error, sync_playwright

    with sync_playwright() as playwright:
        for channel in ("chromium", "chrome", "msedge"):
            try:
                if channel == "chromium":
                    browser = playwright.chromium.launch()
                else:
                    browser = playwright.chromium.launch(channel=channel)
            except Error:
                continue
            browser.close()
            return channel
    pytest.skip("no Playwright browser is installed; run `python3 -m playwright install chromium`")
    return ""
