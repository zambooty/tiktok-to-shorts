from typing import Any, Optional
import json
from redis import Redis
from datetime import timedelta
import os
from functools import wraps

redis_client = Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

class Cache:
    @staticmethod
    def set(key: str, value: Any, expire_in_seconds: int = 3600) -> bool:
        """Set a cache value with expiration"""
        try:
            return redis_client.setex(
                key,
                timedelta(seconds=expire_in_seconds),
                json.dumps(value)
            )
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get a cached value"""
        try:
            value = redis_client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    @staticmethod
    def delete(key: str) -> bool:
        """Delete a cached value"""
        try:
            return redis_client.delete(key) > 0
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

def cached(expire_in_seconds: int = 3600):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create a cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get cached result
            cached_result = Cache.get(key)
            if cached_result is not None:
                return cached_result
            
            # Get fresh result and cache it
            result = await func(*args, **kwargs)
            Cache.set(key, result, expire_in_seconds)
            return result
        return wrapper
    return decorator

class RateLimiter:
    @staticmethod
    def check_rate_limit(key: str, max_requests: int, period: int) -> bool:
        """Check if request is within rate limit
        
        Args:
            key: Unique identifier (e.g., user_id or IP)
            max_requests: Maximum number of requests allowed
            period: Time period in seconds
        """
        try:
            pipe = redis_client.pipeline()
            current = pipe.get(f"ratelimit:{key}")
            pipe.incr(f"ratelimit:{key}")
            pipe.expire(f"ratelimit:{key}", period)
            results = pipe.execute()
            
            # First request or expired key
            if results[0] is None:
                return True
            
            # Check if within limit
            return int(results[0]) <= max_requests
        except Exception as e:
            print(f"Rate limit error: {e}")
            return True  # Allow request on error

    @staticmethod
    def reset_rate_limit(key: str) -> bool:
        """Reset rate limit counter for a key"""
        try:
            return redis_client.delete(f"ratelimit:{key}") > 0
        except Exception as e:
            print(f"Rate limit reset error: {e}")
            return False