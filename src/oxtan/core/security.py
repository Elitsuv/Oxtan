"""SQL identifier validation and parameterization safety for Oxtan."""

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from oxtan.core.errors import SecurityError

_IDENTIFIER_REGEX = re.compile(r"^[a-zA-Z0-9_]+\Z")
_MAX_IDENTIFIER_LENGTH = 64


def validate_identifier(name: str) -> str:
    """Validate a SQL identifier (table name, column name).

    Allows only ASCII letters, digits, and underscores, max 64 characters.
    Rejects spaces, backticks, semicolons, dashes, quotes, unicode, comments,
    and empty strings.

    Raises:
        SecurityError: If identifier fails validation.
    """
    if not isinstance(name, str):
        raise SecurityError(
            f"Identifier must be a string, got {type(name).__name__}.",
            fix_hint="Use alphanumeric names with underscores only.",
        )

    if not name:
        raise SecurityError(
            "Identifier cannot be empty.",
            fix_hint="Provide a valid table or column name.",
        )

    if len(name) > _MAX_IDENTIFIER_LENGTH:
        raise SecurityError(
            f"Identifier '{name[:15]}...' exceeds maximum length of {_MAX_IDENTIFIER_LENGTH} characters.",
            fix_hint=f"Shorten identifier to under {_MAX_IDENTIFIER_LENGTH} characters.",
        )

    if not _IDENTIFIER_REGEX.match(name):
        raise SecurityError(
            f"Invalid identifier '{name}'. Identifiers must contain only letters, digits, and underscores.",
            fix_hint="Remove special characters, spaces, dashes, or punctuation.",
        )

    return name


def quote_identifier(name: str) -> str:
    """Validate and backtick-quote a SQL identifier."""
    valid_name = validate_identifier(name)
    return f"`{valid_name}`"


def validate_and_quote_columns(columns: Union[str, Sequence[str]]) -> str:
    """Validate and quote a column or list of columns.

    Supports '*' as a wildcard.
    """
    if isinstance(columns, str):
        if columns.strip() == "*":
            return "*"
        return quote_identifier(columns.strip())

    if not isinstance(columns, (list, tuple)):
        raise SecurityError(
            "Columns must be '*' or a list of column names.",
            fix_hint="Specify columns as a list of strings, e.g. ['id', 'name'].",
        )

    if not columns:
        raise SecurityError(
            "Column list cannot be empty.",
            fix_hint="Specify at least one column or use '*'.",
        )

    return ", ".join(quote_identifier(col) for col in columns)


def build_where_clause(where: Optional[Union[Dict[str, Any], Tuple[str, Sequence[Any]]]]) -> Tuple[str, List[Any]]:
    """Build a parameterized SQL WHERE clause.

    Accepts:
      - None: returns ('', [])
      - Dict[str, Any]: key-value pairs. Keys are validated and quoted.
        None values generate 'IS NULL' (never '= NULL'). Non-None values are parameterized.
      - Tuple[str, Sequence[Any]]: (sql_fragment, params) tuple.

    Rejects:
      - Raw strings (SQL injection prevention).
      - Anything else.
    """
    if where is None:
        return "", []

    if isinstance(where, str):
        raise SecurityError(
            "Raw string WHERE clauses are rejected for security.",
            fix_hint="Pass a dictionary of key-value pairs or a (sql_fragment, params) tuple.",
        )

    if isinstance(where, dict):
        if not where:
            return "", []

        clauses: List[str] = []
        params: List[Any] = []

        for key, val in where.items():
            quoted_key = quote_identifier(key)
            if val is None:
                clauses.append(f"{quoted_key} IS NULL")
            else:
                clauses.append(f"{quoted_key} = %s")
                params.append(val)

        return " WHERE " + " AND ".join(clauses), params

    if isinstance(where, (tuple, list)):
        if len(where) != 2:
            raise SecurityError(
                "WHERE tuple must contain exactly (sql_fragment, params).",
                fix_hint="Format as ('col1 = %s AND col2 > %s', [val1, val2]).",
            )
        sql_fragment, params_seq = where
        if not isinstance(sql_fragment, str):
            raise SecurityError(
                "SQL fragment in WHERE tuple must be a string.",
                fix_hint="Provide a SQL condition string with %s placeholders.",
            )
        if not isinstance(params_seq, (list, tuple)):
            raise SecurityError(
                "Parameters in WHERE tuple must be a list or tuple.",
                fix_hint="Pass parameters as a sequence, e.g. [1, 'val'].",
            )
        fragment_clean = sql_fragment.strip()
        if not fragment_clean:
            return "", []
        return f" WHERE {fragment_clean}", list(params_seq)

    raise SecurityError(
        f"Unsupported WHERE clause type: {type(where).__name__}.",
        fix_hint="Use a dictionary e.g. {'id': 1} or a ('status = %s', ['active']) tuple.",
    )
