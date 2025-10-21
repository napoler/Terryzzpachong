# Usage

## Running the Application

To run the application, execute the following command from the project's root directory:

```bash
python app.py
```

This will start the web server. You can then access the web interface by opening a web browser and navigating to `http://127.0.0.1:5000`.

## How it Works

The application automatically starts a DHT crawler five seconds after it launches. This crawler listens to the BitTorrent DHT network and discovers new torrents in real-time. As new torrents are discovered, their metadata (name, size, file count, and info-hash) is saved to a local SQLite database (`seeds.db`) and displayed in the web interface.

## Finding Related Seeds

To find seeds related to a torrent in the list, click the "Find Related" button. This will perform a new search using the name of the selected torrent as the query and display the results in the torrent table.
