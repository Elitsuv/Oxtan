"""peek command (alias: p): view first few rows of a table."""

from oxtan.cli.output import print_results
from oxtan.core.connection import execute_query
from oxtan.core.errors import UsageError
from oxtan.core.profiles import ProfileManager
from oxtan.core.security import quote_identifier, validate_identifier


def setup(parser):
    """Setup arguments for peek command."""
    parser.description = "Peek at the first few rows of a table."
    parser.add_argument("table", help="Name of table to peek")
    parser.add_argument("--limit", type=int, default=5, help="Maximum rows to fetch (default: 5)")
    parser.add_argument("--format", choices=["table", "json", "csv"], default="table", help="Output format")


def run(args, pm: ProfileManager, quiet: bool = False) -> int:
    """Execute peek command."""
    validate_identifier(args.table)
    if args.limit < 1:
        raise UsageError("Limit must be a positive integer.", fix_hint="Use --limit 5")

    _, prof = pm.get_profile()
    sql = f"SELECT * FROM {quote_identifier(args.table)} LIMIT %s"  # nosec B608
    cols, chunks = execute_query(prof, sql, params=[args.limit], read_only=True)
    all_rows = []
    for chunk in chunks:
        all_rows.extend(chunk)

    print_results(cols, all_rows, fmt=args.format, quiet=quiet)
    return 0
