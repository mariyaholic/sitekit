// SPDX-License-Identifier: Apache-2.0

import assert from "node:assert/strict";
import test from "node:test";

import { parseArgs } from "../../src/args.mjs";
import { UsageError } from "../../src/errors.mjs";

test("uses documented defaults", () => {
  const options = parseArgs([]);
  assert.equal(options.catalog, "examples/room-catalog/catalog.json");
  assert.equal(options.out, "dist");
  assert.equal(options.schema, undefined);
  assert.equal(options.check, false);
  assert.equal(options.warnUnsupported, false);
  assert.equal(options.json, false);
});

test("accepts space-separated and inline values", () => {
  const spaced = parseArgs(["--catalog", "a.json", "--out", "build"]);
  assert.equal(spaced.catalog, "a.json");
  assert.equal(spaced.out, "build");

  const inline = parseArgs(["--catalog=b.json", "--schema=c.json", "--out=out"]);
  assert.equal(inline.catalog, "b.json");
  assert.equal(inline.schema, "c.json");
  assert.equal(inline.out, "out");
});

test("parses boolean flags", () => {
  const options = parseArgs(["--check", "--warn-unsupported", "--json"]);
  assert.equal(options.check, true);
  assert.equal(options.warnUnsupported, true);
  assert.equal(options.json, true);
});

test("recognises help", () => {
  assert.equal(parseArgs(["-h"]).help, true);
  assert.equal(parseArgs(["--help"]).help, true);
});

test("rejects a missing value", () => {
  assert.throws(() => parseArgs(["--catalog"]), UsageError);
  assert.throws(() => parseArgs(["--out", "--check"]), UsageError);
});

test("rejects unknown options and positional arguments", () => {
  assert.throws(() => parseArgs(["--nope"]), /unknown option/);
  assert.throws(() => parseArgs(["catalog.json"]), /unexpected argument/);
});

test("rejects values on boolean flags", () => {
  assert.throws(() => parseArgs(["--check=yes"]), /does not take a value/);
});

test("rejects empty paths", () => {
  assert.throws(() => parseArgs(["--out", ""]), /must not be empty/);
});
