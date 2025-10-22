# BTSeedAggregator

BTSeedAggregator is a Python application for discovering and aggregating BT seeds from the BitTorrent DHT network. It is designed to be a lightweight, ad-free, and user-friendly tool for finding torrents.

## Getting Started

### Prerequisites

*   Python 3.7+
*   `libtorrent` library installed. The specific version depends on your OS.
    *   **Ubuntu/Debian:** `sudo apt-get install python3-libtorrent`
    *   **macOS:** `brew install libtorrent-rasterbar`
    *   **Windows:** Download a compatible wheel from a third-party source or build from source.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/BTSeedAggregator.git
    cd BTSeedAggregator
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

1.  **Start the Flask server:**
    ```bash
    python app.py
    ```

2.  **Open your web browser** and navigate to `http://127.0.0.1:5000`.

## Technology Stack

*   **Web Framework:** Flask
*   **Real-time Communication:** Flask-SocketIO
*   **DHT Crawler:** `libtorrent`, a powerful and efficient C++ library with Python bindings.
*   **Database:** SQLite for local storage of torrent metadata.
*   **Frontend:** Bootstrap, jQuery, Socket.IO

## Web Interface

The application is organized into several pages:

*   **Search:** The main page for searching discovered torrents. You can filter by name, size, and sort the results.
*   **Latest:** Displays a real-time list of the most recently discovered torrents.
*   **Logs:** A live stream of the application's log messages, providing insight into the crawler's status and activities.
*   **Settings:** A comprehensive page to configure the application, including starting/stopping the crawler, managing the database, setting performance profiles, and configuring a proxy.
*   **API:** A help page documenting the public JSON API for programmatic access to the data.

## Features

*   **DHT Crawler:** A lightweight crawler that connects to the BitTorrent DHT network to discover new torrents.
*   **Web User Interface:** A clean, user-friendly web UI to interact with the application.
*   **Advanced Search:** Filter and sort search results by name, size, and file count.
*   **Real-time Updates:** The web UI is updated in real-time with new torrents and log messages.
*   **Crawler Control:** Start and stop the crawler from the settings page.
*   **DHT State Persistence:** Automatically saves and loads the DHT state for faster startups.
*   **Configurable Discovery Aids:** Set custom bootstrap nodes, public trackers, and startup info-hashes to accelerate peer discovery.
*   **Proxy Support:** Configure an HTTP or SOCKS5 proxy for the crawler.
*   **Performance Profiles:** Choose between Low Power, Balanced, and High Performance profiles.
*   **Database Management:** A feature to clear all torrents from the database.
*   **Public API:** A JSON API for accessing torrent data programmatically.
*   **Enhanced Logging:** Structured, real-time logging to the web UI, console, and a file (`app.log`).
