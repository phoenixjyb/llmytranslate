"""
Redis-based cache service for translation results.
"""

import json
from typing import Optional, Dict, Any
import redis.asyncio as redis
from datetime import datetime, timedelta

from ..core.config import get_settings

# Mock logger
class MockLogger:
    def info(self, msg, **kwargs): pass
    def error(self, msg, **kwargs): pass
    def warning(self, msg, **kwargs): pass

logger = MockLogger()


class CacheService:
    """Async Redis cache service for translation results."""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client: Optional[redis.Redis] = None
        self.redis_url = self.settings.redis.redis_url
        self.default_ttl = self.settings.redis.cache_ttl
    
    async def __aenter__(self):
        """Async context manager entry."""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.redis_client:
            await self.redis_client.close()
    
    async def get_translation(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached translation result."""
        if not self.redis_client:
            return None
        
        try:
            cached_data = await self.redis_client.get(f"translation:{cache_key}")
            if cached_data:
                result = json.loads(cached_data)
                
                # Update hit count
                await self.redis_client.incr(f"hit_count:{cache_key}")
                
                logger.info("Cache hit", cache_key=cache_key)
                return result
            return None
        except Exception as e:
            logger.error("Cache get failed", cache_key=cache_key, error=str(e))
            return None
    
    async def set_translation(
        self,
        cache_key: str,
        translation_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Set translation result in cache."""
        if not self.redis_client:
            return False
        
        try:
            cache_ttl = ttl or self.default_ttl
            
            # Add metadata
            cached_data = {
                **translation_data,
                "cached_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(seconds=cache_ttl)).isoformat()
            }
            
            # Store translation
            await self.redis_client.setex(
                f"translation:{cache_key}",
                cache_ttl,
                json.dumps(cached_data)
            )
            
            # Initialize hit count
            await self.redis_client.setex(
                f"hit_count:{cache_key}",
                cache_ttl,
                0
            )
            
            logger.info("Translation cached", cache_key=cache_key, ttl=cache_ttl)
            return True
        except Exception as e:
            logger.error("Cache set failed", cache_key=cache_key, error=str(e))
            return False
    
    async def delete_translation(self, cache_key: str) -> bool:
        """Delete cached translation."""
        if not self.redis_client:
            return False
        
        try:
            deleted = await self.redis_client.delete(
                f"translation:{cache_key}",
                f"hit_count:{cache_key}"
            )
            return deleted > 0
        except Exception as e:
            logger.error("Cache delete failed", cache_key=cache_key, error=str(e))
            return False
    
    async def clear_cache(self) -> bool:
        """Clear all cached translations."""
        if not self.redis_client:
            return False
        
        try:
            keys = await self.redis_client.keys("translation:*")
            hit_count_keys = await self.redis_client.keys("hit_count:*")
            
            if keys or hit_count_keys:
                await self.redis_client.delete(*(keys + hit_count_keys))
            
            logger.info("Cache cleared", keys_deleted=len(keys) + len(hit_count_keys))
            return True
        except Exception as e:
            logger.error("Cache clear failed", error=str(e))
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.redis_client:
            return {
                "status": "unavailable",
                "total_keys": 0,
                "memory_usage": 0
            }
        
        try:
            # Get basic Redis info
            info = await self.redis_client.info("memory")
            
            # Count cache keys
            translation_keys = await self.redis_client.keys("translation:*")
            hit_count_keys = await self.redis_client.keys("hit_count:*")
            
            # Calculate total hits
            total_hits = 0
            if hit_count_keys:
                hit_counts = await self.redis_client.mget(*hit_count_keys)
                total_hits = sum(int(count or 0) for count in hit_counts)
            
            return {
                "status": "healthy",
                "total_translation_keys": len(translation_keys),
                "total_hit_count_keys": len(hit_count_keys),
                "total_cache_hits": total_hits,
                "memory_usage_bytes": info.get("used_memory", 0),
                "memory_usage_human": info.get("used_memory_human", "0B"),
                "connected_clients": info.get("connected_clients", 0)
            }
        except Exception as e:
            logger.error("Failed to get cache stats", error=str(e))
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, str]:
        """Check cache service health."""
        if not self.redis_client:
            return {"status": "unhealthy", "error": "Redis client not initialized"}
        
        try:
            # Test basic operations
            test_key = "health_check"
            await self.redis_client.set(test_key, "ok", ex=10)
            value = await self.redis_client.get(test_key)
            await self.redis_client.delete(test_key)
            
            if value == "ok":
                return {"status": "healthy"}
            else:
                return {"status": "unhealthy", "error": "Redis operation test failed"}
        except Exception as e:
            logger.error("Cache health check failed", error=str(e))
            return {"status": "unhealthy", "error": str(e)}
    
    async def rate_limit_check(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> Dict[str, Any]:
        """Check rate limit for a given key."""
        if not self.redis_client:
            return {"allowed": True, "remaining": limit}
        
        try:
            current_count = await self.redis_client.incr(key)
            
            if current_count == 1:
                # First request in window, set expiration
                await self.redis_client.expire(key, window_seconds)
            
            remaining = max(0, limit - current_count)
            allowed = current_count <= limit
            
            return {
                "allowed": allowed,
                "remaining": remaining,
                "current_count": current_count,
                "limit": limit,
                "window_seconds": window_seconds
            }
        except Exception as e:
            logger.error("Rate limit check failed", key=key, error=str(e))
            # Default to allowing the request if Redis is down
            return {"allowed": True, "remaining": limit}


# Global cache service instance
cache_service = CacheService()
