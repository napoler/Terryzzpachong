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

            # --- FTS5 Setup for Search ---
            # 1. Create the virtual table for full-text search on torrent names
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS torrent_fts USING fts5(
                    info_hash UNINDEXED,
                    name,
                    content='data_cache',
                    content_rowid='key'
                )
            """)

            # 2. Create a trigger to automatically update the FTS table when data is inserted
            # This will attempt to extract the 'name' from the JSON value. If the value is not
            # valid JSON or doesn't have a name, it will be ignored.
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS data_cache_after_insert
                AFTER INSERT ON data_cache
                WHEN json_valid(new.value) AND json_extract(new.value, '$.name') IS NOT NULL
                BEGIN
                    INSERT INTO torrent_fts(rowid, info_hash, name)
                    VALUES (
                        new.key,
                        new.key,
                        json_extract(new.value, '$.name')
                    );
                END;
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
        """
        Retrieves a list of the most commented-on torrents, including their names.
        """
        hot_torrents = []
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    c.info_hash,
                    COUNT(c.id) as comment_count,
                    dc.value as metadata
                FROM comments c
                LEFT JOIN data_cache dc ON c.info_hash = dc.key
                GROUP BY c.info_hash
                ORDER BY comment_count DESC
                LIMIT ?
            """, (limit,))

            for row in cursor.fetchall():
                row_dict = dict(row)
                name = "Unknown (metadata not yet fetched)"
                if row_dict['metadata']:
                    try:
                        metadata = json.loads(row_dict['metadata'])
                        name = metadata.get("name", "Name not found in metadata")
                    except (json.JSONDecodeError, TypeError):
                        name = "Invalid metadata format"

                hot_torrents.append({
                    "info_hash": row_dict['info_hash'],
                    "comment_count": row_dict['comment_count'],
                    "name": name
                })
        return hot_torrents

    def get_hashes_without_metadata(self, limit: int = 10) -> List[str]:
        """
        Retrieves a list of info_hashes (keys) that have no associated metadata (empty value).
        """
        hashes = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Select keys where value is an empty blob or NULL
            cursor.execute("""
                SELECT key FROM data_cache
                WHERE value IS NULL OR value = ''
                ORDER BY last_seen DESC
                LIMIT ?
            """, (limit,))
            results = cursor.fetchall()
            hashes = [row[0] for row in results]
        return hashes

    def get_recent_torrents(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves the most recently discovered torrents that have metadata."""
        recent_torrents = []
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT key as info_hash, value
                FROM data_cache
                WHERE value IS NOT NULL AND value != ''
                ORDER BY last_seen DESC
                LIMIT ?
            """, (limit,))
            for row in cursor.fetchall():
                try:
                    data = json.loads(row['value'])
                    recent_torrents.append({
                        "info_hash": row['info_hash'],
                        "name": data.get("name", "Unknown")
                    })
                except (json.JSONDecodeError, TypeError):
                    # Skip rows with invalid JSON in the value
                    continue
        return recent_torrents

    def search_torrents(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Performs a full-text search for torrents by name."""
        search_results = []
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # FTS5 uses a special MATCH operator for searching
            cursor.execute("""
                SELECT info_hash, name
                FROM torrent_fts
                WHERE name MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit))
            for row in cursor.fetchall():
                search_results.append(dict(row))
        return search_results
