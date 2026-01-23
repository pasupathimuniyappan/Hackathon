import json
import hashlib
from typing import Optional, Any
import redis.asyncio as redis
from ..config.settings import settings
from ..config.logger import logger


class CacheManager:
    """Redis-based cache manager for analysis results."""
    
    def __init__(self):
        """Initialize Redis client."""
        self.client: Optional[redis.Redis] = None
        self.enabled = settings.cache_enabled
        self.ttl = settings.cache_ttl
        
    async def connect(self):
        """Establish Redis connection."""
        if not self.enabled:
            logger.info("⚠️  Cache disabled")
            return
        
        try:
            self.client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            await self.client.ping()
            logger.info("✅ Redis connected successfully")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.enabled = False
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            cached = await self.client.get(key)
            if cached:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(cached)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Store value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: settings.cache_ttl)
        """
        if not self.enabled or not self.client:
            return
        
        try:
            ttl = ttl or self.ttl
            await self.client.setex(
                key,
                ttl,
                json.dumps(value)
            )
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    async def delete(self, key: str):
        """Delete key from cache."""
        if not self.enabled or not self.client:
            return
        
        try:
            await self.client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
    
    async def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern."""
        if not self.enabled or not self.client:
            return
        
        try:
            keys = await self.client.keys(pattern)
            if keys:
                await self.client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries matching '{pattern}'")
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")
    
    @staticmethod
    def generate_key(prefix: str, text: str, **kwargs) -> str:
        """
        Generate cache key from text and parameters.
        
        Args:
            prefix: Key prefix (e.g., "analysis", "optimization")
            text: Text to hash
            **kwargs: Additional parameters to include in hash
            
        Returns:
            Cache key string
        """
        # Create hash from text and parameters
        hash_input = text + json.dumps(kwargs, sort_keys=True)
        text_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        return f"{prefix}:{text_hash}"
    
    async def is_connected(self) -> bool:
        """Check if Redis is connected."""
        if not self.enabled or not self.client:
            return False
        
        try:
            await self.client.ping()
            return True
        except:
            return False


# Global cache manager instance
cache_manager = CacheManager()
