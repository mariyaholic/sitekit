# Third-party software and assets

sitekit is Apache-2.0 (see [LICENSE](LICENSE) and [NOTICE](NOTICE)). The
builder has no npm dependencies: `package.json` declares none and there is no
package-lock or installed node_modules to audit. The following versions are
pinned in the requirements files. Licences were checked against installed
Python distribution METADATA and declared licence files in the reviewed
virtual environment; raw metadata is retained in the review scratch directory.

| Package | Version | Licence from installed metadata | Purpose |
| --- | --- | --- | --- |
| Playwright | 1.64.1 | Apache-2.0 | Browser audit |
| greenlet | 3.5.6 | MIT AND PSF-2.0 | Playwright dependency |
| pyee | 14.0.0 | MIT | Playwright dependency |
| typing_extensions | 4.16.0 | PSF-2.0 | pyee dependency |
| pytest | 9.2.0 | MIT | Tests |
| iniconfig | 2.3.1 | MIT | Tests |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | Tests |
| pluggy | 1.7.0 | MIT | Tests |
| Pygments | 2.21.0 | BSD-2-Clause | Tests |

**PSF-2.0 acceptance:** greenlet 3.5.6 and typing_extensions 4.16.0 were
accepted by the Manager on 2026-10-28 because PSF-2.0 is permissive,
OSI-approved, and attribution is retained. Preserve the applicable PSF licence
text and attribution with redistributed components. The external Python runtime
also uses PSF-2.0 and is not bundled. Node.js is an external runtime. Playwright's installed distribution
contains a driver and bundled third-party notices; browser binaries are
separate and were not audited. Preserve upstream licence and notice files when
redistributing these components; no browser is redistributed by sitekit.
Pip 25.1.1 (MIT, metadata) is an environment tool, not a project dependency.

## Assets and provenance

The CSS, JavaScript and four SVGs in `examples/room-catalog/assets/` carry
Apache-2.0 SPDX headers and are present in local commit `6d42366`. The local
history does not establish their original authorship, extraction history or
third-party rights. The prior claim that all assets were original work by
Maria is not independently verified. The original source fixture is not
available for a byte-compatibility comparison. These points require owner
review before redistribution; no additional attribution can be verified offline.

When adding dependencies, record version, licence and verification here. The
allowed list is MIT, BSD, ISC, Apache-2.0, Zlib, Unicode and justified CC0 or
public domain. PSF-2.0 is also allowed for greenlet 3.5.6 and
typing_extensions 4.16.0 under the Manager's acceptance above; flag other
licences and other uses of PSF-2.0 for review.
