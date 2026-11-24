"""about command: show tool info, mark, and cheat sheet."""

import sys

from oxtan.cli.banner import print_banner_and_cheatsheet
from oxtan.core.profiles import ProfileManager


def setup(parser):
    """Setup arguments for about command."""
    parser.description = "Show Oxtan banner, version, and quick cheat sheet."


def run(args, pm: ProfileManager, quiet: bool = False) -> int:
    """Execute about command."""
    no_color = getattr(args, "no_color", False)
    print_banner_and_cheatsheet(quiet=quiet, force=False, no_color=no_color, stream=sys.stdout)
    return 0
