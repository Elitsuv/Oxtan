import os
import getpass
import logging
import mysql.connector
from mysql.connector import pooling, Error
from typing import Optional, Any, List, Dict, Union
import pandas as pd

# Setup basic logger
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("oxtan")

class OxtanDB:
    def __init__(self, **kwargs):
        """
        MNC Standard: Initializes silently. No input() prompts.
        Relies strictly on kwargs or Environment Variables.
        """
        self.config = {
            "host": kwargs.get("host") or os.getenv("MYSQL_HOST", "localhost"),
            "user": kwargs.get("user") or os.getenv("MYSQL_USER", "root"),
            "password": kwargs.get("password") or os.getenv("MYSQL_PASSWORD"),
            "database": kwargs.get("database") or os.getenv("MYSQL_DATABASE"),
            "port": int(kwargs.get("port") or os.getenv("MYSQL_PORT", 3306)),
        }

        # Fail fast if critical data is missing
        if not self.config["password"] or not self.config["database"]:
            raise ValueError("❌ Missing password or database! Pass them as kwargs or use .env variables.")

        self.pool = None
        self._initialize_pool(kwargs.get("pool_name", "oxtan_pool"), kwargs.get("pool_size", 5))

    @classmethod
    def from_cli(cls):
        """
        Alternative Constructor: Use this if you specifically WANT an interactive prompt.
        Example: db = OxtanDB.from_cli()
        """
        print("--- Oxtan Interactive Setup ---")
        host = input("🔡 Enter MySQL Host (default: localhost): ").strip() or "localhost"
        user = input("🔡 Enter MySQL User (default: root): ").strip() or "root"
        database = input("🔡 Enter Database Name: ").strip()
        password = getpass.getpass(f"🔑 Password for {user}@{host}: ")
        
        return cls(host=host, user=user, password=password, database=database)

    def _initialize_pool(self, name: str, size: int):
        try:
            self.pool = pooling.MySQLConnectionPool(
                pool_name=name,
                pool_size=size,
                pool_reset_session=True,
                **self.config
            )
            logger.info(f"✅ Oxtan Connected to database: {self.config['database']}")
        except Error as e:
            raise ConnectionError(f"❌ Pool Initialization Failed: {e}")

    def _execute(self, sql: str, params: tuple = None, fetch: bool = False, commit: bool = True) -> Any:
        """Internal method handling the actual pool borrowing and cursor logic."""
        conn = self.pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(sql, params or ())
            if fetch:
                return cursor.fetchall()
            if commit:
                conn.commit()
            return cursor.rowcount
        except Error as e:
            conn.rollback()
            logger.error(f"SQL Error: {e} | Query: {sql}")
            raise RuntimeError(f"Database Error: {e}")
        finally:
            cursor.close()
            conn.close() # Returns connection to the pool

    def select(self, table: str, columns: Union[str, List[str]] = "*", where: Dict[str, Any] = None, as_df: bool = True) -> Union[List[Dict], pd.DataFrame]:
        """Fetches data. Returns a Pandas DataFrame by default for ML workflows."""
        cols = ", ".join(columns) if isinstance(columns, list) else columns
        sql = f"SELECT {cols} FROM {table}"
        params = []
        
        if where:
            sql += " WHERE " + " AND ".join([f"{k} = %s" for k in where.keys()])
            params = list(where.values())
            
        results = self._execute(sql, tuple(params), fetch=True)
        
        if as_df:
            return pd.DataFrame(results) if results else pd.DataFrame()
        return results

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        keys = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        sql = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
        return self._execute(sql, tuple(data.values()))

    def update(self, table: str, data: Dict[str, Any], where: Dict[str, Any]) -> int:
        if not where:
            raise ValueError("🔒 Oxtan Safety Lock: Blocked UPDATE without WHERE clause to prevent overwriting all rows.")
            
        set_clause = ", ".join([f"{k} = %s" for k in data.keys()])
        where_clause = " AND ".join([f"{k} = %s" for k in where.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        params = list(data.values()) + list(where.values())
        return self._execute(sql, tuple(params))

    def delete(self, table: str, where: Dict[str, Any]) -> int:
        if not where:
            raise ValueError("🔒 Oxtan Safety Lock: Blocked DELETE without WHERE clause to prevent wiping the table.")
            
        where_clause = " AND ".join([f"{k} = %s" for k in where.keys()])
        sql = f"DELETE FROM {table} WHERE {where_clause}"
        return self._execute(sql, tuple(where.values()))

    def raw(self, sql: str, params: tuple = None, as_df: bool = False) -> Any:
        is_select = sql.strip().upper().startswith("SELECT")
        results = self._execute(sql, params, fetch=is_select)
        if is_select and as_df:
             return pd.DataFrame(results) if results else pd.DataFrame()
        return results

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Even though pools manage themselves, this allows users to use the 'with' statement cleanly.
        pass

    def get_tables(self) -> List[str]:
        res = self.raw("SHOW TABLES")
        return [list(r.values())[0] for r in res] if res else []
