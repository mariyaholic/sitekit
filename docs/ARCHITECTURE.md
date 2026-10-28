# sitekit

## Six fields

1. **One-line pitch:** [inferred] Release a catalog-driven static-page generator and browser audit gate as an Apache-2.0 developer tool.
2. **Who it's for:** [inferred] Maintainers of sites using the supported room-style catalog and interaction contract who want reproducible output and a CI check.
3. **5-second demo shot:** [inferred] Change a catalog entry, run `node build.mjs --check`, and see the stale generated files named.
4. **Overlap check:** [inferred] Windows built-ins and PowerToys do not supply this combined catalog build and interaction gate; static-site generators, JSON Schema validators and Playwright test suites cover overlapping jobs and are more flexible for other site designs.
5. **Reuse:** [measured] The separate, non-Yozora [sitekit README](/workspace/desk/ava/repo-survey/targets/sitekit/README.md:3), [build.mjs](/workspace/desk/ava/repo-survey/targets/sitekit/build.mjs:79), [audit.py](/workspace/desk/ava/repo-survey/targets/sitekit/audit.py:121), [audit.config.json](/workspace/desk/ava/repo-survey/targets/sitekit/audit.config.json:1), and [catalog.schema.json](/workspace/desk/ava/repo-survey/targets/sitekit/catalog.schema.json:1) are the release starting point. [measured] The builder uses fixed room asset paths and emits room-specific markup ([build.mjs](/workspace/desk/ava/repo-survey/targets/sitekit/build.mjs:144)); the audit derives expectations from catalog entries ([audit.py](/workspace/desk/ava/repo-survey/targets/sitekit/audit.py:286)).
6. **Caveats:** [measured] The brief records no sitekit license ([BRIEF.md](/workspace/qol-portfolio/BRIEF.md:77)); verify ownership, extraction history and third-party rights before an Apache-2.0 release. [measured] The validator implements only a schema subset, and the tool requires fixed room asset names and a specific markup contract ([README](/workspace/desk/ava/repo-survey/targets/sitekit/README.md:40), [README](/workspace/desk/ava/repo-survey/targets/sitekit/README.md:48), [README](/workspace/desk/ava/repo-survey/targets/sitekit/README.md:183)). [inferred] Do not advertise full JSON Schema validation or arbitrary-site compatibility. Browser audit requires Playwright and a supported browser ([measured] [README](/workspace/desk/ava/repo-survey/targets/sitekit/README.md:21)).

## Edge over defaults

[inferred] For a compatible catalog, one check can detect stale HTML and text output, while one browser run checks catalog-derived counts, navigation, accessibility-related interactions and configured tokens. Test that claim using a sample catalog and deliberately stale output or broken interaction. This is a focused workflow advantage; general-purpose generators and browser tests can implement the same checks and are better suited to different markup.

## Architecture

- **Stack:** [measured] Retain Node built-ins for the builder and Python plus Playwright for audit ([README](/workspace/desk/ava/repo-survey/targets/sitekit/README.md:7)); Node 22+ and Python 3.13+ are the stated requirements ([README](/workspace/desk/ava/repo-survey/targets/sitekit/README.md:21)). [inferred] Avoid adding a framework unless generalization proves necessary.
- **Modules:** [inferred] Separate argument handling, documented subset validation, catalog-to-HTML/Markdown rendering and freshness comparison; retain audit config merging, catalog-derived expectations, loopback server, browser checks and machine-readable report. [measured] The server binds loopback ([audit.py](/workspace/desk/ava/repo-survey/targets/sitekit/audit.py:70)); browser launch tries Edge, Chrome and bundled Chromium ([audit.py](/workspace/desk/ava/repo-survey/targets/sitekit/audit.py:101)). [inferred] Extract room-specific templates/assets into an explicit example and define a supported template contract before claiming reuse beyond it; preserve a byte-compatible room fixture.
- **Key platform APIs:** [measured] Node filesystem/path and Python HTTP server plus Playwright browser APIs are used ([build.mjs](/workspace/desk/ava/repo-survey/targets/sitekit/build.mjs:11), [audit.py](/workspace/desk/ava/repo-survey/targets/sitekit/audit.py:70), [audit.py](/workspace/desk/ava/repo-survey/targets/sitekit/audit.py:329)); no Windows-specific API is required [inferred].
- **Data/config:** [measured] Catalog JSON, example schema, CSS/JS/SVG and audit JSON drive generated `index.html`, `catalog.md` and optional audit report ([README](/workspace/desk/ava/repo-survey/targets/sitekit/README.md:14), [audit.py](/workspace/desk/ava/repo-survey/targets/sitekit/audit.py:266)). [inferred] Document the six supported schema keywords and fail or explicitly warn on unsupported keywords so users cannot mistake partial validation for full validation. Keep `--check` non-writing.
- **Packaging:** [inferred] After rights review, distribute source and example fixtures in a versioned GitHub Release; publish runtime and browser setup instructions. A source-only developer tool needs neither winget nor MSIX; revisit only if a standalone Windows executable is produced. Include Apache-2.0 `LICENSE`, SPDX headers, and a `THIRD_PARTY` license inventory, preserving upstream notices. [measured] The brief directs that winutil's hardcoded mutex and credential prefix become per-app in internal cleanup, not a separate library release ([BRIEF-v5.md](/workspace/qol-portfolio/BRIEF-v5.md:20); [sysutil.go](/workspace/desk/ava/repo-survey/targets/winutil/sysutil/sysutil.go:30), [credman.go](/workspace/desk/ava/repo-survey/targets/winutil/credman/credman.go:37)).
- **Signing:** [measured] Ava's supplied [SignPath terms](https://signpath.org/terms), not independently re-verified, say developer tools are likely exempt from the reputation check; approval remains discretionary and application is the Manager's call. Requirements include GitHub and SignPath 2FA, CI-built binaries, manual approval per release, a “Code signing policy” naming authors/reviewers/approvers and a download-page privacy statement; signed publisher is “SignPath Foundation” ([BRIEF.md](/workspace/qol-portfolio/BRIEF.md:87)). [inferred] Source-only releases do not require executable signing. If binaries are later shipped, provide SHA256SUMS and “not code-signed yet”/SmartScreen caveat on GitHub and winget until approved; apps need an uninstaller and warning before changing system settings. [measured] The brief supplies, without independent verification, that the Store re-signs MSIX after certification; EXE/MSI submissions require trusted pre-signing and reject self-signed certificates ([BRIEF.md](/workspace/qol-portfolio/BRIEF.md:76)).
- **Tests:** [inferred] Use a redistributable fixture to compare deterministic outputs, `--check` fresh/stale and exit codes, bad input and each supported schema keyword; explicitly test unsupported-keyword handling, escaping, missing files and overrides. Run browser audits on narrow/wide viewports with broken navigation, token and reduced-motion fixtures; verify missing browser fails. Run Node/Python tests on a clean CI runner and verify provenance and notices before release.
- **Size:** [guess] S–M: 3–7 developer days and 300–800 changed LOC, excluding rights clearance and any broad template redesign.

## Licensing

[measured] The Manager requires Apache-2.0 for every project ([Amendment 10a](/workspace/qol-portfolio/BRIEF-v5.md:40)). Include the full Apache-2.0 text in `LICENSE`, use `SPDX-License-Identifier: Apache-2.0` on project source where practical, and open every README with “Made by Maria”. If a UI app is introduced, its About screen must show “Made by Maria”. Store copy, where applicable: “free and open source (Apache-2.0)”. The root `NOTICE` is exactly:

```text
sitekit
Copyright 2026 Maria (https://github.com/mariyaholic)

Made by Maria. This product includes software developed by Maria.
```

[inferred] MIT, BSD, ISC, Apache-2.0 and Zlib dependencies are compatible subject to their terms; retain required third-party notices in `THIRD_PARTY` so the required root template stays exact. Audit all code, transitive dependencies and assets; do not reuse GPL code such as mukunku/ParquetViewer. Rights and obligations still require review.

[measured] The [SignPath application draft](/workspace/qol-portfolio/SIGNPATH_APPLICATION_DRAFT.md:1) is draft only; a public repository and an existing public release are prerequisites and the Manager decides publication/application. Apache-2.0 preserves eligibility; no application or publishing is authorized by this architecture.

## Open questions

- [inferred] Who owns each extracted file and example asset, and are all dependencies and assets redistributable under their existing terms alongside Apache-2.0?
- [inferred] Is the intended first release limited to the room contract, or must templates and asset names be configurable? This decision changes scope and estimate.
- [inferred] Should unsupported schema keywords fail by default, and which browser/runtime versions will CI support?
