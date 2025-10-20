import unittest
import os
import sqlite3
from db.database import create_connection, create_table, insert_seed, search_seeds

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_file = 'test.db'
        self.conn = create_connection(self.db_file)
        create_table(self.conn)

    def tearDown(self):
        self.conn.close()
        os.remove(self.db_file)

    def test_insert_and_search(self):
        insert_seed(self.conn, 'test_hash', 'test_torrent', 12345, 1)
        results = search_seeds(self.conn, 'test_torrent')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], 'test_hash')
        self.assertEqual(results[0][2], 'test_torrent')
        self.assertEqual(results[0][3], 12345)
        self.assertEqual(results[0][4], 1)

if __name__ == '__main__':
    unittest.main()
