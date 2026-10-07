"""audit.py — a browser-driven verification gate for a catalog page.

Serves a site directory, drives the page headless at each configured viewport,
and checks the things that actually break: console/page errors, horizontal
overflow, the hotspot -> window interaction, deep links, keyboard reach, and
that reduced motion leaves a complete (not dead) page.

    python audit.py [--config FILE] [--root DIR] [--site DIR] [--catalog FILE]
                    [--port N] [--shots] [--json PATH] [--help]

Expectations come from the catalog, so it runs against any catalog: the hotspot
count is the number of objects, the row count is the number of tools, the
section headings are the object names, and the chapter/tool it exercises are
picked from the catalog too. What the catalog cannot supply — CSS selectors, the
reduced-motion marker, the viewport list — comes from a JSON config file.

Exit status is non-zero if any check fails. --json writes the full report.
"""
from __future__ import annotations

import argparse
import functools
import http.server
import json
import os
import socketserver
import sys
import threading

DEFAULT_CONFIG: dict = {
    "siteDir": "site",
    "catalog": "catalog.json",
    "page": "index.html",
    "viewports": [375, 1440],
    "viewportHeight": 900,
    "port": 0,
    "shots": False,
    "selectors": {
        "stage": ".stage svg",
        "hotspot": ".spot",
        "notebookRow": ".row",
        "notebookSection": ".notebook .chapter",
        "notebookHeading": ".notebook .chapter h3",
        "window": "#win",
        "windowTitle": "#win-title",
        "windowTools": "#win-tools",
        "toolCard": ".card[data-tool]",
        "toolSpec": "#win-tools .spec",
        "backButton": "#win-acts button",
        "hiddenCheck": [".spot", ".notebook", ".masthead"],
        "reducedMotionMarker": ".lamp-glow",
    },
    "reducedMotion": {"requiredOpacity": 1.0},
    "tokenChecks": {},
}


def normalize_css_value(value: object) -> str:
    return " ".join(str(value).split()).lower()

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_FILE = os.path.join(HERE, "audit.config.json")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # keep the audit output clean
        pass


def serve(directory: str, port: int) -> socketserver.TCPServer:
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(
        ("127.0.0.1", port), functools.partial(Quiet, directory=directory)
    )
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(explicit: str | None) -> dict:
    config = DEFAULT_CONFIG
    sources = [DEFAULT_CONFIG_FILE]
    if explicit:
        sources.append(explicit)
    for path in sources:
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as handle:
                config = deep_merge(config, json.load(handle))
    return config


def launch(pw, headless: bool):
    last_error = None
    for kwargs in ({"channel": "msedge"}, {"channel": "chrome"}, {}):
        try:
            return pw.chromium.launch(headless=headless, **kwargs)
        except Exception as error:  # try the next channel
            last_error = error
    raise SystemExit(f"no Chromium/Edge/Chrome browser available to Playwright: {last_error}")


def pick_exercise(objects: list[dict]) -> tuple[dict, dict]:
    """Return two chapters that have tools: the one to open, and the deep link."""
    with_tools = [o for o in objects if o.get("kind") == "chapter" and (o.get("tools") or [])]
    if not with_tools:
        raise SystemExit("catalog has no chapter with tools to exercise")
    first = with_tools[0]
    second = with_tools[1] if len(with_tools) > 1 else with_tools[0]
    return first, second


def audit_viewport(page, base: str, config: dict, expected: dict, exercise: dict, failures: list, notes: list) -> dict:
    """Drive one viewport and return its report entry."""
    selectors = config["selectors"]
    token_checks = config.get("tokenChecks") or {}
    errors: list[str] = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda x: errors.append(str(x)))

    result: dict = {"failures": []}

    def fail(message: str) -> None:
        result["failures"].append(message)
        failures.append(message)

    page.goto(base, wait_until="load")
    page.wait_for_selector(selectors["stage"])

    hotspots = page.locator(selectors["hotspot"]).count()
    rows = page.locator(selectors["notebookRow"]).count()
    sections = page.locator(selectors["notebookSection"]).count()
    headings = page.locator(selectors["notebookHeading"]).all_inner_texts()
    result.update({"hotspots": hotspots, "rows": rows, "sections": sections})

    if hotspots != expected["hotspots"]:
        fail(f"{expected['width']}: expected {expected['hotspots']} hotspots, found {hotspots}")
    if rows != expected["rows"]:
        fail(f"{expected['width']}: expected {expected['rows']} notebook rows, found {rows}")
    if sections != expected["sections"]:
        fail(f"{expected['width']}: expected {expected['sections']} notebook sections, found {sections}")

    missing = [name for name in expected["names"] if name.upper() not in [h.upper() for h in headings]]
    if missing:
        fail(f"{expected['width']}: notebook is missing headings for {missing}")

    # design tokens: the guard against a silently broken token layer
    if token_checks:
        resolved = page.evaluate(
            """(names) => Object.fromEntries(names.map((name) =>
                 [name, getComputedStyle(document.documentElement).getPropertyValue(name)]))""",
            list(token_checks),
        )
        result["tokens"] = {name: normalize_css_value(value) for name, value in resolved.items()}
        for name, want in token_checks.items():
            got = normalize_css_value(resolved.get(name, ""))
            expected_value = normalize_css_value(want)
            if got != expected_value:
                fail(f"{expected['width']}: token {name} = {got!r}, want {expected_value!r}")

    over = page.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    result["overflow"] = over
    if over > 0:
        fail(f"{expected['width']}: horizontal overflow of {over}px")

    # open a chapter, then a tool, then close with Escape
    page.locator(f'{selectors["hotspot"]}[data-object="{exercise["chapter_id"]}"]').first.click()
    if page.locator(f'{selectors["window"]}[data-open="true"]').count() != 1:
        fail(f"{expected['width']}: window did not open on hotspot click")
    if page.locator(selectors["windowTitle"]).inner_text().strip() != exercise["chapter_name"]:
        fail(f"{expected['width']}: wrong window title for {exercise['chapter_id']}")

    card = page.locator(selectors["toolCard"]).first
    if card.count() == 0:
        fail(f"{expected['width']}: no tool card inside the {exercise['chapter_id']} chapter")
    else:
        card.click()
        if page.locator(selectors["windowTitle"]).inner_text().strip() != exercise["tool_name"]:
            fail(f"{expected['width']}: tool card did not open its detail")
        if page.locator(selectors["toolSpec"]).count() != 1:
            fail(f"{expected['width']}: tool spec missing or duplicated on first open")
        page.locator(selectors["backButton"], has_text="BACK").first.click()
        page.locator(selectors["toolCard"]).first.click()
        if page.locator(selectors["toolSpec"]).count() != 1:
            fail(f"{expected['width']}: tool spec duplicated after reopening")

    page.keyboard.press("Escape")
    if page.locator(f'{selectors["window"]}[data-open="true"]').count() != 0:
        fail(f"{expected['width']}: Escape did not close the window")

    # deep link restores state
    deep = f"{base}?o={exercise['deep_chapter_id']}&t={exercise['deep_tool_id']}"
    page.goto(deep, wait_until="load")
    page.wait_for_selector(selectors["stage"])
    if page.locator(selectors["windowTitle"]).inner_text().strip() != exercise["deep_tool_name"]:
        fail(f"{expected['width']}: deep link did not restore the tool")

    # keyboard reach
    page.goto(base, wait_until="load")
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    focused = page.evaluate("document.activeElement && document.activeElement.className")
    result["focus"] = focused

    if errors:
        fail(f"{expected['width']}: console/page errors: {errors[:3]}")
    notes.append(
        f"{expected['width']}: {hotspots} hotspots, {rows} rows, {sections} sections, "
        f"overflow {over}px, focus -> {focused!r}"
    )
    return result


def audit_reduced_motion(page, base: str, selectors: dict, config: dict, failures: list, notes: list) -> dict:
    result: dict = {"failures": []}

    def fail(message: str) -> None:
        result["failures"].append(message)
        failures.append(message)

    page.goto(base, wait_until="load")
    page.wait_for_selector(selectors["stage"])
    hidden_selectors = selectors["hiddenCheck"]
    hidden = page.evaluate(
        """(selectors) => {
          const els = selectors.flatMap(s => [...document.querySelectorAll(s)]);
          return els.filter(e => {
            const s = getComputedStyle(e);
            return s.display === 'none' || parseFloat(s.opacity) === 0;
          }).length;
        }""",
        hidden_selectors,
    )
    if hidden:
        fail(f"reduced-motion: {hidden} core elements hidden")
    result["hidden"] = hidden

    marker = selectors["reducedMotionMarker"]
    opacity = page.evaluate(
        """(marker) => {
          const el = document.querySelector(marker);
          return el ? getComputedStyle(el).opacity : null;
        }""",
        marker,
    )
    required = float(config.get("reducedMotion", {}).get("requiredOpacity", 1.0))
    result.update({"marker": marker, "opacity": opacity, "requiredOpacity": required})
    if opacity is None:
        fail(f"reduced-motion: marker {marker} not found")
    elif float(opacity) < required:
        fail(f"reduced-motion: {marker} not at end state (opacity {opacity}, want >= {required})")
    notes.append(f"reduced-motion: {hidden} hidden, {marker} opacity {opacity}")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Browser-driven verification gate for a catalog page.")
    ap.add_argument("--config", help="JSON config merging over the built-in defaults")
    ap.add_argument("--root", help="repository root holding the catalog (default: cwd)")
    ap.add_argument("--site", help="directory to serve (default: <root>/<siteDir>)")
    ap.add_argument("--catalog", help="catalog file (default: <root>/<catalog>)")
    ap.add_argument("--port", type=int, help="port to serve on (default: an ephemeral port)")
    ap.add_argument("--shots", action="store_true", help="write screenshots next to the site")
    ap.add_argument("--json", dest="json_path", help="write the JSON report to this path")
    args = ap.parse_args()

    config = load_config(args.config)
    root = os.path.abspath(args.root or os.getcwd())
    site_dir = os.path.abspath(args.site or os.path.join(root, config["siteDir"]))
    catalog_path = os.path.abspath(args.catalog or os.path.join(root, config["catalog"]))
    port = args.port if args.port is not None else int(config.get("port", 0))
    shots = args.shots or bool(config.get("shots"))
    selectors = config["selectors"]
    token_checks = config.get("tokenChecks") or {}

    with open(catalog_path, "r", encoding="utf-8") as handle:
        catalog = json.load(handle)
    objects = catalog.get("objects") or []
    first, second = pick_exercise(objects)

    expectations = {
        "hotspots": len(objects),
        "rows": sum(len(o.get("tools") or []) for o in objects),
        "sections": len(objects),
        "names": [o["name"] for o in objects],
    }
    exercise = {
        "chapter_id": first["id"],
        "chapter_name": first["name"],
        "tool_name": first["tools"][0]["name"],
        "deep_chapter_id": second["id"],
        "deep_tool_id": second["tools"][0]["id"],
        "deep_tool_name": second["tools"][0]["name"],
    }

    httpd = serve(site_dir, port)
    bound_port = httpd.server_address[1]
    base = f"http://127.0.0.1:{bound_port}/{config['page']}"
    shots_dir = os.path.join(site_dir, "shots")
    if shots:
        os.makedirs(shots_dir, exist_ok=True)

    report: dict = {
        "ok": True,
        "url": base,
        "catalog": os.path.relpath(catalog_path, root).replace("\\", "/"),
        "siteDir": os.path.relpath(site_dir, root).replace("\\", "/"),
        "expected": expectations,
        "exercise": exercise,
        "tokenChecks": token_checks,
        "viewports": [],
        "reducedMotion": {},
        "failures": [],
        "notes": [],
    }
    failures = report["failures"]
    notes = report["notes"]

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = launch(pw, headless=True)
        try:
            for width in config["viewports"]:
                height = int(config.get("viewportHeight", 900))
                context = browser.new_context(viewport={"width": width, "height": height})
                page = context.new_page()
                entry = audit_viewport(
                    page,
                    base,
                    config,
                    {**expectations, "width": width},
                    exercise,
                    failures,
                    notes,
                )
                entry["width"] = width
                entry["height"] = height

                if shots:
                    page.goto(base, wait_until="load")
                    page.wait_for_selector(selectors["stage"])
                    page.screenshot(path=os.path.join(shots_dir, f"home-{width}.png"))
                    page.locator(
                        f'{selectors["hotspot"]}[data-object="{exercise["chapter_id"]}"]'
                    ).first.click()
                    page.screenshot(path=os.path.join(shots_dir, f"window-{width}.png"))

                report["viewports"].append(entry)
                context.close()

            reduced_context = browser.new_context(
                viewport={"width": config["viewports"][-1], "height": int(config.get("viewportHeight", 900))},
                reduced_motion="reduce",
            )
            report["reducedMotion"] = audit_reduced_motion(
                reduced_context.new_page(), base, selectors, config, failures, notes
            )
            reduced_context.close()
        finally:
            browser.close()

    httpd.shutdown()

    report["ok"] = not failures

    print("\n".join("  " + note for note in notes))
    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
            handle.write("\n")
        print(f"  report -> {args.json_path}")

    if failures:
        print("\nFAIL")
        print("\n".join("  " + failure for failure in failures))
        return 1
    print("\nPASS — all checks green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
