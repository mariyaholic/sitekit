Made by Maria

# sitekit

Release a catalog-driven static-page generator and browser audit gate as an
Apache-2.0 developer tool.

free and open source (Apache-2.0). See [LICENSE](LICENSE) and [NOTICE](NOTICE).

sitekit renders one room-style catalog into a deterministic static page and
Markdown, then checks the built page in a real browser against the same
catalog: room and item counts, navigation, the details interaction,
reduced-motion behaviour, theme tokens and horizontal overflow at narrow and
wide viewports. It is deliberately narrow; see
[docs/CONTRACT.md](docs/CONTRACT.md) for the supported catalog, markup and
CLI contract, and [ROADMAP.md](ROADMAP.md) for what is out of scope.

## Requirements

- Node.js 22 or newer (builder, no npm dependencies).
- Python 3.13 or newer for the optional browser audit.
- Playwright for Python plus one supported browser for the audit
  (Edge, Chrome or Playwright's bundled Chromium).

## Install and build

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt  # exact reviewed versions
.venv/bin/python -m playwright install chromium

node build.mjs                 # writes dist/ from the example catalog
node build.mjs --check         # CI gate: fails when dist/ is stale
.venv/bin/python audit.py      # browser audit, writes audit-report.json
```

Change a catalog entry, run `node build.mjs --check`, and stale generated
files are named without anything being written.

The deterministic build and freshness check also run together via
`./scripts/build.sh` or `scripts/build.ps1` on Windows. Generated `dist/`
and `audit-report.json` are local outputs and are not tracked.

## Usage and configuration

Configure audit viewports, tokens and paths with `--config audit.config.json`;
CLI flags override configuration values. See [the contract](docs/CONTRACT.md).

## Commands

| Command | Purpose |
| --- | --- |
| `node build.mjs` | Render `examples/room-catalog/catalog.json` into `dist/`. |
| `node build.mjs --check` | Verify `dist/` is byte-identical; never writes. Exit `1` when stale. |
| `node build.mjs --catalog <file> --out <dir>` | Build another compatible catalog. |
| `node build.mjs --warn-unsupported` | Warn instead of fail on unsupported schema keywords. |
| `.venv/bin/python audit.py` | Audit `dist/` against the catalog on a loopback server. |
| `python3 audit.py --browser chromium --no-report` | Explicit browser, no report file. |
| `npm test` | Node unit/golden tests plus the Python pytest suite. |

Exit codes: builder `0` success, `1` invalid input or stale output, `2` usage
or I/O error. Audit `0` all checks pass, `1` a check failed, `2` setup failed
(missing Playwright, browser or config). A missing browser is an explicit
failure, never a silent pass.

## Supported contract

The catalog is validated against a documented **six-keyword** JSON Schema
subset (`type`, `properties`, `required`, `items`, `enum`,
`additionalProperties`). Unsupported keywords anywhere in supported subschemas fail by default so partial
validation cannot be mistaken for full JSON Schema support. Room ids map to
fixed asset paths (`assets/rooms/<id>.svg`); the page contract, ARIA wiring
and audit report shape are documented in
[docs/CONTRACT.md](docs/CONTRACT.md).

## Repository layout

```text
build.mjs                 builder CLI
src/                      argument parsing, subset validator, renderer, freshness check
audit.py                  audit CLI
sitekit_audit/            config merging, expectations, server, browser checks, report
examples/room-catalog/    example catalog, schema, CSS/JS and room illustrations
tests/node/               node:test unit and CLI tests
tests/python/             pytest config, server, report and browser tests
tests/golden/             recorded golden HTML and Markdown
docs/CONTRACT.md          supported v1 contract
```

## Privacy and network use

The builder never uses the network. The audit starts a loopback HTTP server on
`127.0.0.1` with a random port to serve the local built site, and uses
Playwright against a local browser; nothing is uploaded and there is no
telemetry. Installation of Playwright and its browser is a one-time developer
step.

## Status

Early development, v1 scope. Not affiliated with MetaQuotes; MetaTrader 5
(MT5) is a MetaQuotes trademark, and sitekit contains no MT5 integration.
Windows binaries, if produced in future, are not code-signed yet; Windows
SmartScreen may warn when they are downloaded or run. This source-only project
does not currently ship Windows binaries.

See [docs/TESTING.md](docs/TESTING.md) for test guidance, and
[THIRD_PARTY.md](THIRD_PARTY.md) for dependency licences.

Python requirements pin the reviewed runtime and test dependencies exactly.
See [THIRD_PARTY.md](THIRD_PARTY.md) for licence exceptions and asset provenance.
