"""Main CLI entrypoint for Oxtan."""

import sys
import traceback
from typing import List, Optional

from oxtan.cli.banner import print_banner_and_cheatsheet
from oxtan.cli.registry import CommandRegistry
from oxtan.commands import (
    about,
    add_db,
    count,
    current,
    dbs,
    doctor,
    peek,
    query,
    schema,
    tables,
    use,
)
from oxtan.core.errors import OxtanError, UsageError
from oxtan.core.profiles import ProfileManager


def build_registry() -> CommandRegistry:
    """Build and populate the command registry."""
    registry = CommandRegistry()
    registry.register("add-db", add_db.setup, add_db.run)
    registry.register("use", use.setup, use.run)
    registry.register("dbs", dbs.setup, dbs.run)
    registry.register("current", current.setup, current.run)
    registry.register("tables", tables.setup, tables.run, aliases=["t"])
    registry.register("schema", schema.setup, schema.run, aliases=["s"])
    registry.register("peek", peek.setup, peek.run, aliases=["p"])
    registry.register("count", count.setup, count.run)
    registry.register("query", query.setup, query.run, aliases=["q"])
    registry.register("doctor", doctor.setup, doctor.run)
    registry.register("about", about.setup, about.run)
    return registry


def main(args: Optional[List[str]] = None) -> int:
    """Oxtan CLI main function.

    Exit codes:
      0: ok
      1: runtime / database error
      2: usage error
      130: Ctrl+C (KeyboardInterrupt)
    """
    if args is None:
        args = sys.argv[1:]

    if not args:
        print_banner_and_cheatsheet(force=True, stream=sys.stdout)
        return 0

    # Configure standard streams for graceful Unicode replacement on legacy terminals
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(errors="replace")
        except Exception:
            pass  # nosec B110
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(errors="replace")
        except Exception:
            pass  # nosec B110

    registry = build_registry()
    debug = "--debug" in args
    no_color = "--no-color" in args

    try:
        parsed, run_func = registry.parse_args(args)
        if not parsed.command or run_func is None:
            print_banner_and_cheatsheet(quiet=parsed.quiet, force=False, no_color=no_color, stream=sys.stdout)
            return 0

        pm = ProfileManager()
        result = run_func(parsed, pm, quiet=parsed.quiet)
        return int(result) if result is not None else 0
    except KeyboardInterrupt:
        sys.stderr.write("\n")
        return 130
    except UsageError as e:
        if debug:
            traceback.print_exc(file=sys.stderr)
        else:
            sys.stderr.write(f"{e.format_error()}\n")
        return 2
    except OxtanError as e:
        if debug:
            traceback.print_exc(file=sys.stderr)
        else:
            sys.stderr.write(f"{e.format_error()}\n")
        return 1
    except Exception as e:
        if debug:
            traceback.print_exc(file=sys.stderr)
        else:
            sys.stderr.write(f"Error: {e}\nHint: Run with --debug to inspect traceback.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
