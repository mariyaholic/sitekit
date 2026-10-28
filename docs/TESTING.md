# Testing

Run `SITEKIT_PYTHON=<python> npm test` with the exact versions in
`requirements-dev.txt`, then run `<python> -m pytest` and `<python> audit.py`.
Browser tests require Playwright and Chromium; install the browser on a
network-enabled development or CI machine. Browser tests skip when unavailable.
`python scripts/check_format.py` checks tracked Python and JavaScript source
for LF endings, final newlines, trailing whitespace and tab indentation even
on a clean checkout. It is a whitespace check, not a full code formatter.

Run `./scripts/build.sh` or `scripts/build.ps1` to build the example and check
its generated output. Node tests cover validation, rendering, golden files,
CLI errors and freshness; Python tests cover configuration, expectations,
server containment, reporting and browser behaviour.

The Linux review environment built the example and passed the socket-free
schema and descriptor tests. Full suites and browser audit were blocked by
child-process and loopback socket restrictions; see STATUS.md. Real Windows
checks are needed for the open-handle containment code, symlinks, PowerShell,
and Chromium, Edge and Chrome. No native executable is built.
