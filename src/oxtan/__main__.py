"""Execution shim for python -m oxtan."""

import sys

from oxtan.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
