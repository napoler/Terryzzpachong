import libtorrent as lt

class Crawler:
    def __init__(self, conn, bootstrap_nodes):
        self.conn = conn
        nodes_str = ",".join(bootstrap_nodes)
        self.session = lt.session({'dht_bootstrap_nodes': nodes_str})
        for node in bootstrap_nodes:
            host, port = node.split(':')
            self.session.add_dht_router(host, int(port))
        self.session.listen_on(6881, 6891)
        self.metadata_session = lt.session()
        self.metadata_session.listen_on(6892, 6902)

    def stop(self):
        self.session.pause()
        self.metadata_session.pause()
