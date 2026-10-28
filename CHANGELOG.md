# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - Unreleased

### Added

- Catalog-driven static site builder and optional browser audit.
- Cross-platform build scripts, CI configuration, and contribution guidance.

### Changed

- Record the Manager's acceptance of PSF-2.0 for the pinned greenlet and typing_extensions dependencies.

### Fixed

- Validate nested schemas even when data is absent or arrays are empty.
- Serve files from verified open handles and reject raced symlinks.
- Check source whitespace in CI on clean checkouts and pin Python dependencies.

- Reject malformed audit catalog statuses and slugs and foreign audit server requests.
