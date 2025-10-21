# BTSeedAggregator

BTSeedAggregator is a Python application for discovering and aggregating BT seeds from the BitTorrent DHT network. It is designed to be a lightweight, ad-free, and user-friendly alternative to other torrent clients.

## Technology Stack

*   **Web Framework:** Flask
*   **Real-time Communication:** Flask-SocketIO
*   **DHT Crawler:** `libtorrent`, a powerful and efficient C++ library with Python bindings.
*   **Database:** SQLite for local storage of torrent metadata.

## Features

### Implemented

*   **DHT Crawler:** A lightweight crawler that connects to the BitTorrent DHT network to discover new torrents.
*   **SQLite Database:** A local SQLite database to store and manage discovered torrents.
*   **Web User Interface:** A user-friendly web UI to interact with the application.
*   **Related Seed Discovery:** A feature to find seeds related to a selected torrent.
*   **Delayed Crawler Start:** The crawler starts automatically 5 seconds after the application starts.
*   **Real-time Updates:** The web UI is updated in real-time with new torrents and log messages.

### Planned

*   **Tracker and PEX Crawling:** Add support for tracker and PEX crawling to discover more seeds.
*   **Advanced Filtering:** Add a sidebar for filtering results by category, size, etc.
*   **Detailed Torrent Information:** Add a bottom panel to show detailed information about the selected torrent.
*   **More Comprehensive Tests:** Add more comprehensive tests to ensure the application is stable and correct.

## Development Status

This project is under active development. The core features, including DHT crawling, database storage, and the web UI, are implemented and functional. The application is now in a usable state for discovering and viewing torrents. Future work will focus on adding more advanced features and improving stability.
