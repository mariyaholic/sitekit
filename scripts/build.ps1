# SPDX-License-Identifier: Apache-2.0
$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')
try {
    node build.mjs @args
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    node build.mjs --check @args
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally { Pop-Location }
