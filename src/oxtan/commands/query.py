"""query command (alias: q): run raw SQL queries with read-only safety."""

import sys

from oxtan.cli.output import print_results
from oxtan.core.connection import execute_query
from oxtan.core.errors import UsageError
from oxtan.core.profiles import ProfileManager


def setup(parser):
    """Setup arguments for query command."""
    parser.description = "Execute a SQL query against the active database (READ-ONLY by default)."
    parser.add_argument("sql", help="SQL query string to execute")
    parser.add_argument(
        "--write", action="store_true", help="Allow modifying statements (INSERT, UPDATE, DELETE, etc.)"
    )
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt for write operations")
    parser.add_argument(
        "--param", action="append", default=[], help="Bind parameter for query placeholders (repeatable)"
    )
    parser.add_argument("--format", choices=["table", "json", "csv"], default="table", help="Output format")


def run(args, pm: ProfileManager, quiet: bool = False) -> int:
    """Execute query command."""
    _, prof = pm.get_profile()

    # If --write requested, ask for confirmation unless --yes is passed
    if args.write and not args.yes:
        if sys.stdin.isatty():
            confirm = input(f"Execute modifying query on '{prof.get('database')}'? [y/N]: ").strip().lower()
            if confirm not in ("y", "yes"):
                sys.stderr.write("Operation cancelled.\n")
                return 0
        else:
            raise UsageError(
                "Modifying queries in non-interactive mode require --yes.",
                fix_hint="Pass --yes to confirm changes.",
            )

    read_only = not args.write
    cols, chunks = execute_query(prof, args.sql, params=args.param, read_only=read_only)
    all_rows = []
    for chunk in chunks:
        all_rows.extend(chunk)

    print_results(cols, all_rows, fmt=args.format, quiet=quiet)
    return 0
