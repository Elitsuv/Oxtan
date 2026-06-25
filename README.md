> [!NOTE] 
> This project is under development and contains bugs.

# 🛡️ OxtanDB v3

**A Secure, High-Performance, Reduced-Syntax MySQL Wrapper and CLI for Python.**

OxtanDB is a utility designed to eliminate the repetitive boilerplate code associated with MySQL connections. It provides a fluent, developer-friendly API that handles connection pooling, prevents SQL injection, and returns data as clean Python dictionaries or Pandas DataFrames.

Version 2 introduces a scalable CLI architecture to manage your databases directly from the terminal!

---

## ✨ Features

* **🚀 Zero Boilerplate**: Perform standard CRUD operations with single-line methods.
* **🔒 Security First**: 100% protection against SQL injection using enforced parameterized queries.
* **⚡ High Performance**: Built-in `MySQLConnectionPool` for thread-safe, fast, and concurrent database access.
* **🧠 Smart Results**: Access your data naturally via column names (e.g., `row['username']`) or as DataFrames.
* **💻 Command Line Interface**: Manage connection profiles, view schemas, and query tables via the terminal.

---

## 🏗 Architecture

Oxtan v2 has been refactored into a scalable modular architecture. 
See the detailed documentation:
* [Architecture](docs/architecture.md)
* [Contributing](docs/contributing.md)

---

## 🛠️ CLI Usage

You can run the Oxtan CLI from the project root:

```bash
python main.py --help
```

### Available Commands:
* `add-db`: Add a new database connection profile.
* `use`: Set the active database profile.
* `dbs`: List all saved database profiles.
* `tables`: List all tables in the active database.
* `schema`: Show the schema for a specific table.
* `peek`: Peek at the first few rows of a table.
* `count`: Count the number of rows in a table.
