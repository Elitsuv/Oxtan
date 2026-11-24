"""MySQL connection management and execution for Oxtan.

Implements context-managed database connections, read-only session enforcement,
stale-connection error handling, and chunked cursor streaming.
"""

import time
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional, Sequence, Tuple

from oxtan.core.errors import DatabaseConnectionError, QueryExecutionError


def _map_mysql_error(error: Exception, profile: Dict[str, Any]) -> DatabaseConnectionError:
    """Map driver errors to user-friendly DatabaseConnectionError with safe hints."""
    errno = getattr(error, "errno", None)
    err_msg = str(error)

    # 1045: Access denied
    if errno == 1045:
        user = profile.get("user", "")
        host = profile.get("host", "")
        return DatabaseConnectionError(
            f"Access denied for user '{user}' at host '{host}'.",
            fix_hint="Verify username and password using 'oxtan add-db'.",
        )

    # 2003 / 2002: Can't connect to server
    if errno in (2002, 2003):
        host = profile.get("host", "")
        port = profile.get("port", 3306)
        return DatabaseConnectionError(
            f"Cannot connect to MySQL server at '{host}:{port}'.",
            fix_hint="Ensure MySQL is running and network/firewall allows access.",
        )

    # 1049: Unknown database
    if errno == 1049:
        database = profile.get("database", "")
        return DatabaseConnectionError(
            f"Database '{database}' does not exist on server.",
            fix_hint="Verify database name or create it in MySQL.",
        )

    # 2006, 2013: Server gone away / lost connection
    if errno in (2006, 2013):
        return DatabaseConnectionError(
            "MySQL connection was lost or timed out.",
            fix_hint="Check server health and network stability.",
        )

    # Generic connection error
    return DatabaseConnectionError(
        f"Database connection error: {err_msg}",
        fix_hint="Check server status and connection credentials.",
    )


@contextmanager
def get_connection(
    profile: Dict[str, Any],
    read_only: bool = False,
    timeout: int = 10,
) -> Generator[Any, None, None]:
    """Context manager yielding a live MySQL connection.

    Always closes the connection on exit.
    Enforces SET SESSION TRANSACTION READ ONLY if read_only=True.
    """
    # Lazy import of mysql.connector
    try:
        import mysql.connector
    except ImportError as e:
        raise DatabaseConnectionError(
            "MySQL driver (mysql-connector-python) is not installed.",
            fix_hint="Install dependencies with 'pip install .'.",
        ) from e

    conn = None
    try:
        conn = mysql.connector.connect(
            host=profile["host"],
            port=profile["port"],
            user=profile["user"],
            password=profile.get("password", ""),
            database=profile.get("database"),
            connection_timeout=timeout,
        )
    except Exception as e:
        raise _map_mysql_error(e, profile) from e

    try:
        if read_only:
            cursor = conn.cursor()
            try:
                cursor.execute("SET SESSION TRANSACTION READ ONLY")
            finally:
                cursor.close()
        yield conn
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass  # nosec B110


def execute_query(
    profile: Dict[str, Any],
    sql: str,
    params: Optional[Sequence[Any]] = None,
    read_only: bool = True,
    chunk_size: int = 1000,
) -> Tuple[List[str], Generator[List[Dict[str, Any]], None, None]]:
    """Execute a query and stream results in chunks.

    Returns:
        (column_names, chunk_generator)
    """
    with get_connection(profile, read_only=read_only) as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(sql, tuple(params or ()))

            # If not a result-producing statement (e.g. UPDATE, INSERT)
            if cursor.description is None:
                if not read_only:
                    conn.commit()
                rowcount = cursor.rowcount

                def empty_gen():
                    yield [{"affected_rows": rowcount}]

                return ["affected_rows"], empty_gen()

            column_names = [col[0] for col in cursor.description]

            def row_chunks():
                while True:
                    rows = cursor.fetchmany(chunk_size)
                    if not rows:
                        break
                    yield rows

            all_chunks = list(row_chunks())
            return column_names, (c for c in all_chunks)
        except Exception as e:
            if not read_only:
                try:
                    conn.rollback()
                except Exception:
                    pass  # nosec B110
            # Check if this is a read-only transaction violation
            err_msg = str(e)
            msg_lower = err_msg.lower()
            if "read-only" in msg_lower or "read only" in msg_lower or getattr(e, "errno", None) == 1792:
                raise QueryExecutionError(
                    "Cannot execute modifying query in read-only mode.",
                    fix_hint="Use --write to allow database modifications.",
                ) from e
            raise QueryExecutionError(
                f"Query execution failed: {err_msg}",
                fix_hint="Verify SQL syntax and database permissions.",
            ) from e
        finally:
            cursor.close()


def test_connection(profile: Dict[str, Any]) -> Tuple[bool, str, float]:
    """Test MySQL connection and measure round-trip latency.

    Returns:
        (success, server_version, latency_ms)
    """
    t0 = time.perf_counter()
    with get_connection(profile, read_only=True, timeout=5) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT VERSION()")
            row = cursor.fetchone()
            version = row[0] if row else "unknown"
            latency = (time.perf_counter() - t0) * 1000.0
            return True, str(version), latency
        finally:
            cursor.close()
