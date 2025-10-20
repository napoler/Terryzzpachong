# BTSeedAggregator

BTSeedAggregator is a Python application for discovering and aggregating BT seeds from the BitTorrent DHT network. It is designed to be a lightweight, ad-free, and user-friendly alternative to other torrent clients.

## Features

### Implemented

*   **DHT Crawler:** A lightweight crawler that connects to the BitTorrent DHT network to discover new torrents.
*   **SQLite Database:** A local SQLite database to store and manage discovered torrents.
*   **Graphical User Interface:** A user-friendly GUI to interact with the application, inspired by qBittorrent.
*   **Related Seed Discovery:** A feature to find seeds related to a selected torrent.
*   **DPI Scaling:** The application is DPI-aware to ensure it looks good on high-resolution displays.
*   **Delayed Crawler Start:** The crawler starts automatically 5 seconds after the application starts.
*   **Main Menu Bar:** A main menu bar with `File`, `Tools`, and `Help` menus.
*   **Settings Page:** A placeholder settings page, accessible from the "Tools" menu.

### Planned

*   **Tracker and PEX Crawling:** Add support for tracker and PEX crawling to discover more seeds.
*   **Advanced Filtering:** Add a sidebar for filtering results by category, size, etc.
*   **Detailed Torrent Information:** Add a bottom panel to show detailed information about the selected torrent.
*   **More Comprehensive Tests:** Add more comprehensive tests to ensure the application is stable and correct.

## Development Status

This project is currently under development. The core components are in place, but the DHT crawler is not yet fully functional.
