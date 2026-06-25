import argparse
from typing import Callable, Dict

class CommandRegistry:
    """Central registry for Oxtan CLI commands."""
    
    def __init__(self):
        self.commands: Dict[str, Callable] = {}
        self.parser = argparse.ArgumentParser(
            description="Oxtan v3 CLI - A Secure, High-Performance MySQL Wrapper"
        )
        self.subparsers = self.parser.add_subparsers(dest="command", help="Available commands")

    def register(self, name: str, setup_func: Callable, run_func: Callable):
        """
        Registers a command with its argument setup and execution function.
        
        Args:
            name: The name of the command (e.g., 'add-db').
            setup_func: A function that takes an argparse.ArgumentParser and adds arguments.
            run_func: A function that takes parsed arguments and executes the command logic.
        """
        parser = self.subparsers.add_parser(name, help=setup_func.__doc__)
        setup_func(parser)
        self.commands[name] = run_func

    def execute(self, args: list = None):
        """Parses arguments and executes the corresponding command."""
        parsed_args = self.parser.parse_args(args)
        if not parsed_args.command:
            self.parser.print_help()
            return

        run_func = self.commands.get(parsed_args.command)
        if run_func:
            run_func(parsed_args)
        else:
            print(f"Unknown command: {parsed_args.command}")
