// SPDX-License-Identifier: Apache-2.0

import { statusLabel, roomAssetPath } from "./catalog.mjs";
import { escapeHtml, escapeMarkdown } from "./escape.mjs";

/**
 * Render the room catalog as one deterministic HTML page.
 * @param {object} catalog
 * @returns {string}
 */
export function renderHtml(catalog) {
  const { site, rooms } = catalog;
  const lines = [
    "<!doctype html>",
    '<html lang="en">',
    "  <head>",
    '    <meta charset="utf-8">',
    '    <meta name="viewport" content="width=device-width, initial-scale=1">',
    `    <meta name="description" content="${escapeHtml(site.description)}">`,
    `    <title>${escapeHtml(site.title)}</title>`,
    '    <link rel="stylesheet" href="assets/site.css">',
    '    <script src="assets/site.js" defer></script>',
    "  </head>",
    "  <body>",
    '    <a class="skip-link" href="#content">Skip to content</a>',
    '    <header class="site-header">',
    `      <h1>${escapeHtml(site.title)}</h1>`,
    `      <p class="site-tagline">${escapeHtml(site.tagline)}</p>`,
    "    </header>",
    '    <nav class="room-nav" aria-label="Rooms">',
    "      <ul>",
  ];

  for (const room of rooms) {
    lines.push(
      `        <li><a href="#room-${escapeHtml(room.id)}">${escapeHtml(room.name)}</a></li>`,
    );
  }

  lines.push("      </ul>", "    </nav>", '    <main id="content">');

  for (const room of rooms) {
    const roomId = escapeHtml(room.id);
    const name = escapeHtml(room.name);
    const detailsId = `room-${roomId}-details`;
    lines.push(
      `      <section class="room" id="room-${roomId}" data-room-id="${roomId}" aria-labelledby="room-${roomId}-title">`,
      '        <header class="room__header">',
      `          <h2 id="room-${roomId}-title">${name}</h2>`,
      `          <p class="room__status" data-status="${escapeHtml(room.status)}">${escapeHtml(statusLabel(room.status))}</p>`,
      "        </header>",
      `        <img class="room__image" src="${escapeHtml(roomAssetPath(room.id))}" alt="Illustration for ${name}" width="320" height="180">`,
      `        <p class="room__summary">${escapeHtml(room.summary)}</p>`,
      '        <ul class="room__tags" aria-label="Tags">',
    );
    for (const tag of room.tags) {
      lines.push(`          <li class="room__tag">${escapeHtml(tag)}</li>`);
    }
    lines.push(
      "        </ul>",
      `        <button class="room__toggle" type="button" aria-expanded="false" aria-controls="${detailsId}" aria-label="Details for ${name}">Details</button>`,
      `        <div class="room__details" id="${detailsId}" hidden>`,
      '          <h3 class="room__items-title">Items</h3>',
      '          <ul class="room__items">',
    );
    for (const item of room.items) {
      const note = Object.hasOwn(item, "note")
        ? `\n              <span class="room__item-note">${escapeHtml(item.note)}</span>`
        : "";
      lines.push(
        `            <li class="room__item" data-item-id="${escapeHtml(item.id)}">`,
        `              <span class="room__item-label">${escapeHtml(item.label)}</span>${note}`,
        "            </li>",
      );
    }
    lines.push("          </ul>", "        </div>", "      </section>");
  }

  lines.push(
    "    </main>",
    '    <footer class="site-footer">',
    "      <p>Made by Maria. Free and open source (Apache-2.0).</p>",
    "    </footer>",
    "  </body>",
    "</html>",
    "",
  );

  return lines.join("\n");
}

/**
 * Render the catalog as Markdown.
 * @param {object} catalog
 * @returns {string}
 */
export function renderMarkdown(catalog) {
  const { site, rooms } = catalog;
  const lines = [
    `# ${escapeMarkdown(site.title)}`,
    "",
    escapeMarkdown(site.tagline),
    "",
    escapeMarkdown(site.description),
    "",
    "## Rooms",
    "",
  ];

  for (const room of rooms) {
    lines.push(
      `### ${escapeMarkdown(room.name)}`,
      "",
      `- Status: ${escapeMarkdown(statusLabel(room.status))}`,
      `- Tags: ${room.tags.map((tag) => escapeMarkdown(tag)).join(", ") || "none"}`,
      "",
      escapeMarkdown(room.summary),
      "",
    );
    for (const item of room.items) {
      const note = Object.hasOwn(item, "note") ? ` — ${escapeMarkdown(item.note)}` : "";
      lines.push(`- ${escapeMarkdown(item.label)}${note}`);
    }
    lines.push("");
  }

  return lines.join("\n");
}
