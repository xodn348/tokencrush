"""Semantic caching module using SQLite and FAISS for vector similarity search."""

import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass
class CacheStats:
    """Statistics about cache performance."""

    total_queries: int
    cache_hits: int
    cache_misses: int
    hit_rate: float


class SemanticCache:
    """Semantic cache using local embeddings and vector similarity search.

    Uses sentence-transformers for embeddings (no external API calls),
    SQLite for metadata storage, and FAISS for efficient vector search.
    """

    DEFAULT_MODEL = "all-MiniLM-L6-v2"  # Fast, lightweight, 384 dimensions
    DEFAULT_THRESHOLD = 0.85
    DEFAULT_TTL = 86400  # 24 hours in seconds
    DEFAULT_MAX_SIZE = 10000  # Maximum cache entries

    def __init__(
        self,
        db_path: Optional[str] = None,
        threshold: float = DEFAULT_THRESHOLD,
        ttl: int = DEFAULT_TTL,
        max_size: int = DEFAULT_MAX_SIZE,
        model_name: Optional[str] = None,
    ):
        """Initialize the semantic cache.

        Args:
            db_path: Path to SQLite database. Defaults to ~/.cache/tokencrush/cache.db
            threshold: Similarity threshold for cache hits (0.0-1.0). Default 0.85
            ttl: Time-to-live for cache entries in seconds. Default 86400 (24h)
            max_size: Maximum number of cache entries. Default 10000
            model_name: Sentence transformer model name. Default all-MiniLM-L6-v2
        """
        # Set up database path
        if db_path is None:
            cache_dir = Path.home() / ".cache" / "tokencrush"
            cache_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(cache_dir / "cache.db")
        else:
            db_path = os.path.expanduser(db_path)
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.threshold = threshold
        self.ttl = ttl
        self.max_size = max_size

        # Initialize embedding model
        self._model = SentenceTransformer(model_name or self.DEFAULT_MODEL)
        self._embedding_dim = self._model.get_sentence_embedding_dimension()

        # Initialize database and FAISS index
        self._init_database()
        self._init_faiss_index()

        # Statistics
        self._total_queries = 0
        self._cache_hits = 0
        self._cache_misses = 0

    def _init_database(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT NOT NULL,
                response_text TEXT NOT NULL,
                embedding BLOB NOT NULL,
                timestamp REAL NOT NULL,
                access_count INTEGER DEFAULT 0,
                last_accessed REAL NOT NULL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON cache_entries(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_last_accessed 
            ON cache_entries(last_accessed)
        """)

        conn.commit()
        conn.close()

    def _init_faiss_index(self):
        """Initialize or load FAISS index from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Load existing embeddings
        cursor.execute("SELECT id, embedding FROM cache_entries ORDER BY id")
        rows = cursor.fetchall()

        # Create FAISS index (using inner product for cosine similarity)
        self._index = faiss.IndexFlatIP(self._embedding_dim)
        self._id_map = {}  # Maps FAISS index position to database ID

        if rows:
            embeddings = []
            for idx, (db_id, embedding_blob) in enumerate(rows):
                embedding = np.frombuffer(embedding_blob, dtype=np.float32)
                embeddings.append(embedding)
                self._id_map[idx] = db_id

            embeddings_array = np.array(embeddings, dtype=np.float32)
            # Normalize for cosine similarity
            faiss.normalize_L2(embeddings_array)
            self._index.add(embeddings_array)

        conn.close()

    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding vector for text.

        Args:
            text: Input text to embed

        Returns:
            Normalized embedding vector
        """
        embedding = self._model.encode(text, convert_to_numpy=True)
        # Normalize for cosine similarity
        embedding = embedding / np.linalg.norm(embedding)
        return embedding.astype(np.float32)

    def _evict_if_needed(self):
        """Evict old entries if cache exceeds max_size using LRU strategy."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM cache_entries")
        count = cursor.fetchone()[0]

        if count >= self.max_size:
            # Delete oldest 10% by last access time
            delete_count = max(1, count // 10)
            cursor.execute(
                """
                DELETE FROM cache_entries 
                WHERE id IN (
                    SELECT id FROM cache_entries 
                    ORDER BY last_accessed ASC 
                    LIMIT ?
                )
            """,
                (delete_count,),
            )
            conn.commit()

            # Rebuild FAISS index after eviction
            self._init_faiss_index()

        conn.close()

    def _clean_expired(self):
        """Remove expired entries based on TTL."""
        if self.ttl <= 0:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_time = time.time() - self.ttl
        cursor.execute("DELETE FROM cache_entries WHERE timestamp < ?", (cutoff_time,))

        if cursor.rowcount > 0:
            conn.commit()
            # Rebuild FAISS index after cleanup
            self._init_faiss_index()

        conn.close()

    def get(self, query: str) -> Optional[str]:
        """Retrieve cached response for semantically similar query.

        Args:
            query: Query text to search for

        Returns:
            Cached response if similarity exceeds threshold, None otherwise
        """
        self._total_queries += 1

        if not query or not query.strip():
            self._cache_misses += 1
            return None

        # Clean expired entries periodically
        if self._total_queries % 100 == 0:
            self._clean_expired()

        # Generate query embedding
        query_embedding = self._generate_embedding(query)

        # Search FAISS index
        if self._index.ntotal == 0:
            self._cache_misses += 1
            return None

        # Search for top 1 most similar
        query_vector = query_embedding.reshape(1, -1)
        similarities, indices = self._index.search(query_vector, k=1)

        if len(similarities[0]) == 0:
            self._cache_misses += 1
            return None

        similarity = float(similarities[0][0])

        # Check threshold
        if similarity < self.threshold:
            self._cache_misses += 1
            return None

        # Get cached response from database
        faiss_idx = int(indices[0][0])
        db_id = self._id_map.get(faiss_idx)

        if db_id is None:
            self._cache_misses += 1
            return None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT response_text FROM cache_entries WHERE id = ?", (db_id,))
        row = cursor.fetchone()

        if row is None:
            conn.close()
            self._cache_misses += 1
            return None

        # Update access statistics
        cursor.execute(
            """
            UPDATE cache_entries 
            SET access_count = access_count + 1,
                last_accessed = ?
            WHERE id = ?
        """,
            (time.time(), db_id),
        )
        conn.commit()
        conn.close()

        self._cache_hits += 1
        return row[0]

    def set(self, query: str, response: str):
        """Store query-response pair in cache.

        Args:
            query: Query text
            response: Response text to cache
        """
        if not query or not query.strip() or not response:
            return

        # Evict if needed
        self._evict_if_needed()

        # Generate embedding
        embedding = self._generate_embedding(query)
        embedding_blob = embedding.tobytes()

        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        current_time = time.time()
        cursor.execute(
            """
            INSERT INTO cache_entries 
            (query_text, response_text, embedding, timestamp, last_accessed)
            VALUES (?, ?, ?, ?, ?)
        """,
            (query, response, embedding_blob, current_time, current_time),
        )

        db_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Add to FAISS index
        embedding_normalized = embedding.reshape(1, -1)
        self._index.add(embedding_normalized)
        self._id_map[self._index.ntotal - 1] = db_id

    def stats(self) -> CacheStats:
        """Get cache statistics.

        Returns:
            CacheStats object with hit rate and counts
        """
        hit_rate = (
            self._cache_hits / self._total_queries if self._total_queries > 0 else 0.0
        )

        return CacheStats(
            total_queries=self._total_queries,
            cache_hits=self._cache_hits,
            cache_misses=self._cache_misses,
            hit_rate=hit_rate,
        )

    def clear(self):
        """Clear all cache entries."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cache_entries")
        conn.commit()
        conn.close()

        # Reinitialize FAISS index
        self._init_faiss_index()

        # Reset statistics
        self._total_queries = 0
        self._cache_hits = 0
        self._cache_misses = 0
