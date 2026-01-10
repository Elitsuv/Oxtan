> [!NOTE] 
> This project is under development and contains bugs.

# 🛡️ OxtanDB

**A Secure, High-Performance, Reduced-Syntax MySQL Wrapper for Python.**

OxtanDB is a lightweight utility designed to eliminate the repetitive boilerplate code associated with MySQL connections. It provides a fluent, developer-friendly API that handles connection pooling, prevents SQL injection, and returns data as clean Python dictionaries by default.

---

## ✨ Features

* **🚀 Zero Boilerplate**: Perform standard CRUD operations (Insert, Update, Delete, Select) with single-line methods.
* **🔒 Security First**: 100% protection against SQL injection using enforced parameterized queries.
* **⚡ High Performance**: Built-in `MySQLConnectionPool` for thread-safe, fast, and concurrent database access.
* **🧠 Smart Results**: No more index-based tuples (e.g., `row[1]`). Access your data naturally via column names (e.g., `row['username']`).
* **🤖 CI/CD Ready**: Designed for automation with no interactive prompts; fully configurable via environment variables.

---
