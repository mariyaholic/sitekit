// SPDX-License-Identifier: Apache-2.0

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { exampleCatalog } from "./helpers.mjs";
import {
  parseCatalog,
  roomAssetPath,
  statusLabel,
} from "../../src/catalog.mjs";

const catalog = JSON.parse(await readFile(exampleCatalog, "utf8"));

function clone() {
  return structuredClone(catalog);
}

test("accepts the example catalog", () => {
  assert.doesNotThrow(() => parseCatalog(clone()));
});

test("maps status labels deterministically", () => {
  assert.equal(statusLabel("open"), "Open");
  assert.equal(statusLabel("closed"), "Closed");
  assert.equal(statusLabel("planned"), "Planned");
  assert.equal(statusLabel("other"), "other");
});

test("derives the fixed room asset path", () => {
  assert.equal(roomAssetPath("studio"), "assets/rooms/studio.svg");
});

test("rejects duplicate room ids", () => {
  const document = clone();
  document.rooms[1].id = document.rooms[0].id;
  assert.throws(
    () => parseCatalog(document),
    (error) => {
      assert.match(error.message, /does not satisfy/);
      assert.ok(error.details.some((line) => line.includes("duplicate room id")));
      return true;
    },
  );
});

test("rejects non-slug ids", () => {
  const document = clone();
  document.rooms[0].id = "Studio Room";
  assert.throws(() => parseCatalog(document), /does not satisfy/);
});

test("rejects a room without items", () => {
  const document = clone();
  document.rooms[0].items = [];
  assert.throws(
    () => parseCatalog(document),
    (error) => error.details.some((line) => line.includes("at least one item")),
  );
});

test("rejects duplicate item ids inside a room", () => {
  const document = clone();
  document.rooms[0].items[1].id = document.rooms[0].items[0].id;
  assert.throws(
    () => parseCatalog(document),
    (error) => error.details.some((line) => line.includes("duplicate item id")),
  );
});

test("rejects empty strings that the schema only types as strings", () => {
  const document = clone();
  document.site.title = "   ";
  assert.throws(
    () => parseCatalog(document),
    (error) => error.details.some((line) => line.includes("/site/title")),
  );
});

test("rejects an unknown status", () => {
  const document = clone();
  document.rooms[0].status = "draft";
  assert.throws(
    () => parseCatalog(document),
    (error) => error.details.some((line) => line.includes("expected one of")),
  );
});

test("rejects a non-object catalog", () => {
  assert.throws(() => parseCatalog(null), /catalog must be a JSON object/);
  assert.throws(() => parseCatalog([]), /catalog must be a JSON object/);
});
