// SPDX-License-Identifier: Apache-2.0

/**
 * Error type shared by the builder modules. `exitCode` is the process status
 * the CLI should use: 1 for invalid input or stale output, 2 for usage/I/O.
 */
export class SitekitError extends Error {
  constructor(message, { exitCode = 1, details = [] } = {}) {
    super(message);
    this.name = "SitekitError";
    this.exitCode = exitCode;
    this.details = details;
  }
}

export class UsageError extends SitekitError {
  constructor(message) {
    super(message, { exitCode: 2 });
    this.name = "UsageError";
  }
}
