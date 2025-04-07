import asyncio
import contextlib
import contextvars
import logging
import time
import weakref
import redis  # New import
from redis.asyncio import Redis  # Async Redis client
from typing import Optional, Tuple

import aiopg
from . import models
from . import settings

log = logging.getLogger(__name__)

# Database connections
conn = weakref.WeakKeyDictionary()
cur = contextvars.ContextVar("cur", default=None)
redis_pool: Optional[Redis] = None  # Redis connection pool

class CacheError(Exception):
    """Base exception for cache-related errors"""
    pass

class NotInTransactionError(Exception):
    """Trying to get cursor outside of a transaction context manager"""

class NotInAsyncIOError(Exception):
    """Trying to use connection outside of asyncio context"""

async def init_redis():
    """Initialize Redis connection pool"""
    global redis_pool
    try:
        redis_pool = Redis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            decode_responses=True,
            socket_timeout=5,
            health_check_interval=30
        )
        await redis_pool.ping()  # Test connection
    except Exception as e:
        log.error(f"Redis connection failed: {str(e)}")
        raise CacheError("Redis initialization failed") from e

async def close_redis():
    """Close Redis connection"""
    global redis_pool
    if redis_pool:
        await redis_pool.close()
        redis_pool = None

async def get_conn():
    """Get current database connection, creating it if needed"""
    global conn
    loop = asyncio.get_running_loop()
    if loop is None:
        raise NotInAsyncIOError("This method only works with asyncio")
    _conn = conn.get(loop)
    if _conn is None:
        _conn = await aiopg.create_pool(
            dbname=settings.POSTGRES_DATABASE,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOST,
            async_=True,
        )
        conn[loop] = _conn
    return _conn

async def get_cache_key(query: str, params: tuple) -> str:
    """Generate consistent cache key for queries"""
    return f"query:{hash(query + str(params))}"

async def db_exec(query: str, params: tuple = ()) -> Tuple[aiopg.Cursor, str]:
    """
    Execute postgresql query with Redis caching layer
    """
    global redis_pool
    
    # Try Redis cache first
    cache_key = await get_cache_key(query, params)
    cached_result = None
    
    if redis_pool:
        try:
            cached_result = await redis_pool.get(cache_key)
            if cached_result:
                log.debug(f"Cache hit for {cache_key}")
                # Return a dummy cursor with cached data
                class CachedCursor:
                    def __init__(self, result):
                        self._result = result
                    async def fetchone(self):
                        return self._result
                    async def fetchall(self):
                        return [self._result]
                    @property
                    def rowcount(self):
                        return 1
                
                return CachedCursor(eval(cached_result)), "0ms (cached)"
        except redis.RedisError as e:
            log.warning(f"Redis error: {str(e)} - falling back to DB")

    # Fallback to PostgreSQL
    t = time.monotonic()
    try:
        _cursor = cursor()
        await _cursor.execute(query, params)
        exec_time = str(round(time.monotonic()-t, 4)*1000)+"ms"
        
        # Cache the result if Redis is available
        if redis_pool and not query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
            try:
                result = await _cursor.fetchone()
                await redis_pool.setex(
                    cache_key,
                    settings.CACHE_TTL,
                    str(result)  # Simple serialization
                )
            except redis.RedisError as e:
                log.warning(f"Failed to cache result: {str(e)}")
        
        return _cursor, exec_time
    except Exception as e:
        log.error(f"DB query failed: {str(e)}")
        raise

async def invalidate_cache(patterns: list):
    """Invalidate cache keys matching patterns"""
    if not redis_pool:
        return
        
    try:
        for pattern in patterns:
            keys = await redis_pool.keys(pattern)
            if keys:
                await redis_pool.delete(*keys)
    except redis.RedisError as e:
        log.error(f"Cache invalidation failed: {str(e)}")
        raise CacheError("Cache invalidation failed") from e

# [Rest of the file remains unchanged...]
