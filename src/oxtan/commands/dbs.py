"""dbs command: list saved database profiles."""

import sys

from oxtan.cli.output import print_results
from oxtan.core.profiles import ProfileManager


def setup(parser):
    """Setup arguments for dbs command."""
    parser.description = "List all saved database profiles."


def run(args, pm: ProfileManager, quiet: bool = False) -> int:
    """Execute dbs command."""
    active = pm.get_active_profile()
    profiles = pm.list_profiles()
    if not profiles:
        if not quiet:
            sys.stderr.write("No profiles saved yet. Use 'oxtan add-db <name>' to add one.\n")
        return 0

    rows = []
    for name in profiles:
        _, prof = pm.get_profile(name)
        rows.append(
            {
                "active": "*" if name == active else "",
                "name": name,
                "host": prof.get("host", ""),
                "port": prof.get("port", 3306),
                "user": prof.get("user", ""),
                "database": prof.get("database", ""),
            }
        )

    print_results(["active", "name", "host", "port", "user", "database"], rows, fmt="table", quiet=quiet)
    return 0
