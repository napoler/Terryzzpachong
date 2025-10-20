import libtorrent as lt
from db.database import insert_seed

class Crawler:
    def __init__(self, conn):
        self.conn = conn
        self.session = lt.session({'dht_bootstrap_nodes': 'router.bittorrent.com:6881,dht.transmissionbt.com:6881,router.utorrent.com:6881'})
        self.session.add_dht_router("router.bittorrent.com", 6881)
        self.session.add_dht_router("dht.transmissionbt.com", 6881)
        self.session.add_dht_router("router.utorrent.com", 6881)
        self.session.listen_on(6881, 6891)
        self.metadata_session = lt.session()
        self.metadata_session.listen_on(6892, 6902)

    def insert_seed(self, name, size, files, info_hash):
        insert_seed(self.conn, info_hash, name, size, files)
