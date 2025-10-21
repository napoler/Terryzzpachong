import libtorrent as lt

class Crawler:
    def __init__(self, conn, bootstrap_nodes, trackers, startup_torrents):
        self.conn = conn
        settings = {
            'dht_bootstrap_nodes': ",".join(bootstrap_nodes),
            'listen_interfaces': '0.0.0.0:6881',
        }
        self.session = lt.session(settings)

        for tracker in trackers:
            self.session.add_dht_router(tracker.split(':')[0], int(tracker.split(':')[1]))

        for info_hash in startup_torrents:
            params = {
                'save_path': '.',
                'storage_mode': lt.storage_mode_t(2),
                'paused': False,
                'auto_managed': True,
                'duplicate_is_error': True,
                'info_hash': info_hash
            }
            self.session.add_torrent(params)

        self.metadata_session = lt.session()
        self.metadata_session.listen_on(6892, 6902)

    def stop(self):
        self.session.pause()
        self.metadata_session.pause()
