# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

from sitekit_audit.checks import BrowserUnavailable, launch_browser, run_audit
from sitekit_audit.config import load_config
from sitekit_audit.expectations import load_expectations
from sitekit_audit.server import SiteServer


def audit_config(built_site, repo_root, **overrides):
    return load_config(
        None,
        {
            "root": str(built_site),
            "catalog": str(repo_root / "examples" / "room-catalog" / "catalog.json"),
            "report": None,
            "viewports": [
                {"name": "narrow", "width": 375, "height": 812},
                {"name": "wide", "width": 1280, "height": 800},
            ],
            **overrides,
        },
    )


def failures(results):
    return [result for result in results if result.status == "fail"]


def test_generated_site_passes_every_check(
    browser_available, built_site, repo_root
):
    site = load_expectations(repo_root / "examples" / "room-catalog" / "catalog.json")
    config = audit_config(built_site, repo_root)
    with SiteServer(built_site) as server:
        results = run_audit(server.base_url, site, config)
    assert len(results) == 84
    assert failures(results) == []
    check_ids = {result.id for result in results}
    assert "room-studio-interaction" in check_ids
    assert "token-sk-color-accent" in check_ids
    assert "reduced-motion" in check_ids


def test_broken_navigation_is_detected(browser_available, site_copy, repo_root):
    index = site_copy / "index.html"
    html = index.read_text(encoding="utf-8")
    index.write_text(html.replace('href="#room-library"', 'href="#room-elsewhere"'), encoding="utf-8")

    site = load_expectations(repo_root / "examples" / "room-catalog" / "catalog.json")
    config = audit_config(site_copy, repo_root, viewports=[{"name": "wide", "width": 1280, "height": 800}])
    with SiteServer(site_copy) as server:
        results = run_audit(server.base_url, site, config)
    failed_ids = {result.id for result in failures(results)}
    assert "nav-links" in failed_ids


def test_wrong_token_is_detected(browser_available, built_site, repo_root):
    site = load_expectations(repo_root / "examples" / "room-catalog" / "catalog.json")
    config = audit_config(
        built_site,
        repo_root,
        viewports=[{"name": "wide", "width": 1280, "height": 800}],
        tokens={"selectors": {":root": {"--sk-color-accent": "#000000"}}},
    )
    with SiteServer(built_site) as server:
        results = run_audit(server.base_url, site, config)
    failed_ids = {result.id for result in failures(results)}
    assert "token-sk-color-accent" in failed_ids


def test_missing_reduced_motion_support_is_detected(browser_available, site_copy, repo_root):
    css = site_copy / "assets" / "site.css"
    css.write_text(
        css.read_text(encoding="utf-8")
        + "\n.room__details { transition: opacity 200ms ease !important; }\n",
        encoding="utf-8",
    )
    site = load_expectations(repo_root / "examples" / "room-catalog" / "catalog.json")
    config = audit_config(site_copy, repo_root, viewports=[{"name": "wide", "width": 1280, "height": 800}])
    with SiteServer(site_copy) as server:
        results = run_audit(server.base_url, site, config)
    failed_ids = {result.id for result in failures(results)}
    assert "reduced-motion" in failed_ids


class FakeChromium:
    def __init__(self, failing=()):
        self.failing = set(failing)
        self.calls: list[str] = []

    def launch(self, channel=None):
        name = channel or "chromium"
        self.calls.append(name)
        if name in self.failing:
            raise RuntimeError(f"{name} is not installed")
        return object()


class FakePlaywright:
    def __init__(self, failing=()):
        self.chromium = FakeChromium(failing)


def test_auto_tries_edge_then_chrome_then_chromium():
    playwright = FakePlaywright(failing=("msedge", "chrome"))
    launch_browser(playwright, "auto")
    assert playwright.chromium.calls == ["msedge", "chrome", "chromium"]


def test_explicit_browser_is_the_only_candidate():
    playwright = FakePlaywright()
    launch_browser(playwright, "chrome")
    assert playwright.chromium.calls == ["chrome"]


def test_no_browser_raises_with_actionable_message():
    playwright = FakePlaywright(failing=("msedge", "chrome", "chromium"))
    with pytest.raises(BrowserUnavailable, match="playwright install chromium"):
        launch_browser(playwright, "auto")
