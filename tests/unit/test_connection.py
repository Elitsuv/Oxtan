"""Unit tests for database connection handling."""

import pytest

from oxtan.core.connection import (
    execute_query,
    get_connection,
)
from oxtan.core.connection import (
    test_connection as run_doctor_test_connection,
)
from oxtan.core.errors import DatabaseConnectionError, QueryExecutionError


def test_get_connection_success(mock_mysql_connector):
    mock_driver, mock_conn, mock_cursor = mock_mysql_connector

    profile = {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "secret_password",
        "database": "my_db",
    }

    with get_connection(profile, read_only=False) as conn:
        assert conn == mock_conn

    # Check connection was established with parameters and closed on exit
    mock_driver.connect.assert_called_once_with(
        host="localhost",
        port=3306,
        user="root",
        password="secret_password",
        database="my_db",
        connection_timeout=10,
        allow_local_infile=False,
    )
    mock_conn.close.assert_called_once()


def test_get_connection_read_only_enforcement(mock_mysql_connector):
    mock_driver, mock_conn, mock_cursor = mock_mysql_connector

    profile = {"host": "localhost", "port": 3306, "user": "root", "password": "", "database": "db"}

    with get_connection(profile, read_only=True) as conn:
        assert conn == mock_conn

    mock_cursor.execute.assert_called_with("SET SESSION TRANSACTION READ ONLY")
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()


def test_connection_always_closed_on_exception(mock_mysql_connector):
    mock_driver, mock_conn, mock_cursor = mock_mysql_connector
    profile = {"host": "localhost", "port": 3306, "user": "root", "password": "", "database": "db"}

    with pytest.raises(RuntimeError):
        with get_connection(profile):
            raise RuntimeError("Unexpected failure during operation")

    # Ensure connection closed even when exception thrown
    mock_conn.close.assert_called_once()


def test_execute_query_select(mock_mysql_connector):
    mock_driver, mock_conn, mock_cursor = mock_mysql_connector
    profile = {"host": "localhost", "port": 3306, "user": "root", "password": "", "database": "db"}

    # Mock cursor description and fetchmany
    mock_cursor.description = [("id",), ("name",)]
    mock_cursor.fetchmany.side_effect = [
        [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
        [],
    ]

    cols, chunks = execute_query(profile, "SELECT * FROM users", read_only=True)
    assert cols == ["id", "name"]
    result_chunks = list(chunks)
    assert len(result_chunks) == 1
    assert len(result_chunks[0]) == 2
    assert result_chunks[0][0]["name"] == "Alice"


def test_execute_query_modifying_blocked_in_read_only(mock_mysql_connector):
    mock_driver, mock_conn, mock_cursor = mock_mysql_connector
    profile = {"host": "localhost", "port": 3306, "user": "root", "password": "", "database": "db"}

    mock_cursor.execute.side_effect = [
        None,  # SET SESSION TRANSACTION READ ONLY succeeds
        Exception("1792 (25006): Cannot execute statement in a READ ONLY transaction."),  # INSERT fails
    ]

    with pytest.raises(QueryExecutionError) as exc_info:
        execute_query(profile, "INSERT INTO users (name) VALUES ('Charlie')", read_only=True)
    assert "read-only mode" in str(exc_info.value).lower()
    assert "--write" in exc_info.value.fix_hint


def test_execute_query_write_commits(mock_mysql_connector):
    mock_driver, mock_conn, mock_cursor = mock_mysql_connector
    profile = {"host": "localhost", "port": 3306, "user": "root", "password": "", "database": "db"}

    mock_cursor.description = None  # Non-select statement
    mock_cursor.rowcount = 1

    cols, chunks = execute_query(profile, "UPDATE users SET name='Alice' WHERE id=1", read_only=False)
    assert cols == ["affected_rows"]
    rows = list(chunks)[0]
    assert rows == [{"affected_rows": 1}]
    mock_conn.commit.assert_called_once()


def test_doctor_connection_measurement(mock_mysql_connector):
    mock_driver, mock_conn, mock_cursor = mock_mysql_connector
    profile = {"host": "localhost", "port": 3306, "user": "root", "password": "", "database": "db"}

    mock_cursor.fetchone.return_value = ("8.0.36",)

    success, version, latency = run_doctor_test_connection(profile)
    assert success is True
    assert version == "8.0.36"
    assert latency >= 0.0


def test_map_mysql_errors(mock_mysql_connector):
    mock_driver, mock_conn, mock_cursor = mock_mysql_connector
    profile = {"host": "remotehost", "port": 3306, "user": "alice", "password": "x", "database": "inventory"}

    class DummyDriverError(Exception):
        def __init__(self, errno, msg):
            super().__init__(msg)
            self.errno = errno

    # 1045 Access denied
    mock_driver.connect.side_effect = DummyDriverError(1045, "Access denied")
    with pytest.raises(DatabaseConnectionError) as exc:
        with get_connection(profile):
            pass
    assert "Access denied for user 'alice'" in str(exc.value)

    # 2003 Can't connect
    mock_driver.connect.side_effect = DummyDriverError(2003, "Can't connect to server")
    with pytest.raises(DatabaseConnectionError) as exc:
        with get_connection(profile):
            pass
    assert "Cannot connect to MySQL server at 'remotehost:3306'" in str(exc.value)

    # 1049 Unknown database
    mock_driver.connect.side_effect = DummyDriverError(1049, "Unknown database")
    with pytest.raises(DatabaseConnectionError) as exc:
        with get_connection(profile):
            pass
    assert "Database 'inventory' does not exist" in str(exc.value)

    # 2006 Lost connection
    mock_driver.connect.side_effect = DummyDriverError(2006, "MySQL server has gone away")
    with pytest.raises(DatabaseConnectionError) as exc:
        with get_connection(profile):
            pass
    assert "MySQL connection was lost or timed out" in str(exc.value)

    # Generic error
    mock_driver.connect.side_effect = DummyDriverError(9999, "Other error")
    with pytest.raises(DatabaseConnectionError) as exc:
        with get_connection(profile):
            pass
    assert "Database connection error" in str(exc.value)


def test_error_redacts_password(mock_mysql_connector):
    mock_driver, mock_conn, mock_cursor = mock_mysql_connector
    profile = {"host": "localhost", "port": 3306, "user": "root", "password": "my_secret_123", "database": "db"}

    mock_driver.connect.side_effect = RuntimeError("Auth failed using password my_secret_123 on host")
    with pytest.raises(DatabaseConnectionError) as exc_info:
        with get_connection(profile):
            pass
    assert "my_secret_123" not in str(exc_info.value)
    assert "***" in str(exc_info.value)


def test_execute_query_error_redacts_password(mock_mysql_connector):
    mock_driver, mock_conn, mock_cursor = mock_mysql_connector
    profile = {"host": "localhost", "port": 3306, "user": "root", "password": "my_secret_123", "database": "db"}

    mock_cursor.execute.side_effect = [
        None,  # SET SESSION TRANSACTION READ ONLY
        RuntimeError("Driver leaked my_secret_123 in trace"),
    ]
    with pytest.raises(QueryExecutionError) as exc_info:
        execute_query(profile, "SELECT 1", read_only=True)
    assert "my_secret_123" not in str(exc_info.value)
    assert "***" in str(exc_info.value)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM users INTO OUTFILE '/tmp/out.csv'",
        "SELECT * FROM users INTO DUMPFILE '/tmp/out.bin'",
        "LOAD DATA INFILE '/etc/passwd' INTO TABLE users",
    ],
)
def test_execute_query_blocks_file_clauses_in_read_only(mock_mysql_connector, sql):
    profile = {"host": "localhost", "port": 3306, "user": "root", "password": "", "database": "db"}
    with pytest.raises(QueryExecutionError) as exc_info:
        execute_query(profile, sql, read_only=True)
    assert "read-only mode" in str(exc_info.value).lower()
    assert "--write" in exc_info.value.fix_hint


def test_execute_query_allows_literal_into_outfile_text(mock_mysql_connector):
    mock_driver, mock_conn, mock_cursor = mock_mysql_connector
    profile = {"host": "localhost", "port": 3306, "user": "root", "password": "", "database": "db"}
    mock_cursor.description = [("msg",)]
    mock_cursor.fetchmany.side_effect = [[{"msg": "into outfile"}], []]

    cols, chunks = execute_query(profile, "SELECT 'into outfile' AS msg", read_only=True)
    assert cols == ["msg"]
    assert list(chunks)[0][0]["msg"] == "into outfile"
