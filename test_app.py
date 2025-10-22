import unittest
import os
import json
from app import app, db_file
from db.database import create_connection, create_table, insert_seed

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.db_file = db_file
        self.conn = create_connection(self.db_file)
        create_table(self.conn)
        insert_seed(self.conn, 'test_hash_1', 'test_torrent_1', 12345, 1, '[]')
        insert_seed(self.conn, 'test_hash_2', 'test_torrent_2', 67890, 2, '[]')

    def tearDown(self):
        self.conn.close()
        os.remove(self.db_file)

    def test_get_torrent(self):
        response = self.app.get('/api/torrent/test_hash_1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['info_hash'], 'test_hash_1')

    def test_search_torrents(self):
        response = self.app.get('/api/search/test_torrent')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)

    def test_latest_torrents(self):
        response = self.app.get('/api/latest')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['info_hash'], 'test_hash_2')

if __name__ == '__main__':
    unittest.main()
