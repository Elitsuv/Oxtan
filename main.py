import sys
import logging
from cli.registry import CommandRegistry
from commands import add_db, use, dbs, tables, schema, peek, count, current

# Setup basic logging for the CLI
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    """Oxtan v2 CLI Entry Point."""
    registry = CommandRegistry()
    
    # Register all commands
    registry.register("add-db", add_db.setup, add_db.run)
    registry.register("use", use.setup, use.run)
    registry.register("dbs", dbs.setup, dbs.run)
    registry.register("tables", tables.setup, tables.run)
    registry.register("schema", schema.setup, schema.run)
    registry.register("peek", peek.setup, peek.run)
    registry.register("count", count.setup, count.run)
    registry.register("current", current.setup, current.run)
    
    # Execute the CLI
    registry.execute(sys.argv[1:])

if __name__ == "__main__":
    main()
