import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO
import threading
import time
import libtorrent as lt
from crawler import Crawler
from db.database import create_connection, create_table, search_seeds, insert_seed, get_torrent_by_hash, get_latest_torrents
from config import load_config, save_config

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')
db_file = "seeds.db"
crawler_instance = None
crawler_running = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    global crawler_running
    if request.method == 'POST':
        nodes_text = request.form.get('bootstrap_nodes')
        nodes_list = [node.strip() for node in nodes_text.splitlines() if node.strip()]
        config = load_config()
        config['bootstrap_nodes'] = nodes_list
        save_config(config)
        return redirect(url_for('settings'))

    config = load_config()
    nodes_text = "\n".join(config.get('bootstrap_nodes', []))
    return render_template('settings.html', bootstrap_nodes=nodes_text, crawler_status=crawler_running)

@app.route('/start_crawler')
def start_crawler():
    global crawler_running
    if not crawler_running:
        crawler_running = True
        socketio.start_background_task(target=crawler_thread)
    return redirect(url_for('settings'))

@app.route('/stop_crawler')
def stop_crawler():
    global crawler_running, crawler_instance
    if crawler_running:
        crawler_running = False
        if crawler_instance:
            crawler_instance.stop()
    return redirect(url_for('settings'))

# API Endpoints
@app.route('/api/torrent/<info_hash>')
def api_get_torrent(info_hash):
    conn = create_connection(db_file)
    rows = get_torrent_by_hash(conn, info_hash)
    conn.close()
    if rows:
        row = rows[0]
        return jsonify({'id': row[0], 'info_hash': row[1], 'name': row[2], 'size': row[3], 'files': row[4]})
    return jsonify({'error': 'Torrent not found'}), 404

@app.route('/api/search/<query>')
def api_search_torrents(query):
    conn = create_connection(db_file)
    rows = search_seeds(conn, query)
    conn.close()
    results = [{'id': row[0], 'info_hash': row[1], 'name': row[2], 'size': row[3], 'files': row[4]} for row in rows]
    return jsonify(results)

@app.route('/api/latest')
def api_latest_torrents():
    conn = create_connection(db_file)
    rows = get_latest_torrents(conn)
    conn.close()
    results = [{'id': row[0], 'info_hash': row[1], 'name': row[2], 'size': row[3], 'files': row[4]} for row in rows]
    return jsonify(results)


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
    global crawler_running, crawler_instance
    conn = create_connection(db_file)
    create_table(conn)
    config = load_config()
    crawler_instance = Crawler(conn, bootstrap_nodes=config['bootstrap_nodes'])
    while crawler_running:
        try:
            alerts = crawler_instance.session.pop_alerts()
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
                    crawler_instance.metadata_session.add_torrent(params)

            metadata_alerts = crawler_instance.metadata_session.pop_alerts()
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
    start_crawler() # Start crawler by default
    socketio.run(app, host='0.0.0.0', port=5000)
