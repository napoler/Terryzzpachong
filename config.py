import json

DEFAULT_CONFIG = {
    "bootstrap_nodes": [
        "router.bittorrent.com:6881",
        "dht.transmissionbt.com:6881",
        "router.utorrent.com:6881"
    ],
    "trackers": [],
    "startup_torrents": []
}

def load_config():
    """Loads the configuration from config.json, ensuring all default keys are present."""
    try:
        with open('config.json', 'r') as f:
            user_config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        user_config = {}

    # Ensure all default keys are present
    config = DEFAULT_CONFIG.copy()
    config.update(user_config)
    return config

def save_config(config):
    """Saves the configuration to config.json."""
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
