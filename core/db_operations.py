import os
import pandas as pd
from typing import Optional, Any, List, Dict, Union
from database.connection import DatabaseConnection
from utils.query_builder import build_where_clause

class OxtanDB:
    """Core class for Oxtan database CRUD operations."""
    
    def __init__(self, **kwargs):
        """
        Initializes the Oxtan database operations layer.
        
        It sets up the database connection using kwargs or environment variables.
        """
        config = {
            "host": kwargs.get("host") or os.getenv("DB_HOST", "localhost"),
            "user": kwargs.get("user") or os.getenv("DB_USER", "root"),
            "password": kwargs.get("password") or os.getenv("DB_PASS"),
            "database": kwargs.get("database") or os.getenv("DB_NAME"),
            "port": int(kwargs.get("port") or os.getenv("DB_PORT", 3306)),
        }

        if not config["password"] or not config["database"]:
            raise ValueError(
                "❌ CRITICAL: Missing password or database! "
                "Pass them as kwargs or set DB_PASS and DB_NAME in your environment variables."
            )

        pool_name = kwargs.get("pool_name", "oxtan_pool")
        pool_size = kwargs.get("pool_size", 5)
        
        self.db = DatabaseConnection(config, pool_name, pool_size)

    def select(self, table: str, columns: Union[str, List[str]] = "*", where: Union[str, Dict[str, Any]] = None, as_df: bool = True) -> Union[List[Dict], pd.DataFrame]:
        """Fetches data and optionally returns a Pandas DataFrame."""
        cols = ", ".join(columns) if isinstance(columns, list) else columns
        sql = f"SELECT {cols} FROM {table}"
        
        where_clause, params = build_where_clause(where)
        sql += where_clause
            
        results = self.db.execute(sql, tuple(params), fetch=True)
        
        if as_df:
            return pd.DataFrame(results) if results else pd.DataFrame()
        return results

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """Inserts a new record into the specified table."""
        keys = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        sql = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
        return self.db.execute(sql, tuple(data.values()))

    def update(self, table: str, data: Dict[str, Any], where: Union[str, Dict[str, Any]]) -> int:
        """Updates existing records in the table."""
        if not where:
            raise ValueError("🔒 Oxtan Safety Lock: Blocked UPDATE without WHERE clause to prevent overwriting all rows.")
            
        set_clause = ", ".join([f"{k} = %s" for k in data.keys()])
        sql = f"UPDATE {table} SET {set_clause}"
        
        where_clause, where_params = build_where_clause(where)
        sql += where_clause
        
        params = list(data.values()) + where_params
        return self.db.execute(sql, tuple(params))

    def delete(self, table: str, where: Union[str, Dict[str, Any]]) -> int:
        """Deletes records from the table."""
        if not where:
            raise ValueError("🔒 Oxtan Safety Lock: Blocked DELETE without WHERE clause to prevent wiping the table.")
            
        sql = f"DELETE FROM {table}"
        where_clause, params = build_where_clause(where)
        sql += where_clause
             
        return self.db.execute(sql, tuple(params))

    def raw(self, sql: str, params: tuple = None, as_df: bool = False) -> Any:
        """Executes a raw SQL query."""
        sql_upper = sql.strip().upper()
        returns_data = sql_upper.startswith(("SELECT", "SHOW", "DESCRIBE", "EXPLAIN"))
        
        results = self.db.execute(sql, params, fetch=returns_data)
        
        if returns_data and as_df:
             return pd.DataFrame(results) if results else pd.DataFrame()
        return results

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def get_tables(self) -> List[str]:
        """Retrieves a list of tables in the current database."""
        res = self.db.execute("SHOW TABLES", fetch=True)
        return [list(r.values())[0] for r in res] if res else []
