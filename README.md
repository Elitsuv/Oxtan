<p align="center">
  <img src="assets/oxtan.png" alt="OxtanDB Logo" width="150" />
</p>

<h1 align="center">OxtanDB</h1>

<p align="center">
  <strong>Command-line tool for MySQL — quick lookups, read-only by default.</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg" alt="License" /></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-brightgreen.svg" alt="Python Version" /></a>
  <img src="https://img.shields.io/badge/status-beta%20(v0.1.0)-orange.svg" alt="Beta Status" />
</p>

---

> **Beta release (`v0.1.0`):** Expect rough edges and breaking changes before `1.0`. Bug reports and feedback are welcome.

OxtanDB is a small Python CLI wrapper for inspecting, querying, and managing MySQL databases, built on top of `mysql-connector-python`. It saves named connection profiles locally, keeps queries read-only unless explicitly overridden, and separates `stdout` data from `stderr` diagnostics so results pipe cleanly into tools like `jq` and `cut`.

## Highlights

- **Read-Only by Default**: `query` runs inside `SET SESSION TRANSACTION READ ONLY`. Modifying queries require `--write` and confirmation (`[y/N]`, or `--yes` in scripts).
- **Identifier & Parameter Safety**: Table and column names are validated against `^[a-zA-Z0-9_]+\Z` (max 64 chars) and backtick-quoted. Values use `%s` bind parameters.
- **No `--password` Flag**: Passwords are read via masked prompt (`getpass`) and stored locally in `~/.oxtan/profiles.json` (`0o600` on POSIX).
- **Lazy Driver Loading**: `mysql-connector-python` is imported only when running a database command; `--help` and `about` do not load the driver.
- **Pipeline-Friendly**: Query output goes to `stdout`; banners, row counts, and errors go to `stderr`.

---

## Installation

### Using `pipx`
```bash
pipx install git+https://github.com/Elitsuv/Oxtan.git
```

### Using `pip`
```bash
pip install git+https://github.com/Elitsuv/Oxtan.git
```
*(Or `pip install .` inside a cloned repository.)*

### Run without adding to `PATH`
If `oxtan` is not recognized after installing (common with `pip install --user` on Windows), run it as a module:
```bash
python -m oxtan --help
```

---

## Quickstart

### 1. Add a Database Profile
```bash
oxtan add-db dev --host 127.0.0.1 --port 3306 --user root --database my_service
```
*(Prompts securely for your password.)*

### 2. Check Connectivity
```bash
oxtan doctor
```

### 3. List and Describe Tables
```bash
# List all tables (alias: t)
oxtan tables

# Inspect column schema (alias: s)
oxtan schema users
```

### 4. Peek and Count Data
```bash
# Preview first 5 rows (alias: p)
oxtan peek users --limit 5

# Quick row count
oxtan count users
```

### 5. Run Queries
```bash
# Read-only query (alias: q)
oxtan query "SELECT id, email, created_at FROM users WHERE active = %s" --param 1

# Export results as JSON or CSV
oxtan query "SELECT id, email FROM users" --format json > users.json
oxtan query "SELECT id, email FROM users" --format csv > users.csv

# Modify data with explicit confirmation
oxtan query "UPDATE users SET active = 0 WHERE id = 42" --write
```

---

## Command Reference

| Command | Alias | Description | Output Formats |
| :--- | :--- | :--- | :--- |
| `add-db` | - | Save a MySQL connection profile | - |
| `use` | - | Switch the active connection profile | - |
| `dbs` | - | List all saved database profiles | table, json, csv |
| `current` | - | Display currently active profile | text |
| `tables` | `t` | List all tables in active database | table, json, csv |
| `schema` | `s` | Inspect column structure and types of a table | table, json, csv |
| `peek` | `p` | Preview the first N rows of a table (default: `5`) | table, json, csv |
| `count` | - | Count total rows in a table | text |
| `query` | `q` | Execute SQL query (read-only by default) | table, json, csv |
| `doctor` | - | Run environment and connectivity diagnostics | text |
| `about` | - | Display banner and quick command reference | text |

### Global Flags

- `--version`: Show tool version (`oxtan 0.1.0`) and exit.
- `--quiet`: Suppress banners, hints, and row counts.
- `--no-color`: Disable ANSI color codes (also respected via `NO_COLOR`).
- `--debug`: Show full Python tracebacks on errors (default prints one error line and a hint).

---

## Piping & Stream Separation

- **`stdout`**: Query results, tables, JSON, CSV, row counts.
- **`stderr`**: Banners, status notes, warnings, errors.

```bash
# Pipe JSON into jq
oxtan query "SELECT id, name FROM users" --format json | jq '.[] | select(.id > 10)'

# Stream CSV into Unix tools
oxtan peek transactions --format csv | cut -d',' -f2
```

For full command details and CI usage (`OXTAN_PASSWORD`), see [docs/USER_GUIDE.md](docs/USER_GUIDE.md).

---

## Performance

- `oxtan --help` avoids importing `mysql-connector-python`, Pandas, or external table libraries.
- Measured on Python 3.13.0 (Windows 11): cumulative `oxtan.cli.main` import time is **~272 ms** via `python -X importtime -m oxtan --help`, with warm subprocess wall time around **0.46 s**.
- These figures measure CLI startup, not query execution. Queries run through `mysql-connector-python`.

---

## Security & Safety

**What Oxtan does:**
- Strict identifier validation (`^[a-zA-Z0-9_]+\Z`, max 64 chars) and backtick quoting on structured commands (`schema`, `peek`, `count`).
- Runs `query` inside `SET SESSION TRANSACTION READ ONLY` unless `--write` is passed.
- Has no `--password` CLI flag; `OXTAN_PASSWORD` is only read when stdin is non-interactive.
- Writes `~/.oxtan/profiles.json` atomically with `0o600` permissions on POSIX.

**Limits:**
- Passing `--write` runs raw SQL directly against MySQL — review destructive statements carefully before confirming.
- Passwords in `~/.oxtan/profiles.json` rely on filesystem permissions rather than an OS keyring.
- This is a beta release and has not been independently security audited.

**Recommended practices:**
- Connect with a database user that has only the privileges you need (for example, `SELECT`-only for inspection).
- Back up important data before running any `--write` statement.
- Try new connection profiles against a development database first.

To report a vulnerability or bug, please open an issue on the repository. Do not include passwords, connection strings, or private data in public issues.

---

## Dependencies & Driver

- **Driver**: `mysql-connector-python>=8.0.0` (the official MySQL connector for Python, with built-in `caching_sha2_password` support).
- **Driver License**: GPLv2 with the Universal FOSS Exception. It is installed separately as a dependency and is not bundled with or copied into OxtanDB.

---

## Trademarks & Independence

OxtanDB is an independent open-source project and is not affiliated with, endorsed by, or sponsored by Oracle or MySQL. The name "MySQL" is used only to describe the database this tool works with.

Oracle, Java, MySQL, and NetSuite are registered trademarks of Oracle and/or its affiliates. Other names may be trademarks of their respective owners.

## License

[Apache License, Version 2.0](LICENSE)

This software is provided "as is", without warranties or conditions of any kind, as set out in the license.
