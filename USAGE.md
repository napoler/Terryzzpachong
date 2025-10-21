# Usage

## Running the Application

To run the application, execute the following command from the project's root directory:

```bash
python app.py
```

This will start the web server. You can then access the web interface by opening a web browser and navigating to `http://127.0.0.1:5000`.

## How it Works

By default, the application automatically starts a DHT crawler upon launch. This crawler listens to the BitTorrent DHT network and discovers new torrents in real-time. As new torrents are discovered, their metadata (name, size, file count, and info-hash) is saved to a local SQLite database (`seeds.db`) and displayed in the web interface.

## Settings Page

The settings page allows you to configure the application. You can access it by clicking the "Settings" link on the main page.

### Crawler Control

On the settings page, you can see the current status of the crawler and start or stop it using the provided buttons.

### Custom Bootstrap Nodes

You can also specify a custom list of initial DHT bootstrap nodes. Enter one node per line in the format `hostname:port`.

## Finding Related Seeds

To find seeds related to a torrent in the list, click the "Find Related" button. This will perform a new search using the name of the selected torrent as the query and display the results in the torrent table.

## Public API

The application provides a JSON API for programmatic access to the torrent data.

### Get Torrent by Info Hash

*   **URL:** `/api/torrent/<info_hash>`
*   **Method:** `GET`
*   **Description:** Retrieves the details of a single torrent.
*   **Example:** `curl http://127.0.0.1:5000/api/torrent/YOUR_INFO_HASH`

### Search Torrents

*   **URL:** `/api/search/<query>`
*   **Method:** `GET`
*   **Description:** Searches for torrents matching the query.
*   **Example:** `curl http://127.0.0.1:5000/api/search/ubuntu`

### Get Latest Torrents

*   **URL:** `/api/latest`
*   **Method:** `GET`
*   **Description:** Retrieves a list of the 50 most recently discovered torrents.
*   **Example:** `curl http://127.0.0.1:5000/api/latest`
