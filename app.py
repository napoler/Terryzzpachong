import trio
import logging
from threading import Thread
from quart import Quart, render_template, request, jsonify
from quart_cors import cors
import queue
import os
import uuid

from database import DatabaseManager
from p2p import P2PNode, KEY_FILE
from coordinator import DataCoordinator, COMMENT_TOPIC

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Global State ---
request_queue = queue.Queue()
response_queue = queue.Queue()

# --- Quart Web Application ---
app = Quart(__name__)
app = cors(app, allow_origin="*")

@app.route("/")
def index():
    return "Welcome! Go to /hot to see popular torrents or /stats for network info."

@app.route("/hot")
async def hot_torrents_page():
    return await render_template("hot.html")

@app.route("/stats")
async def stats_page():
    return await render_template("stats.html")

@app.route("/comments/<info_hash>")
async def comment_page(info_hash):
    return await render_template("comments.html", info_hash=info_hash)

@app.route("/api/stats")
async def stats_api():
    """API endpoint to get P2P network stats."""
    request_id = str(uuid.uuid4())
    request_queue.put({"type": "get_stats", "id": request_id})

    try:
        while True:
            response = response_queue.get(timeout=5)
            if response.get("request_id") == request_id:
                return jsonify(response.get("data"))
    except queue.Empty:
        return jsonify({"error": "Failed to get stats from P2P node."}), 504

@app.route("/api/hot-torrents")
async def hot_torrents_api():
    db_manager = app.config["db_manager"]
    hot_torrents = db_manager.get_hot_torrents()
    return jsonify(hot_torrents)

@app.route("/api/comments/<info_hash>", methods=["GET"])
async def get_comments_api(info_hash):
    db_manager = app.config["db_manager"]
    comments = db_manager.get_comments(info_hash)
    return jsonify([comment._asdict() for comment in comments])

@app.route("/api/comments/<info_hash>", methods=["POST"])
async def post_comment_api(info_hash):
    data = await request.get_json()
    comment_text = data.get("text")
    if not comment_text:
        return jsonify({"error": "Comment text cannot be empty."}), 400

    request_queue.put({
        "type": "post_comment",
        "info_hash": info_hash,
        "text": comment_text,
    })
    return jsonify({"status": "success", "message": "Comment received."})

# --- P2P and Coordinator Logic ---

async def p2p_worker(quart_app):
    db_manager = DatabaseManager()
    p2p_node = P2PNode()
    quart_app.config["db_manager"] = db_manager

    async with trio.open_nursery() as nursery:
        coordinator = DataCoordinator(p2p_node, db_manager, nursery)
        quart_app.config["coordinator"] = coordinator

        async def request_handler():
            while True:
                try:
                    req = await trio.to_thread.run_sync(request_queue.get)
                    if req["type"] == "post_comment":
                        coordinator.post_comment(req["info_hash"], req["text"])
                    elif req["type"] == "get_stats":
                        peers = p2p_node.host.get_network().get_peers()
                        stats = {
                            "peer_id": p2p_node.host.get_id().to_string(),
                            "connected_peers": len(peers),
                            "peer_list": [p.to_string() for p in peers],
                        }
                        response_queue.put({"request_id": req["id"], "data": stats})
                except trio.Cancelled:
                    break
                except Exception as e:
                    logger.error(f"[P2P WORKER] Error: {e}")

        nursery.start_soon(request_handler)
        await p2p_node.run(
            pubsub_topics=[COMMENT_TOPIC],
            handler_callback=coordinator.handle_comment_message
        )

def run_p2p_thread(quart_app):
    logger.info("Starting P2P background thread.")
    try:
        trio.run(p2p_worker, quart_app)
    except KeyboardInterrupt:
        pass
    logger.info("P2P background thread stopped.")

# --- Application Entry Point ---

if __name__ == "__main__":
    if os.path.exists(KEY_FILE):
        os.remove(KEY_FILE)

    p2p_thread = Thread(target=run_p2p_thread, args=(app,), daemon=True)
    p2p_thread.start()

    app.run(port=5003)
