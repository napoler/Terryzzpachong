import libtorrent as lt
import time
import sqlite3
from db.database import insert_seed

class Crawler:
    def __init__(self, db_file):
        self._running = False
        self.db_file = db_file
        self.session = lt.session({'dht_bootstrap_nodes': 'router.bittorrent.com:6881,dht.transmissionbt.com:6881,router.utorrent.com:6881'})
        self.session.add_dht_router("router.bittorrent.com", 6881)
        self.session.add_dht_router("dht.transmissionbt.com", 6881)
        self.session.add_dht_router("router.utorrent.com", 6881)
        self.session.listen_on(6881, 6891)
        self.metadata_session = lt.session()
        self.metadata_session.listen_on(6892, 6902)
        self.conn = sqlite3.connect(self.db_file)

    def run(self):
        self._running = True
        while self._running:
            alerts = self.session.pop_alerts()
            for alert in alerts:
                if isinstance(alert, lt.dht_announce_alert):
                    info_hash = alert.info_hash
                    params = {
                        'save_path': '.',
                        'storage_mode': lt.storage_mode_t(2),
                        'paused': False,
                        'auto_managed': True,
                        'duplicate_is_error': True,
                        'info_hash': info_hash
                    }
                    h = self.metadata_session.add_torrent(params)

            metadata_alerts = self.metadata_session.pop_alerts()
            for alert in metadata_alerts:
                if isinstance(alert, lt.metadata_received_alert):
                    info = alert.get_torrent_info()
                    size = info.total_size()
                    files = info.num_files()
                    insert_seed(self.conn, str(info.info_hash()), info.name(), size, files)
            time.sleep(1)

    def stop(self):
        self._running = False
        self.conn.close()
