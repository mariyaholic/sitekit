# Roadmap

Items below are explicitly **not** part of v1 and are not implemented.

- Configurable template directories and asset names, instead of the fixed
  room contract in [docs/CONTRACT.md](docs/CONTRACT.md).
- Full JSON Schema validation (or at least `pattern`, `minItems`, `oneOf`,
  `$defs`/`$ref`). v1 fails on unsupported keywords on purpose.
- Additional audit checks: colour contrast ratios, screenshots, link crawl.
- Windows standalone executable, winget/MSIX packaging and code signing. v1 is
  a source-only developer tool, so signing is not required.
- GitHub Release automation and provenance attestations (publication is a
  separate, Manager-owned decision).
- Multi-page catalogs and incremental builds.
