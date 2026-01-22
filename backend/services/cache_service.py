"""
Cache service for storing and retrieving recommendations.
Supports both in-memory caching and Redis (when available).
"""

import hashlib
import logging
import time
from typing import Optional
from config import REDIS_HOST, REDIS_PORT, REDIS_DB, CACHE_DEFAULT_TTL, CACHE_MAX_SIZE

logger = logging.getLogger(__name__)

# In-memory cache storage with size limits
_cache: dict[str, str] = {}
_cache_ttl: dict[str, float] = {}

# Redis client (optional, will be None if Redis is not available)
_redis_client = None

try:
    import redis
    # Try to connect to Redis if available
    try:
        _redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1
        )
        # Test connection
        _redis_client.ping()
        logger.info(f"Redis cache initialized successfully at {REDIS_HOST}:{REDIS_PORT}")
    except (redis.ConnectionError, redis.TimeoutError, Exception) as e:
        logger.info(f"Redis not available, using in-memory cache: {str(e)}")
        _redis_client = None
except ImportError:
    logger.info("Redis package not installed, using in-memory cache only")


def get_cache_key(book_name: str, tags: list[str]) -> str:
    """
    Generate a cache key from book name and tags.
    
    Args:
        book_name: Name of the book
        tags: List of tags
        
    Returns:
        MD5 hash of the normalized cache key
    """
    # Normalize: lowercase, strip whitespace, sort tags
    normalized_name = book_name.lower().strip()
    normalized_tags = sorted([tag.lower().strip() for tag in tags if tag])
    key_data = f"{normalized_name}:{normalized_tags}"
    return hashlib.md5(key_data.encode()).hexdigest()


def get_cached(book_name: str, tags: list[str], ttl: int = None) -> Optional[str]:
    """
    Get cached recommendations if available and not expired.
    
    Args:
        book_name: Name of the book
        tags: List of tags
        ttl: Time-to-live in seconds (uses CACHE_DEFAULT_TTL if None)
        
    Returns:
        Cached recommendations string or None if not found/expired
    """
    if ttl is None:
        ttl = CACHE_DEFAULT_TTL
    key = get_cache_key(book_name, tags)
    
    # Try Redis first if available
    if _redis_client:
        try:
            cached_data = _redis_client.get(f"recommendations:{key}")
            if cached_data:
                logger.debug(f"Cache hit (Redis) for key: {key[:8]}...")
                return cached_data
        except Exception as e:
            logger.warning(f"Redis get error, falling back to in-memory: {str(e)}")
    
    # Fall back to in-memory cache
    if key in _cache:
        if time.time() < _cache_ttl.get(key, 0):
            logger.debug(f"Cache hit (in-memory) for key: {key[:8]}...")
            return _cache[key]
        else:
            # Expired, remove it
            del _cache[key]
            del _cache_ttl[key]
    
    logger.debug(f"Cache miss for key: {key[:8]}...")
    return None


def set_cached(book_name: str, tags: list[str], result: str, ttl: int = None):
    """
    Cache recommendations with TTL.
    
    Args:
        book_name: Name of the book
        tags: List of tags
        result: Recommendations result string
        ttl: Time-to-live in seconds (uses CACHE_DEFAULT_TTL if None)
    """
    if ttl is None:
        ttl = CACHE_DEFAULT_TTL
    
    key = get_cache_key(book_name, tags)
    cache_key = f"recommendations:{key}"
    
    # Try Redis first if available
    if _redis_client:
        try:
            _redis_client.setex(cache_key, ttl, result)
            logger.debug(f"Cached (Redis) key: {key[:8]}... with TTL: {ttl}s")
            return
        except Exception as e:
            logger.warning(f"Redis set error, falling back to in-memory: {str(e)}")
    
    # Fall back to in-memory cache with size limit
    # Remove oldest entries if cache is full (simple LRU-like eviction)
    if len(_cache) >= CACHE_MAX_SIZE:
        # Remove expired entries first
        current_time = time.time()
        expired_keys = [k for k, expiry in _cache_ttl.items() if current_time >= expiry]
        for k in expired_keys:
            _cache.pop(k, None)
            _cache_ttl.pop(k, None)
        
        # If still full, remove oldest entry
        if len(_cache) >= CACHE_MAX_SIZE:
            oldest_key = min(_cache_ttl.items(), key=lambda x: x[1])[0]
            _cache.pop(oldest_key, None)
            _cache_ttl.pop(oldest_key, None)
            logger.debug(f"Cache full, evicted oldest entry: {oldest_key[:8]}...")
    
    _cache[key] = result
    _cache_ttl[key] = time.time() + ttl
    logger.debug(f"Cached (in-memory) key: {key[:8]}... with TTL: {ttl}s")


def clear_cache():
    """Clear all cached data."""
    global _cache, _cache_ttl
    
    if _redis_client:
        try:
            # Clear Redis keys matching pattern
            keys = _redis_client.keys("recommendations:*")
            if keys:
                _redis_client.delete(*keys)
            logger.info("Redis cache cleared")
        except Exception as e:
            logger.warning(f"Error clearing Redis cache: {str(e)}")
    
    _cache.clear()
    _cache_ttl.clear()
    logger.info("In-memory cache cleared")


def get_cache_stats() -> dict:
    """
    Get cache statistics.
    
    Returns:
        Dictionary with cache statistics
    """
    stats = {
        "in_memory_size": len(_cache),
        "redis_available": _redis_client is not None
    }
    
    if _redis_client:
        try:
            keys = _redis_client.keys("recommendations:*")
            stats["redis_size"] = len(keys)
        except Exception:
            stats["redis_size"] = 0
    
    return stats
