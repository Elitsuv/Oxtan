"""Pytest fixtures and configuration."""

import os
import sys
import tempfile
from unittest.mock import MagicMock

import pytest

# Ensure src is on sys.path
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


@pytest.fixture
def temp_profile_dir():
    """Create a temporary directory for isolated profile tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def mock_mysql_connector(monkeypatch):
    """Mock mysql.connector for unit tests."""
    mock_driver = MagicMock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    mock_driver.connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    mock_mysql_pkg = MagicMock()
    mock_mysql_pkg.connector = mock_driver

    monkeypatch.setitem(sys.modules, "mysql", mock_mysql_pkg)
    monkeypatch.setitem(sys.modules, "mysql.connector", mock_driver)
    return mock_driver, mock_conn, mock_cursor
