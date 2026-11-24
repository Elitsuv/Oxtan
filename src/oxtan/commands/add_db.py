"""add-db command: add a new database connection profile."""

import getpass
import os
import sys

from oxtan.core.errors import UsageError
from oxtan.core.profiles import ProfileManager


def setup(parser):
    """Setup arguments for add-db command."""
    parser.description = "Add a new database connection profile."
    parser.add_argument("name", nargs="?", default=None, help="Profile name (e.g. dev, staging, prod)")
    parser.add_argument("--name", dest="flag_name", default=None, help="Profile name (optional flag)")
    parser.add_argument("--host", default="localhost", help="Database host (default: localhost)")
    parser.add_argument("--port", type=int, default=3306, help="Database port (default: 3306)")
    parser.add_argument("--user", default="root", help="Database user (default: root)")
    parser.add_argument("--database", required=True, help="Database name")


def run(args, pm: ProfileManager, quiet: bool = False) -> int:
    """Execute add-db command."""
    profile_name = getattr(args, "name", None) or getattr(args, "flag_name", None)
    if not profile_name:
        raise UsageError(
            "Profile name is required.",
            fix_hint="Provide a profile name, e.g. 'oxtan add-db dev --database mydb'.",
        )

    password = ""  # nosec B105
    # For non-interactive use (CI/scripts) allow OXTAN_PASSWORD env var ONLY when there is no TTY
    if not sys.stdin.isatty():
        env_pass = os.environ.get("OXTAN_PASSWORD")
        if env_pass is not None:
            password = env_pass
        else:
            password = sys.stdin.readline().rstrip("\r\n")
    else:
        password = getpass.getpass(f"Enter password for {args.user}@{args.host}: ")

    pm.save_profile(
        name=profile_name,
        host=args.host,
        port=args.port,
        user=args.user,
        password=password,
        database=args.database,
    )
    if not quiet:
        sys.stderr.write(f"Saved profile '{profile_name}'.\n")
    return 0
