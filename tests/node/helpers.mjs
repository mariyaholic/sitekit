// SPDX-License-Identifier: Apache-2.0

import { spawnSync } from "node:child_process";
import { mkdir, mkdtemp, rm } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

export const repoRoot = fileURLToPath(new URL("../..", import.meta.url));
export const exampleCatalog = join(repoRoot, "examples", "room-catalog", "catalog.json");

/**
 * Create a scratch directory inside the repository (gitignored) and remove it
 * when the test finishes.
 * @param {import("node:test").TestContext} t
 * @returns {Promise<string>}
 */
export async function makeTmpDir(t) {
  const base = join(repoRoot, "tests", "tmp");
  await mkdir(base, { recursive: true });
  const dir = await mkdtemp(join(base, "case-"));
  t.after(async () => {
    await rm(dir, { recursive: true, force: true });
  });
  return dir;
}

/**
 * Run the builder CLI from the repository root.
 * @param {string[]} args
 * @returns {{status: number, stdout: string, stderr: string}}
 */
export function runCli(args) {
  const result = spawnSync(process.execPath, [join(repoRoot, "build.mjs"), ...args], {
    cwd: repoRoot,
    encoding: "utf8",
  });
  if (result.error) {
    throw result.error;
  }
  return { status: result.status ?? -1, stdout: result.stdout, stderr: result.stderr };
}
