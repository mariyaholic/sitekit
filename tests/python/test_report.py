# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json

from sitekit_audit.checks import CheckResult
from sitekit_audit.expectations import from_catalog
from sitekit_audit.report import build_report, write_report


def make_results():
    return [
        CheckResult("page-title", "narrow", "pass", "title 'Atrium Rooms'"),
        CheckResult("nav-links", "narrow", "pass", "4 navigation links"),
        CheckResult("layout-overflow", "wide", "fail", "horizontal overflow"),
    ]


def test_report_summarises_results(example_catalog):
    site = from_catalog(example_catalog)
    report = build_report(make_results(), site)
    assert report["tool"] == "sitekit-audit"
    assert report["version"] == "0.1.0"
    assert report["site"] == {"title": "Atrium Rooms", "roomCount": 4}
    assert report["summary"] == {"total": 3, "passed": 2, "failed": 1}
    assert report["checks"][0] == {
        "id": "page-title",
        "viewport": "narrow",
        "status": "pass",
        "detail": "title 'Atrium Rooms'",
    }


def test_report_has_no_timestamp_and_round_trips(example_catalog):
    site = from_catalog(example_catalog)
    report = build_report(make_results(), site)
    assert "generatedAt" not in report
    serialised = json.dumps(report, sort_keys=True)
    assert json.loads(serialised) == report


def test_report_is_stable_for_identical_results(example_catalog):
    site = from_catalog(example_catalog)
    first = build_report(make_results(), site)
    second = build_report(make_results(), site)
    assert first == second


def test_write_report_creates_parents_and_trailing_newline(example_catalog, scratch_factory):
    site = from_catalog(example_catalog)
    target = scratch_factory() / "nested" / "dir" / "report.json"
    written = write_report(target, build_report(make_results(), site))
    assert written == target
    text = target.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert json.loads(text)["summary"]["total"] == 3
