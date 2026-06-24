# Oxtan v2 Architecture

Oxtan v2 is designed as a maintainable, scalable CLI application and Python wrapper.

## Directory Structure

*   `cli/`: Core command registry and argument parsing using `argparse`.
*   `commands/`: Individual command implementations (e.g., `add-db`, `use`, `tables`).
*   `database/`: MySQL connection management and pooling logic.
*   `core/`: Business logic for database CRUD operations (`OxtanDB` class).
*   `config/`: Profile management for storing and switching between database connections.
*   `formatters/`: Terminal output styling and formatting.
*   `utils/`: Shared helper functions (e.g., query building logic).
*   `tests/`: Test suite.
*   `docs/`: Project documentation.

## Command Flow

1.  The user executes `python main.py <command>`.
2.  The `CommandRegistry` inside `cli/registry.py` parses the input.
3.  Execution is routed to the corresponding command module inside the `commands/` directory.
4.  The command utilizes `core/db_operations.py`, `config/profiles.py`, and `formatters/terminal.py` as needed to fulfill the request.
