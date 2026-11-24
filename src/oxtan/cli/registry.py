"""Command registry and argument parsing for Oxtan CLI."""

import argparse
from typing import Any, Callable, Dict, List, Optional, Tuple

from oxtan import __version__
from oxtan.core.errors import UsageError

COMMAND_DESCRIPTIONS = {
    "add-db": "Add a new database connection profile",
    "use": "Set the active database connection profile",
    "dbs": "List all saved database profiles",
    "current": "Show the current active connection profile",
    "tables": "List all tables in the active database",
    "schema": "Show column schema for a table",
    "peek": "Peek at the first few rows of a table",
    "count": "Count total rows in a table",
    "query": "Execute a SQL query (READ-ONLY by default)",
    "doctor": "Run diagnostic checks on environment and connectivity",
    "about": "Show Oxtan banner, version, and quick cheat sheet",
}


class OxtanArgumentParser(argparse.ArgumentParser):
    """Custom ArgumentParser that raises UsageError instead of exiting on error."""

    def error(self, message: str):
        raise UsageError(message, fix_hint="Run 'oxtan --help' for available commands and options.")


class CommandRegistry:
    """Registry for Oxtan CLI commands and aliases."""

    def __init__(self):
        self.common_parser = argparse.ArgumentParser(add_help=False)
        self.common_parser.add_argument(
            "--quiet",
            action="store_true",
            help="Suppress notes, hints, row counts, and banners",
        )
        self.common_parser.add_argument(
            "--no-color",
            action="store_true",
            help="Disable ANSI color codes",
        )
        self.common_parser.add_argument(
            "--debug",
            action="store_true",
            help="Show full traceback on error",
        )

        self.parser = OxtanArgumentParser(
            prog="oxtan",
            description="Oxtan - Fast, safe command-line tool for MySQL.",
            parents=[self.common_parser],
            add_help=True,
        )
        self.parser.add_argument(
            "--version",
            action="version",
            version=f"oxtan {__version__}",
            help="Show Oxtan version and exit",
        )

        self.subparsers = self.parser.add_subparsers(
            dest="command",
            metavar="<command>",
            help="Command to run",
            parser_class=OxtanArgumentParser,
        )
        self.commands: Dict[str, Callable[..., int]] = {}
        self.aliases: Dict[str, str] = {}

    def register(
        self,
        name: str,
        setup_func: Callable[..., Any],
        run_func: Callable[..., int],
        aliases: Optional[List[str]] = None,
    ) -> None:
        """Register a command with its arguments setup and runner function."""
        alias_list = aliases or []
        help_text = COMMAND_DESCRIPTIONS.get(name, f"Run {name} command")
        subparser = self.subparsers.add_parser(
            name,
            aliases=alias_list,
            help=help_text,
            parents=[self.common_parser],
        )
        setup_func(subparser)
        self.commands[name] = run_func
        for alias in alias_list:
            self.aliases[alias] = name

    def parse_args(self, args: Optional[List[str]] = None) -> Tuple[argparse.Namespace, Optional[Callable[..., int]]]:
        """Parse arguments and resolve runner function."""
        parsed = self.parser.parse_args(args)
        cmd_name = parsed.command
        if not cmd_name:
            return parsed, None

        canonical = self.aliases.get(cmd_name, cmd_name)
        run_func = self.commands.get(canonical)
        return parsed, run_func
