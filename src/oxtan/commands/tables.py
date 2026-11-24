"""tables command (alias: t): list tables in active database."""

from oxtan.cli.output import print_results
from oxtan.core.connection import execute_query
from oxtan.core.profiles import ProfileManager


def setup(parser):
    """Setup arguments for tables command."""
    parser.description = "List all tables in the active database."
    parser.add_argument("--format", choices=["table", "json", "csv"], default="table", help="Output format")


def run(args, pm: ProfileManager, quiet: bool = False) -> int:
    """Execute tables command."""
    _, prof = pm.get_profile()
    cols, chunks = execute_query(prof, "SHOW TABLES", read_only=True)
    all_rows = []
    for chunk in chunks:
        all_rows.extend(chunk)

    normalized_rows = [{"table": list(r.values())[0] if r else ""} for r in all_rows]
    print_results(["table"], normalized_rows, fmt=args.format, quiet=quiet)
    return 0
