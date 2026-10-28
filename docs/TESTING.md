# Testing

Run `npm test` for the Node tests and Python pytest suite. Set
`SITEKIT_PYTHON` to a Python interpreter with `requirements-dev.txt`
installed if the repository virtual environment is absent. Browser tests
require Playwright and Chromium; install it with
`python -m playwright install chromium` on a network-enabled development or CI
machine. Browser-dependent tests skip when the browser is unavailable.

Run `./scripts/build.sh` or `scripts/build.ps1` to build the example and check
its generated output. Node tests cover validation, rendering, golden files,
CLI errors and freshness; Python tests cover configuration, expectations,
server containment, reporting and browser behaviour.

Windows CI exercises the same suites. Real Windows testing is still needed
for Edge and Chrome browser channels and for confirmation of platform-specific
filesystem and browser behaviour. No native executable is built.

## Current local verification

On Linux, `./scripts/build.sh` passed (8 generated files and a fresh check).
`npm test` failed: 4 Node test files passed and 1 failed because this
environment rejects child process creation with `EPERM`; its Python stage did
not run. `python3 -m pytest -q` failed because pytest is not installed.
`node --test --experimental-test-isolation=none tests/node/args.test.mjs
tests/node/catalog.test.mjs tests/node/render.test.mjs tests/node/schema.test.mjs`
passed 41 tests. `python3 -m compileall -q sitekit_audit tests/python audit.py`
passed. Tests must be rerun in a complete environment.

Source and test files total 3,424 lines as measured in this review (excluding
styles, JSON, documentation and generated output).
