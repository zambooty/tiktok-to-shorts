import os
import psutil
import shutil
from typing import Dict, Any
from sqlalchemy import text
from redis import Redis
from datetime import datetime

class HealthCheck:
    def __init__(self, db_session, redis_client: Redis):
        self.db_session = db_session
        self.redis_client = redis_client

    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = datetime.now()
            await self.db_session.execute(text('SELECT 1'))
            response_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'status': 'healthy',
                'response_time': response_time,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance"""
        try:
            start_time = datetime.now()
            self.redis_client.ping()
            response_time = (datetime.now() - start_time).total_seconds()
            
            info = self.redis_client.info()
            return {
                'status': 'healthy',
                'response_time': response_time,
                'used_memory': info['used_memory_human'],
                'connected_clients': info['connected_clients'],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def check_storage(self) -> Dict[str, Any]:
        """Check storage space in upload and processed directories"""
        try:
            upload_dir = os.getenv('UPLOAD_DIR', './uploads')
            processed_dir = os.getenv('PROCESSED_DIR', './processed')
            
            upload_usage = shutil.disk_usage(upload_dir)
            processed_usage = shutil.disk_usage(processed_dir)
            
            return {
                'status': 'healthy',
                'upload_dir': {
                    'total': upload_usage.total,
                    'used': upload_usage.used,
                    'free': upload_usage.free,
                    'percent_used': (upload_usage.used / upload_usage.total) * 100
                },
                'processed_dir': {
                    'total': processed_usage.total,
                    'used': processed_usage.used,
                    'free': processed_usage.free,
                    'percent_used': (processed_usage.used / processed_usage.total) * 100
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def check_system_resources(self) -> Dict[str, Any]:
        """Check system CPU, memory, and disk usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            return {
                'status': 'healthy',
                'cpu': {
                    'percent_used': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent_used': memory.percent
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def check_celery(self) -> Dict[str, Any]:
        """Check Celery worker status"""
        try:
            # Use Redis to check if Celery workers are responding
            workers = self.redis_client.client_list()
            worker_count = len([c for c in workers if b'celery' in c.get(b'name', b'')])
            
            return {
                'status': 'healthy' if worker_count > 0 else 'degraded',
                'active_workers': worker_count,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def get_full_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of all components"""
        db_status = await self.check_database()
        redis_status = self.check_redis()
        storage_status = self.check_storage()
        system_status = self.check_system_resources()
        celery_status = self.check_celery()
        
        overall_status = 'healthy'
        if any(s['status'] == 'unhealthy' for s in [
            db_status, redis_status, storage_status, system_status, celery_status
        ]):
            overall_status = 'unhealthy'
        elif any(s['status'] == 'degraded' for s in [
            db_status, redis_status, storage_status, system_status, celery_status
        ]):
            overall_status = 'degraded'
        
        return {
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'components': {
                'database': db_status,
                'redis': redis_status,
                'storage': storage_status,
                'system': system_status,
                'celery': celery_status
            }
        }