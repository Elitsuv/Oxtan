# Contributing to Oxtan

We welcome contributions to Oxtan! Please adhere to the following guidelines when submitting code:

## 1. Architectural Adherence
Respect the module boundaries established in `docs/architecture.md`. 
* Do not place business logic in CLI command files.
* Do not place database connection logic outside of `database/`.

## 2. Developer Experience
* **Type Hints**: All new functions and methods must use Python type hints.
* **Docstrings**: Provide clear, concise docstrings for classes and public methods.
* **Error Handling**: Use specific exception types. Leverage `formatters/terminal.py` to display user-facing errors clearly.

## 3. Scope
Oxtan is currently focused solely on MySQL. Please do not submit PRs adding support for PostgreSQL, SQLite, or other databases at this time.
