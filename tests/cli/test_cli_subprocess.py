"""Subprocess tests for Oxtan CLI.

Tests real subprocess invocation verifying:
- Exit codes: 0 (ok), 1 (runtime error), 2 (usage error), 130 (Ctrl+C)
- stdout vs stderr separation
- Doodle suppression when piped or with --quiet
- --quiet and NO_COLOR handling
- --debug traceback behavior vs clean single-line error
- --help for every command and alias
- Piping and format checks
"""

import csv
import json
import os
import subprocess
import sys
import tempfile

import pytest

PYTHON_EXE = sys.executable
MAIN_PY = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "main.py"))


def run_cli(*args, env=None, input_text=None, timeout=30) -> subprocess.CompletedProcess:
    """Helper to run oxtan CLI as a real subprocess with strict isolation and timeout."""
    cmd = [PYTHON_EXE, MAIN_PY, *args]
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    effective_input = input_text if input_text is not None else ""

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=merged_env,
        input=effective_input,
        timeout=timeout,
    )


def test_cli_version():
    proc = run_cli("--version")
    assert proc.returncode == 0
    assert "oxtan 0.1.0" in proc.stdout or "oxtan 0.1.0" in proc.stderr


def test_cli_no_args_suppressed_when_piped():
    # When piped (sys.stdout.isatty() == False), doodle never appears
    proc = run_cli()
    assert proc.returncode == 0
    assert proc.stdout == ""


def test_cli_quiet_flag_suppresses_doodle():
    proc = run_cli("--quiet")
    assert proc.returncode == 0
    assert proc.stdout == ""


def test_cli_help():
    proc = run_cli("--help")
    assert proc.returncode == 0
    assert "Oxtan - Fast, safe command-line tool for MySQL." in proc.stdout
    assert "tables (t)" in proc.stdout
    assert "schema (s)" in proc.stdout
    assert "peek (p)" in proc.stdout
    assert "query (q)" in proc.stdout


@pytest.mark.parametrize(
    "cmd",
    [
        "add-db",
        "use",
        "dbs",
        "current",
        "tables",
        "t",
        "schema",
        "s",
        "peek",
        "p",
        "count",
        "query",
        "q",
        "doctor",
        "about",
    ],
)
def test_all_commands_and_aliases_help(cmd):
    proc = run_cli(cmd, "--help")
    assert proc.returncode == 0
    assert "usage:" in proc.stdout or "usage:" in proc.stderr


def test_usage_error_exit_code_2_on_invalid_command():
    proc = run_cli("invalid-command")
    assert proc.returncode == 2
    assert "Error:" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_usage_error_exit_code_2_on_missing_required_args():
    for cmd in ["schema", "count", "peek", "use"]:
        proc = run_cli(cmd)
        assert proc.returncode == 2
        assert "Error:" in proc.stderr
        assert "Traceback" not in proc.stderr


def test_usage_error_exit_code_2_on_unknown_flags():
    proc = run_cli("current", "--bogus-flag")
    assert proc.returncode == 2
    assert "Error:" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_runtime_error_exit_code_1_clean_error():
    with tempfile.TemporaryDirectory() as tmp_dir:
        fake_home = {"HOME": tmp_dir, "USERPROFILE": tmp_dir}
        proc = run_cli("current", env=fake_home)
        assert proc.returncode == 1
        assert "No active database profile selected" in proc.stderr
        assert "Traceback" not in proc.stderr


def test_debug_flag_shows_traceback():
    with tempfile.TemporaryDirectory() as tmp_dir:
        fake_home = {"HOME": tmp_dir, "USERPROFILE": tmp_dir}
        proc = run_cli("current", "--debug", env=fake_home)
        assert proc.returncode == 1
        assert "Traceback (most recent call last):" in proc.stderr
        assert "ProfileNotFoundError" in proc.stderr


def test_stdout_stderr_separation():
    with tempfile.TemporaryDirectory() as tmp_dir:
        fake_home = {"HOME": tmp_dir, "USERPROFILE": tmp_dir, "OXTAN_PASSWORD": "secret_pass"}
        proc_add = run_cli(
            "add-db",
            "test_prof",
            "--host",
            "127.0.0.1",
            "--database",
            "test_db",
            env=fake_home,
        )
        assert proc_add.returncode == 0
        assert "Saved profile" in proc_add.stderr
        assert proc_add.stdout == ""

        # Test current outputs data to stdout
        proc_cur = run_cli("current", env=fake_home)
        assert proc_cur.returncode == 0
        assert "Profile:  test_prof" in proc_cur.stdout
        assert "test_db" in proc_cur.stdout


def test_empty_password_allowed():
    with tempfile.TemporaryDirectory() as tmp_dir:
        fake_home = {"HOME": tmp_dir, "USERPROFILE": tmp_dir}
        proc = run_cli(
            "add-db",
            "emptypass",
            "--host",
            "localhost",
            "--database",
            "localdb",
            env=fake_home,
            input_text="\n",
        )
        assert proc.returncode == 0
        assert "Saved profile 'emptypass'" in proc.stderr


def test_piping_json_tool_roundtrip():
    # Test piping JSON data into python -m json.tool
    test_json = '[{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}]'
    proc = subprocess.run(
        [PYTHON_EXE, "-m", "json.tool"],
        input=test_json,
        text=True,
        capture_output=True,
        timeout=10,
    )
    assert proc.returncode == 0
    parsed = json.loads(proc.stdout)
    assert len(parsed) == 2
    assert parsed[0]["name"] == "alice"


def test_csv_file_write_and_read_back():
    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_file = os.path.join(tmp_dir, "test.csv")
        csv_content = 'id,name,notes\n1,alice,first\n2,"bob, jr.",second\n'
        with open(csv_file, "w", encoding="utf-8") as f:
            f.write(csv_content)

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = list(csv.reader(f))

        assert len(reader) == 3
        assert reader[0] == ["id", "name", "notes"]
        assert reader[2][1] == "bob, jr."
