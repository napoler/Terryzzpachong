import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO
import threading
import time
import libtorrent as lt
from crawler import Crawler
from db.database import create_connection, create_table, search_seeds, insert_seed, get_torrent_by_hash, get_latest_torrents, clear_database
from config import load_config, save_config
from logger import setup_logger

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')
log = setup_logger(socketio)
db_file = "seeds.db"
crawler_instance = None
crawler_running = False

@app.route('/')
def index():
    log.info("Serving index page.")
    return render_template('index.html')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    global crawler_running
    if request.method == 'POST':
        log.info("Saving new settings.")
        config = load_config()

        nodes_text = request.form.get('bootstrap_nodes')
        config['bootstrap_nodes'] = [node.strip() for node in nodes_text.splitlines() if node.strip()]

        trackers_text = request.form.get('trackers')
        config['trackers'] = [tracker.strip() for tracker in trackers_text.splitlines() if tracker.strip()]

        torrents_text = request.form.get('startup_torrents')
        config['startup_torrents'] = [torrent.strip() for torrent in torrents_text.splitlines() if torrent.strip()]

        config['proxy']['hostname'] = request.form.get('proxy_hostname')
        config['proxy']['port'] = request.form.get('proxy_port')
        config['proxy']['username'] = request.form.get('proxy_username')
        config['proxy']['password'] = request.form.get('proxy_password')
        config['proxy']['type'] = request.form.get('proxy_type')

        config['performance_profile'] = request.form.get('performance_profile')

        save_config(config)
        return redirect(url_for('settings'))

    log.info("Serving settings page.")
    config = load_config()
    nodes_text = "\n".join(config.get('bootstrap_nodes', []))
    trackers_text = "\n".join(config.get('trackers', []))
    torrents_text = "\n".join(config.get('startup_torrents', []))

    return render_template('settings.html',
                           bootstrap_nodes=nodes_text,
                           trackers=trackers_text,
                           startup_torrents=torrents_text,
                           proxy=config.get('proxy'),
                           performance_profile=config.get('performance_profile'),
                           crawler_status=crawler_running)

@app.route('/start_crawler')
def start_crawler_route():
    global crawler_running
    log.info("Attempting to start crawler.")
    if not crawler_running:
        crawler_running = True
        socketio.start_background_task(target=crawler_thread)
        log.info("Crawler started.")
    else:
        log.info("Crawler is already running.")
    return redirect(url_for('settings'))

@app.route('/stop_crawler')
def stop_crawler():
    global crawler_running, crawler_instance
    log.info("Attempting to stop crawler.")
    if crawler_running:
        crawler_running = False
        if crawler_instance:
            crawler_instance.stop()
        log.info("Crawler stopped.")
    else:
        log.info("Crawler is not running.")
    return redirect(url_for('settings'))

@app.route('/clear_database')
def clear_database_route():
    log.info("Clearing database.")
    conn = create_connection(db_file)
    clear_database(conn)
    conn.close()
    socketio.emit('clear_torrents')
    return redirect(url_for('settings'))

# API Endpoints
@app.route('/api/help')
def api_help():
    return render_template('api_help.html')

@app.route('/api/torrent/<info_hash>')
def api_get_torrent(info_hash):
    log.info(f"API request for torrent: {info_hash}")
    conn = create_connection(db_file)
    rows = get_torrent_by_hash(conn, info_hash)
    conn.close()
    if rows:
        row = rows[0]
        return jsonify({'id': row[0], 'info_hash': row[1], 'name': row[2], 'size': row[3], 'files': row[4]})
    log.warning(f"API request for non-existent torrent: {info_hash}")
    return jsonify({'error': 'Torrent not found'}), 404

@app.route('/api/search/<query>')
def api_search_torrents(query):
    log.info(f"API search request for: {query}")
    conn = create_connection(db_file)
    rows = search_seeds(conn, query)
    conn.close()
    results = [{'id': row[0], 'info_hash': row[1], 'name': row[2], 'size': row[3], 'files': row[4]} for row in rows]
    return jsonify(results)

@app.route('/api/latest')
def api_latest_torrents():
    log.info("API request for latest torrents.")
    conn = create_connection(db_file)
    rows = get_latest_torrents(conn)
    conn.close()
    results = [{'id': row[0], 'info_hash': row[1], 'name': row[2], 'size': row[3], 'files': row[4]} for row in rows]
    return jsonify(results)


@socketio.on('connect')
def handle_connect():
    """Sends existing torrents to a new client."""
    log.info("Client connected to WebSocket.")
    conn = create_connection(db_file)
    results = search_seeds(conn, '') # Get all seeds
    conn.close()
    for row in results:
        socketio.emit('new_torrent', {'name': row[2], 'size': row[3], 'files': row[4], 'info_hash': row[1]})


@socketio.on('search')
def handle_search(data):
    query = data.get('query', '')
    min_size = data.get('min_size')
    max_size = data.get('max_size')
    sort_by = data.get('sort_by', 'name')
    sort_order = data.get('sort_order', 'asc')

    log.info(f"Searching for: {query}, min_size: {min_size}, max_size: {max_size}, sort_by: {sort_by}, sort_order: {sort_order}")
    socketio.emit('clear_torrents')
    conn = create_connection(db_file)
    results = search_seeds(conn, query, min_size, max_size, sort_by, sort_order)
    conn.close()
    for row in results:
        socketio.emit('new_torrent', {'name': row[2], 'size': row[3], 'files': row[4], 'info_hash': row[1]})

def crawler_thread():
    global crawler_running, crawler_instance
    log.info("Crawler thread starting.")
    conn = create_connection(db_file)
    create_table(conn)
    config = load_config()
    crawler_instance = Crawler(conn, config)

    last_status_log_time = time.time()

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
                    log.info(f"Discovered new torrent: {name}")
                    insert_seed(conn, info_hash_str, name, size, files)
                    socketio.emit('new_torrent', {'name': name, 'size': size, 'files': files, 'info_hash': info_hash_str})

            # Log status every 10 seconds
            current_time = time.time()
            if current_time - last_status_log_time > 10:
                s = crawler_instance.session.status()
                log.info(f"DHT nodes: {s.dht_nodes} | Torrents: {s.num_torrents}")
                last_status_log_time = current_time

            socketio.sleep(1) # Use socketio.sleep for eventlet
        except Exception as e:
            log.error(f"Crawler error: {e}", exc_info=True)

def start_crawler_background():
    global crawler_running
    if not crawler_running:
        crawler_running = True
        socketio.start_background_task(target=crawler_thread)

if __name__ == '__main__':
    log.info("Starting application.")
    start_crawler_background() # Start crawler by default
    socketio.run(app, host='0.0.0.0', port=5000)
