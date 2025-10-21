# Usage

## Running the Application

To run the application, execute the following command from the project's root directory:

```bash
python app.py
```

This will start the web server. You can then access the web interface by opening a web browser and navigating to `http://127.0.0.1:5000`.

## How it Works

By default, the application automatically starts a DHT crawler upon launch. This crawler listens to the BitTorrent DHT network and discovers new torrents in real-time. As new torrents are discovered, their metadata (name, size, file count, and info-hash) is saved to a local SQLite database (`seeds.db`) and displayed in the web interface.

## Main Page

### Searching and Filtering

The main page provides several controls for searching and filtering the discovered torrents:

*   **Search:** Enter a query in the search box to find torrents by name.
*   **Size Filtering:** Specify a minimum and/or maximum size in bytes to filter the results.
*   **Sorting:** Sort the results by name, size, or file count, in either ascending or descending order.
*   **Find Related:** Click the "Find Related" button on any torrent to perform a new search using that torrent's name.

## Settings Page

The settings page allows you to configure the application. You can access it by clicking the "Settings" link on the main page.

### Crawler Control

On the settings page, you can see the current status of the crawler and start or stop it using the provided buttons.

### Database Control

You can also clear all torrents from the database by clicking the "Clear Database" button.

### Custom Bootstrap Nodes

You can also specify a custom list of initial DHT bootstrap nodes. Enter one node per line in the format `hostname:port`.

### Custom Trackers

To help the crawler discover peers more quickly, you can provide a list of public tracker URLs. Enter one URL per line in the format `hostname:port`.

### Startup Torrents

You can also provide a list of info-hashes for popular torrents. The crawler will use these to immediately start finding peers, which will rapidly populate the DHT. Enter one info-hash per line.

## Public API

The application provides a JSON API for programmatic access to the torrent data. Click the "API Help" link on the main page for more information.
