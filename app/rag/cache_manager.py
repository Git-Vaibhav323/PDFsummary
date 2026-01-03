"""
In-memory LRU cache for RAG responses and retrieval results.
Provides fast response caching with TTL support.
"""
import logging
import time
from functools import lru_cache
from typing import List, Dict, Optional, Tuple
import hashlib
import json

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages in-memory LRU cache for queries and responses."""
    
    def __init__(self, max_cache_size: int = 500, default_ttl: int = 300):
        """
        Initialize cache manager.
        
        Args:
            max_cache_size: Maximum number of cached items (LRU)
            default_ttl: Default time-to-live in seconds (5 minutes)
        """
        self.max_cache_size = max_cache_size
        self.default_ttl = default_ttl
        self._response_cache: Dict[str, Tuple[str, float]] = {}  # hash -> (response, timestamp)
        self._retrieval_cache: Dict[str, Tuple[List[Dict], float]] = {}  # hash -> (results, timestamp)
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info(f"✅ CacheManager initialized: max_size={max_cache_size}, ttl={default_ttl}s")
    
    @staticmethod
    def _hash_query(query: str, context: str = "") -> str:
        """
        Generate cache key from query and optional context.
        
        Args:
            query: User query
            context: Optional context (e.g., document_id)
            
        Returns:
            Hash string for cache key
        """
        cache_string = f"{query}:{context}".lower().strip()
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _is_expired(self, timestamp: float, ttl: Optional[int] = None) -> bool:
        """Check if cache entry is expired."""
        ttl = ttl or self.default_ttl
        return (time.time() - timestamp) > ttl
    
    def _evict_expired(self) -> None:
        """Remove expired entries from all caches."""
        current_time = time.time()
        
        # Remove expired response cache entries
        expired_keys = [
            k for k, (_, ts) in self._response_cache.items()
            if self._is_expired(ts)
        ]
        for k in expired_keys:
            del self._response_cache[k]
        
        # Remove expired retrieval cache entries
        expired_keys = [
            k for k, (_, ts) in self._retrieval_cache.items()
            if self._is_expired(ts)
        ]
        for k in expired_keys:
            del self._retrieval_cache[k]
        
        if expired_keys:
            logger.debug(f"🧹 Evicted {len(expired_keys)} expired cache entries")
    
    def _enforce_size_limit(self, cache_dict: Dict, max_size: int) -> None:
        """Remove oldest entries if cache exceeds max size (simple FIFO)."""
        if len(cache_dict) > max_size:
            # Remove oldest 10% of entries
            to_remove = len(cache_dict) - int(max_size * 0.9)
            for _ in range(to_remove):
                # Remove oldest by timestamp
                oldest_key = min(
                    cache_dict.keys(),
                    key=lambda k: cache_dict[k][1] if len(cache_dict[k]) > 1 else 0
                )
                del cache_dict[oldest_key]
    
    def get_response(self, query: str, document_id: str = "") -> Optional[str]:
        """
        Get cached response for query.
        
        Args:
            query: User query
            document_id: Optional document context
            
        Returns:
            Cached response or None if not found/expired
        """
        self._evict_expired()
        cache_key = self._hash_query(query, document_id)
        
        if cache_key in self._response_cache:
            response, timestamp = self._response_cache[cache_key]
            if not self._is_expired(timestamp):
                self._cache_hits += 1
                logger.debug(f"✅ Response cache HIT: {query[:50]}... (hits: {self._cache_hits})")
                return response
            else:
                # Expired, remove it
                del self._response_cache[cache_key]
        
        self._cache_misses += 1
        return None
    
    def set_response(self, query: str, response: str, document_id: str = "", ttl: Optional[int] = None) -> None:
        """
        Cache a response.
        
        Args:
            query: User query
            response: LLM response
            document_id: Optional document context
            ttl: Optional custom TTL (overrides default)
        """
        cache_key = self._hash_query(query, document_id)
        self._response_cache[cache_key] = (response, time.time())
        self._enforce_size_limit(self._response_cache, self.max_cache_size)
        logger.debug(f"💾 Response cached: {query[:50]}... (total: {len(self._response_cache)})")
    
    def get_retrieval(self, query: str, document_id: str = "") -> Optional[List[Dict]]:
        """
        Get cached retrieval results for query.
        
        Args:
            query: User query
            document_id: Optional document context
            
        Returns:
            Cached retrieval results or None if not found/expired
        """
        self._evict_expired()
        cache_key = self._hash_query(query, document_id)
        
        if cache_key in self._retrieval_cache:
            results, timestamp = self._retrieval_cache[cache_key]
            if not self._is_expired(timestamp):
                self._cache_hits += 1
                logger.debug(f"✅ Retrieval cache HIT: {len(results)} chunks (hits: {self._cache_hits})")
                return results
            else:
                del self._retrieval_cache[cache_key]
        
        self._cache_misses += 1
        return None
    
    def set_retrieval(self, query: str, results: List[Dict], document_id: str = "") -> None:
        """
        Cache retrieval results.
        
        Args:
            query: User query
            results: Retrieved chunks
            document_id: Optional document context
        """
        cache_key = self._hash_query(query, document_id)
        self._retrieval_cache[cache_key] = (results, time.time())
        self._enforce_size_limit(self._retrieval_cache, self.max_cache_size)
        logger.debug(f"💾 Retrieval cached: {len(results)} chunks (total: {len(self._retrieval_cache)})")
    
    def clear_document_cache(self, document_id: str) -> None:
        """Clear cache entries for a specific document (on re-upload)."""
        # Clear entries with this document_id
        keys_to_remove = [
            k for k, (_, _) in self._retrieval_cache.items()
            if str(document_id) in k or document_id in str(self._retrieval_cache[k])
        ]
        for k in keys_to_remove:
            del self._retrieval_cache[k]
            if k in self._response_cache:
                del self._response_cache[k]
        logger.info(f"🧹 Cleared {len(keys_to_remove)} cache entries for document: {document_id}")
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate_percent": round(hit_rate, 2),
            "response_cache_size": len(self._response_cache),
            "retrieval_cache_size": len(self._retrieval_cache),
            "total_cached_items": len(self._response_cache) + len(self._retrieval_cache)
        }
    
    def clear_all(self) -> None:
        """Clear all cache."""
        self._response_cache.clear()
        self._retrieval_cache.clear()
        logger.info("🧹 All cache cleared")


# Global cache instance (singleton)
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(max_cache_size=500, default_ttl=300)
    return _cache_manager
