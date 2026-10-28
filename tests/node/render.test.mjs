// SPDX-License-Identifier: Apache-2.0

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { exampleCatalog } from "./helpers.mjs";
import { escapeHtml, escapeMarkdown } from "../../src/escape.mjs";
import { renderHtml, renderMarkdown } from "../../src/render.mjs";

const catalog = JSON.parse(await readFile(exampleCatalog, "utf8"));

test("escapes HTML metacharacters", () => {
  assert.equal(
    escapeHtml(`<a href="x">&'`),
    "&lt;a href=&quot;x&quot;&gt;&amp;&#39;",
  );
});

test("escapes pipes and newlines for Markdown", () => {
  assert.equal(escapeMarkdown("a|b\nc"), "a\\|b c");
});

test("renders the contract structure", () => {
  const html = renderHtml(catalog);
  assert.match(html, /^<!doctype html>\n<html lang="en">/);
  assert.match(html, /<a class="skip-link" href="#content">Skip to content<\/a>/);
  assert.match(html, /<nav class="room-nav" aria-label="Rooms">/);
  assert.match(html, /<main id="content">/);
  assert.equal((html.match(/class="room"/g) ?? []).length, catalog.rooms.length);
  assert.match(html, /Made by Maria\. Free and open source \(Apache-2\.0\)\./);
  for (const room of catalog.rooms) {
    assert.ok(html.includes(`id="room-${room.id}"`));
    assert.ok(html.includes(`href="#room-${room.id}"`));
    assert.ok(html.includes(`src="assets/rooms/${room.id}.svg"`));
    assert.ok(html.includes(`aria-controls="room-${room.id}-details"`));
  }
});

test("renders the status label, not the raw enum", () => {
  const html = renderHtml(catalog);
  assert.ok(html.includes('data-status="open">Open</p>'));
  assert.ok(html.includes('data-status="closed">Closed</p>'));
  assert.ok(html.includes('data-status="planned">Planned</p>'));
});

test("escapes catalog content in HTML", () => {
  const document = structuredClone(catalog);
  document.site.title = `<script>alert("x")</script>`;
  document.site.description = `a & b`;
  document.rooms[0].name = `Stu<dio>`;
  document.rooms[0].summary = `one & two`;
  document.rooms[0].tags = [`<b>tag</b>`];
  document.rooms[0].items[0].label = `"quoted"`;
  const html = renderHtml(document);
  assert.ok(!html.includes("<script>alert"));
  assert.ok(html.includes("&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;"));
  assert.ok(html.includes("a &amp; b"));
  assert.ok(html.includes("Stu&lt;dio&gt;"));
  assert.ok(html.includes("&lt;b&gt;tag&lt;/b&gt;"));
  assert.ok(html.includes("&quot;quoted&quot;"));
});

test("renders Markdown with one section per room", () => {
  const markdown = renderMarkdown(catalog);
  assert.match(markdown, /^# Atrium Rooms\n/);
  assert.match(markdown, /^## Rooms$/m);
  for (const room of catalog.rooms) {
    assert.ok(markdown.includes(`### ${room.name}`));
    assert.ok(markdown.includes(`- Status: ${room.status[0].toUpperCase()}${room.status.slice(1)}`));
  }
  assert.ok(markdown.endsWith("\n"));
});

test("rendering is deterministic", () => {
  assert.equal(renderHtml(catalog), renderHtml(structuredClone(catalog)));
  assert.equal(renderMarkdown(catalog), renderMarkdown(structuredClone(catalog)));
});

test("matches the recorded golden output", async () => {
  const goldenHtml = await readFile(
    new URL("../golden/index.html", import.meta.url),
    "utf8",
  );
  const goldenMarkdown = await readFile(
    new URL("../golden/catalog.md", import.meta.url),
    "utf8",
  );
  assert.equal(renderHtml(catalog), goldenHtml);
  assert.equal(renderMarkdown(catalog), goldenMarkdown);
});
