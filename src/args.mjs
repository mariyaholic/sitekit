// SPDX-License-Identifier: Apache-2.0

import { UsageError } from "./errors.mjs";
import { DEFAULT_CATALOG, DEFAULT_OUT } from "./build.mjs";

export const HELP = `sitekit build

Usage:
  node build.mjs [options]

Options:
  --catalog <file>        catalog to render (default: ${DEFAULT_CATALOG})
  --schema <file>         schema for the catalog (default: catalog.schema.json
                          next to the catalog)
  --out <dir>             output directory (default: ${DEFAULT_OUT})
  --check                 verify outputs are fresh; never writes
  --warn-unsupported      warn instead of fail on unsupported schema keywords
  --json                  machine-readable summary on stdout
  -h, --help              show this help

Exit codes:
  0  success, or fresh output with --check
  1  invalid catalog/schema, missing input, or stale output
  2  usage or I/O error
`;

/**
 * @param {string[]} argv
 * @returns {{catalog: string, schema: string|undefined, out: string, check: boolean, warnUnsupported: boolean, json: boolean, help: boolean}}
 */
export function parseArgs(argv) {
  const options = {
    catalog: DEFAULT_CATALOG,
    schema: undefined,
    out: DEFAULT_OUT,
    check: false,
    warnUnsupported: false,
    json: false,
    help: false,
  };

  const takeValue = (flag, index) => {
    const value = argv[index + 1];
    if (value === undefined || value.startsWith("--")) {
      throw new UsageError(`option ${flag} requires a value`);
    }
    return value;
  };

  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    const equals = argument.indexOf("=");
    const flag = argument.startsWith("--") && equals > -1 ? argument.slice(0, equals) : argument;
    const inlineValue = argument.startsWith("--") && equals > -1 ? argument.slice(equals + 1) : undefined;

    switch (flag) {
      case "--catalog":
        options.catalog = inlineValue ?? takeValue(flag, index);
        if (inlineValue === undefined) index += 1;
        break;
      case "--schema":
        options.schema = inlineValue ?? takeValue(flag, index);
        if (inlineValue === undefined) index += 1;
        break;
      case "--out":
        options.out = inlineValue ?? takeValue(flag, index);
        if (inlineValue === undefined) index += 1;
        break;
      case "--check":
      case "--warn-unsupported":
      case "--json":
        if (inlineValue !== undefined) {
          throw new UsageError(`option ${flag} does not take a value`);
        }
        options[flag === "--check" ? "check" : flag === "--json" ? "json" : "warnUnsupported"] = true;
        break;
      case "-h":
      case "--help":
        options.help = true;
        break;
      default:
        if (argument.startsWith("-")) {
          throw new UsageError(`unknown option ${argument}`);
        }
        throw new UsageError(`unexpected argument ${argument}`);
    }
  }

  if (options.catalog.trim() === "") {
    throw new UsageError("--catalog must not be empty");
  }
  if (options.out.trim() === "") {
    throw new UsageError("--out must not be empty");
  }

  return options;
}
