# OxtanDB User Guide

OxtanDB is a fast, safe, zero-bloat command-line tool for inspecting, querying, and managing MySQL databases.

---

## Table of Contents
1. [Installation](#installation)
2. [Managing Database Profiles](#managing-database-profiles)
3. [Health Diagnostics (`doctor`)](#health-diagnostics-doctor)
4. [Inspecting Databases (`tables`, `schema`, `count`)](#inspecting-databases-tables-schema-count)
5. [Previewing Data (`peek`)](#previewing-data-peek)
6. [Executing Queries (`query`)](#executing-queries-query)
7. [Output Formatting & Piping](#output-formatting--piping)
8. [Global Flags & Options](#global-flags--options)
9. [Security & Credentials](#security--credentials)

---

## Installation

### With `pipx` (Recommended)
`pipx` installs OxtanDB into an isolated environment and exposes the `oxtan` executable globally on your PATH:
```bash
pipx install git+https://github.com/Elitsuv/Oxtan.git
```

### With `pip`
```bash
pip install .
```

### Direct Module Execution
If you do not install the console script, you can run OxtanDB directly using Python:
```bash
python -m oxtan --help
```

---

## Managing Database Profiles

OxtanDB stores connection details in named profiles under `~/.oxtan/profiles.json`.

### Adding a Profile (`add-db`)
```bash
oxtan add-db <profile-name> --host <host> --port <port> --user <user> --database <dbname>
```
*Example:*
```bash
oxtan add-db dev --host 127.0.0.1 --port 3306 --user root --database my_service
```
You will be prompted to enter your MySQL password interactively. The password is masked and never displayed on screen.

### Listing Profiles (`dbs`)
```bash
oxtan dbs
```
Lists all saved profiles and highlights the currently active profile with an asterisk (`*`).

### Switching Active Profile (`use`)
```bash
oxtan use <profile-name>
```

### Showing Active Profile (`current`)
```bash
oxtan current
```

---

## Health Diagnostics (`doctor`)

The `doctor` command verifies your local environment, driver installation, profile integrity, and tests live database connectivity with latency measurements:
```bash
oxtan doctor
```
Output displays:
- Python runtime version
- MySQL driver availability
- Active profile configuration status
- Server connection test and round-trip ping latency in milliseconds

---

## Inspecting Databases (`tables`, `schema`, `count`)

### Listing Tables (`tables` / `t`)
```bash
oxtan tables
# or using short alias:
oxtan t
```
Displays all tables in the active database.

### Inspecting Table Schema (`schema` / `s`)
```bash
oxtan schema <table-name>
# or using short alias:
oxtan s users
```
Displays column names, data types, nullability, key constraints, defaults, and extra attributes.

### Row Count (`count`)
```bash
oxtan count <table-name>
```
Returns the exact total row count for the table.

---

## Previewing Data (`peek`)

Preview rows from a table without typing manual SQL queries:
```bash
oxtan peek <table-name> [--limit N]
# or using short alias:
oxtan p users --limit 10
```
Default limit is 10 rows.

---

## Executing Queries (`query`)

### Read-Only Queries (Default)
By default, queries are executed in a read-only transaction (`SET SESSION TRANSACTION READ ONLY`):
```bash
oxtan query "SELECT id, email, created_at FROM users WHERE status = %s" --param active
# or using short alias:
oxtan q "SELECT COUNT(*) FROM orders"
```

### Bind Parameters (`--param`)
Always use `--param` instead of concatenating raw values:
```bash
oxtan query "SELECT * FROM users WHERE role = %s AND points > %s" --param admin --param 100
```

### Modifying Queries (`--write`)
To execute statements that modify data (`INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`), pass `--write`:
```bash
oxtan query "UPDATE users SET status = 'inactive' WHERE last_login < '2025-01-01'" --write
```
You will be asked to confirm execution before the query runs. To skip the prompt in automated scripts, pass `--yes` or `-y`:
```bash
oxtan query "DELETE FROM sessions WHERE expired = 1" --write --yes
```

---

## Output Formatting & Piping

The `tables`, `schema`, `peek`, and `query` commands support three output formats via `--format`:

- `table`: Clean ASCII table with aligned columns (default).
- `json`: JSON array of row objects.
- `csv`: Comma-separated values with standard header row.

### Piping and Redirection
OxtanDB writes data to `stdout` and diagnostic messages (row counts, banners, notes, errors) to `stderr`.

```bash
# Filter JSON output with jq
oxtan query "SELECT id, email FROM users" --format json | jq '.[] | select(.id > 100)'

# Export directly to a CSV file
oxtan peek transactions --limit 500 --format csv > transactions.csv

# Process CSV with standard Unix tools
oxtan query "SELECT id, name FROM categories" --format csv | cut -d',' -f2
```

---

## Global Flags & Options

Global flags can be passed anywhere in the command line:

- `--version`: Print OxtanDB version and exit.
- `--quiet`: Suppress decorative banners, row counts, and hints.
- `--no-color`: Disable ANSI color escape codes (also enabled by setting the `NO_COLOR` environment variable).
- `--debug`: Print full Python tracebacks when an unhandled error occurs.

---

## Security & Credentials

1. **No `--password` Flag**: Passwords are never accepted via command-line arguments to prevent leakage into shell history files and system process tables.
2. **Interactive Input**: Passwords are read via standard masked terminal input.
3. **Automated / Headless Environments**: If running in a script or CI pipeline where stdin is not a TTY, the `OXTAN_PASSWORD` environment variable may be supplied:
   ```bash
   export OXTAN_PASSWORD="secret_password"
   oxtan add-db ci_db --host 127.0.0.1 --user ci_runner --database testdb < /dev/null
   ```
4. **File Permissions**: Profile configurations are written to `~/.oxtan/profiles.json` using atomic temporary file creation with restricted permissions (`0o600` on POSIX systems).
