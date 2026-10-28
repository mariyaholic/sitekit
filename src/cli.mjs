// SPDX-License-Identifier: Apache-2.0

import { relative } from "node:path";

import { parseArgs, HELP } from "./args.mjs";
import { buildSite, compareOutputs, writeOutputs } from "./build.mjs";
import { SitekitError } from "./errors.mjs";

function printWarnings(warnings, stderr) {
  for (const warning of warnings) {
    stderr.write(`sitekit: warning: ${warning}\n`);
  }
}

/**
 * CLI entry point.
 * @param {string[]} argv
 * @param {{stdout?: NodeJS.WritableStream, stderr?: NodeJS.WritableStream}} [streams]
 * @returns {Promise<number>} process exit code
 */
export async function main(argv, streams = {}) {
  const stdout = streams.stdout ?? process.stdout;
  const stderr = streams.stderr ?? process.stderr;

  let options;
  try {
    options = parseArgs(argv);
  } catch (error) {
    if (error instanceof SitekitError) {
      stderr.write(`sitekit: ${error.message}\n`);
      stderr.write("Try `node build.mjs --help`.\n");
      return error.exitCode;
    }
    throw error;
  }

  if (options.help) {
    stdout.write(HELP);
    return 0;
  }

  try {
    const result = await buildSite({
      catalogPath: options.catalog,
      schemaPath: options.schema,
      outDir: options.out,
      warnUnsupported: options.warnUnsupported,
    });
    printWarnings(result.warnings, stderr);

    if (options.check) {
      const stale = await compareOutputs(result.outDir, result.files);
      if (options.json) {
        stdout.write(
          `${JSON.stringify(
            {
              ok: stale.length === 0,
              mode: "check",
              out: options.out,
              files: [...result.files.keys()],
              stale,
              warnings: result.warnings,
            },
            null,
            2,
          )}\n`,
        );
      } else if (stale.length === 0) {
        stdout.write(
          `sitekit: output is up to date (${result.files.size} files in ${options.out})\n`,
        );
      } else {
        for (const entry of stale) {
          stdout.write(`sitekit: ${entry.state}: ${entry.path}\n`);
        }
        stdout.write(
          `sitekit: output is stale (${stale.length} of ${result.files.size} files); run \`node build.mjs\`\n`,
        );
      }
      return stale.length === 0 ? 0 : 1;
    }

    await writeOutputs(result.outDir, result.files);
    if (options.json) {
      stdout.write(
        `${JSON.stringify(
          {
            ok: true,
            mode: "build",
            out: options.out,
            files: [...result.files.keys()],
            warnings: result.warnings,
          },
          null,
          2,
        )}\n`,
      );
    } else {
      stdout.write(
        `sitekit: wrote ${result.files.size} files to ${options.out} (${relative(
          process.cwd(),
          result.outDir,
        ) || "."})\n`,
      );
    }
    return 0;
  } catch (error) {
    if (error instanceof SitekitError) {
      if (options.json) {
        stdout.write(
          `${JSON.stringify(
            {
              ok: false,
              mode: options.check ? "check" : "build",
              error: { message: error.message, details: error.details },
            },
            null,
            2,
          )}\n`,
        );
      } else {
        stderr.write(`sitekit: ${error.message}\n`);
        for (const detail of error.details) {
          stderr.write(`  ${detail}\n`);
        }
      }
      return error.exitCode;
    }
    throw error;
  }
}
