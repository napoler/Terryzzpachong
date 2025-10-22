import libtorrent as lt
from urllib.parse import urlparse
from logger import log

class Crawler:
    def __init__(self, conn, config):
        self.conn = conn

        performance_profile = config.get('performance_profile', 'balanced')
        if performance_profile == 'low_power':
            settings_pack = lt.settings_pack()
            settings_pack.set_int(lt.settings_pack.active_dht_limit, 200)
            settings_pack.set_int(lt.settings_pack.dht_upload_rate_limit, 5000)
            settings_pack.set_int(lt.settings_pack.cache_size, 256) # 256 * 16KB blocks = 4MB
        elif performance_profile == 'high_performance':
            settings_pack = lt.settings_pack()
            settings_pack.set_int(lt.settings_pack.active_dht_limit, 800)
            settings_pack.set_int(lt.settings_pack.dht_upload_rate_limit, 50000)
            settings_pack.set_int(lt.settings_pack.cache_size, 2048) # 2048 * 16KB blocks = 32MB
        else: # balanced
            settings_pack = lt.settings_pack()
            settings_pack.set_int(lt.settings_pack.active_dht_limit, 400)
            settings_pack.set_int(lt.settings_pack.dht_upload_rate_limit, 15000)
            settings_pack.set_int(lt.settings_pack.cache_size, 1024) # 1024 * 16KB blocks = 16MB

        settings_pack.set_str(lt.settings_pack.dht_bootstrap_nodes, ",".join(config['bootstrap_nodes']))
        settings_pack.set_str(lt.settings_pack.listen_interfaces, '0.0.0.0:6881')
        settings_pack.set_bool(lt.settings_pack.enable_pex, True)

        proxy = config.get('proxy')
        if proxy and proxy.get('hostname') and proxy.get('port'):
            log.info(f"Using proxy: {proxy['hostname']}:{proxy['port']}")
            settings_pack.set_str(lt.settings_pack.proxy_hostname, proxy['hostname'])
            settings_pack.set_int(lt.settings_pack.proxy_port, int(proxy['port']))
            settings_pack.set_int(lt.settings_pack.proxy_type, 1 if proxy.get('type') == 'http' else 2) # 1=http, 2=socks5
            if proxy.get('username'):
                settings_pack.set_str(lt.settings_pack.proxy_username, proxy['username'])
            if proxy.get('password'):
                settings_pack.set_str(lt.settings_pack.proxy_password, proxy['password'])

        self.session = lt.session(settings_pack)

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
