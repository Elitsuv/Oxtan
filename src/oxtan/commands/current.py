"""current command: show current active profile."""

import sys

from oxtan.core.profiles import ProfileManager


def setup(parser):
    """Setup arguments for current command."""
    parser.description = "Show the current active database connection profile."


def run(args, pm: ProfileManager, quiet: bool = False) -> int:
    """Execute current command."""
    name, prof = pm.get_profile()
    sys.stdout.write(f"Profile:  {name}\n")
    sys.stdout.write(f"Host:     {prof.get('host')}:{prof.get('port')}\n")
    sys.stdout.write(f"User:     {prof.get('user')}\n")
    sys.stdout.write(f"Database: {prof.get('database')}\n")
    return 0
