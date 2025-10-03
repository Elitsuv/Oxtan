import unittest
from build.core import OxtanDB

class TestOxtanDB(unittest.TestCase):
    def setUp(self):
        self.test_config = {
            'host': '',
            'user': '',
            'password': '',
            'database': ''
        }

    def test_basic_connection(self):
        db = OxtanDB(**self.test_config)
        self.assertIsNotNone(db.conn)
        self.assertIsNotNone(db.cursor)
        db.close()

    def test_simple_query(self):
        """Test if basic SELECT query works"""
        with OxtanDB(**self.test_config) as db:
            result = db.run("SELECT 1")
            self.assertIsNotNone(result)

    def test_invalid_connection(self):
        """Test handling of invalid connection"""
        bad_config = self.test_config.copy()
        bad_config['password'] = 'wrong_password'
        
        db = OxtanDB(**bad_config)
        self.assertIsNone(db.conn)
        self.assertIsNone(db.cursor)

if __name__ == '__main__':
    unittest.main()