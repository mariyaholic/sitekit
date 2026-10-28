#!/usr/bin/env node
// SPDX-License-Identifier: Apache-2.0
// Runs the Python test suite (or an arbitrary Python entry point) with the
// repository virtualenv when one exists, otherwise the system interpreter.

import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = fileURLToPath(new URL("..", import.meta.url));
const candidates = [
  process.env.SITEKIT_PYTHON,
  join(repoRoot, ".venv", "bin", "python"),
  join(repoRoot, ".venv", "Scripts", "python.exe"),
  "python3",
  "python",
].filter(Boolean);

const python = candidates.find((candidate) => {
  if (candidate.includes("/") || candidate.includes("\\")) {
    return existsSync(candidate);
  }
  const probe = spawnSync(candidate, ["--version"], { encoding: "utf8" });
  return probe.status === 0;
});

if (!python) {
  console.error("sitekit: no Python interpreter found. Install Python 3.13+ and retry.");
  process.exit(2);
}

const passthrough = process.argv.slice(2);
const args = passthrough[0] === "--" ? passthrough.slice(1) : passthrough;
const finalArgs = args.length > 0 ? args : ["-m", "pytest", "tests/python"];

const result = spawnSync(python, finalArgs, {
  cwd: repoRoot,
  stdio: "inherit",
  env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" },
});

if (result.error) {
  console.error(`sitekit: could not run ${python}: ${result.error.message}`);
  process.exit(2);
}

process.exit(result.status ?? 2);
