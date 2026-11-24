"""Unit tests for all CLI command handlers."""

import argparse
import io
import os
from unittest.mock import MagicMock, patch

import pytest

from oxtan.commands import (
    about,
    add_db,
    count,
    current,
    dbs,
    doctor,
    peek,
    query,
    schema,
    tables,
    use,
)
from oxtan.core.errors import ProfileNotFoundError, UsageError
from oxtan.core.profiles import ProfileManager


@pytest.fixture
def test_pm(temp_profile_dir):
    config_file = os.path.join(temp_profile_dir, "profiles.json")
    pm = ProfileManager(config_file)
    pm.save_profile("test_prof", "127.0.0.1", 3306, "root", "secret", "mydb")
    return pm


def test_add_db_interactive(test_pm):
    args = argparse.Namespace(
        name="new_prof",
        host="localhost",
        port=3306,
        user="testuser",
        database="newdb",
    )
    with patch("sys.stdin.isatty", return_value=True):
        with patch("getpass.getpass", return_value="pass123"):
            res = add_db.run(args, test_pm)
            assert res == 0

    name, prof = test_pm.get_profile("new_prof")
    assert prof["user"] == "testuser"
    assert prof["password"] == "pass123"


def test_add_db_env_password_non_interactive(test_pm):
    args = argparse.Namespace(
        name="ci_prof",
        host="localhost",
        port=3306,
        user="ci",
        database="cidb",
    )
    with patch("sys.stdin.isatty", return_value=False):
        with patch.dict(os.environ, {"OXTAN_PASSWORD": "env_password_secret"}):
            res = add_db.run(args, test_pm)
            assert res == 0

    _, prof = test_pm.get_profile("ci_prof")
    assert prof["password"] == "env_password_secret"


def test_use_command(test_pm):
    test_pm.save_profile("other", "host", 3306, "u", "p", "d")
    args = argparse.Namespace(name="other")
    res = use.run(args, test_pm)
    assert res == 0
    assert test_pm.get_active_profile() == "other"


def test_dbs_command(test_pm):
    args = argparse.Namespace()
    out = io.StringIO()
    err = io.StringIO()
    with patch("sys.stdout", out), patch("sys.stderr", err):
        res = dbs.run(args, test_pm)
        assert res == 0
    assert "test_prof" in out.getvalue()
    assert "*" in out.getvalue()  # Active marker


def test_dbs_empty(temp_profile_dir):
    pm = ProfileManager(os.path.join(temp_profile_dir, "empty.json"))
    args = argparse.Namespace()
    err = io.StringIO()
    with patch("sys.stderr", err):
        res = dbs.run(args, pm)
        assert res == 0
    assert "No profiles saved yet" in err.getvalue()


def test_current_command(test_pm):
    args = argparse.Namespace()
    out = io.StringIO()
    with patch("sys.stdout", out):
        res = current.run(args, test_pm)
        assert res == 0
    assert "Profile:  test_prof" in out.getvalue()
    assert "Database: mydb" in out.getvalue()


def test_current_no_active(temp_profile_dir):
    pm = ProfileManager(os.path.join(temp_profile_dir, "empty.json"))
    args = argparse.Namespace()
    with pytest.raises(ProfileNotFoundError):
        current.run(args, pm)


def test_tables_command(test_pm, monkeypatch):
    mock_execute = MagicMock(
        return_value=(["Tables_in_mydb"], [[{"Tables_in_mydb": "users"}], [{"Tables_in_mydb": "orders"}]])
    )
    monkeypatch.setattr("oxtan.commands.tables.execute_query", mock_execute)

    args = argparse.Namespace(format="table")
    out = io.StringIO()
    with patch("sys.stdout", out):
        res = tables.run(args, test_pm)
        assert res == 0
    assert "users" in out.getvalue()
    assert "orders" in out.getvalue()


def test_schema_command(test_pm, monkeypatch):
    mock_execute = MagicMock(
        return_value=(["Field", "Type"], [[{"Field": "id", "Type": "int"}, {"Field": "name", "Type": "varchar(50)"}]])
    )
    monkeypatch.setattr("oxtan.commands.schema.execute_query", mock_execute)

    args = argparse.Namespace(table="users", format="table")
    out = io.StringIO()
    with patch("sys.stdout", out):
        res = schema.run(args, test_pm)
        assert res == 0
    assert "Field" in out.getvalue()
    assert "varchar(50)" in out.getvalue()


def test_peek_command(test_pm, monkeypatch):
    mock_execute = MagicMock(return_value=(["id", "name"], [[{"id": 1, "name": "alice"}]]))
    monkeypatch.setattr("oxtan.commands.peek.execute_query", mock_execute)

    args = argparse.Namespace(table="users", limit=5, format="table")
    out = io.StringIO()
    with patch("sys.stdout", out):
        res = peek.run(args, test_pm)
        assert res == 0
    assert "alice" in out.getvalue()

    # Invalid limit
    args_bad = argparse.Namespace(table="users", limit=0, format="table")
    with pytest.raises(UsageError):
        peek.run(args_bad, test_pm)


def test_count_command(test_pm, monkeypatch):
    mock_execute = MagicMock(return_value=(["total"], [[{"total": 42}]]))
    monkeypatch.setattr("oxtan.commands.count.execute_query", mock_execute)

    args = argparse.Namespace(table="users")
    out = io.StringIO()
    with patch("sys.stdout", out):
        res = count.run(args, test_pm)
        assert res == 0
    assert out.getvalue().strip() == "42"


def test_query_command_read_only(test_pm, monkeypatch):
    mock_execute = MagicMock(return_value=(["val"], [[{"val": 100}]]))
    monkeypatch.setattr("oxtan.commands.query.execute_query", mock_execute)

    args = argparse.Namespace(sql="SELECT 100 AS val", write=False, yes=False, param=[], format="table")
    out = io.StringIO()
    with patch("sys.stdout", out):
        res = query.run(args, test_pm)
        assert res == 0
    assert "100" in out.getvalue()
    mock_execute.assert_called_with(test_pm.get_profile()[1], "SELECT 100 AS val", params=[], read_only=True)


def test_query_command_write_confirmation(test_pm, monkeypatch):
    mock_execute = MagicMock(return_value=(["affected_rows"], [[{"affected_rows": 1}]]))
    monkeypatch.setattr("oxtan.commands.query.execute_query", mock_execute)

    # Confirmed with 'yes'
    args = argparse.Namespace(sql="DELETE FROM users WHERE id=1", write=True, yes=False, param=[], format="table")
    with patch("sys.stdin.isatty", return_value=True):
        with patch("builtins.input", return_value="y"):
            res = query.run(args, test_pm)
            assert res == 0
    mock_execute.assert_called_with(
        test_pm.get_profile()[1], "DELETE FROM users WHERE id=1", params=[], read_only=False
    )

    # Cancelled with 'no'
    err = io.StringIO()
    with patch("sys.stdin.isatty", return_value=True):
        with patch("builtins.input", return_value="n"), patch("sys.stderr", err):
            res = query.run(args, test_pm)
            assert res == 0
    assert "cancelled" in err.getvalue().lower()


def test_doctor_command(test_pm, monkeypatch):
    monkeypatch.setattr("oxtan.commands.doctor.test_connection", MagicMock(return_value=(True, "8.0.36", 1.5)))
    args = argparse.Namespace()
    out = io.StringIO()
    with patch("sys.stdout", out):
        res = doctor.run(args, test_pm)
        assert res == 0
    assert "[PASS] Python version" in out.getvalue()
    assert "[PASS] Active Profile" in out.getvalue()
    assert "[PASS] MySQL Connection" in out.getvalue()


def test_doctor_command_failures(temp_profile_dir, monkeypatch):
    empty_pm = ProfileManager(os.path.join(temp_profile_dir, "empty.json"))
    args = argparse.Namespace()

    # 1. No active profile -> returns 1
    out = io.StringIO()
    with patch("sys.stdout", out):
        res = doctor.run(args, empty_pm)
        assert res == 1
    assert "[FAIL] Active Profile: No active profile configured" in out.getvalue()

    # 2. Corrupt active profile -> returns 1
    empty_pm.save_profile("p1", "h", 3306, "u", "p", "d")
    with patch.object(empty_pm, "get_profile", side_effect=Exception("Disk error")):
        out2 = io.StringIO()
        with patch("sys.stdout", out2):
            res2 = doctor.run(args, empty_pm)
            assert res2 == 1
        assert "[FAIL] Active Profile: Corrupt configuration" in out2.getvalue()

    # 3. Old Python version (<3.10)
    fake_ver = (3, 9, 7, "final", 0)
    with patch("sys.version_info", fake_ver):
        out3 = io.StringIO()
        with patch("sys.stdout", out3):
            doctor.run(args, empty_pm)
        assert "[FAIL] Python version: 3.9.7" in out3.getvalue()

    # 4. Connection test failure
    monkeypatch.setattr("oxtan.commands.doctor.test_connection", MagicMock(return_value=(False, "unknown", 0.0)))
    out4 = io.StringIO()
    with patch("sys.stdout", out4):
        res4 = doctor.run(args, empty_pm)
        assert res4 == 1
    assert "[FAIL] MySQL Connection: Could not verify server version" in out4.getvalue()

    # 5. Connection test exception
    monkeypatch.setattr("oxtan.commands.doctor.test_connection", MagicMock(side_effect=Exception("Network down")))
    out5 = io.StringIO()
    with patch("sys.stdout", out5):
        res5 = doctor.run(args, empty_pm)
        assert res5 == 1
    assert "[FAIL] MySQL Connection: Network down" in out5.getvalue()


def test_add_db_non_interactive_stdin(test_pm):
    args = argparse.Namespace(
        name="stdin_prof",
        host="localhost",
        port=3306,
        user="testuser",
        database="newdb",
    )
    with patch("sys.stdin.isatty", return_value=False):
        with patch.dict(os.environ, {}, clear=True):
            with patch("sys.stdin.readline", return_value="stdin_secret\n"):
                res = add_db.run(args, test_pm)
                assert res == 0

    _, prof = test_pm.get_profile("stdin_prof")
    assert prof["password"] == "stdin_secret"


def test_query_non_interactive_write_with_yes(test_pm, monkeypatch):
    mock_execute = MagicMock(return_value=(["affected_rows"], [[{"affected_rows": 5}]]))
    monkeypatch.setattr("oxtan.commands.query.execute_query", mock_execute)

    args = argparse.Namespace(sql="UPDATE users SET active=1", write=True, yes=True, param=[], format="table")
    out = io.StringIO()
    with patch("sys.stdout", out):
        res = query.run(args, test_pm)
        assert res == 0
    assert "5" in out.getvalue()


def test_about_command(test_pm):
    args = argparse.Namespace()
    out = io.StringIO()
    out.isatty = lambda: True
    with patch("sys.stdout", out):
        res = about.run(args, test_pm)
        assert res == 0
    assert "Oxtan v0.1.0" in out.getvalue()
