# SPDX-License-Identifier: Apache-2.0
"""Command line interface for the sitekit browser audit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .checks import BrowserUnavailable, CheckResult, run_audit
from .config import BROWSERS, ConfigError, load_config
from .expectations import ExpectationError, load_expectations
from .report import build_report, write_report
from .server import SiteServer

_UNSET = object()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sitekit-audit",
        description=(
            "Audit a sitekit-generated room page against its catalog. "
            "Starts a loopback server and checks structure, interaction, "
            "reduced motion, tokens and layout at each configured viewport."
        ),
    )
    parser.add_argument("--config", metavar="FILE", help="JSON audit configuration")
    parser.add_argument("--root", metavar="DIR", help="built site directory to serve")
    parser.add_argument("--catalog", metavar="FILE", help="catalog used to derive expectations")
    parser.add_argument(
        "--report",
        metavar="FILE",
        default=_UNSET,
        help="write the JSON report here (default: audit.config.json value)",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="do not write a JSON report",
    )
    parser.add_argument(
        "--browser",
        choices=BROWSERS,
        help="browser to launch (default: try Edge, Chrome, then Chromium)",
    )
    parser.add_argument("--version", action="version", version=f"sitekit-audit {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    overrides: dict[str, object] = {}
    if args.root is not None:
        overrides["root"] = args.root
    if args.catalog is not None:
        overrides["catalog"] = args.catalog
    if args.browser is not None:
        overrides["browser"] = args.browser
    if args.no_report:
        overrides["report"] = None
    elif args.report is not _UNSET:
        overrides["report"] = args.report

    try:
        config = load_config(args.config, overrides)
    except ConfigError as error:
        print(f"sitekit-audit: {error}", file=sys.stderr)
        return 2

    root = Path(config["root"])
    if not root.is_dir() or not (root / "index.html").is_file():
        print(
            f"sitekit-audit: {root} does not contain index.html; "
            "run `node build.mjs` first or pass --root.",
            file=sys.stderr,
        )
        return 2

    try:
        site = load_expectations(config["catalog"])
    except ExpectationError as error:
        print(f"sitekit-audit: {error}", file=sys.stderr)
        return 2

    try:
        with SiteServer(root) as server:
            results = run_audit(server.base_url, site, config)
    except BrowserUnavailable as error:
        print(f"sitekit-audit: {error}", file=sys.stderr)
        return 2

    failed = [result for result in results if result.status == "fail"]
    for failure in failed:
        print(
            f"FAIL [{failure.viewport}] {failure.id}: {failure.detail}",
            file=sys.stderr,
        )

    report = build_report(results, site)
    summary = report["summary"]
    print(
        f"sitekit-audit: {summary['total']} checks, "
        f"{summary['passed']} passed, {summary['failed']} failed"
    )

    report_path = config["report"]
    if report_path is not None:
        try:
            target = write_report(report_path, report)
        except OSError as error:
            print(f"sitekit-audit: cannot write report {report_path}: {error}", file=sys.stderr)
            return 2
        print(f"sitekit-audit: report written to {target}")

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
