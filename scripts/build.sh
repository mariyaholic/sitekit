#!/usr/bin/env sh
# SPDX-License-Identifier: Apache-2.0
set -eu
cd "$(dirname "$0")/.."
node build.mjs "$@"
node build.mjs --check "$@"
