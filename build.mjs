#!/usr/bin/env node
// SPDX-License-Identifier: Apache-2.0
// sitekit builder CLI. See docs/CONTRACT.md for the supported contract.

import { main } from "./src/cli.mjs";

try {
  process.exitCode = await main(process.argv.slice(2));
} catch (error) {
  process.stderr.write(`sitekit: unexpected error: ${error?.stack ?? error}\n`);
  process.exitCode = 2;
}
