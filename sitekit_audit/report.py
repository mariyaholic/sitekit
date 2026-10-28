# SPDX-License-Identifier: Apache-2.0
"""Machine-readable audit report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import __version__
from .checks import CheckResult
from .expectations import SiteExpectation


def build_report(results: list[CheckResult], site: SiteExpectation) -> dict[str, Any]:
    """Build the stable JSON report. No timestamps, so runs are reproducible."""
    passed = sum(1 for result in results if result.status == "pass")
    failed = sum(1 for result in results if result.status == "fail")
    return {
        "tool": "sitekit-audit",
        "version": __version__,
        "site": {"title": site.title, "roomCount": len(site.rooms)},
        "summary": {"total": len(results), "passed": passed, "failed": failed},
        "checks": [result.to_dict() for result in results],
    }


def write_report(path: str | Path, report: dict[str, Any]) -> Path:
    """Write the report as UTF-8 JSON with a trailing newline."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return target
