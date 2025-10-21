import libtorrent as lt
from urllib.parse import urlparse
from logger import log

class Crawler:
    def __init__(self, conn, config):
        self.conn = conn
        settings = {
            'dht_bootstrap_nodes': ",".join(config['bootstrap_nodes']),
            'listen_interfaces': '0.0.0.0:6881',
            'enable_pex': True
        }

        proxy = config.get('proxy')
        if proxy and proxy.get('hostname') and proxy.get('port'):
            log.info(f"Using proxy: {proxy['hostname']}:{proxy['port']}")
            proxy_settings = {
                'proxy_hostname': proxy['hostname'],
                'proxy_port': int(proxy['port']),
                'proxy_type': 1 if proxy.get('type') == 'http' else 2 # 1=http, 2=socks5
            }
            if proxy.get('username'):
                proxy_settings['proxy_username'] = proxy['username']
            if proxy.get('password'):
                proxy_settings['proxy_password'] = proxy['password']
            settings.update(proxy_settings)

        self.session = lt.session(settings)

        for tracker_url in config['trackers']:
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

        for info_hash in config['startup_torrents']:
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
