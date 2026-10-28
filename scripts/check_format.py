# SPDX-License-Identifier: Apache-2.0
"""Check basic repository source whitespace, including clean checkouts."""

from pathlib import Path
import subprocess
import sys


def problems(data: bytes):
    issues = []
    if data and not data.endswith(b"\n"):
        issues.append("missing final newline")
    if b"\r" in data:
        issues.append("non-LF line ending")
    for number, line in enumerate(data.splitlines(), 1):
        if line.rstrip(b" \t") != line:
            issues.append(f"line {number}: trailing whitespace")
        if line.startswith(b"\t"):
            issues.append(f"line {number}: tab indentation")
    return issues


def main():
    paths = subprocess.check_output(["git", "ls-files", "-z"], text=True).split("\0")
    failed = False
    for name in paths:
        path = Path(name)
        if path.suffix not in {".py", ".mjs"} or not path.is_file():
            continue
        for issue in problems(path.read_bytes()):
            print(f"{path}: {issue}")
            failed = True
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
