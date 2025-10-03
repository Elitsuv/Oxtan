import mysql.connector
import getpass

class OxtanDB:
    def __init__(self, host=None, user=None, password=None, database=None):
        self.host = host or self._require_input("Enter MySQL host (default: localhost): ", default="localhost")
        self.user = user or self._require_input("Enter MySQL username (default: root): ", default="root")
        self.password = password or self._require_input("Enter MySQL password: ", is_password=True)
        self.database = database or self._require_input("Enter database name: ")
        self.conn = None
        self.cursor = None
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
            self.conn, self.cursor = None, None
    
    def _require_input(self, prompt, default=None, attempts=3, is_password=False):
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
    
    def run(self, query, values=None, fetch="all"):
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
            self.conn.rollback()
            return f"❌ Error executing '{qtype}': {e}"
    
    def close(self):
        if self.cursor: self.cursor.close()
        if self.conn: self.conn.close()
        print("✅ Connection closed.")
    
    def __enter__(self): 
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb): 
        self.close()