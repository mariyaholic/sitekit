# Status

Made by Maria. Apache-2.0. Last updated: 2026-10-28.

## What is built (v1)

A source-only developer tool in two halves, following
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and the contract in
[docs/CONTRACT.md](docs/CONTRACT.md):

- **Builder (Node 22+, no npm dependencies)** — `build.mjs` plus `src/`:
  argument parsing, JSON Schema subset validation (six validating keywords,
  unsupported keywords fail unless `--warn-unsupported`), semantic catalog
  checks (slugs, uniqueness, non-empty content, at least one item per room),
  deterministic HTML and Markdown rendering with escaping, fixed room asset
  copying, and a non-writing `--check` freshness gate. Exit codes are 0/1/2
  as documented.
- **Audit (Python 3.13+)** — `audit.py` plus `sitekit_audit/`: defaults →
  JSON file → CLI config merging with validation, catalog-derived
  expectations, a loopback-only HTTP server (random port, traversal
  containment), Playwright browser checks (Edge → Chrome → bundled Chromium),
  narrow/wide viewports, catalog counts, navigation, per-room content,
  details interaction by click and Enter, reduced motion, theme tokens,
  horizontal overflow, footer credit, and a stable JSON report. A missing
  Playwright or browser exits 2 with an actionable message.
- **Example fixture** — `examples/room-catalog/` with a schema, four rooms,
  CSS tokens and transitions, disclosure JS, and four original SVG
  illustrations.
- **Tests** — 60 Node tests (`node:test`) including golden HTML/Markdown and
  CLI process tests; 51 pytest tests covering config merge, expectations,
  server, report, CLI, and real-browser checks.

No MT5/trading code is present; the read-only MT5 rule does not apply to this
repository. No telemetry, no publishing, no network use beyond the local
loopback audit server.

## Verification

Environment: Linux x86_64, Node v22.23.4, Python 3.13.5, pytest 9.2.0,
Playwright 1.64.1 with bundled Chromium headless shell 156.

Commands run from the repository root, with exact results:

```text
$ npm test
# node --test "tests/node/*.test.mjs"
# tests 60
# pass 60
# fail 0
# pytest: 51 passed in 11.77s
exit 0

$ node build.mjs
sitekit: wrote 8 files to dist (dist)
exit 0

$ node build.mjs --check
sitekit: output is up to date (8 files in dist)
exit 0

$ .venv/bin/python audit.py
sitekit-audit: 84 checks, 84 passed, 0 failed
sitekit-audit: report written to audit-report.json
exit 0
```

Browser tests also assert that broken navigation, a wrong theme token and a
missing reduced-motion override each produce a failing check. The suite skips
browser tests (with a message) when Playwright or a browser is unavailable;
none were skipped in the run above.

## Lines of code

Tracked source, excluding generated `dist/` and the Python virtualenv:

| Area | Lines |
| --- | --- |
| Builder (`build.mjs`, `src/`, `scripts/`) | 1,044 |
| Audit (`audit.py`, `sitekit_audit/`) | 952 |
| Node tests | 665 |
| Python tests | 692 |
| Example catalog assets | 425 |
| Docs/config/Markdown | 610 |
| Golden output | 191 |

## Tests needing real Windows

None. No test requires Windows, and no Windows-only API is used. The browser
audit has only been exercised on Linux with bundled Chromium in this
environment; Edge/Chrome channels and Windows behaviour remain unverified.

## Open issues

- **Upstream provenance not verified.** `docs/ARCHITECTURE.md` points at a
  `repo-survey` copy outside this repository. The agent brief forbids reading
  outside the repository, so v1 was implemented from the architecture text;
  the claimed byte-compatible room fixture could not be compared with the
  original. Ownership, extraction history and third-party rights still need
  review before any release.
- **Deliberately partial validation.** Only six schema keywords are
  implemented; everything else fails by default. This is documented, not a
  bug, but users must not advertise it as full JSON Schema.
- **Fixed room template contract.** Template/asset names are not configurable
  in v1; a different site design needs code changes (see
  [ROADMAP.md](ROADMAP.md)).
- **Browser matrix.** Only bundled Chromium was available for verification;
  Edge and Chrome launch paths are implemented and unit-tested with fakes but
  not exercised on real browsers or real Windows.
- **CI environment setup.** The test suite expects Playwright plus
  `python3 -m playwright install chromium`; a clean CI runner needs that step
  (and pytest) before `npm test` can cover the browser tests.
- **Signing/packaging not started** and intentionally out of v1 scope; no
  binaries are produced, so no `SHA256SUMS`/SmartScreen copy applies yet.
