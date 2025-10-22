# BTSeedAggregator

BTSeedAggregator is a Python application for discovering and aggregating BT seeds from the BitTorrent DHT network. It is designed to be a lightweight, ad-free, and user-friendly alternative to other torrent clients.

## Technology Stack

*   **Web Framework:** Flask
*   **Real-time Communication:** Flask-SocketIO
*   **DHT Crawler:** `libtorrent`, a powerful and efficient C++ library with Python bindings.
*   **Database:** SQLite for local storage of torrent metadata.
*   **Logging:** Python's built-in `logging` module.

## Features

### Implemented

*   **DHT Crawler:** A lightweight crawler that connects to the BitTorrent DHT network to discover new torrents.
*   **SQLite Database:** A local SQLite database to store and manage discovered torrents.
*   **Web User Interface:** A user-friendly web UI to interact with the application.
*   **Search Result Filtering:** Filter and sort search results by name, size, and file count.
*   **Real-time Updates:** The web UI is updated in real-time with new torrents and log messages.
*   **Crawler Control:** Start and stop the crawler from the settings page.
*   **Configurable Bootstrap Nodes:** Set your own initial DHT bootstrap nodes.
*   **Configurable Trackers:** Provide a list of public trackers to aid in peer discovery.
*   **Startup Torrents:** Provide a list of info-hashes to kickstart the crawling process.
*   **Peer Exchange (PEX):** Enabled for more efficient peer discovery.
*   **Proxy Support:** Configure a proxy for the crawler.
*   **Performance Profiles:** Choose between Low Power, Balanced, and High Performance profiles.
*   **Clear Database:** A feature to clear all torrents from the database.
*   **Public API:** A JSON API for accessing torrent data programmatically, with a dedicated help page.
*   **Enhanced Logging:** Structured, real-time logging to both the console and a file (`app.log`).

### Planned

*   **Advanced Filtering:** Add a sidebar for filtering results by category, size, etc.
*   **Detailed Torrent Information:** Add a bottom panel to show detailed information about the selected torrent.
*   **More Comprehensive Tests:** Add more comprehensive tests to ensure the application is stable and correct.

## Development Status

This project is under active development. The core features, including DHT crawling, database storage, and the web UI, are implemented and functional. The application is now in a usable state for discovering and viewing torrents. Future work will focus on adding more advanced features and improving stability.
