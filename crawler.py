import libtorrent as lt
from urllib.parse import urlparse
from logger import log

class Crawler:
    def __init__(self, conn, bootstrap_nodes, trackers, startup_torrents):
        self.conn = conn
        settings = {
            'dht_bootstrap_nodes': ",".join(bootstrap_nodes),
            'listen_interfaces': '0.0.0.0:6881',
            'enable_pex': True
        }
        self.session = lt.session(settings)

        for tracker_url in trackers:
            try:
                parsed_url = urlparse(tracker_url)
                hostname = parsed_url.hostname
                port = parsed_url.port
                if hostname and port:
                    self.session.add_dht_router(hostname, port)
                else:
                    log.warning(f"Could not parse tracker URL: {tracker_url}")
            except Exception as e:
                log.error(f"Error parsing tracker URL {tracker_url}: {e}")

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
