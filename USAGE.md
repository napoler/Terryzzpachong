# Usage

## Running the Application

To run the application, execute the following command from the project's root directory:

```bash
python main.py
```

This will open the main window.

## How it Works

The application automatically starts a DHT crawler five seconds after it launches. This crawler listens to the BitTorrent DHT network and discovers new torrents in real-time. As new torrents are discovered, their metadata (name, size, file count, and info-hash) is saved to a local SQLite database (`seeds.db`) and displayed in the main window.

## Finding Related Seeds

To find seeds related to a torrent in the list, right-click on the torrent and select "Find Related Seeds". This will perform a new search using the name of the selected torrent as the query and display the results in the log panel for now.
