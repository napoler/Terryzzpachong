import libtorrent as lt
from urllib.parse import urlparse
from logger import log
import os

class Crawler:
    def __init__(self, conn, config):
        self.conn = conn
        self.dht_state_file = 'dht_state'

        settings = {}
        performance_profile = config.get('performance_profile', 'balanced')
        if performance_profile == 'low_power':
            settings['active_dht_limit'] = 200
            settings['dht_upload_rate_limit'] = 5000
            settings['cache_size'] = 256 # 256 * 16KB blocks = 4MB
        elif performance_profile == 'high_performance':
            settings['active_dht_limit'] = 800
            settings['dht_upload_rate_limit'] = 50000
            settings['cache_size'] = 2048 # 2048 * 16KB blocks = 32MB
        else: # balanced
            settings['active_dht_limit'] = 400
            settings['dht_upload_rate_limit'] = 15000
            settings['cache_size'] = 1024 # 1024 * 16KB blocks = 16MB

        settings['dht_bootstrap_nodes'] = ",".join(config['bootstrap_nodes'])
        settings['listen_interfaces'] = '0.0.0.0:6881'
        settings['enable_pex'] = True

        proxy = config.get('proxy')
        if proxy and proxy.get('hostname') and proxy.get('port'):
            log.info(f"Using proxy: {proxy['hostname']}:{proxy['port']}")
            settings['proxy_hostname'] = proxy['hostname']
            settings['proxy_port'] = int(proxy['port'])
            settings['proxy_type'] = 1 if proxy.get('type') == 'http' else 2 # 1=http, 2=socks5
            if proxy.get('username'):
                settings['proxy_username'] = proxy['username']
            if proxy.get('password'):
                settings['proxy_password'] = proxy['password']

        # Load DHT state if it exists
        if os.path.exists(self.dht_state_file):
            log.info("Loading DHT state from file.")
            with open(self.dht_state_file, 'rb') as f:
                dht_state = f.read()
            self.session = lt.session({'dht_state': dht_state, **settings})
        else:
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
        self.save_dht_state()
        self.session.pause()
        self.metadata_session.pause()

    def save_dht_state(self):
        log.info("Saving DHT state to file.")
        dht_state = self.session.save_dht_state()
        with open(self.dht_state_file, 'wb') as f:
            f.write(dht_state)
