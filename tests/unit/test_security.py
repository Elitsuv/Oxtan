"""Unit tests for SQL identifier validation and parameterization safety."""

import pytest

from oxtan.core.errors import SecurityError
from oxtan.core.security import (
    build_where_clause,
    quote_identifier,
    validate_and_quote_columns,
    validate_identifier,
)

MALFORMED_IDENTIFIER_CORPUS = [
    "",  # 1. Empty string
    " ",  # 2. Single space
    "   ",  # 3. Multiple spaces
    "users ",  # 4. Trailing space
    " users",  # 5. Leading space
    "user name",  # 6. Space in between
    "users; DROP TABLE users; --",  # 7. Semicolon and drop
    "users; SELECT 1;",  # 8. Semicolon multiple statement
    "users--",  # 9. SQL comment dash
    "users/*comment*/",  # 10. Inline comment
    "users#comment",  # 11. Hash comment
    "`users`",  # 12. Raw backtick quoted
    "`",  # 13. Single backtick
    "'",  # 14. Single quote
    '"',  # 15. Double quote
    "users' OR '1'='1",  # 16. Classic single-quote injection
    'users" OR "1"="1',  # 17. Classic double-quote injection
    "users\\",  # 18. Backslash
    "user-table",  # 19. Hyphen
    "user.table",  # 20. Dot notation (schema injection)
    "user$table",  # 21. Dollar sign
    "user@table",  # 22. At symbol
    "user!table",  # 23. Exclamation
    "user%table",  # 24. Percent
    "user^table",  # 25. Caret
    "user&table",  # 26. Ampersand
    "user*table",  # 27. Asterisk
    "user(table)",  # 28. Parentheses
    "user+table",  # 29. Plus
    "user=table",  # 30. Equals
    "user<table",  # 31. Less than
    "user>table",  # 32. Greater than
    "user?table",  # 33. Question mark
    "user/table",  # 34. Slash
    "user|table",  # 35. Pipe
    "user~table",  # 36. Tilde
    "user`name",  # 37. Mid-string backtick
    "a" * 65,  # 38. 65 characters (exceeds max 64)
    "a" * 100,  # 39. 100 characters
    "tablé",  # 40. Unicode accent
    "таблица",  # 41. Cyrillic characters
    "用户",  # 42. CJK characters
    "users\x00",  # 43. Null byte
    "users\n",  # 44. Newline
    "users\r",  # 45. Carriage return
    "users\t",  # 46. Tab character
    "admin'--",  # 47. Injection payload
    "123;SELECT",  # 48. Semicolon without space
    None,  # 49. NoneType
    12345,  # 50. Integer
    ["users"],  # 51. List
]


@pytest.mark.parametrize("payload", MALFORMED_IDENTIFIER_CORPUS)
def test_validate_identifier_rejects_malformed_corpus(payload):
    """Corpus of 50+ injection/malformed payloads must all be rejected."""
    with pytest.raises(SecurityError):
        validate_identifier(payload)  # type: ignore


@pytest.mark.parametrize("valid_name", ["users", "order_items", "user_123", "UserTable", "COL1", "A"])
def test_validate_identifier_accepts_valid_names(valid_name):
    assert validate_identifier(valid_name) == valid_name
    assert quote_identifier(valid_name) == f"`{valid_name}`"


def test_validate_and_quote_columns():
    assert validate_and_quote_columns("*") == "*"
    assert validate_and_quote_columns(["id", "username", "created_at"]) == "`id`, `username`, `created_at`"
    assert validate_and_quote_columns("id") == "`id`"

    with pytest.raises(SecurityError):
        validate_and_quote_columns([])
    with pytest.raises(SecurityError):
        validate_and_quote_columns(["id", "user; DROP TABLE"])


def test_build_where_clause_dict():
    # None
    sql, params = build_where_clause(None)
    assert sql == ""
    assert params == []

    # Empty dict
    sql, params = build_where_clause({})
    assert sql == ""
    assert params == []

    # Simple dict
    sql, params = build_where_clause({"status": "active", "age": 25})
    assert sql == " WHERE `status` = %s AND `age` = %s"
    assert params == ["active", 25]

    # None value becomes IS NULL (never = NULL)
    sql, params = build_where_clause({"deleted_at": None, "active": 1})
    assert sql == " WHERE `deleted_at` IS NULL AND `active` = %s"
    assert params == [1]


def test_build_where_clause_tuple():
    sql, params = build_where_clause(("id > %s AND status = %s", [10, "open"]))
    assert sql == " WHERE id > %s AND status = %s"
    assert params == [10, "open"]

    # Empty fragment
    sql, params = build_where_clause(("", []))
    assert sql == ""
    assert params == []


def test_build_where_clause_rejects_raw_strings_and_invalid():
    # Reject raw strings
    with pytest.raises(SecurityError) as exc_info:
        build_where_clause("1=1; DROP TABLE users;")
    assert "Raw string WHERE clauses are rejected" in str(exc_info.value)

    # Reject invalid types
    with pytest.raises(SecurityError):
        build_where_clause(123)

    # Reject malformed tuple
    with pytest.raises(SecurityError):
        build_where_clause(("only_one_element",))
