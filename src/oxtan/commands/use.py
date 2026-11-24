"""use command: set active database profile."""

import sys

from oxtan.core.profiles import ProfileManager


def setup(parser):
    """Setup arguments for use command."""
    parser.description = "Set the active database connection profile."
    parser.add_argument("name", help="Name of profile to activate")


def run(args, pm: ProfileManager, quiet: bool = False) -> int:
    """Execute use command."""
    pm.set_active_profile(args.name)
    if not quiet:
        sys.stderr.write(f"Switched to profile '{args.name}'.\n")
    return 0
