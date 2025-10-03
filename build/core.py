import mysql.connector
import getpass
from typing import Optional, Any, Tuple, List, Union

class OxtanDB:
    """
    Handles MySQL database connection and queries for Oxtan.
    """

    def __init__(self, host: Optional[str]=None, user: Optional[str]=None, password: Optional[str]=None, database: Optional[str]=None):
        self.host = host or self._require_input("Enter MySQL host (default: localhost): ", default="localhost")
        self.user = user or self._require_input("Enter MySQL username (default: root): ", default="root")
        self.password = password or self._require_input("Enter MySQL password: ", is_password=True)
        self.database = database or self._require_input("Enter database name: ")
        self.conn: Optional[mysql.connector.connection.MySQLConnection] = None
        self.cursor: Optional[mysql.connector.cursor.MySQLCursor] = None
        self._connect()

    def _connect(self) -> None:
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            self.cursor = self.conn.cursor()
            print(f"✅ Connected to database '{self.database}' as {self.user}@{self.host}")
        except mysql.connector.Error as e:
            print(f"❌ Connection failed: {e}")
            self.conn = None
            self.cursor = None

    def _require_input(self, prompt: str, default: Optional[str]=None, attempts: int=3, is_password: bool=False) -> str:
        for attempt in range(1, attempts + 1):
            try:
                if is_password:
                    value = getpass.getpass(prompt)
                else:
                    value = input(prompt) if default is None else input(f"{prompt} (or press Enter for '{default}'): ")
            except Exception:
                value = input(prompt)
            value = (value or "").strip()
            if value or default is not None:
                return value or default
            remaining = attempts - attempt
            if remaining:
                print(f"Input required. {remaining} attempt(s) left.")
        raise ValueError("Required input not provided after max attempts.")

    def run(self, query: str, values: Optional[Union[Tuple[Any, ...], List[Any]]]=None, fetch: str="all") -> Any:
        if not self.cursor:
            return "❌ No active DB connection."
        try:
            params = values or ()
            if not isinstance(params, (list, tuple)):
                params = (params,)
            self.cursor.execute(query, params)
            qtype = query.strip().split()[0].upper()
            if qtype == "SELECT":
                if fetch == "one": return self.cursor.fetchone()
                if fetch == "many": return self.cursor.fetchmany()
                return self.cursor.fetchall()
            else:
                self.conn.commit()
                return f"✅ {qtype} executed."
        except mysql.connector.Error as e:
            if self.conn: self.conn.rollback()
            return f"❌ Error executing '{query}': {e}"

    def close(self) -> None:
        if self.cursor: self.cursor.close()
        if self.conn: self.conn.close()
        print("✅ Connection closed.")

    def __enter__(self): 
        return self

    def __exit__(self, exc_type, exc_val, exc_tb): 
        self.close()