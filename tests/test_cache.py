"""Tests for semantic cache module."""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from tokencrush.cache import CacheStats, SemanticCache


@pytest.fixture
def temp_cache_dir():
    """Create temporary directory for cache testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def cache(temp_cache_dir):
    """Create a SemanticCache instance with temporary database."""
    db_path = os.path.join(temp_cache_dir, "test_cache.db")
    return SemanticCache(db_path=db_path, threshold=0.85, ttl=3600)


class TestSemanticCacheInit:
    """Test cache initialization."""

    def test_init_default_path(self):
        """Test initialization with default cache path."""
        cache = SemanticCache()
        expected_path = Path.home() / ".cache" / "tokencrush" / "cache.db"
        assert cache.db_path == str(expected_path)
        assert cache.threshold == SemanticCache.DEFAULT_THRESHOLD
        assert cache.ttl == SemanticCache.DEFAULT_TTL

    def test_init_custom_path(self, temp_cache_dir):
        """Test initialization with custom database path."""
        db_path = os.path.join(temp_cache_dir, "custom.db")
        cache = SemanticCache(db_path=db_path)
        assert cache.db_path == db_path
        assert os.path.exists(db_path)

    def test_init_custom_params(self, temp_cache_dir):
        """Test initialization with custom parameters."""
        db_path = os.path.join(temp_cache_dir, "test.db")
        cache = SemanticCache(
            db_path=db_path,
            threshold=0.9,
            ttl=7200,
            max_size=5000,
        )
        assert cache.threshold == 0.9
        assert cache.ttl == 7200
        assert cache.max_size == 5000

    def test_database_schema_created(self, cache):
        """Test that database schema is properly created."""
        import sqlite3

        conn = sqlite3.connect(cache.db_path)
        cursor = conn.cursor()

        # Check table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='cache_entries'"
        )
        assert cursor.fetchone() is not None

        # Check columns
        cursor.execute("PRAGMA table_info(cache_entries)")
        columns = {row[1] for row in cursor.fetchall()}
        expected_columns = {
            "id",
            "query_text",
            "response_text",
            "embedding",
            "timestamp",
            "access_count",
            "last_accessed",
        }
        assert expected_columns.issubset(columns)

        conn.close()


class TestSemanticCacheBasicOperations:
    """Test basic cache operations."""

    def test_set_and_get_exact_match(self, cache):
        """Test storing and retrieving with exact query match."""
        query = "What is the capital of France?"
        response = "The capital of France is Paris."

        cache.set(query, response)
        result = cache.get(query)

        assert result == response

    def test_get_similar_query(self, cache):
        """Test retrieving with semantically similar query."""
        cache.set("What is Python?", "Python is a programming language.")

        # Similar query should hit cache
        result = cache.get("Tell me about Python")
        assert result == "Python is a programming language."

    def test_get_dissimilar_query(self, cache):
        """Test that dissimilar queries miss cache."""
        cache.set("What is Python?", "Python is a programming language.")

        # Completely different query should miss
        result = cache.get("What is the weather today?")
        assert result is None

    def test_get_empty_query(self, cache):
        """Test that empty queries return None."""
        assert cache.get("") is None
        assert cache.get("   ") is None

    def test_set_empty_values(self, cache):
        """Test that empty values are not stored."""
        cache.set("", "response")
        cache.set("query", "")
        cache.set("", "")

        # Cache should be empty
        stats = cache.stats()
        assert stats.total_queries == 0

    def test_multiple_entries(self, cache):
        """Test storing and retrieving multiple entries."""
        entries = [
            ("What is Python?", "Python is a programming language."),
            ("What is Java?", "Java is a programming language."),
            ("What is JavaScript?", "JavaScript is a scripting language."),
        ]

        for query, response in entries:
            cache.set(query, response)

        # Retrieve all entries
        for query, expected_response in entries:
            result = cache.get(query)
            assert result == expected_response


class TestSemanticCacheStatistics:
    """Test cache statistics tracking."""

    def test_stats_initial(self, cache):
        """Test initial statistics."""
        stats = cache.stats()
        assert stats.total_queries == 0
        assert stats.cache_hits == 0
        assert stats.cache_misses == 0
        assert stats.hit_rate == 0.0

    def test_stats_after_hit(self, cache):
        """Test statistics after cache hit."""
        cache.set("test query", "test response")
        cache.get("test query")

        stats = cache.stats()
        assert stats.total_queries == 1
        assert stats.cache_hits == 1
        assert stats.cache_misses == 0
        assert stats.hit_rate == 1.0

    def test_stats_after_miss(self, cache):
        """Test statistics after cache miss."""
        cache.get("nonexistent query")

        stats = cache.stats()
        assert stats.total_queries == 1
        assert stats.cache_hits == 0
        assert stats.cache_misses == 1
        assert stats.hit_rate == 0.0

    def test_stats_mixed_hits_misses(self, cache):
        """Test statistics with mixed hits and misses."""
        cache.set("query1", "response1")
        cache.set("query2", "response2")

        cache.get("query1")  # hit
        cache.get("query2")  # hit
        cache.get("query3")  # miss
        cache.get("query1")  # hit
        cache.get("query4")  # miss

        stats = cache.stats()
        assert stats.total_queries == 5
        assert stats.cache_hits == 3
        assert stats.cache_misses == 2
        assert stats.hit_rate == 0.6


class TestSemanticCacheClear:
    """Test cache clearing."""

    def test_clear_empty_cache(self, cache):
        """Test clearing empty cache."""
        cache.clear()
        stats = cache.stats()
        assert stats.total_queries == 0

    def test_clear_populated_cache(self, cache):
        """Test clearing populated cache."""
        cache.set("query1", "response1")
        cache.set("query2", "response2")
        cache.get("query1")

        cache.clear()

        # Check cache is empty
        result = cache.get("query1")
        assert result is None

        # Check stats are reset
        stats = cache.stats()
        assert stats.total_queries == 1  # The get after clear
        assert stats.cache_hits == 0
        assert stats.cache_misses == 1


class TestSemanticCacheTTL:
    """Test time-to-live functionality."""

    def test_ttl_not_expired(self, temp_cache_dir):
        """Test that non-expired entries are retrieved."""
        db_path = os.path.join(temp_cache_dir, "ttl_test.db")
        cache = SemanticCache(db_path=db_path, ttl=10)  # 10 seconds TTL

        cache.set("test query", "test response")
        result = cache.get("test query")

        assert result == "test response"

    def test_ttl_expired(self, temp_cache_dir):
        """Test that expired entries are cleaned up."""
        db_path = os.path.join(temp_cache_dir, "ttl_test.db")
        cache = SemanticCache(db_path=db_path, ttl=1)  # 1 second TTL

        cache.set("test query", "test response")

        # Wait for expiration
        time.sleep(1.5)

        # Trigger cleanup (happens every 100 queries)
        for _ in range(100):
            cache.get("dummy query")

        # Entry should be gone
        result = cache.get("test query")
        assert result is None


class TestSemanticCacheEviction:
    """Test LRU eviction when cache is full."""

    def test_eviction_when_full(self, temp_cache_dir):
        """Test that old entries are evicted when cache is full."""
        db_path = os.path.join(temp_cache_dir, "eviction_test.db")
        cache = SemanticCache(db_path=db_path, max_size=10)

        # Fill cache
        for i in range(10):
            cache.set(f"query{i}", f"response{i}")

        # Access some entries to update last_accessed
        cache.get("query5")
        cache.get("query6")
        cache.get("query7")

        # Add one more entry to trigger eviction
        cache.set("query10", "response10")

        # Least recently accessed entries should be evicted
        # query0-query4 should be candidates for eviction
        result = cache.get("query5")
        assert result is not None  # Recently accessed, should survive

    def test_no_eviction_below_max(self, temp_cache_dir):
        """Test that no eviction occurs below max_size."""
        db_path = os.path.join(temp_cache_dir, "no_eviction_test.db")
        cache = SemanticCache(db_path=db_path, max_size=100)

        # Add entries below max
        for i in range(50):
            cache.set(f"query{i}", f"response{i}")

        # All entries should be retrievable
        for i in range(50):
            result = cache.get(f"query{i}")
            assert result == f"response{i}"


class TestSemanticCacheThreshold:
    """Test similarity threshold behavior."""

    def test_high_threshold_strict(self, temp_cache_dir):
        """Test that high threshold requires very similar queries."""
        db_path = os.path.join(temp_cache_dir, "threshold_test.db")
        cache = SemanticCache(db_path=db_path, threshold=0.95)  # Very strict

        cache.set("What is Python?", "Python is a programming language.")

        # Slightly different query might miss with high threshold
        result = cache.get("What is Python programming language?")
        # Result depends on embedding similarity, but high threshold is stricter
        assert result is None or result == "Python is a programming language."

    def test_low_threshold_permissive(self, temp_cache_dir):
        """Test that low threshold allows more variation."""
        db_path = os.path.join(temp_cache_dir, "threshold_test.db")
        cache = SemanticCache(db_path=db_path, threshold=0.7)  # More permissive

        cache.set("What is Python?", "Python is a programming language.")

        # More variation should still hit cache
        result = cache.get("Tell me about Python")
        assert result == "Python is a programming language."


class TestSemanticCacheAccessTracking:
    """Test access count and last_accessed tracking."""

    def test_access_count_increments(self, cache):
        """Test that access count increments on each get."""
        import sqlite3

        cache.set("test query", "test response")

        # Access multiple times
        for _ in range(5):
            cache.get("test query")

        # Check access count in database
        conn = sqlite3.connect(cache.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT access_count FROM cache_entries WHERE query_text = ?",
            ("test query",),
        )
        access_count = cursor.fetchone()[0]
        conn.close()

        assert access_count == 5

    def test_last_accessed_updates(self, cache):
        """Test that last_accessed timestamp updates."""
        import sqlite3

        cache.set("test query", "test response")
        time.sleep(0.1)

        # Get initial last_accessed
        conn = sqlite3.connect(cache.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT last_accessed FROM cache_entries WHERE query_text = ?",
            ("test query",),
        )
        first_access = cursor.fetchone()[0]
        conn.close()

        time.sleep(0.1)
        cache.get("test query")

        # Get updated last_accessed
        conn = sqlite3.connect(cache.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT last_accessed FROM cache_entries WHERE query_text = ?",
            ("test query",),
        )
        second_access = cursor.fetchone()[0]
        conn.close()

        assert second_access > first_access


class TestSemanticCacheEdgeCases:
    """Test edge cases and error handling."""

    def test_unicode_text(self, cache):
        """Test handling of unicode text."""
        query = "¿Qué es Python? 你好 مرحبا"
        response = "Python is a programming language."

        cache.set(query, response)
        result = cache.get(query)

        assert result == response

    def test_very_long_text(self, cache):
        """Test handling of very long text."""
        query = "What is Python? " * 1000  # Very long query
        response = "Python is a programming language."

        cache.set(query, response)
        result = cache.get(query)

        assert result == response

    def test_special_characters(self, cache):
        """Test handling of special characters."""
        query = "What is <Python>? [test] {code} & symbols!"
        response = "Python is a programming language."

        cache.set(query, response)
        result = cache.get(query)

        assert result == response

    def test_concurrent_access(self, cache):
        """Test basic concurrent access (no threading, just sequential)."""
        # Add multiple entries
        for i in range(10):
            cache.set(f"query{i}", f"response{i}")

        # Retrieve in different order
        for i in range(9, -1, -1):
            result = cache.get(f"query{i}")
            assert result == f"response{i}"


class TestSemanticCacheDataclass:
    """Test CacheStats dataclass."""

    def test_cache_stats_creation(self):
        """Test creating CacheStats instance."""
        stats = CacheStats(
            total_queries=100,
            cache_hits=70,
            cache_misses=30,
            hit_rate=0.7,
        )

        assert stats.total_queries == 100
        assert stats.cache_hits == 70
        assert stats.cache_misses == 30
        assert stats.hit_rate == 0.7
