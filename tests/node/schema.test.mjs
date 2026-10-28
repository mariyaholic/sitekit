// SPDX-License-Identifier: Apache-2.0

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import test from "node:test";

import { exampleCatalog, repoRoot } from "./helpers.mjs";
import { formatIssues, validate } from "../../src/schema.mjs";

const schema = JSON.parse(
  await readFile(
    join(repoRoot, "examples", "room-catalog", "catalog.schema.json"),
    "utf8",
  ),
);
const catalog = JSON.parse(await readFile(exampleCatalog, "utf8"));

function clone(value) {
  return structuredClone(value);
}

test("accepts the example catalog", () => {
  const result = validate(schema, catalog);
  assert.equal(result.valid, true, formatIssues(result.errors).join("\n"));
  assert.deepEqual(result.errors, []);
  assert.deepEqual(result.warnings, []);
});

test("rejects a wrong type and points at the value", () => {
  const document = clone(catalog);
  document.version = "one";
  const result = validate(schema, document);
  assert.equal(result.valid, false);
  assert.equal(result.errors[0].path, "/version");
  assert.match(result.errors[0].message, /expected integer, received string/);
});

test("integer accepts whole numbers only", () => {
  const document = clone(catalog);
  document.version = 1.5;
  const result = validate(schema, document);
  assert.equal(result.valid, false);
  assert.equal(result.errors[0].keyword, "type");
});

test("reports missing required properties", () => {
  const document = clone(catalog);
  delete document.site.tagline;
  const result = validate(schema, document);
  assert.equal(result.valid, false);
  assert.equal(result.errors[0].path, "/site");
  assert.match(result.errors[0].message, /missing required property "tagline"/);
});

test("rejects undeclared properties when additionalProperties is false", () => {
  const document = clone(catalog);
  document.site.extra = true;
  const result = validate(schema, document);
  assert.equal(result.valid, false);
  assert.equal(result.errors[0].path, "/site/extra");
  assert.equal(result.errors[0].keyword, "additionalProperties");
});

test("allows undeclared properties when additionalProperties is absent", () => {
  const result = validate({ type: "object", properties: { a: { type: "string" } } }, { a: "x", b: 2 });
  assert.equal(result.valid, true);
});

test("validates enum membership", () => {
  const document = clone(catalog);
  document.rooms[0].status = "draft";
  const result = validate(schema, document);
  assert.equal(result.valid, false);
  assert.equal(result.errors[0].keyword, "enum");
  assert.equal(result.errors[0].path, "/rooms/0/status");
});

test("validates array items and nested paths", () => {
  const document = clone(catalog);
  document.rooms[1].items[0].label = 7;
  const result = validate(schema, document);
  assert.equal(result.valid, false);
  assert.equal(result.errors[0].path, "/rooms/1/items/0/label");
});

test("fails on unsupported keywords by default", () => {
  const result = validate({ type: "string", pattern: "^a" }, "abc");
  assert.equal(result.valid, false);
  assert.equal(result.errors[0].keyword, "pattern");
  assert.match(result.errors[0].message, /unsupported schema keyword "pattern"/);
});

test("warns on unsupported keywords when requested", () => {
  const result = validate({ type: "string", pattern: "^a" }, "abc", {
    warnUnsupported: true,
  });
  assert.equal(result.valid, true);
  assert.equal(result.warnings.length, 1);
  assert.equal(result.warnings[0].keyword, "pattern");
});

test("ignores annotation keywords", () => {
  const result = validate(
    { $schema: "x", $id: "y", $comment: "z", title: "t", description: "d", default: 1, type: "string" },
    "ok",
  );
  assert.equal(result.valid, true);
  assert.deepEqual(result.errors, []);
});

test("rejects malformed type declarations", () => {
  const result = validate({ type: [] }, "x");
  assert.equal(result.valid, false);
  assert.match(result.errors[0].message, /invalid type declaration/);
});

test("supports a union of types", () => {
  assert.equal(validate({ type: ["string", "null"] }, null).valid, true);
  assert.equal(validate({ type: ["string", "null"] }, "x").valid, true);
  assert.equal(validate({ type: ["string", "null"] }, 3).valid, false);
});

test("rejects non-boolean additionalProperties", () => {
  const result = validate({ type: "object", additionalProperties: { type: "string" } }, {});
  assert.equal(result.valid, false);
  assert.match(result.errors[0].message, /must be true or false/);
});

test("escapes JSON pointer segments in paths", () => {
  const result = validate(
    { type: "object", properties: { "a/b~c": { type: "string" } } },
    { "a/b~c": 1 },
  );
  assert.equal(result.errors[0].path, "/a~1b~0c");
});
