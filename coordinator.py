import trio
import logging
import json
import time
import os
from typing import Optional
import httpx # Using httpx for async HTTP requests
import bencode

from database import DatabaseManager, Comment
from p2p import P2PNode

# --- Constants ---
COMMENT_TOPIC = "/btseedaggregator/comments/1.0"
CRAWLER_TOPIC = "/btseedaggregator/crawler/1.0" # A topic to announce new hashes

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataCoordinator:
    def __init__(self, p2p_node: P2PNode, db_manager: DatabaseManager, nursery):
        self.p2p = p2p_node
        self.db = db_manager
        self.nursery = nursery
        self.http_client = httpx.AsyncClient(timeout=15.0)

    async def start_services(self):
        """Starts all background services."""
        logger.info("Starting background services: Crawler and Metadata Fetcher.")
        self.nursery.start_soon(self._dht_crawler_task, 60)
        self.nursery.start_soon(self._metadata_fetcher_task, 120)

    async def _dht_crawler_task(self, interval: int):
        """Periodically queries the DHT for random info_hashes."""
        await trio.sleep(10) # Initial delay
        while True:
            try:
                random_hash = os.urandom(20) # 20 bytes for a SHA-1 info_hash
                logger.info(f"Crawler: Searching for providers of random hash {random_hash.hex()}")

                providers = await self.p2p.dht.get_providers(random_hash)

                if providers:
                    logger.info(f"Crawler: Found {len(providers)} providers for {random_hash.hex()}")
                    # Announce our successful find to the network
                    await self.p2p.broadcast(CRAWLER_TOPIC, {"info_hash": random_hash.hex()})
                    self.db.set_data(random_hash.hex(), b'', source='dht_crawler')
                else:
                    logger.info(f"Crawler: No providers found for {random_hash.hex()}")

            except Exception as e:
                logger.error(f"Error in DHT crawler task: {e}", exc_info=True)

            await trio.sleep(interval)

    def handle_crawler_message(self, msg):
        """Handles new info_hashes discovered by other peers."""
        try:
            data = json.loads(msg.data.decode('utf-8'))
            info_hash = data.get("info_hash")
            if info_hash:
                logger.info(f"Discovered new info_hash via PubSub: {info_hash}")
                # Store it, the value can be empty for now
                self.db.set_data(info_hash, b'', source='pubsub_crawler')
        except Exception as e:
            logger.error(f"Error handling crawler message: {e}")

    async def _metadata_fetcher_task(self, interval: int):
        """Periodically fetches metadata for info_hashes that are missing it."""
        await trio.sleep(20) # Initial delay
        while True:
            try:
                # This is a placeholder for a method to get hashes without metadata
                # I will implement it in database.py next.
                hashes_to_fetch = self.db.get_hashes_without_metadata(limit=10)

                for info_hash in hashes_to_fetch:
                    logger.info(f"Metadata Fetcher: Attempting to fetch metadata for {info_hash}")
                    try:
                        # Fetch .torrent file from a public service
                        url = f"https://itorrents.org/torrent/{info_hash}.torrent"
                        response = await self.http_client.get(url)
                        response.raise_for_status()

                        torrent_data = response.content
                        metadata = bencode.decode(torrent_data)

                        # Extract relevant info
                        info = metadata.get(b'info', {})
                        name = info.get(b'name', b'unknown').decode('utf-8', 'ignore')

                        files = []
                        if b'files' in info:
                            for f in info[b'files']:
                                path = [p.decode('utf-8', 'ignore') for p in f[b'path']]
                                files.append({"path": "/".join(path), "length": f[b'length']})
                        else:
                            files.append({"path": name, "length": info.get(b'length', 0)})

                        # Store it
                        metadata_json = json.dumps({"name": name, "files": files})
                        self.db.set_data(info_hash, metadata_json.encode('utf-8'), source='itorrents.org')
                        logger.info(f"Metadata Fetcher: Successfully stored metadata for '{name}'")
                        await trio.sleep(1) # Be nice to the public service

                    except httpx.HTTPStatusError as e:
                        logger.warning(f"Metadata Fetcher: HTTP error fetching {info_hash}: {e}")
                    except Exception as e:
                        logger.error(f"Metadata Fetcher: Failed to process {info_hash}: {e}")

            except Exception as e:
                logger.error(f"Error in metadata fetcher task: {e}", exc_info=True)

            await trio.sleep(interval)

    def post_comment(self, info_hash: str, text: str):
        """Creates, signs, and broadcasts a new comment. This is a sync method."""
        logger.info(f"[COORDINATOR] Starting post_comment for {info_hash}")
        timestamp = time.time()

        message_to_sign = f"{info_hash}:{text}:{timestamp}".encode('utf-8')
        logger.info("[COORDINATOR] Signing comment...")
        # .sign() is a synchronous method
        signature = self.p2p.host.get_private_key().sign(message_to_sign)
        logger.info("[COORDINATOR] Comment signed.")

        comment = Comment(
            info_hash=info_hash,
            text=text,
            author_id=self.p2p.host.get_id().to_string(),
            timestamp=timestamp,
            signature=signature.hex()
        )

        logger.info(f"[COORDINATOR] Attempting to add comment to DB for {info_hash}")
        if self.db.add_comment(comment):
            logger.info(f"[COORDINATOR] DB add successful. Broadcasting for {info_hash}")
            self.nursery.start_soon(self.p2p.broadcast, COMMENT_TOPIC, comment._asdict())
        else:
            logger.warning(f"[COORDINATOR] DB add failed for {info_hash} (likely a duplicate).")

    def handle_comment_message(self, msg):
        """Handles an incoming comment, scheduling its verification and storage."""
        try:
            data = json.loads(msg.data.decode('utf-8'))
            logger.info(f"[COORDINATOR] Received PubSub message: {data}")
            self.nursery.start_soon(self._verify_and_store_comment, data)
        except Exception as e:
            logger.error(f"[COORDINATOR] Error handling PubSub message: {e}", exc_info=True)

    async def _verify_and_store_comment(self, comment_data: dict):
        try:
            comment = Comment(**comment_data)
            message_to_sign = f"{comment.info_hash}:{comment.text}:{comment.timestamp}".encode('utf-8')
            author_peer_id = self.p2p.host.get_id().from_string(comment.author_id)

            public_key = await self.p2p.host.get_peerstore().public_key(author_peer_id)
            if not public_key:
                logger.info(f"Public key for {author_peer_id} not in peerstore. Searching DHT...")
                try:
                    peer_info = await self.p2p.dht.find_peer(author_peer_id)
                    public_key = peer_info.public_key
                except Exception as e:
                    logger.warning(f"Could not find peer {author_peer_id} in DHT: {e}")
                    return

            signature_bytes = bytes.fromhex(comment.signature)
            if public_key.verify(message_to_sign, signature_bytes):
                logger.info(f"Signature verified for comment from {comment.author_id}")
                if self.db.add_comment(comment):
                    logger.info(f"Stored new comment for {comment.info_hash} from the network.")
            else:
                logger.warning(f"Invalid signature for comment from {comment.author_id}. Discarding.")
        except Exception as e:
            logger.error(f"Error during comment verification: {e}", exc_info=True)

    async def get_data(self, key: str) -> Optional[bytes]:
        return self.db.get_data(key)
