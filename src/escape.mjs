// SPDX-License-Identifier: Apache-2.0

const HTML_ESCAPES = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
};

/**
 * Escape a value for HTML text and double-quoted attribute contexts.
 * @param {unknown} value
 * @returns {string}
 */
export function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => HTML_ESCAPES[character]);
}

/**
 * Collapse line breaks so a value can live in a Markdown heading or table cell.
 * Pipes are escaped because room summaries may appear inside tables.
 * @param {unknown} value
 * @returns {string}
 */
export function escapeMarkdown(value) {
  return String(value).replace(/\r?\n/g, " ").replace(/\|/g, "\\|");
}
