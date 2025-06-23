"""
Simple in-memory caching service for Fast-Fail assessments
"""
import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CachingService:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache, return None if not found or expired"""
        try:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            if time.time() > entry['expires_at']:
                del self.cache[key]
                return None
            
            return entry['value']
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        try:
            if ttl is None:
                ttl = self.default_ttl
            
            self.cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl,
                'created_at': time.time()
            }
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if key in self.cache:
                del self.cache[key]
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries"""
        try:
            self.cache.clear()
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            current_time = time.time()
            active_entries = 0
            expired_entries = 0
            
            for entry in self.cache.values():
                if current_time > entry['expires_at']:
                    expired_entries += 1
                else:
                    active_entries += 1
            
            return {
                'total_entries': len(self.cache),
                'active_entries': active_entries,
                'expired_entries': expired_entries,
                'cache_size_bytes': len(str(self.cache))
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {'error': str(e)}

# Global cache instance
_cache_instance = None

def get_caching_service() -> CachingService:
    """Get the global caching service instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CachingService()
    return _cache_instance