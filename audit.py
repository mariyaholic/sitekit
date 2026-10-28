#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""sitekit browser audit entry point. See docs/CONTRACT.md."""

import sys

from sitekit_audit.cli import main

if __name__ == "__main__":
    sys.exit(main())
