// SPDX-License-Identifier: Apache-2.0

import assert from "node:assert/strict";
import { access, cp, readFile, readdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import test from "node:test";

import { exampleCatalog, makeTmpDir, repoRoot, runCli } from "./helpers.mjs";
import { buildSite, compareOutputs } from "../../src/build.mjs";

async function copyExample(t) {
  const dir = await makeTmpDir(t);
  const catalogDir = join(dir, "catalog");
  await cp(join(repoRoot, "examples", "room-catalog"), catalogDir, { recursive: true });
  return {
    dir,
    catalog: join(catalogDir, "catalog.json"),
    schema: join(catalogDir, "catalog.schema.json"),
    out: join(dir, "out"),
  };
}

async function exists(path) {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

async function readJson(path) {
  return JSON.parse(await readFile(path, "utf8"));
}

test("builds every output with the CLI", async (t) => {
  const paths = await copyExample(t);
  const result = runCli(["--catalog", paths.catalog, "--out", paths.out]);
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /wrote 8 files/);

  const files = (await readdir(paths.out, { recursive: true })).sort();
  assert.deepEqual(files, [
    "assets",
    "assets/rooms",
    "assets/rooms/garden.svg",
    "assets/rooms/library.svg",
    "assets/rooms/studio.svg",
    "assets/rooms/workshop.svg",
    "assets/site.css",
    "assets/site.js",
    "catalog.md",
    "index.html",
  ]);
  const html = await readFile(join(paths.out, "index.html"), "utf8");
  assert.match(html, /<title>Atrium Rooms<\/title>/);
});

test("--check passes on fresh output", async (t) => {
  const paths = await copyExample(t);
  assert.equal(runCli(["--catalog", paths.catalog, "--out", paths.out]).status, 0);
  const check = runCli(["--catalog", paths.catalog, "--out", paths.out, "--check"]);
  assert.equal(check.status, 0, check.stderr);
  assert.match(check.stdout, /output is up to date/);
});

test("--check reports a missing output directory without creating it", async (t) => {
  const paths = await copyExample(t);
  const result = runCli(["--catalog", paths.catalog, "--out", paths.out, "--check"]);
  assert.equal(result.status, 1);
  assert.match(result.stdout, /missing: index\.html/);
  assert.match(result.stdout, /output is stale/);
  assert.equal(await exists(paths.out), false);
});

test("--check reports stale files and leaves them untouched", async (t) => {
  const paths = await copyExample(t);
  assert.equal(runCli(["--catalog", paths.catalog, "--out", paths.out]).status, 0);
  const indexPath = join(paths.out, "index.html");
  await writeFile(indexPath, "tampered\n");
  const result = runCli(["--catalog", paths.catalog, "--out", paths.out, "--check"]);
  assert.equal(result.status, 1);
  assert.match(result.stdout, /stale: index\.html/);
  assert.equal(await readFile(indexPath, "utf8"), "tampered\n");
});

test("--check reports a stale asset too", async (t) => {
  const paths = await copyExample(t);
  assert.equal(runCli(["--catalog", paths.catalog, "--out", paths.out]).status, 0);
  await writeFile(join(paths.out, "assets", "site.css"), "changed\n");
  const result = runCli(["--catalog", paths.catalog, "--out", paths.out, "--check"]);
  assert.equal(result.status, 1);
  assert.match(result.stdout, /stale: assets\/site\.css/);
});

test("rejects invalid JSON with exit code 1", async (t) => {
  const paths = await copyExample(t);
  await writeFile(paths.catalog, "{not json", "utf8");
  const result = runCli(["--catalog", paths.catalog, "--out", paths.out]);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /cannot parse catalog/);
});

test("rejects schema violations with a pointed message", async (t) => {
  const paths = await copyExample(t);
  const catalog = await readJson(paths.catalog);
  catalog.rooms[0].status = "draft";
  await writeFile(paths.catalog, JSON.stringify(catalog, null, 2));
  const result = runCli(["--catalog", paths.catalog, "--out", paths.out]);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /does not match the supported schema subset/);
  assert.match(result.stderr, /\/rooms\/0\/status/);
});

test("fails on unsupported schema keywords unless asked to warn", async (t) => {
  const paths = await copyExample(t);
  const schema = await readJson(paths.schema);
  schema.properties.site.properties.title.pattern = "^[A-Z]";
  await writeFile(paths.schema, JSON.stringify(schema, null, 2));

  const strict = runCli(["--catalog", paths.catalog, "--out", paths.out]);
  assert.equal(strict.status, 1);
  assert.match(strict.stderr, /unsupported schema keyword "pattern"/);

  const warned = runCli([
    "--catalog",
    paths.catalog,
    "--out",
    paths.out,
    "--warn-unsupported",
  ]);
  assert.equal(warned.status, 0, warned.stderr);
  assert.match(warned.stderr, /warning: .*unsupported schema keyword "pattern"/);
});

test("fails when a required asset is missing", async (t) => {
  const paths = await copyExample(t);
  const { rm } = await import("node:fs/promises");
  await rm(join(paths.dir, "catalog", "assets", "rooms", "garden.svg"));
  const result = runCli(["--catalog", paths.catalog, "--out", paths.out]);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /missing required asset: assets\/rooms\/garden\.svg/);
  assert.equal(await exists(paths.out), false);
});

test("fails on semantic catalog problems the schema cannot see", async (t) => {
  const paths = await copyExample(t);
  const catalog = await readJson(paths.catalog);
  catalog.rooms[1].id = catalog.rooms[0].id;
  await writeFile(paths.catalog, JSON.stringify(catalog, null, 2));
  const result = runCli(["--catalog", paths.catalog, "--out", paths.out]);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /duplicate room id/);
});

test("returns exit code 2 for usage errors", () => {
  assert.equal(runCli(["--unknown"]).status, 2);
  assert.equal(runCli(["--catalog"]).status, 2);
});

test("help exits 0 and documents the flags", () => {
  const result = runCli(["--help"]);
  assert.equal(result.status, 0);
  assert.match(result.stdout, /--check/);
  assert.match(result.stdout, /--warn-unsupported/);
});

test("--json emits a parseable build summary", async (t) => {
  const paths = await copyExample(t);
  const result = runCli(["--catalog", paths.catalog, "--out", paths.out, "--json"]);
  assert.equal(result.status, 0, result.stderr);
  const summary = JSON.parse(result.stdout);
  assert.equal(summary.ok, true);
  assert.equal(summary.mode, "build");
  assert.equal(summary.files.length, 8);
  assert.deepEqual(summary.stale, undefined);
});

test("--json emits a parseable stale summary", async (t) => {
  const paths = await copyExample(t);
  const result = runCli(["--catalog", paths.catalog, "--out", paths.out, "--check", "--json"]);
  assert.equal(result.status, 1);
  const summary = JSON.parse(result.stdout);
  assert.equal(summary.ok, false);
  assert.equal(summary.mode, "check");
  assert.equal(summary.stale.length, 8);
  assert.equal(summary.stale[0].state, "missing");
});

test("--json reports validation errors", async (t) => {
  const paths = await copyExample(t);
  const catalog = await readJson(paths.catalog);
  catalog.rooms[0].status = "draft";
  await writeFile(paths.catalog, JSON.stringify(catalog, null, 2));
  const result = runCli(["--catalog", paths.catalog, "--out", paths.out, "--json"]);
  assert.equal(result.status, 1);
  const summary = JSON.parse(result.stdout);
  assert.equal(summary.ok, false);
  assert.ok(summary.error.details.some((line) => line.includes("/rooms/0/status")));
});

test("builds are deterministic across directories", async (t) => {
  const paths = await copyExample(t);
  const second = join(paths.dir, "out-2");
  assert.equal(runCli(["--catalog", paths.catalog, "--out", paths.out]).status, 0);
  assert.equal(runCli(["--catalog", paths.catalog, "--out", second]).status, 0);
  for (const relative of ["index.html", "catalog.md", "assets/site.css", "assets/site.js"]) {
    assert.deepEqual(
      await readFile(join(paths.out, relative)),
      await readFile(join(second, relative)),
      relative,
    );
  }
});

test("escapes catalog content in the built page", async (t) => {
  const paths = await copyExample(t);
  const catalog = await readJson(paths.catalog);
  catalog.site.title = `<script>alert("x")</script>`;
  catalog.rooms[0].summary = "one & two";
  await writeFile(paths.catalog, JSON.stringify(catalog, null, 2));
  const result = runCli(["--catalog", paths.catalog, "--out", paths.out]);
  assert.equal(result.status, 0, result.stderr);
  const html = await readFile(join(paths.out, "index.html"), "utf8");
  assert.ok(!html.includes("<script>alert"));
  assert.ok(html.includes("&lt;script&gt;alert"));
  assert.ok(html.includes("one &amp; two"));
});

test("buildSite produces outputs in memory without writing", async () => {
  const result = await buildSite({ catalogPath: exampleCatalog });
  assert.equal(result.files.size, 8);
  assert.ok(result.files.get("index.html").toString("utf8").startsWith("<!doctype html>"));
});

test("compareOutputs reports every file when the directory is absent", async (t) => {
  const paths = await copyExample(t);
  const result = await buildSite({
    catalogPath: exampleCatalog,
    outDir: join(paths.dir, "never-written"),
  });
  const problems = await compareOutputs(result.outDir, result.files);
  assert.equal(problems.length, 8);
  assert.ok(problems.every((entry) => entry.state === "missing"));
  assert.equal(await exists(result.outDir), false);
});
