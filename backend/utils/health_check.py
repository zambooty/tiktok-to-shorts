from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from database import get_db
import redis
import os
from typing import Dict, Any
import psutil
import shutil
from utils.logging_config import CustomLogger, api_logger

router = APIRouter()
logger = CustomLogger(api_logger, {'component': 'health_check'})

class HealthChecker:
    def __init__(self, redis_url: str = "redis://redis:6379/0"):
        self.redis_url = redis_url
        self.required_dirs = ['uploads', 'processed', 'logs']
        self.min_disk_space = 1024 * 1024 * 1024  # 1GB

    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            db = next(get_db())
            db.execute(text('SELECT 1'))
            return {
                "status": "healthy",
                "message": "Database connection successful"
            }
        except Exception as e:
            logger.error("Database health check failed", exc_info=e)
            return {
                "status": "unhealthy",
                "message": str(e)
            }

    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity."""
        try:
            redis_client = redis.from_url(self.redis_url)
            redis_client.ping()
            return {
                "status": "healthy",
                "message": "Redis connection successful"
            }
        except Exception as e:
            logger.error("Redis health check failed", exc_info=e)
            return {
                "status": "unhealthy",
                "message": str(e)
            }

    async def check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space."""
        try:
            disk_usage = shutil.disk_usage('.')
            free_space = disk_usage.free
            
            if free_space < self.min_disk_space:
                return {
                    "status": "warning",
                    "message": f"Low disk space: {free_space // (1024*1024)}MB remaining"
                }
            
            return {
                "status": "healthy",
                "message": f"Sufficient disk space: {free_space // (1024*1024)}MB free"
            }
        except Exception as e:
            logger.error("Disk space check failed", exc_info=e)
            return {
                "status": "unhealthy",
                "message": str(e)
            }

    async def check_directories(self) -> Dict[str, Any]:
        """Check required directories exist and are writable."""
        try:
            missing_dirs = []
            unwritable_dirs = []
            
            for dir_name in self.required_dirs:
                if not os.path.exists(dir_name):
                    missing_dirs.append(dir_name)
                elif not os.access(dir_name, os.W_OK):
                    unwritable_dirs.append(dir_name)
            
            if missing_dirs or unwritable_dirs:
                return {
                    "status": "warning",
                    "message": {
                        "missing_directories": missing_dirs,
                        "unwritable_directories": unwritable_dirs
                    }
                }
            
            return {
                "status": "healthy",
                "message": "All required directories are available and writable"
            }
        except Exception as e:
            logger.error("Directory check failed", exc_info=e)
            return {
                "status": "unhealthy",
                "message": str(e)
            }

    async def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            status = "healthy"
            warnings = []
            
            if cpu_percent > 80:
                status = "warning"
                warnings.append(f"High CPU usage: {cpu_percent}%")
            
            if memory.percent > 80:
                status = "warning"
                warnings.append(f"High memory usage: {memory.percent}%")
            
            return {
                "status": status,
                "message": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "warnings": warnings
                }
            }
        except Exception as e:
            logger.error("System resource check failed", exc_info=e)
            return {
                "status": "unhealthy",
                "message": str(e)
            }

@router.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    checker = HealthChecker()
    
    checks = {
        "database": await checker.check_database(),
        "redis": await checker.check_redis(),
        "disk_space": await checker.check_disk_space(),
        "directories": await checker.check_directories(),
        "system_resources": await checker.check_system_resources()
    }
    
    # Determine overall status
    overall_status = "healthy"
    for check in checks.values():
        if check["status"] == "unhealthy":
            overall_status = "unhealthy"
            break
        elif check["status"] == "warning" and overall_status != "unhealthy":
            overall_status = "warning"
    
    response = {
        "status": overall_status,
        "checks": checks,
        "timestamp": psutil.time.time()
    }
    
    if overall_status == "unhealthy":
        logger.error("Health check failed", health_status=response)
        raise HTTPException(status_code=503, detail=response)
    
    return response