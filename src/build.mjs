// SPDX-License-Identifier: Apache-2.0

import { readFile, writeFile, mkdir } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";

import { parseCatalog, roomAssetPath } from "./catalog.mjs";
import { SitekitError } from "./errors.mjs";
import { renderHtml, renderMarkdown } from "./render.mjs";
import { formatIssues, validate } from "./schema.mjs";

export const DEFAULT_CATALOG = "examples/room-catalog/catalog.json";
export const DEFAULT_OUT = "dist";

const STATIC_ASSETS = ["assets/site.css", "assets/site.js"];

function isMissing(error) {
  return error && error.code === "ENOENT";
}

async function readText(path, label) {
  try {
    return await readFile(path, "utf8");
  } catch (error) {
    if (isMissing(error)) {
      throw new SitekitError(`cannot read ${label}: ${path} does not exist`);
    }
    throw new SitekitError(`cannot read ${label} ${path}: ${error.message}`, {
      exitCode: 2,
    });
  }
}

async function readJson(path, label) {
  const text = await readText(path, label);
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new SitekitError(`cannot parse ${label} ${path}: ${error.message}`);
  }
}

async function readAsset(path, relative) {
  try {
    return await readFile(path);
  } catch (error) {
    if (isMissing(error)) {
      throw new SitekitError(`missing required asset: ${relative}`, {
        details: [`expected at ${path}`],
      });
    }
    throw new SitekitError(`cannot read asset ${relative}: ${error.message}`, {
      exitCode: 2,
    });
  }
}

/**
 * Read the catalog and schema, validate both, and produce every output file in
 * memory. Nothing is written here, which keeps `--check` side-effect free.
 *
 * @param {{catalogPath?: string, schemaPath?: string, outDir?: string, warnUnsupported?: boolean}} options
 * @returns {Promise<{catalog: object, outDir: string, files: Map<string, Buffer>, warnings: object[]}>}
 */
export async function buildSite({
  catalogPath = DEFAULT_CATALOG,
  schemaPath,
  outDir = DEFAULT_OUT,
  warnUnsupported = false,
} = {}) {
  const absoluteCatalog = resolve(catalogPath);
  const absoluteSchema = schemaPath
    ? resolve(schemaPath)
    : join(dirname(absoluteCatalog), "catalog.schema.json");
  const absoluteOut = resolve(outDir);

  const catalog = await readJson(absoluteCatalog, "catalog");
  const schema = await readJson(absoluteSchema, "schema");

  const result = validate(schema, catalog, { warnUnsupported });
  if (result.errors.length > 0) {
    throw new SitekitError(
      `catalog ${catalogPath} does not match the supported schema subset`,
      { details: formatIssues(result.errors) },
    );
  }

  parseCatalog(catalog);

  const catalogDir = dirname(absoluteCatalog);
  const files = new Map();
  files.set("index.html", Buffer.from(renderHtml(catalog), "utf8"));
  files.set("catalog.md", Buffer.from(renderMarkdown(catalog), "utf8"));

  for (const relative of STATIC_ASSETS) {
    files.set(relative, await readAsset(join(catalogDir, relative), relative));
  }

  for (const room of catalog.rooms) {
    const relative = roomAssetPath(room.id);
    files.set(relative, await readAsset(join(catalogDir, relative), relative));
  }

  return {
    catalog,
    outDir: absoluteOut,
    files,
    warnings: result.warnings.map(
      (warning) => `${warning.path === "" ? "/" : warning.path}: ${warning.message}`,
    ),
  };
}

/**
 * Write every output file, creating parent directories as needed.
 * @param {string} outDir
 * @param {Map<string, Buffer>} files
 */
export async function writeOutputs(outDir, files) {
  for (const [relative, content] of files) {
    const target = join(outDir, relative);
    try {
      await mkdir(dirname(target), { recursive: true });
      await writeFile(target, content);
    } catch (error) {
      throw new SitekitError(`cannot write ${target}: ${error.message}`, {
        exitCode: 2,
      });
    }
  }
}

/**
 * Compare generated files with what is on disk. Never writes.
 * @param {string} outDir
 * @param {Map<string, Buffer>} files
 * @returns {Promise<Array<{path: string, state: "missing"|"stale"}>>}
 */
export async function compareOutputs(outDir, files) {
  const problems = [];
  for (const [relative, expected] of files) {
    const target = join(outDir, relative);
    let actual;
    try {
      actual = await readFile(target);
    } catch (error) {
      if (isMissing(error)) {
        problems.push({ path: relative, state: "missing" });
        continue;
      }
      throw new SitekitError(`cannot read ${target}: ${error.message}`, {
        exitCode: 2,
      });
    }
    if (!actual.equals(expected)) {
      problems.push({ path: relative, state: "stale" });
    }
  }
  return problems.sort((left, right) => left.path.localeCompare(right.path));
}
