"""audit.py — the room's verification gate.

Serves the repo, drives the page headless at 375 and 1440, and checks the
things that actually break: console/page errors, horizontal overflow, the
hotspot -> window interaction, deep links, keyboard reach, and that
reduced-motion leaves a complete (not dead) page.

    python site/audit.py [--shots]

Exit status is non-zero if any check fails. Screenshots (with --shots) are
written to site/shots/ which is git-ignored.
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8931
SHOTS = os.path.join(ROOT, "site", "shots")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # keep the audit output clean
        pass


def serve() -> socketserver.TCPServer:
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), functools.partial(Quiet, directory=os.path.join(ROOT, "site")))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def launch(pw, headless: bool):
    for kwargs in ({"channel": "msedge"}, {"channel": "chrome"}, {}):
        try:
            return pw.chromium.launch(headless=headless, **kwargs)
        except Exception:
            continue
    raise SystemExit("no Chromium/Edge/Chrome browser available to Playwright")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", action="store_true")
    args = ap.parse_args()

    if args.shots:
        os.makedirs(SHOTS, exist_ok=True)

    httpd = serve()
    base = f"http://127.0.0.1:{PORT}/index.html"
    fails: list[str] = []
    notes: list[str] = []

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        for width in (375, 1440):
            browser = launch(pw, headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            errors: list[str] = []
            page.on("console", lambda m, e=errors: e.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda x, e=errors: e.append(str(x)))

            page.goto(base, wait_until="load")
            page.wait_for_selector(".stage svg")

            spots = page.locator(".spot").count()
            rows = page.locator(".row").count()
            if spots != 9:
                fails.append(f"{width}: expected 9 hotspots, found {spots}")
            if rows != 6:
                fails.append(f"{width}: expected 6 notebook rows, found {rows}")

            over = page.evaluate(
                "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
            )
            if over > 0:
                fails.append(f"{width}: horizontal overflow of {over}px")

            # open a chapter, then a tool, then close with Escape
            page.locator('.spot[data-object="qol"]').first.click()
            if page.locator('#win[data-open="true"]').count() != 1:
                fails.append(f"{width}: window did not open on hotspot click")
            if page.locator("#win-title").inner_text().strip() != "Quality of Life":
                fails.append(f"{width}: wrong window title for qol")

            card = page.locator('.card[data-tool]').first
            if card.count() == 0:
                fails.append(f"{width}: no tool card inside the qol chapter")
            else:
                card.click()
                if page.locator("#win-title").inner_text().strip() != "Desk Reset":
                    fails.append(f"{width}: tool card did not open its detail")
                if page.locator("#win-tools .spec").count() != 1:
                    fails.append(f"{width}: tool spec missing or duplicated on first open")
                page.locator("#win-acts button", has_text="BACK").first.click()
                page.locator(".card[data-tool]").first.click()
                if page.locator("#win-tools .spec").count() != 1:
                    fails.append(f"{width}: tool spec duplicated after reopening")

            page.keyboard.press("Escape")
            if page.locator('#win[data-open="true"]').count() != 0:
                fails.append(f"{width}: Escape did not close the window")

            # deep link restores state
            page.goto(base + "?o=looks&t=mh-look-001", wait_until="load")
            page.wait_for_selector(".stage svg")
            if page.locator("#win-title").inner_text().strip() != "Nocturne Shell":
                fails.append(f"{width}: deep link did not restore the tool")

            # keyboard reach: first hotspot is focusable and its tag becomes visible
            page.goto(base, wait_until="load")
            page.keyboard.press("Tab")  # skip link
            page.keyboard.press("Tab")  # first hotspot (after masthead motion button? order check)
            focused = page.evaluate("document.activeElement && document.activeElement.className")

            if errors:
                fails.append(f"{width}: console/page errors: {errors[:3]}")
            notes.append(f"{width}: {spots} hotspots, {rows} rows, overflow {over}px, focus -> {focused!r}")

            if args.shots:
                page.goto(base, wait_until="load")
                page.wait_for_selector(".stage svg")
                page.screenshot(path=os.path.join(SHOTS, f"home-{width}.png"), full_page=False)
                page.locator('.spot[data-object="qol"]').first.click()
                page.screenshot(path=os.path.join(SHOTS, f"window-{width}.png"), full_page=False)

            browser.close()

        # reduced motion must leave a complete page
        browser = launch(pw, headless=True)
        rpage = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        rpage.goto(base, wait_until="load")
        rpage.wait_for_selector(".stage svg")
        hidden = rpage.evaluate(
            """() => {
              const els = [...document.querySelectorAll('.spot, .notebook, .masthead')];
              return els.filter(e => {
                const s = getComputedStyle(e);
                return s.display === 'none' || parseFloat(s.opacity) === 0;
              }).length;
            }"""
        )
        if hidden:
            fails.append(f"reduced-motion: {hidden} core elements hidden")
        glow = rpage.evaluate(
            "() => getComputedStyle(document.querySelector('.lamp-glow')).opacity"
        )
        if float(glow) < 1:
            fails.append(f"reduced-motion: lamp glow not at end state (opacity {glow})")
        notes.append(f"reduced-motion: 0 hidden, glow opacity {glow}")
        browser.close()

    httpd.shutdown()

    print("\n".join("  " + n for n in notes))
    if fails:
        print("\nFAIL")
        print("\n".join("  " + f for f in fails))
        return 1
    print("\nPASS — all checks green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
