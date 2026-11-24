"""Unit tests for errors module."""

from oxtan.core.errors import (
    ConfigurationError,
    DatabaseConnectionError,
    OxtanError,
    ProfileNotFoundError,
    QueryExecutionError,
    SecurityError,
    UsageError,
)


def test_oxtan_error_formatting():
    err1 = OxtanError("Something went wrong", fix_hint="Try again")
    assert err1.format_error() == "Error: Something went wrong\nHint: Try again"

    err2 = OxtanError("Bare error")
    assert err2.format_error() == "Error: Bare error"


def test_error_subclasses():
    assert issubclass(ConfigurationError, OxtanError)
    assert issubclass(ProfileNotFoundError, ConfigurationError)
    assert issubclass(SecurityError, OxtanError)
    assert issubclass(DatabaseConnectionError, OxtanError)
    assert issubclass(QueryExecutionError, OxtanError)
    assert issubclass(UsageError, OxtanError)
