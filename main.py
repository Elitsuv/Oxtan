"""Root execution shim for backwards compatibility (python main.py)."""

import sys
import os

# Add src to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from oxtan.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
