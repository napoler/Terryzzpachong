import unittest
import os
from db.database import create_database, insert_seed, search_seeds

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_file = 'test.db'
        create_database(self.db_file)

    def tearDown(self):
        os.remove(self.db_file)

    def test_insert_and_search(self):
        insert_seed('test_hash', 'test_name', 12345, 1, db_file=self.db_file)
        results = search_seeds('test', db_file=self.db_file)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][2], 'test_name')

if __name__ == '__main__':
    unittest.main()
