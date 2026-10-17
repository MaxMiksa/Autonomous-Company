#!/usr/bin/env python3
"""Compatibility CLI forwarding to the product center."""

from pathlib import Path
import sys

DASHBOARD_DIR = Path(__file__).resolve().parent
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))


def main(argv=None):
    from center_server import main as center_main
    return center_main(argv)


if __name__ == "__main__":
    main()
