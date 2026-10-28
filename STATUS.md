# Status

The v1 catalog builder and optional browser audit are implemented. Schema
preflight now visits absent properties and empty-array item schemas. The audit
server serves verified open file handles. Python dependencies are pinned; see
THIRD_PARTY.md for unresolved licence exceptions and asset provenance.

Source and test code: 3,587 lines (Python and JavaScript, including scripts;
excludes styles, JSON, documentation and generated output).

Linux review results (2026-10-28):

- `SITEKIT_PYTHON=/tmp/sitekit-venv/bin/python npm test`: failed, 4 Node test files passed and 1 failed (child process `EPERM`); Python stage did not run.
- `/tmp/sitekit-venv/bin/python -m pytest`: 44 passed, 12 failed, 4 skipped; all failures occurred creating loopback sockets (`PermissionError`).
- `/tmp/sitekit-venv/bin/python audit.py`: failed creating a loopback socket (`PermissionError`).
- `node --test --experimental-test-isolation=none tests/node/args.test.mjs tests/node/catalog.test.mjs tests/node/render.test.mjs tests/node/schema.test.mjs`: 42 passed.
- `./scripts/build.sh`: passed; 8 files generated and freshness check passed.
- `python3 scripts/check_format.py`: passed.

Real Windows testing remains necessary for the handle path check, symlinks,
PowerShell and browser channels. The complete test suite has not passed in
this sandbox. Asset ownership and upstream rights remain unresolved; two
Python dependencies carry PSF-2.0, outside the permitted dependency list.
