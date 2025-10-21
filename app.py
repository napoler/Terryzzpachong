import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import time
import libtorrent as lt
from crawler import Crawler
from db.database import create_connection, create_table, search_seeds, insert_seed

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')
db_file = "seeds.db"

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    """Sends existing torrents to a new client."""
    conn = create_connection(db_file)
    results = search_seeds(conn, '') # Get all seeds
    conn.close()
    for row in results:
        socketio.emit('new_torrent', {'name': row[2], 'size': row[3], 'files': row[4], 'info_hash': row[1]})


@socketio.on('find_related')
def handle_find_related(data):
    name = data['name']
    socketio.emit('clear_torrents')
    conn = create_connection(db_file)
    results = search_seeds(conn, name)
    conn.close()
    for row in results:
        socketio.emit('new_torrent', {'name': row[2], 'size': row[3], 'files': row[4], 'info_hash': row[1]})

def crawler_thread():
    conn = create_connection(db_file)
    create_table(conn)
    crawler = Crawler(conn)
    while True:
        try:
            alerts = crawler.session.pop_alerts()
            for alert in alerts:
                if isinstance(alert, lt.dht_announce_alert):
                    info_hash = alert.info_hash
                    params = {
                        'save_path': '.',
                        'storage_mode': lt.storage_mode_t(2),
                        'paused': False,
                        'auto_managed': True,
                        'duplicate_is_error': True,
                        'info_hash': info_hash
                    }
                    crawler.metadata_session.add_torrent(params)

            metadata_alerts = crawler.metadata_session.pop_alerts()
            for alert in metadata_alerts:
                if isinstance(alert, lt.metadata_received_alert):
                    info = alert.get_torrent_info()
                    size = info.total_size()
                    files = info.num_files()
                    name = info.name()
                    info_hash_str = str(info.info_hash())
                    insert_seed(conn, info_hash_str, name, size, files)
                    socketio.emit('new_torrent', {'name': name, 'size': size, 'files': files, 'info_hash': info_hash_str})
            socketio.sleep(1) # Use socketio.sleep for eventlet
        except Exception as e:
            socketio.emit('log_message', {'data': f"Crawler error: {e}"})

if __name__ == '__main__':
    threading.Timer(5.0, lambda: socketio.start_background_task(crawler_thread)).start()
    socketio.run(app, host='0.0.0.0', port=5000)
