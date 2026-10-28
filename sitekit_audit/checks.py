# SPDX-License-Identifier: Apache-2.0
"""Browser checks derived from the catalog expectations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable

from .expectations import RoomExpectation, SiteExpectation

BROWSER_ORDER = ("msedge", "chrome", "chromium")


class BrowserUnavailable(Exception):
    """Raised when Playwright or a supported browser cannot start."""


@dataclass(frozen=True)
class CheckResult:
    id: str
    viewport: str
    status: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _one_line(value: object, limit: int = 240) -> str:
    text = str(value).replace("\n", " ").strip()
    return text[:limit] if len(text) > limit else text


def _run(
    results: list[CheckResult],
    check_id: str,
    viewport: str,
    function: Callable[[], str],
) -> None:
    try:
        detail = function()
    except AssertionError as error:
        results.append(CheckResult(check_id, viewport, "fail", _one_line(error)))
    except Exception as error:  # noqa: BLE001 - report unexpected DOM errors as failures
        results.append(
            CheckResult(
                check_id,
                viewport,
                "fail",
                _one_line(f"{type(error).__name__}: {error}"),
            )
        )
    else:
        results.append(CheckResult(check_id, viewport, "pass", _one_line(detail or "ok")))


def _load_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        raise BrowserUnavailable(
            "Playwright for Python is not installed. "
            "Install it with `python3 -m pip install -r requirements.txt` and "
            "`python3 -m playwright install chromium`."
        ) from error
    return sync_playwright


def launch_browser(playwright, name: str):
    """Launch Edge, Chrome or bundled Chromium; raise BrowserUnavailable."""
    order = BROWSER_ORDER if name == "auto" else (name,)
    errors: list[str] = []
    for candidate in order:
        try:
            if candidate == "chromium":
                return playwright.chromium.launch()
            return playwright.chromium.launch(channel=candidate)
        except Exception as error:  # noqa: BLE001 - each candidate is optional
            errors.append(f"{candidate}: {_one_line(error, 160)}")
    detail = "; ".join(errors) if errors else "no candidates"
    raise BrowserUnavailable(
        f"no supported browser could be launched (tried {', '.join(order)}): {detail}. "
        "Install Chromium with `python3 -m playwright install chromium` or pass "
        "--browser <name>."
    )


def _room_locator(page, room: RoomExpectation):
    return page.locator(f"#room-{room.id}")


def _check_title(page, site: SiteExpectation) -> str:
    actual = page.title()
    _require(actual == site.title, f"expected {site.title!r}, got {actual!r}")
    return f"title {actual!r}"


def _check_skip_link(page) -> str:
    skip = page.locator("a.skip-link")
    _require(skip.count() == 1, f"expected one skip link, found {skip.count()}")
    href = skip.get_attribute("href")
    _require(href == "#content", f"expected href #content, got {href!r}")
    _require(page.locator("#content").count() == 1, "missing #content target")
    return "skip link targets #content"


def _check_nav(page, site: SiteExpectation) -> str:
    hrefs = page.locator("nav.room-nav a").evaluate_all(
        "elements => elements.map(element => element.getAttribute('href'))"
    )
    expected = [f"#room-{room.id}" for room in site.rooms]
    _require(
        hrefs == expected,
        f"expected navigation {expected}, got {hrefs}",
    )
    return f"{len(hrefs)} navigation links"


def _check_room_count(page, site: SiteExpectation) -> str:
    count = page.locator("main#content section.room").count()
    _require(
        count == len(site.rooms),
        f"expected {len(site.rooms)} rooms, found {count}",
    )
    return f"{count} rooms"


def _check_footer(page) -> str:
    text = page.locator("footer.site-footer").all_text_contents()
    joined = " ".join(text)
    _require("Made by Maria" in joined, "footer does not credit Made by Maria")
    return "footer credits Made by Maria"


def _check_heading(page, room: RoomExpectation) -> str:
    headings = _room_locator(page, room).locator("h2").all_text_contents()
    _require(len(headings) == 1, f"expected one h2, found {len(headings)}")
    _require(
        headings[0].strip() == room.name,
        f"expected heading {room.name!r}, got {headings[0].strip()!r}",
    )
    return f"heading {room.name!r}"


def _check_status(page, room: RoomExpectation) -> str:
    status = _room_locator(page, room).locator(".room__status")
    _require(status.count() == 1, f"expected one status, found {status.count()}")
    text = (status.text_content() or "").strip()
    marker = status.get_attribute("data-status")
    _require(text == room.status_label, f"expected label {room.status_label!r}, got {text!r}")
    _require(marker == room.status, f"expected data-status {room.status!r}, got {marker!r}")
    return f"status {room.status_label!r}"


def _check_summary(page, room: RoomExpectation) -> str:
    text = _room_locator(page, room).locator(".room__summary").all_text_contents()
    _require(len(text) == 1, f"expected one summary, found {len(text)}")
    _require(text[0].strip() == room.summary, "summary text does not match the catalog")
    return "summary matches catalog"


def _check_tags(page, room: RoomExpectation) -> str:
    tags = [
        value.strip()
        for value in _room_locator(page, room).locator(".room__tag").all_text_contents()
    ]
    _require(tags == list(room.tags), f"expected tags {list(room.tags)}, got {tags}")
    return f"{len(tags)} tags"


def _check_items(page, room: RoomExpectation) -> str:
    scope = _room_locator(page, room)
    labels = [value.strip() for value in scope.locator(".room__item-label").all_text_contents()]
    expected = [item.label for item in room.items]
    _require(labels == expected, f"expected item labels {expected}, got {labels}")
    notes = [value.strip() for value in scope.locator(".room__item-note").all_text_contents()]
    expected_notes = [item.note for item in room.items if item.note is not None]
    _require(notes == expected_notes, f"expected item notes {expected_notes}, got {notes}")
    return f"{len(labels)} items"


def _check_image(page, room: RoomExpectation) -> str:
    image = _room_locator(page, room).locator("img.room__image")
    _require(image.count() == 1, f"expected one illustration, found {image.count()}")
    source = image.get_attribute("src")
    _require(
        source == room.asset,
        f"expected illustration {room.asset!r}, got {source!r}",
    )
    loaded = image.evaluate("element => Boolean(element.complete && element.naturalWidth > 0)")
    _require(loaded, f"illustration {room.asset} did not load")
    return f"illustration {room.asset}"


def _check_toggle(page, room: RoomExpectation) -> str:
    scope = _room_locator(page, room)
    toggle = scope.locator(".room__toggle")
    panel = scope.locator(".room__details")
    _require(toggle.count() == 1, f"expected one toggle, found {toggle.count()}")
    _require(panel.count() == 1, f"expected one details panel, found {panel.count()}")
    _require(
        toggle.get_attribute("aria-expanded") == "false",
        "toggle must start collapsed",
    )
    controls = toggle.get_attribute("aria-controls")
    _require(
        controls == panel.get_attribute("id"),
        f"aria-controls {controls!r} does not match the panel id",
    )
    _require(panel.get_attribute("hidden") is not None, "details panel must start hidden")
    return "toggle wired to collapsed panel"


def _check_interaction(page, room: RoomExpectation) -> str:
    scope = _room_locator(page, room)
    toggle = scope.locator(".room__toggle")
    panel = scope.locator(".room__details")

    toggle.click()
    _require(
        toggle.get_attribute("aria-expanded") == "true",
        "click did not expand the panel",
    )
    _require(panel.get_attribute("hidden") is None, "panel still hidden after click")
    _require(panel.is_visible(), "panel is not visible after click")

    toggle.focus()
    page.keyboard.press("Enter")
    _require(
        toggle.get_attribute("aria-expanded") == "false",
        "Enter did not collapse the panel",
    )
    _require(panel.get_attribute("hidden") is not None, "panel still visible after Enter")
    return "click and Enter toggle the panel"


def _check_reduced_motion(page) -> str:
    page.emulate_media(reduced_motion="reduce")
    values = page.evaluate(
        """() => {
          const element = document.querySelector('.room__details');
          const style = getComputedStyle(element);
          return {
            transition: style.transitionDuration,
            animation: style.animationDuration,
          };
        }"""
    )
    for key, value in values.items():
        parts = [part.strip() for part in value.split(",") if part.strip()]
        _require(
            all(part in {"0s", "0ms"} for part in parts),
            f"{key} duration is {value!r} under prefers-reduced-motion: reduce",
        )
    return "no transition or animation under reduced motion"


def _check_tokens(page, tokens: dict[str, Any]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for selector, properties in tokens["selectors"].items():
        for prop, expected in properties.items():
            check_id = f"token-{prop.lstrip('-')}"
            try:
                actual = page.evaluate(
                    """([selector, property]) => {
                      const element = document.querySelector(selector);
                      if (!element) return null;
                      return getComputedStyle(element).getPropertyValue(property).trim();
                    }""",
                    [selector, prop],
                )
            except Exception as error:  # noqa: BLE001
                results.append(
                    CheckResult(check_id, "", "fail", _one_line(f"{type(error).__name__}: {error}"))
                )
                continue
            if actual is None:
                results.append(
                    CheckResult(check_id, "", "fail", f"selector {selector!r} not found")
                )
            elif actual != expected:
                results.append(
                    CheckResult(
                        check_id,
                        "",
                        "fail",
                        f"{selector} {prop}: expected {expected!r}, got {actual!r}",
                    )
                )
            else:
                results.append(
                    CheckResult(check_id, "", "pass", f"{selector} {prop} = {actual}")
                )
    return results


def _check_overflow(page) -> str:
    metrics = page.evaluate(
        """() => ({
          scrollWidth: document.documentElement.scrollWidth,
          innerWidth: window.innerWidth,
        })"""
    )
    _require(
        metrics["scrollWidth"] <= metrics["innerWidth"] + 1,
        f"horizontal overflow: {metrics['scrollWidth']}px content in {metrics['innerWidth']}px viewport",
    )
    return "no horizontal overflow"


def _run_viewport_checks(
    page,
    site: SiteExpectation,
    viewport: str,
    config: dict[str, Any],
    results: list[CheckResult],
) -> None:
    _run(results, "page-title", viewport, lambda: _check_title(page, site))
    _run(results, "skip-link", viewport, lambda: _check_skip_link(page))
    _run(results, "nav-links", viewport, lambda: _check_nav(page, site))
    _run(results, "room-count", viewport, lambda: _check_room_count(page, site))
    _run(results, "footer-credit", viewport, lambda: _check_footer(page))

    for room in site.rooms:
        _run(results, f"room-{room.id}-heading", viewport, lambda room=room: _check_heading(page, room))
        _run(results, f"room-{room.id}-status", viewport, lambda room=room: _check_status(page, room))
        _run(results, f"room-{room.id}-summary", viewport, lambda room=room: _check_summary(page, room))
        _run(results, f"room-{room.id}-tags", viewport, lambda room=room: _check_tags(page, room))
        _run(results, f"room-{room.id}-items", viewport, lambda room=room: _check_items(page, room))
        _run(results, f"room-{room.id}-image", viewport, lambda room=room: _check_image(page, room))
        _run(results, f"room-{room.id}-toggle", viewport, lambda room=room: _check_toggle(page, room))
        _run(
            results,
            f"room-{room.id}-interaction",
            viewport,
            lambda room=room: _check_interaction(page, room),
        )

    _run(results, "reduced-motion", viewport, lambda: _check_reduced_motion(page))
    _run(results, "layout-overflow", viewport, lambda: _check_overflow(page))

    for result in _check_tokens(page, config["tokens"]):
        results.append(
            CheckResult(result.id, viewport, result.status, result.detail)
        )


def run_audit(
    base_url: str, site: SiteExpectation, config: dict[str, Any]
) -> list[CheckResult]:
    """Load the generated page at every configured viewport and check it."""
    sync_playwright = _load_playwright()
    results: list[CheckResult] = []
    with sync_playwright() as playwright:
        browser = launch_browser(playwright, config["browser"])
        try:
            for viewport in config["viewports"]:
                context = browser.new_context(
                    viewport={"width": viewport["width"], "height": viewport["height"]}
                )
                page = context.new_page()
                page.set_default_timeout(config["timeout_ms"])
                try:
                    page.goto(f"{base_url}/index.html", wait_until="load")
                    _run_viewport_checks(page, site, viewport["name"], config, results)
                finally:
                    context.close()
        finally:
            browser.close()
    return results
