import os
import getpass
import logging
import mysql.connector
from mysql.connector import pooling, Error
from typing import Optional, Any, List, Dict, Union

logger = logging.getLogger("oxtan")

class OxtanDB:
    def __init__(self, **kwargs):
        self.config = {
            "host": kwargs.get("host") or os.getenv("MYSQL_HOST") or self._ask("Host", "localhost"),
            "user": kwargs.get("user") or os.getenv("MYSQL_USER") or self._ask("User", "root"),
            "database": kwargs.get("database") or os.getenv("MYSQL_DATABASE") or self._ask("Database Name"),
            "port": int(kwargs.get("port") or os.getenv("MYSQL_PORT", 3306)),
        }
        
        password = kwargs.get("password") or os.getenv("MYSQL_PASSWORD")
        if not password:
            password = getpass.getpass(f"🔑 Password for {self.config['user']}@{self.config['host']}: ")
        
        self.config["password"] = password
        self.pool = None
        self._initialize_pool(kwargs.get("pool_name", "oxtan_pool"), kwargs.get("pool_size", 5))

    def _ask(self, field: str, default: str = None) -> str:
        prompt = f"🔡 Enter MySQL {field}"
        if default:
            prompt += f" (default: {default})"
        val = input(f"{prompt}: ").strip()
        return val if val else default

    def _initialize_pool(self, name: str, size: int):
        try:
            self.pool = pooling.MySQLConnectionPool(
                pool_name=name,
                pool_size=size,
                pool_reset_session=True,
                **self.config
            )
            print(f"✅ Oxtan Connected: {self.config['database']}")
        except Error as e:
            raise ConnectionError(f"❌ Initialization Failed: {e}")

    def _execute(self, sql: str, params: tuple = None, fetch: bool = False, commit: bool = True) -> Any:
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
            logger.error(f"SQL Error: {e}")
            raise RuntimeError(f"Database Error: {e}")
        finally:
            cursor.close()
            conn.close()

    def select(self, table: str, columns: Union[str, List[str]] = "*", where: Dict[str, Any] = None) -> List[Dict]:
        cols = ", ".join(columns) if isinstance(columns, list) else columns
        sql = f"SELECT {cols} FROM {table}"
        params = []
        if where:
            sql += " WHERE " + " AND ".join([f"{k} = %s" for k in where.keys()])
            params = list(where.values())
        return self._execute(sql, tuple(params), fetch=True)

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        keys = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        sql = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
        return self._execute(sql, tuple(data.values()))

    def update(self, table: str, data: Dict[str, Any], where: Dict[str, Any]) -> int:
        set_clause = ", ".join([f"{k} = %s" for k in data.keys()])
        where_clause = " AND ".join([f"{k} = %s" for k in where.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        params = list(data.values()) + list(where.values())
        return self._execute(sql, tuple(params))

    def delete(self, table: str, where: Dict[str, Any]) -> int:
        where_clause = " AND ".join([f"{k} = %s" for k in where.keys()])
        sql = f"DELETE FROM {table} WHERE {where_clause}"
        return self._execute(sql, tuple(where.values()))

    def raw(self, sql: str, params: tuple = None) -> Any:
        is_select = sql.strip().upper().startswith("SELECT")
        return self._execute(sql, params, fetch=is_select)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def get_tables(self) -> List[str]:
        res = self.raw("SHOW TABLES")
        return [list(r.values())[0] for r in res]