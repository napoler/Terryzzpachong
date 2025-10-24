import trio
import logging
import json
import os
from typing import Callable

from libp2p import new_host
from libp2p.crypto.secp256k1 import create_new_key_pair, Secp256k1PrivateKey
from libp2p.crypto.keys import KeyPair
from libp2p.host.basic_host import BasicHost
from libp2p.peer.peerinfo import info_from_p2p_addr
from libp2p.pubsub.gossipsub import GossipSub
from libp2p.pubsub.pubsub import Pubsub, ISubscriptionAPI
from libp2p.kad_dht.kad_dht import KadDHT, DHTMode
from libp2p.network.exceptions import SwarmException
from libp2p.tools.async_service import background_trio_service, Service
from libp2p.custom_types import TProtocol
from multiaddr import Multiaddr

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
BOOTSTRAP_NODES = [
    "/dnsaddr/bootstrap.libp2p.io/p2p/QmNnooDu7bfjPFoTZYxMNLWUQJyrVwtbZg5gBMjTezGAJN",
    "/dnsaddr/bootstrap.libp2p.io/p2p/QmQCU2EcMqAqQPR2i9bChDtGNJchTf6NA6w52sLoWnVvJo",
]
KEY_FILE = "p2p_key.pem"
GOSSIPSUB_PROTOCOL_ID = TProtocol("/meshsub/1.0.0")

class P2PNode:
    def __init__(self):
        self.host: BasicHost = None
        self.dht: KadDHT = None
        self.pubsub: Pubsub = None
        self.gossip: GossipSub = None

    async def run(self, listen_port: int = 0, pubsub_topics: list = None, handler_callback: Callable = None):
        key_pair = self._load_or_create_key()
        self.host = new_host(key_pair=key_pair)

        listen_addrs = [Multiaddr(f"/ip4/0.0.0.0/tcp/{listen_port}")]

        async with self.host.run(listen_addrs=listen_addrs), trio.open_nursery() as nursery:
            self._log_host_info()

            self.dht = KadDHT(self.host, mode=DHTMode.SERVER, enable_random_walk=True)
            nursery.start_soon(self._run_service, self.dht)
            logger.info("Kademlia DHT service with Random Walk enabled.")

            self.gossip = GossipSub(
                protocols=[GOSSIPSUB_PROTOCOL_ID],
                degree=6,
                degree_low=4,
                degree_high=8
            )
            self.pubsub = Pubsub(self.host, self.gossip)
            nursery.start_soon(self._run_service, self.pubsub)
            nursery.start_soon(self._run_service, self.gossip)
            logger.info("PubSub services starting.")

            try:
                await self._connect_to_bootstrap_nodes()
            except Exception as e:
                logger.error(f"Failed to connect to bootstrap nodes: {e}")

            if handler_callback and pubsub_topics:
                for topic in pubsub_topics:
                    subscription = await self.pubsub.subscribe(topic)
                    logger.info(f"Subscribed to PubSub topic: {topic}")
                    nursery.start_soon(self._message_handler_loop, subscription, handler_callback)

            logger.info("Node is fully operational. Running indefinitely.")
            await trio.sleep_forever()

    async def _run_service(self, service: Service):
        async with background_trio_service(service):
            await trio.sleep_forever()

    def _load_or_create_key(self) -> KeyPair:
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, "rb") as f:
                key_bytes = f.read()
            private_key = Secp256k1PrivateKey.deserialize(key_bytes)
            public_key = private_key.get_public_key()
            logger.info(f"Loaded existing key from {KEY_FILE}")
            return KeyPair(private_key, public_key)
        else:
            key_pair = create_new_key_pair()
            with open(KEY_FILE, "wb") as f:
                f.write(key_pair.private_key.serialize())
            logger.info(f"Created and saved new key to {KEY_FILE}")
            return key_pair

    def _log_host_info(self):
        logger.info(f"Host created with ID: {self.host.get_id().to_string()}")
        for addr in self.host.get_addrs():
            logger.info(f"Listening on: {addr}")

    async def _connect_to_bootstrap_nodes(self):
        try:
            async with trio.open_nursery() as nursery:
                for addr_str in BOOTSTRAP_NODES:
                    try:
                        maddr = Multiaddr(addr_str)
                        peer_info = info_from_p2p_addr(maddr)
                        nursery.start_soon(self.host.connect, peer_info)
                    except Exception as e:
                        logger.warning(f"Failed to parse bootstrap node address {addr_str}: {e}")
        except SwarmException as e:
            logger.warning(f"Error during bootstrap connection: {e}")
        logger.info("Bootstrap connection process completed.")

    async def _message_handler_loop(self, subscription: ISubscriptionAPI, handler_callback: Callable):
        while True:
            try:
                msg = await subscription.get()
                handler_callback(msg)
            except Exception as e:
                logger.error(f"Error in PubSub message handler: {e}", exc_info=True)

    async def broadcast(self, topic: str, data: dict):
        if not self.pubsub:
            logger.warning("Cannot broadcast: PubSub is not initialized.")
            return
        try:
            encoded_message = json.dumps(data).encode('utf-8')
            await self.pubsub.publish(topic, encoded_message)
            logger.info(f"Broadcasted to topic '{topic}': {data}")
        except Exception as e:
            logger.error(f"Failed to broadcast to topic '{topic}': {e}")
