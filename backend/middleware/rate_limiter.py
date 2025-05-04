from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import time
import redis
from utils.logging_config import CustomLogger, api_logger

logger = CustomLogger(api_logger, {'component': 'rate_limiter'})

class RateLimiter:
    def __init__(self, redis_url: str = "redis://redis:6379/0"):
        self.redis = redis.from_url(redis_url)
        self.window_size = 60  # 1 minute
        self.max_requests = {
            "upload": 10,      # 10 uploads per minute
            "process": 20,     # 20 processing requests per minute
            "default": 100     # 100 requests per minute for other endpoints
        }

    async def __call__(self, request: Request):
        client_ip = request.client.host
        path = request.url.path
        current_time = int(time.time())

        # Determine rate limit based on endpoint
        if "upload" in path:
            endpoint_type = "upload"
        elif "process" in path:
            endpoint_type = "process"
        else:
            endpoint_type = "default"

        max_requests = self.max_requests[endpoint_type]

        try:
            # Create a sliding window in Redis
            key = f"rate_limit:{client_ip}:{endpoint_type}:{current_time // self.window_size}"
            
            # Increment request count
            request_count = self.redis.incr(key)
            
            # Set expiry if this is the first request in the window
            if request_count == 1:
                self.redis.expire(key, self.window_size)
            
            # Check if rate limit exceeded
            if request_count > max_requests:
                logger.warning(
                    "Rate limit exceeded",
                    client_ip=client_ip,
                    endpoint_type=endpoint_type,
                    request_count=request_count
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Too many requests. Please try again later.",
                        "retry_after": self.window_size
                    }
                )

            # Log request
            logger.info(
                "Request processed",
                client_ip=client_ip,
                endpoint_type=endpoint_type,
                request_count=request_count
            )

        except redis.RedisError as e:
            logger.error(
                "Redis error in rate limiter",
                exc_info=e,
                client_ip=client_ip,
                endpoint_type=endpoint_type
            )
            # Allow request through if Redis fails
            return None

        return None

class ConcurrencyLimiter:
    def __init__(self, redis_url: str = "redis://redis:6379/0"):
        self.redis = redis.from_url(redis_url)
        self.max_concurrent = {
            "upload": 5,      # 5 concurrent uploads
            "process": 10     # 10 concurrent processing tasks
        }

    async def acquire_lock(self, key: str, limit: int) -> bool:
        """Try to acquire a processing slot."""
        try:
            current = int(self.redis.get(key) or 0)
            if current >= limit:
                return False
            
            self.redis.incr(key)
            return True
        except redis.RedisError as e:
            logger.error("Redis error acquiring lock", exc_info=e, key=key)
            return True  # Allow operation if Redis fails

    async def release_lock(self, key: str):
        """Release a processing slot."""
        try:
            current = int(self.redis.get(key) or 1)
            if current > 0:
                self.redis.decr(key)
        except redis.RedisError as e:
            logger.error("Redis error releasing lock", exc_info=e, key=key)

    async def __call__(self, request: Request):
        path = request.url.path
        
        # Determine concurrency limit based on endpoint
        if "upload" in path:
            operation = "upload"
        elif "process" in path:
            operation = "process"
        else:
            return None

        limit = self.max_concurrent.get(operation)
        if not limit:
            return None

        key = f"concurrent:{operation}"
        if not await self.acquire_lock(key, limit):
            logger.warning(
                "Concurrency limit reached",
                operation=operation,
                limit=limit
            )
            return JSONResponse(
                status_code=503,
                content={
                    "detail": f"Server is busy. Maximum concurrent {operation} operations reached."
                }
            )

        # Add cleanup to response handlers
        response = await request.call_next(request)
        await self.release_lock(key)
        return response