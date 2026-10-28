# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json

import pytest

from sitekit_audit.config import (
    DEFAULT_CONFIG,
    ConfigError,
    load_config,
    validate_config,
)


def write_config(directory, payload) -> str:
    path = directory / "audit.config.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def test_defaults_are_valid_and_not_shared():
    first = load_config()
    second = load_config()
    assert first["root"] == "dist"
    assert first["browser"] == "auto"
    assert first["report"] == "audit-report.json"
    assert [viewport["name"] for viewport in first["viewports"]] == ["narrow", "wide"]
    first["viewports"][0]["width"] = 1
    assert second["viewports"][0]["width"] == 375
    assert DEFAULT_CONFIG["viewports"][0]["width"] == 375


def test_file_values_override_defaults(scratch_factory):
    path = write_config(
        scratch_factory(),
        {
            "root": "public",
            "viewports": [{"name": "phone", "width": 360, "height": 740}],
            "tokens": {"selectors": {":root": {"--sk-color-ink": "#000000"}}},
        },
    )
    config = load_config(path)
    assert config["root"] == "public"
    assert config["catalog"] == DEFAULT_CONFIG["catalog"]
    assert config["viewports"] == [{"name": "phone", "width": 360, "height": 740}]
    assert config["tokens"]["selectors"][":root"]["--sk-color-ink"] == "#000000"
    # Nested objects merge, so untouched tokens keep their defaults.
    assert config["tokens"]["selectors"][":root"]["--sk-color-accent"] == "#1f6f5c"


def test_cli_overrides_file(scratch_factory):
    path = write_config(scratch_factory(), {"root": "public", "browser": "chrome"})
    config = load_config(path, {"root": "build", "browser": "chromium", "report": None})
    assert config["root"] == "build"
    assert config["browser"] == "chromium"
    assert config["report"] is None


def test_unset_overrides_are_not_passed(scratch_factory):
    path = write_config(scratch_factory(), {"root": "public"})
    config = load_config(path, {})
    assert config["root"] == "public"
    assert config["browser"] == "auto"


def test_report_can_be_disabled_by_an_explicit_none():
    config = load_config(None, {"report": None})
    assert config["report"] is None


def test_unknown_top_level_key_is_rejected(scratch_factory):
    path = write_config(scratch_factory(), {"viewports": DEFAULT_CONFIG["viewports"], "colour": "red"})
    with pytest.raises(ConfigError, match="unknown keys: colour"):
        load_config(path)


def test_unknown_browser_is_rejected():
    with pytest.raises(ConfigError, match="browser: expected one of"):
        load_config(None, {"browser": "firefox"})


@pytest.mark.parametrize(
    "viewports, message",
    [
        ([], "viewports: expected a non-empty array"),
        ([{"name": "narrow", "width": 0, "height": 10}], "width: expected a positive integer"),
        ([{"name": "narrow", "width": 10}], "height: expected a positive integer"),
        (
            [
                {"name": "narrow", "width": 10, "height": 10},
                {"name": "narrow", "width": 20, "height": 20},
            ],
            "duplicate viewport name",
        ),
        (
            [{"name": "narrow", "width": 10, "height": 10, "device": "phone"}],
            "unknown keys device",
        ),
    ],
)
def test_invalid_viewports_are_rejected(viewports, message):
    with pytest.raises(ConfigError, match=message):
        validate_config({**copy.deepcopy(DEFAULT_CONFIG), "viewports": viewports})


def test_invalid_timeout_is_rejected():
    with pytest.raises(ConfigError, match="timeout_ms"):
        load_config(None, {"timeout_ms": 0})


def test_invalid_tokens_are_rejected():
    empty = copy.deepcopy(DEFAULT_CONFIG)
    empty["tokens"] = {"selectors": {}}
    with pytest.raises(ConfigError, match="tokens/selectors"):
        validate_config(empty)
    with pytest.raises(ConfigError, match="expected a non-empty string"):
        load_config(None, {"tokens": {"selectors": {":root": {"--x": ""}}}})


def test_missing_and_malformed_files_are_rejected(scratch_factory):
    with pytest.raises(ConfigError, match="cannot read config"):
        load_config(scratch_factory() / "absent.json")
    path = scratch_factory() / "bad.json"
    path.write_text("{nope", encoding="utf-8")
    with pytest.raises(ConfigError, match="cannot parse config"):
        load_config(path)
    array = scratch_factory() / "array.json"
    array.write_text("[]", encoding="utf-8")
    with pytest.raises(ConfigError, match="must contain a JSON object"):
        load_config(array)
