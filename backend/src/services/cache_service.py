"""
Intelligent Caching Service for Perplexity Intelligence Hub
Provides Redis-like caching functionality with fallback to in-memory caching
"""

import json
import time
import hashlib
import asyncio
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from collections import defaultdict, OrderedDict
import logging

# Setup logging
logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """Cache strategies for different types of data"""
    IMMEDIATE = "immediate"      # Cache immediately, short TTL
    BATCH = "batch"             # Batch requests, medium TTL  
    LONG_TERM = "long_term"     # Long TTL for stable data
    SESSION = "session"         # Session-based TTL
    TREND = "trend"            # Trend analysis data

@dataclass
class CacheConfig:
    """Configuration for cache behavior"""
    default_ttl: int = 3600  # 1 hour
    max_size: int = 10000    # Maximum cache entries
    batch_window: float = 0.5  # Batch window in seconds
    strategies: Dict[str, Dict] = None
    
    def __post_init__(self):
        if self.strategies is None:
            self.strategies = {
                CacheStrategy.IMMEDIATE.value: {"ttl": 300, "batch": False},      # 5 minutes
                CacheStrategy.BATCH.value: {"ttl": 1800, "batch": True},         # 30 minutes  
                CacheStrategy.LONG_TERM.value: {"ttl": 86400, "batch": False},   # 24 hours
                CacheStrategy.SESSION.value: {"ttl": 7200, "batch": False},      # 2 hours
                CacheStrategy.TREND.value: {"ttl": 43200, "batch": False},       # 12 hours
            }

@dataclass
class CacheEntry:
    """Represents a cached item"""
    key: str
    value: Any
    created_at: float
    ttl: int
    access_count: int = 0
    last_accessed: float = None
    strategy: str = CacheStrategy.IMMEDIATE.value
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() > (self.created_at + self.ttl)
    
    @property
    def age_seconds(self) -> float:
        """Get age of cache entry in seconds"""
        return time.time() - self.created_at
    
    def touch(self):
        """Update last accessed time and increment access count"""
        self.last_accessed = time.time()
        self.access_count += 1

class RequestBatcher:
    """Batches similar requests to minimize API calls"""
    
    def __init__(self, window_size: float = 0.5):
        self.window_size = window_size
        self.pending_requests: Dict[str, List] = defaultdict(list)
        self.batch_timers: Dict[str, threading.Timer] = {}
        self.lock = threading.Lock()
    
    async def add_request(self, key: str, callback, *args, **kwargs) -> Any:
        """Add a request to the batch"""
        future = asyncio.Future()
        
        with self.lock:
            self.pending_requests[key].append((future, callback, args, kwargs))
            
            # Start batch timer if not already running
            if key not in self.batch_timers:
                timer = threading.Timer(self.window_size, self._execute_batch, args=[key])
                self.batch_timers[key] = timer
                timer.start()
        
        return await future
    
    def _execute_batch(self, key: str):
        """Execute all batched requests for a key"""
        with self.lock:
            requests = self.pending_requests.pop(key, [])
            self.batch_timers.pop(key, None)
        
        if not requests:
            return
        
        try:
            # Execute the first request (others are duplicates)
            future, callback, args, kwargs = requests[0]
            result = callback(*args, **kwargs)
            
            # Set result for all waiting futures
            for req_future, _, _, _ in requests:
                if not req_future.done():
                    req_future.set_result(result)
                    
        except Exception as e:
            # Set exception for all waiting futures
            for req_future, _, _, _ in requests:
                if not req_future.done():
                    req_future.set_exception(e)

class IntelligentCache:
    """Main caching service with intelligent strategies"""
    
    def __init__(self, config: CacheConfig = None, use_redis: bool = False):
        self.config = config or CacheConfig()
        self.use_redis = use_redis
        self._redis_client = None
        
        # In-memory cache as fallback
        self._memory_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._cache_lock = threading.RLock()
        
        # Request batching
        self.batcher = RequestBatcher(self.config.batch_window)
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "api_calls_saved": 0,
            "batch_requests": 0
        }
        
        # Initialize Redis if requested
        if use_redis:
            self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis client with fallback"""
        try:
            import redis
            self._redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            self._redis_client.ping()
            logger.info("Redis cache initialized successfully")
            
        except (ImportError, Exception) as e:
            logger.warning(f"Redis not available, using in-memory cache: {e}")
            self._redis_client = None
            self.use_redis = False
    
    def _generate_key(self, prefix: str, params: Dict) -> str:
        """Generate cache key from parameters"""
        # Sort parameters for consistent keys
        sorted_params = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:12]
        return f"{prefix}:{param_hash}"
    
    def _get_strategy_config(self, strategy: CacheStrategy) -> Dict:
        """Get configuration for a caching strategy"""
        return self.config.strategies.get(strategy.value, 
                                         self.config.strategies[CacheStrategy.IMMEDIATE.value])
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if self.use_redis and self._redis_client:
            return await self._get_redis(key)
        else:
            return self._get_memory(key)
    
    async def set(self, key: str, value: Any, ttl: int = None, 
                  strategy: CacheStrategy = CacheStrategy.IMMEDIATE) -> bool:
        """Set value in cache"""
        if ttl is None:
            strategy_config = self._get_strategy_config(strategy)
            ttl = strategy_config["ttl"]
        
        if self.use_redis and self._redis_client:
            return await self._set_redis(key, value, ttl, strategy)
        else:
            return self._set_memory(key, value, ttl, strategy)
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if self.use_redis and self._redis_client:
            return await self._delete_redis(key)
        else:
            return self._delete_memory(key)
    
    async def get_or_compute(self, key: str, compute_func, *args, 
                           strategy: CacheStrategy = CacheStrategy.IMMEDIATE,
                           **kwargs) -> Any:
        """Get from cache or compute and cache the result"""
        
        # Check cache first
        cached_value = await self.get(key)
        if cached_value is not None:
            self.stats["hits"] += 1
            return cached_value
        
        self.stats["misses"] += 1
        
        # Determine if we should batch this request
        strategy_config = self._get_strategy_config(strategy)
        
        if strategy_config.get("batch", False):
            # Use request batching
            self.stats["batch_requests"] += 1
            result = await self.batcher.add_request(key, compute_func, *args, **kwargs)
        else:
            # Direct computation
            if asyncio.iscoroutinefunction(compute_func):
                result = await compute_func(*args, **kwargs)
            else:
                result = compute_func(*args, **kwargs)
        
        # Cache the result
        await self.set(key, result, strategy=strategy)
        self.stats["api_calls_saved"] += 1
        
        return result
    
    def _get_memory(self, key: str) -> Optional[Any]:
        """Get from in-memory cache"""
        with self._cache_lock:
            if key in self._memory_cache:
                entry = self._memory_cache[key]
                
                if entry.is_expired:
                    del self._memory_cache[key]
                    return None
                
                entry.touch()
                # Move to end (LRU)
                self._memory_cache.move_to_end(key)
                return entry.value
            
            return None
    
    def _set_memory(self, key: str, value: Any, ttl: int, strategy: CacheStrategy) -> bool:
        """Set in in-memory cache"""
        with self._cache_lock:
            # Evict expired entries
            self._evict_expired()
            
            # Evict LRU entries if at capacity
            while len(self._memory_cache) >= self.config.max_size:
                oldest_key = next(iter(self._memory_cache))
                del self._memory_cache[oldest_key]
                self.stats["evictions"] += 1
            
            # Add new entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                ttl=ttl,
                strategy=strategy.value
            )
            
            self._memory_cache[key] = entry
            return True
    
    def _delete_memory(self, key: str) -> bool:
        """Delete from in-memory cache"""
        with self._cache_lock:
            if key in self._memory_cache:
                del self._memory_cache[key]
                return True
            return False
    
    def _evict_expired(self):
        """Remove expired entries from memory cache"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._memory_cache.items()
            if current_time > (entry.created_at + entry.ttl)
        ]
        
        for key in expired_keys:
            del self._memory_cache[key]
    
    async def _get_redis(self, key: str) -> Optional[Any]:
        """Get from Redis cache"""
        try:
            value = self._redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return self._get_memory(key)
    
    async def _set_redis(self, key: str, value: Any, ttl: int, strategy: CacheStrategy) -> bool:
        """Set in Redis cache"""
        try:
            serialized = json.dumps(value, default=str)
            return self._redis_client.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return self._set_memory(key, value, ttl, strategy)
    
    async def _delete_redis(self, key: str) -> bool:
        """Delete from Redis cache"""
        try:
            return self._redis_client.delete(key) > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return self._delete_memory(key)
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
            "cache_size": len(self._memory_cache),
            "redis_available": self.use_redis and self._redis_client is not None
        }
    
    def clear(self):
        """Clear all cached data"""
        with self._cache_lock:
            self._memory_cache.clear()
        
        if self.use_redis and self._redis_client:
            try:
                self._redis_client.flushdb()
            except Exception as e:
                logger.error(f"Redis clear error: {e}")

# Global cache instance
_cache_instance: Optional[IntelligentCache] = None

def get_cache() -> IntelligentCache:
    """Get the global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = IntelligentCache(use_redis=True)
    return _cache_instance

def initialize_cache(config: CacheConfig = None, use_redis: bool = True) -> IntelligentCache:
    """Initialize the global cache instance"""
    global _cache_instance
    _cache_instance = IntelligentCache(config, use_redis)
    return _cache_instance

# Convenience decorators
def cached(ttl: int = 3600, strategy: CacheStrategy = CacheStrategy.IMMEDIATE):
    """Decorator for caching function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Generate cache key
            key_params = {"args": args, "kwargs": kwargs}
            key = cache._generate_key(f"func:{func.__name__}", key_params)
            
            return await cache.get_or_compute(key, func, *args, strategy=strategy, **kwargs)
        
        return wrapper
    return decorator