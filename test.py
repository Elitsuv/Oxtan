import unittest
import os
from build.core import OxtanDB

class TestOxtanDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initialize connection using environment variables."""
        # We fetch from env; if missing, we use defaults that the dev should set up
        db_name = os.getenv("MYSQL_DATABASE", "exam")
        
        try:
            cls.db = OxtanDB(database=db_name)
            cls.table = "oxtan_unittest"
            
            # Clean setup
            cls.db.raw(f"DROP TABLE IF EXISTS {cls.table}")
            cls.db.raw(f"CREATE TABLE {cls.table} (id INT PRIMARY KEY, name VARCHAR(50))")
        except Exception as e:
            raise unittest.SkipTest(f"Skipping tests: Could not connect to MySQL. {e}")

    @classmethod
    def tearDownClass(cls):
        """Clean up the database after tests."""
        if hasattr(cls, 'db'):
            cls.db.raw(f"DROP TABLE IF EXISTS {cls.table}")

    def test_1_insert(self):
        result = self.db.insert(self.table, {"id": 1, "name": "Unit Tester"})
        self.assertEqual(result, 1)

    def test_2_select(self):
        rows = self.db.select(self.table, where={"id": 1})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['name'], "Unit Tester")

    def test_3_update(self):
        self.db.update(self.table, {"name": "Passed"}, {"id": 1})
        rows = self.db.select(self.table, where={"id": 1})
        self.assertEqual(rows[0]['name'], "Passed")

    def test_4_raw_query(self):
        res = self.db.raw(f"SELECT COUNT(*) as count FROM {self.table}")
        self.assertEqual(res[0]['count'], 1)

    def test_5_delete(self):
        self.db.delete(self.table, {"id": 1})
        rows = self.db.select(self.table)
        self.assertEqual(len(rows), 0)

if __name__ == "__main__":
    unittest.main()