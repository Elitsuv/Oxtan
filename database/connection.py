import logging
from mysql.connector import pooling, Error
from typing import Any, Dict

logger = logging.getLogger("oxtan")

class DatabaseConnection:
    """Handles MySQL connection pooling and execution of SQL queries."""
    
    def __init__(self, config: Dict[str, Any], pool_name: str = "oxtan_pool", pool_size: int = 5):
        """
        Initializes the database connection pool.
        
        Args:
            config: MySQL connection configuration dictionary.
            pool_name: Name of the connection pool.
            pool_size: Number of connections to keep in the pool.
        """
        self.config = config
        self.pool = None
        self._initialize_pool(pool_name, pool_size)

    def _initialize_pool(self, name: str, size: int):
        try:
            self.pool = pooling.MySQLConnectionPool(
                pool_name=name,
                pool_size=size,
                pool_reset_session=True,
                **self.config
            )
            logger.info(f"✅ Oxtan Connected to database: {self.config.get('database')}")
        except Error as e:
            raise ConnectionError(f"❌ Pool Initialization Failed: {e}")

    def execute(self, sql: str, params: tuple = None, fetch: bool = False, commit: bool = True) -> Any:
        """
        Executes a SQL query securely using parameters.
        
        Args:
            sql: The SQL query string.
            params: Tuple of parameters for the SQL query.
            fetch: Whether to fetch all rows (for SELECT).
            commit: Whether to commit the transaction (for INSERT/UPDATE/DELETE).
            
        Returns:
            Fetched rows if fetch=True, otherwise the rowcount.
        """
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
            conn.close()
