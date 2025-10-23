import sqlite3
import time
import json
import logging
from typing import Optional, List, Dict, Any, NamedTuple

DB_PATH = "p2p_cache.db"
logger = logging.getLogger(__name__)

class Comment(NamedTuple):
    info_hash: str
    text: str
    author_id: str
    timestamp: float
    signature: str

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._create_tables()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS data_cache (key TEXT PRIMARY KEY, value BLOB, last_seen TIMESTAMP, source TEXT)")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    info_hash TEXT NOT NULL,
                    comment_text TEXT NOT NULL,
                    author_peer_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    signature TEXT NOT NULL,
                    UNIQUE(info_hash, signature)
                )
            """)
            conn.commit()

    def set_data(self, key: str, value: bytes, source: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO data_cache (key, value, last_seen, source)
                VALUES (?, ?, ?, ?)
            """, (key, value, time.time(), source))
            conn.commit()

    def get_data(self, key: str) -> Optional[bytes]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM data_cache WHERE key = ?", (key,))
            result = cursor.fetchone()
            return result[0] if result else None

    def add_comment(self, comment: Comment) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO comments (info_hash, comment_text, author_peer_id, timestamp, signature)
                    VALUES (?, ?, ?, ?, ?)
                """, (comment.info_hash, comment.text, comment.author_id, comment.timestamp, comment.signature))
                conn.commit()
                logger.info(f"Successfully inserted comment for {comment.info_hash} into DB.")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"IntegrityError: Failed to add duplicate comment for {comment.info_hash}.")
            return False
        except sqlite3.Error as e:
            logger.error(f"Database Error: Failed to add comment for {comment.info_hash}. Error: {e}", exc_info=True)
            return False

    def get_comments(self, info_hash: str) -> List[Comment]:
        comments = []
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT info_hash, comment_text as text, author_peer_id as author_id, timestamp, signature
                FROM comments WHERE info_hash = ?
                ORDER BY timestamp DESC
            """, (info_hash,))
            for row in cursor.fetchall():
                comments.append(Comment(**dict(row)))
        return comments

    def get_hot_torrents(self, limit: int = 20) -> List[Dict[str, Any]]:
        hot_torrents = []
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT info_hash, COUNT(*) as comment_count
                FROM comments
                GROUP BY info_hash
                ORDER BY comment_count DESC
                LIMIT ?
            """, (limit,))
            for row in cursor.fetchall():
                hot_torrents.append(dict(row))
        return hot_torrents
