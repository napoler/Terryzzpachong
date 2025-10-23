import trio
import logging
import json
import time
from typing import Optional

from database import DatabaseManager, Comment
from p2p import P2PNode

# --- Constants ---
COMMENT_TOPIC = "/btseedaggregator/comments/1.0"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataCoordinator:
    def __init__(self, p2p_node: P2PNode, db_manager: DatabaseManager, nursery):
        self.p2p = p2p_node
        self.db = db_manager
        self.nursery = nursery

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
