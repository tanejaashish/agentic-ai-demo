"""
Cache Service for Redis integration
Handles caching and session management
"""

import asyncio
import json
import redis.asyncio as redis
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)

class CacheService:
    """
    Service for managing cache using Redis
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        default_ttl: int = 3600
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.default_ttl = default_ttl
        self.client = None
        
        logger.info(f"CacheService initialized with Redis at {host}:{port}")
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True
            )
            # Test connection
            await self.client.ping()
            logger.info("Connected to Redis successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # Create a dummy cache for demo if Redis is unavailable
            self.client = DummyCache()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.client:
            await self.connect()
        
        try:
            value = await self.client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        if not self.client:
            await self.connect()
        
        try:
            # Serialize value if needed
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            # Set with TTL
            ttl = ttl or self.default_ttl
            await self.client.setex(key, ttl, value)
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.client:
            await self.connect()
        
        try:
            result = await self.client.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.client:
            await self.connect()
        
        try:
            return await self.client.exists(key) > 0
            
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    async def get_or_set(
        self,
        key: str,
        factory_func: callable,
        ttl: Optional[int] = None
    ) -> Any:
        """Get from cache or compute and set"""
        value = await self.get(key)
        if value is None:
            value = await factory_func()
            await self.set(key, value, ttl)
        return value
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter"""
        if not self.client:
            await self.connect()
        
        try:
            return await self.client.incrby(key, amount)
            
        except Exception as e:
            logger.error(f"Cache increment error: {e}")
            return 0
    
    async def get_keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        if not self.client:
            await self.connect()
        
        try:
            if hasattr(self.client, 'keys'):
                return await self.client.keys(pattern)
            return []
            
        except Exception as e:
            logger.error(f"Cache get_keys error: {e}")
            return []
    
    async def flush(self):
        """Flush all keys in current database"""
        if not self.client:
            await self.connect()
        
        try:
            await self.client.flushdb()
            logger.info("Cache flushed")
            
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
    
    async def close(self):
        """Close Redis connection"""
        if self.client and hasattr(self.client, 'close'):
            await self.client.close()
            logger.info("CacheService closed")
    
    def generate_key(self, *args) -> str:
        """Generate a cache key from arguments"""
        key_str = ":".join(str(arg) for arg in args)
        return hashlib.md5(key_str.encode()).hexdigest()


class DummyCache:
    """
    In-memory cache fallback when Redis is unavailable
    """
    
    def __init__(self):
        self.cache = {}
        self.ttls = {}
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if key in self.cache:
            # Check TTL
            if key in self.ttls and datetime.now() > self.ttls[key]:
                del self.cache[key]
                del self.ttls[key]
                return None
            return self.cache[key]
        return None
    
    async def setex(self, key: str, ttl: int, value: str) -> bool:
        """Set value with TTL"""
        self.cache[key] = value
        self.ttls[key] = datetime.now() + timedelta(seconds=ttl)
        return True
    
    async def delete(self, key: str) -> int:
        """Delete key"""
        if key in self.cache:
            del self.cache[key]
            if key in self.ttls:
                del self.ttls[key]
            return 1
        return 0
    
    async def exists(self, key: str) -> int:
        """Check if key exists"""
        return 1 if key in self.cache else 0
    
    async def incrby(self, key: str, amount: int) -> int:
        """Increment counter"""
        if key not in self.cache:
            self.cache[key] = "0"
        current = int(self.cache[key])
        new_value = current + amount
        self.cache[key] = str(new_value)
        return new_value
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        if pattern == "*":
            return list(self.cache.keys())
        # Simple pattern matching for demo
        return [k for k in self.cache.keys() if pattern.replace("*", "") in k]
    
    async def flushdb(self):
        """Clear cache"""
        self.cache.clear()
        self.ttls.clear()
    
    async def ping(self) -> bool:
        """Health check"""
        return True
    
    async def close(self):
        """Close (no-op for dummy cache)"""
        pass