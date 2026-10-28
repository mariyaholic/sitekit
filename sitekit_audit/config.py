# SPDX-License-Identifier: Apache-2.0
"""Audit configuration: built-in defaults, file merge, CLI override."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

BROWSERS = ("auto", "msedge", "chrome", "chromium")
TOP_LEVEL_KEYS = (
    "root",
    "catalog",
    "report",
    "browser",
    "timeout_ms",
    "viewports",
    "tokens",
)

DEFAULT_CONFIG: dict[str, Any] = {
    "root": "dist",
    "catalog": "examples/room-catalog/catalog.json",
    "report": "audit-report.json",
    "browser": "auto",
    "timeout_ms": 15000,
    "viewports": [
        {"name": "narrow", "width": 375, "height": 812},
        {"name": "wide", "width": 1280, "height": 800},
    ],
    "tokens": {
        "selectors": {
            ":root": {
                "--sk-color-ink": "#14201b",
                "--sk-color-paper": "#f7f4ec",
                "--sk-color-accent": "#1f6f5c",
            }
        }
    },
}


class ConfigError(Exception):
    """Raised when the audit configuration is unusable."""


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _require_string(config: dict[str, Any], key: str, problems: list[str]) -> None:
    value = config.get(key)
    if not isinstance(value, str) or value.strip() == "":
        problems.append(f"{key}: expected a non-empty string")


def _validate_viewports(viewports: Any, problems: list[str]) -> None:
    if not isinstance(viewports, list) or not viewports:
        problems.append("viewports: expected a non-empty array")
        return
    names: set[str] = set()
    for index, viewport in enumerate(viewports):
        base = f"viewports/{index}"
        if not isinstance(viewport, dict):
            problems.append(f"{base}: expected an object")
            continue
        name = viewport.get("name")
        if not isinstance(name, str) or name.strip() == "":
            problems.append(f"{base}/name: expected a non-empty string")
        elif name in names:
            problems.append(f"{base}/name: duplicate viewport name {name!r}")
        else:
            names.add(name)
        for dimension in ("width", "height"):
            value = viewport.get(dimension)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                problems.append(f"{base}/{dimension}: expected a positive integer")
        extra = set(viewport) - {"name", "width", "height"}
        if extra:
            problems.append(f"{base}: unknown keys {', '.join(sorted(extra))}")


def _validate_tokens(tokens: Any, problems: list[str]) -> None:
    if not isinstance(tokens, dict):
        problems.append("tokens: expected an object")
        return
    extra = set(tokens) - {"selectors"}
    if extra:
        problems.append(f"tokens: unknown keys {', '.join(sorted(extra))}")
    selectors = tokens.get("selectors")
    if not isinstance(selectors, dict) or not selectors:
        problems.append("tokens/selectors: expected a non-empty object")
        return
    for selector, properties in selectors.items():
        if not isinstance(selector, str) or selector.strip() == "":
            problems.append("tokens/selectors: selector keys must be non-empty strings")
            continue
        if not isinstance(properties, dict) or not properties:
            problems.append(f"tokens/selectors/{selector}: expected a non-empty object")
            continue
        for prop, expected in properties.items():
            if not isinstance(prop, str) or not prop.strip():
                problems.append(f"tokens/selectors/{selector}: empty property name")
            if not isinstance(expected, str) or expected.strip() == "":
                problems.append(
                    f"tokens/selectors/{selector}/{prop}: expected a non-empty string"
                )


def validate_config(config: dict[str, Any]) -> None:
    """Validate a fully merged configuration, collecting every problem."""
    problems: list[str] = []
    unknown = set(config) - set(TOP_LEVEL_KEYS)
    if unknown:
        problems.append(f"unknown keys: {', '.join(sorted(unknown))}")

    for key in ("root", "catalog"):
        _require_string(config, key, problems)
    report = config.get("report")
    if report is not None and (not isinstance(report, str) or report.strip() == ""):
        problems.append("report: expected a non-empty string or null")

    browser = config.get("browser")
    if browser not in BROWSERS:
        problems.append(f"browser: expected one of {', '.join(BROWSERS)}")

    timeout = config.get("timeout_ms")
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
        problems.append("timeout_ms: expected a positive integer")

    _validate_viewports(config.get("viewports"), problems)
    _validate_tokens(config.get("tokens"), problems)

    if problems:
        raise ConfigError("invalid audit configuration:\n  " + "\n  ".join(problems))


def load_config(
    path: str | Path | None = None, overrides: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Merge defaults, an optional JSON file and non-None CLI overrides."""
    config = copy.deepcopy(DEFAULT_CONFIG)

    if path is not None:
        config_path = Path(path)
        try:
            text = config_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise ConfigError(f"cannot read config {config_path}: {error}") from error
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError as error:
            raise ConfigError(f"cannot parse config {config_path}: {error}") from error
        if not isinstance(loaded, dict):
            raise ConfigError(f"config {config_path} must contain a JSON object")
        config = _merge(config, loaded)

    if overrides:
        config = _merge(config, overrides)

    validate_config(config)
    return config
