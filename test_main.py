import unittest
import os
import sqlite3
from db.database import create_database, insert_seed, search_seeds

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_file = 'test.db'
        self.conn = sqlite3.connect(self.db_file)
        create_database(self.db_file)

    def tearDown(self):
        self.conn.close()
        os.remove(self.db_file)

    def test_insert_and_search(self):
        insert_seed(self.conn, 'test_hash', 'test_hash', 0, 0)
        results = search_seeds(self.conn, 'test')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], 'test_hash')

if __name__ == '__main__':
    unittest.main()
