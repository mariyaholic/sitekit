# Third-party software

sitekit itself is Apache-2.0 (see [LICENSE](LICENSE) and [NOTICE](NOTICE)).
This file records third-party components and their licences. All are
compatible with Apache-2.0; no GPL code is used.

## Runtime

| Component | Version | Licence | Use |
| --- | --- | --- | --- |
| [Playwright for Python](https://playwright.dev/python/) | 1.64.x (>=1.40,<2) | Apache-2.0 | Optional browser audit (`audit.py`). Not required by the Node builder. |
| [Python](https://www.python.org/) | 3.13+ | PSF-2.0 | Audit runtime and test interpreter. |

Playwright installs its own browser builds on first use; those are covered by
the upstream Playwright notices. sitekit does not redistribute them.

## Development and test only

| Component | Version | Licence | Use |
| --- | --- | --- | --- |
| [pytest](https://pytest.org/) | 9.x (>=8,<10) | MIT | Python test runner. |
| [Node.js](https://nodejs.org/) | 22+ | MIT | Builder runtime and `node:test` runner. |

The builder has no npm dependencies; it uses Node built-ins only.

## Assets

The example SVG illustrations and CSS/JS in `examples/room-catalog/assets/`
are original work by Maria, licensed with the project under Apache-2.0.

## Updating this file

When adding a dependency, record it here before merging. Allowed licences:
MIT, BSD, ISC, Apache-2.0, Zlib. Do not add GPL or unknown-licence code.
