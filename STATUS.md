# Status

The v1 catalog builder and optional browser audit are implemented. Schema
preflight visits absent properties and empty-array item schemas. The audit
server serves verified open file handles. The Manager accepted PSF-2.0 for
pinned greenlet and typing_extensions; see THIRD_PARTY.md for terms and asset
provenance.

Source and test code: 3,608 lines (tracked Python and JavaScript, including
scripts and example JavaScript; excludes styles, JSON, documentation and
generated output; `git ls-files '*.py' '*.mjs' '*.js' | xargs wc -l`).

Linux review results (2026-10-28, run by Ava outside the Terra sandbox):

- `SITEKIT_PYTHON=/tmp/sitekit-venv/bin/python npm test`: passed; 61 Node tests passed, then the Python stage.
- `/tmp/sitekit-venv/bin/python -m pytest`: 60 passed.
- `/tmp/sitekit-venv/bin/python audit.py`: 84 checks, 84 passed.
- `./scripts/build.sh`: passed; 8 files generated and freshness check passed.
- `python3 scripts/check_format.py`: passed.

There is no Go or Rust module or native executable to cross-build; Windows
runtime and PowerShell checks were not run here.
Real Windows testing remains necessary for the handle path check, symlinks,
PowerShell and browser channels. Asset ownership and upstream rights remain
unresolved.
