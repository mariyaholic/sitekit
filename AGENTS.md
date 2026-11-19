# Agent brief — sitekit

Made by Maria. Licence: Apache-2.0 (LICENSE, NOTICE). Credit name is "Maria" only.

1. Follow docs/ARCHITECTURE.md. Implement **v1 scope only**; roadmap/future items stay out (write them in ROADMAP.md if useful).
2. MT5 / MetaTrader: **strictly read-only**. No order placement, modification, closing or any trading call. Not affiliated with MetaQuotes; MT5 is a MetaQuotes trademark.
3. Tests are required for every module: unit tests for core logic, golden/fixture tests for parsers. Work is done only when build and tests pass; report the exact commands and results in STATUS.md.
4. Node/Python: `npm test` (and `pytest` if Python is used) must pass on Linux.
5. No network publishing: no git push, no git remote, no package publishing, no uploads, no telemetry. Network use at runtime only where the architecture requires it, opt-in and documented.
6. Stay inside this repository directory. Do not read or modify anything outside it (other than toolchain caches). Never read or print credentials.
7. Keep LICENSE and NOTICE unchanged. README must keep "Made by Maria" as its first line. UI apps show "Made by Maria" in an About screen. Store copy: "free and open source (Apache-2.0)". Add SPDX-License-Identifier: Apache-2.0 headers to source files. Third-party deps: MIT/BSD/ISC/Apache-2.0/Zlib only; record them in THIRD_PARTY.md; no GPL code.
8. Commit locally in small, meaningful commits (author Maria). At the end write STATUS.md: what is built, build/test commands and results, LOC, tests needing real Windows, open issues.

<!-- uika:law:begin -->
## Uika estate law (generated — do not edit inside the markers)

This repo is part of the Uika estate. The estate layer lives in the harness homes; this
block carries only what every session here must obey. Edit the source (Uika `estate.json`),
never this block; `uika docs render` regenerates it.

- **Session start:** freshness scan (mtime-first), then read `WORKSTACK.md`.
- **Handoff:** one 6-line block in the WORKSTACK thread — `From→To / Done / Next / Files / Verify / Blockers` (skills/handoff-protocol).
- **Names:** handle `<harness>.<role>`; harness ∈ {claude, codex, opencode, cline, gemini, commandcode, dsh, freebuff, mimo, hermes}; role ∈ {tower, scout, impl, review, judge}. Model is a field, never a name.
- **Branches:** `<feat|fix|docs|chore>/<kebab-topic>`, ≤ 4 words, no agent names. Never push or rewrite main.
- **Posture:** near-autopilot, secrets egress-locked, self-edit lock full.
- **Find things:** `uika find` / `uika where` before exploring; `uika path` / `uika layout` for where a file goes.
- **Prose:** in chat replies, files, code comments, commits and product text, never write a negation-first reveal, significance designation, abstraction agency, deferred noun, coy or thesis-shaped header, aphoristic closer, straw-man knockdown, fragment cadence, dressed metaphor or label-first framing (skills/plain-prose, ADR-0062).
- **Finish:** run the wrap checklist; update `WORKSTACK.md`.

Full laws: Uika `AGENTS.md` and `register/adr/`. Skills: skills/handoff-protocol, find-fast, estate-sync, plain-prose.
<!-- uika:generated from estate.json; edit the source, not this file -->
<!-- uika:docs v1 · sha256:e2ad5a28c274 -->
<!-- uika:law:end -->
