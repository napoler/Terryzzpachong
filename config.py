import json

DEFAULT_CONFIG = {
    "bootstrap_nodes": [
        "router.bittorrent.com:6881",
        "dht.transmissionbt.com:6881",
        "router.utorrent.com:6881"
    ]
}

def load_config():
    """Loads the configuration from config.json."""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            if not config.get("bootstrap_nodes"):
                return DEFAULT_CONFIG
            return config
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_CONFIG

def save_config(config):
    """Saves the configuration to config.json."""
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
