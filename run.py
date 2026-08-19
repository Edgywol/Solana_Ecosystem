#!/usr/bin/env python3
"""Root entrypoint to execute the Solana Ecosystem Report & Dashboard pipeline."""

import sys
from collector.run import main

if __name__ == "__main__":
    sys.exit(main())
