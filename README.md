# BTSeedAggregator: A Local-First P2P Seed Discovery Engine

BTSeedAggregator is a decentralized, local-first application for discovering and sharing torrent info-hashes in real-time. It leverages the power of peer-to-peer networking through `py-libp2p` to create a resilient and censorship-resistant metadata aggregation system. Users can not only discover the latest torrents circulating in the DHT but also engage in discussions through a built-in, cryptographically-secure commenting system.

The project features a clean, responsive web interface built with Quart, allowing users to monitor network activity, browse hot torrents, and participate in discussions from any modern web browser.

## Key Features

- **Decentralized Discovery:** Utilizes a Kademlia DHT to crawl for new info-hashes, ensuring no central point of failure.
- **Real-time Sharing:** Employs a GossipSub (PubSub) topic to instantly share newly discovered hashes among all connected peers.
- **Automatic Metadata Fetching:** An asynchronous background task fetches torrent metadata (name, files, size) from public sources for discovered hashes.
- **Secure P2P Commenting:** Users can post comments on any info-hash. Each comment is cryptographically signed with the user's private peer ID and verified by other peers, preventing spoofing.
- **"Hot" Torrents:** A real-time updated page shows which torrents are generating the most discussion across the network.
- **Local-First Architecture:** All discovered metadata and comments are stored in a local SQLite database, making the application fast and available offline.
- **Modern Web UI:** A simple and intuitive web interface for interacting with the network, viewing stats, and reading/writing comments.
- **Network Transparency:** A dedicated stats page displays your node's Peer ID and the list of currently connected peers.

## Architecture Overview

The application is built on a "Local-First" philosophy, where your data is stored on your machine first and then shared with the network.

- **L1 - Persistence Layer (`database.py`):** An SQLite database that stores all torrent metadata, comments, and peer information.
- **L2 - P2P Network Layer (`p2p.py`):** Manages the `libp2p` host, including the Kademlia DHT for discovery and GossipSub for real-time messaging.
- **L3 - Data Orchestrator (`coordinator.py`):** The core logic that connects the P2P layer with the database. It handles incoming messages, verifies data, and runs background tasks like the DHT crawler and metadata fetcher.
- **L4 - Web Application Layer (`app.py`):** A Quart-based web server that provides a user interface and a JSON API for interacting with the system.

## Tech Stack

- **Backend:** Python 3, Quart, py-libp2p, Trio (for structured concurrency)
- **Database:** SQLite3
- **Frontend:** Vanilla HTML, CSS, and JavaScript

## Getting Started

### Prerequisites

- Python 3.8+
- A C++ compiler (required for some `py-libp2p` dependencies)

### Installation & Running

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd BTSeedAggregator
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `py-libp2p` has several dependencies. If you encounter compilation issues, you may need to install system-level development libraries.*

4.  **Run the application:**
    ```bash
    python app.py
    ```

5.  **Open your browser:**
    Navigate to `http://127.0.0.1:5000` to access the web interface.

## API Endpoints

The application exposes several API endpoints:

- `GET /api/hot-torrents`: Returns a JSON list of the most commented-on torrents.
- `GET /api/stats`: Returns a JSON object with the node's Peer ID and a list of connected peers.
- `GET /api/comments/<info_hash>`: Returns a JSON list of all comments for a given info-hash.
- `POST /api/comments/<info_hash>`: Submits a new comment for a given info-hash. Requires a JSON body with a `text` field: `{"text": "Your comment here"}`.
