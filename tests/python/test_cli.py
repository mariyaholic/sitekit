# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json

import pytest

from sitekit_audit import cli
from sitekit_audit.checks import BrowserUnavailable, CheckResult


def cli_args(built_site, repo_root, report, *extra):
    return [
        "--root",
        str(built_site),
        "--catalog",
        str(repo_root / "examples" / "room-catalog" / "catalog.json"),
        "--report",
        str(report),
        *extra,
    ]


def test_success_writes_a_report(monkeypatch, built_site, repo_root, scratch_factory, capsys):
    monkeypatch.setattr(
        cli,
        "run_audit",
        lambda base_url, site, config: [CheckResult("page-title", "narrow", "pass", "ok")],
    )
    report = scratch_factory() / "report.json"
    code = cli.main(cli_args(built_site, repo_root, report))
    assert code == 0
    output = capsys.readouterr()
    assert "1 checks, 1 passed, 0 failed" in output.out
    summary = json.loads(report.read_text(encoding="utf-8"))
    assert summary["summary"] == {"total": 1, "passed": 1, "failed": 0}


def test_failures_exit_1_and_are_printed(
    monkeypatch, built_site, repo_root, scratch_factory, capsys
):
    monkeypatch.setattr(
        cli,
        "run_audit",
        lambda base_url, site, config: [
            CheckResult("nav-links", "wide", "fail", "expected 4 links, got 3")
        ],
    )
    report = scratch_factory() / "report.json"
    code = cli.main(cli_args(built_site, repo_root, report))
    assert code == 1
    output = capsys.readouterr()
    assert "FAIL [wide] nav-links" in output.err
    assert "0 passed, 1 failed" in output.out
    assert json.loads(report.read_text(encoding="utf-8"))["summary"]["failed"] == 1


def test_no_report_writes_nothing(monkeypatch, built_site, repo_root, scratch_factory):
    monkeypatch.setattr(
        cli,
        "run_audit",
        lambda base_url, site, config: [CheckResult("page-title", "narrow", "pass", "ok")],
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("write_report must not be called with --no-report")

    monkeypatch.setattr(cli, "write_report", forbidden)
    code = cli.main(cli_args(built_site, repo_root, "unused.json", "--no-report"))
    assert code == 0


def test_missing_root_exits_2(scratch_factory, capsys):
    code = cli.main(["--root", str(scratch_factory() / "absent")])
    assert code == 2
    assert "does not contain index.html" in capsys.readouterr().err


def test_root_without_index_exits_2(scratch_factory, capsys):
    root = scratch_factory()
    (root / "other.html").write_text("x", encoding="utf-8")
    code = cli.main(["--root", str(root)])
    assert code == 2
    assert "run `node build.mjs`" in capsys.readouterr().err


def test_invalid_config_exits_2(scratch_factory, capsys):
    path = scratch_factory() / "audit.json"
    path.write_text("{bad", encoding="utf-8")
    code = cli.main(["--config", str(path)])
    assert code == 2
    assert "cannot parse config" in capsys.readouterr().err


def test_missing_catalog_exits_2(built_site, scratch_factory, capsys):
    code = cli.main(
        [
            "--root",
            str(built_site),
            "--catalog",
            str(scratch_factory() / "absent.json"),
            "--no-report",
        ]
    )
    assert code == 2
    assert "cannot read catalog" in capsys.readouterr().err


def test_missing_browser_is_an_explicit_failure(monkeypatch, built_site, repo_root, capsys):
    def unavailable(*args, **kwargs):
        raise BrowserUnavailable("Playwright for Python is not installed.")

    monkeypatch.setattr(cli, "run_audit", unavailable)
    code = cli.main(cli_args(built_site, repo_root, "unused.json", "--no-report"))
    assert code == 2
    assert "Playwright for Python is not installed" in capsys.readouterr().err


def test_version_exits_zero(capsys):
    with pytest.raises(SystemExit) as error:
        cli.main(["--version"])
    assert error.value.code == 0
    assert "sitekit-audit 0.1.0" in capsys.readouterr().out


def test_invalid_browser_choice_exits_2():
    with pytest.raises(SystemExit) as error:
        cli.main(["--browser", "safari"])
    assert error.value.code == 2
