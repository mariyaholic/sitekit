# Supported contract (v1)

sitekit is deliberately narrow. This document defines the catalog, the
generated page, the asset layout, the CLI and the audit report. Anything not
described here is out of scope for v1; see [ROADMAP.md](../ROADMAP.md).

## Catalog

The catalog is a JSON object validated against a JSON Schema that uses the
six-keyword subset described below. The example lives at
[`examples/room-catalog/catalog.json`](../examples/room-catalog/catalog.json).

```json
{
  "version": 1,
  "site": {
    "title": "Atrium Rooms",
    "tagline": "One page, four rooms, no build framework.",
    "description": "A short page description used for the meta tag."
  },
  "rooms": [
    {
      "id": "studio",
      "name": "Studio",
      "status": "open",
      "summary": "A sentence about the room.",
      "tags": ["writing", "daylight"],
      "items": [
        { "id": "desk", "label": "Oak desk", "note": "Faces the window." }
      ]
    }
  ]
}
```

Rules beyond the schema:

- `room.id` and `item.id` are slugs: `[a-z0-9][a-z0-9-]*`.
- Room ids are unique; item ids are unique within a room.
- Every room must have at least one item, because the generated interaction
  (the details disclosure) needs something to disclose.
- `status` is one of `open`, `closed`, `planned`; the page label is `Open`,
  `Closed` or `Planned`.
- Every room needs an illustration at the fixed path
  `assets/rooms/<room-id>.svg`.

## Schema subset

The validator trusts **only these six validating keywords**:

| Keyword | Behaviour |
| --- | --- |
| `type` | `object`, `array`, `string`, `number`, `integer`, `boolean`, `null`, or an array of those |
| `properties` | Validates each present member against its subschema |
| `required` | Names members that must be present |
| `items` | Validates every array element against one subschema |
| `enum` | Deep equality against a list of allowed values |
| `additionalProperties` | `false` rejects undeclared members; `true` or absent allows them |

`$schema`, `$id`, `title`, `description`, `default` and `$comment` are allowed
as annotations and do not validate anything.

Other keywords (`oneOf`, `pattern`, `minItems`, `format`, ...) encountered
while validating present data are errors by default, because silently ignoring it would suggest full JSON Schema support.
`--warn-unsupported` downgrades those errors to warnings, and the CLI prints
each one. This is a documented subset, not a JSON Schema implementation.

## Generated page

`build.mjs` writes a deterministic page per catalog:

- `index.html` — the site.
- `catalog.md` — the same catalog as Markdown.
- `assets/site.css`, `assets/site.js` — copied unchanged from the catalog
  example's `assets/` directory.
- `assets/rooms/<room-id>.svg` — copied unchanged for every room.

The page contract (class names, ids and ARIA attributes are public API for the
audit and for template authors):

```html
<a class="skip-link" href="#content">Skip to content</a>
<header class="site-header">
  <h1>Site title</h1>
  <p class="site-tagline">Tagline</p>
</header>
<nav class="room-nav" aria-label="Rooms">
  <ul><li><a href="#room-studio">Studio</a></li></ul>
</nav>
<main id="content">
  <section class="room" id="room-studio" data-room-id="studio"
           aria-labelledby="room-studio-title">
    <h2 id="room-studio-title">Studio</h2>
    <p class="room__status" data-status="open">Open</p>
    <img class="room__image" src="assets/rooms/studio.svg" alt="Illustration for Studio">
    <p class="room__summary">...</p>
    <ul class="room__tags"><li class="room__tag">writing</li></ul>
    <button class="room__toggle" type="button"
            aria-expanded="false" aria-controls="room-studio-details">Details</button>
    <div class="room__details" id="room-studio-details" hidden>
      <ul class="room__items">
        <li class="room__item" data-item-id="desk">...</li>
      </ul>
    </div>
  </section>
</main>
<footer class="site-footer"><p>Made by Maria. Free and open source (Apache-2.0).</p></footer>
```

Interaction contract: clicking a room toggle (or focusing it and pressing
Enter/Space) flips `aria-expanded` and the `hidden` attribute of the controlled
panel. The CSS applies a transition only under
`@media (prefers-reduced-motion: no-preference)`, so reduced-motion users get
no animation.

The page exposes the theme tokens on `:root`, and the audit checks them:

```css
:root {
  --sk-color-ink: #14201b;
  --sk-color-paper: #f7f4ec;
  --sk-color-accent: #1f6f5c;
  --sk-radius: 14px;
}
```

## Builder CLI

```text
node build.mjs [--catalog <file>] [--schema <file>] [--out <dir>]
               [--check] [--warn-unsupported] [--json]
```

Defaults: catalog `examples/room-catalog/catalog.json`, schema next to the
catalog (`catalog.schema.json`), output `dist`.

Exit codes: `0` success (or fresh, with `--check`); `1` invalid catalog/schema,
missing input or stale output; `2` usage or I/O error.

`--check` never writes. It reports each missing, stale or non-matching output
and exits `1` when anything differs, so CI can gate a pull request.

## Audit CLI

```text
python3 audit.py [--config <file>] [--root <dir>] [--catalog <file>]
                 [--report <file> | --no-report] [--browser <name>]
```

`--root` is the directory served over loopback (default `dist`); `--catalog` is
the source of expected content. CLI values override the file supplied with `--config`, which overrides
built-in defaults. The example `audit.config.json` is not loaded automatically. Browser names: `auto`, `msedge`, `chrome`,
`chromium`; `auto` tries Edge, then Chrome, then Playwright's bundled Chromium.

The audit starts an HTTP server on `127.0.0.1` with a random port, checks the
catalog-derived structure, the interaction, reduced-motion behaviour, the
configured tokens and horizontal overflow at narrow and wide viewports, writes
an optional JSON report and exits `0` when every check passes, `1` when any
check fails and `2` when setup fails (missing Playwright, missing browser,
invalid config). A missing browser is an explicit failure, never a silent pass.

Report shape (stable, no timestamps so runs are reproducible):

```json
{
  "tool": "sitekit-audit",
  "version": "0.1.0",
  "site": { "title": "Atrium Rooms", "roomCount": 4 },
  "summary": { "total": 40, "passed": 40, "failed": 0 },
  "checks": [
    { "id": "room-count", "viewport": "wide", "status": "pass", "detail": "4 rooms" }
  ]
}
```

## Out of scope for v1

Arbitrary site markup, full JSON Schema, templating languages, non-room
catalogs, publishing, telemetry and any MT5/trading integration.
