from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from redis import Redis
import json
from statistics import mean, median

class MetricsCollector:
    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client
        self.metrics_key_prefix = "metrics:"
        self.retention_days = 30

    def record_processing_time(self, video_id: str, duration: float) -> None:
        """Record video processing duration"""
        key = f"{self.metrics_key_prefix}processing_times"
        timestamp = datetime.now().timestamp()
        self.redis_client.zadd(key, {f"{video_id}:{duration}": timestamp})
        # Clean up old entries
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        self.redis_client.zremrangebyscore(key, "-inf", cutoff.timestamp())

    def record_upload_size(self, video_id: str, size_bytes: int) -> None:
        """Record uploaded video size"""
        key = f"{self.metrics_key_prefix}upload_sizes"
        timestamp = datetime.now().timestamp()
        self.redis_client.zadd(key, {f"{video_id}:{size_bytes}": timestamp})
        self.redis_client.zremrangebyscore(
            key,
            "-inf",
            (datetime.now() - timedelta(days=self.retention_days)).timestamp()
        )

    def record_processing_outcome(self, video_id: str, success: bool) -> None:
        """Record processing success/failure"""
        date_key = datetime.now().strftime("%Y-%m-%d")
        key = f"{self.metrics_key_prefix}outcomes:{date_key}"
        self.redis_client.hincrby(key, "success" if success else "failure", 1)
        self.redis_client.expire(key, timedelta(days=self.retention_days))

    def record_youtube_upload_time(self, video_id: str, duration: float) -> None:
        """Record YouTube upload duration"""
        key = f"{self.metrics_key_prefix}youtube_upload_times"
        timestamp = datetime.now().timestamp()
        self.redis_client.zadd(key, {f"{video_id}:{duration}": timestamp})
        self.redis_client.zremrangebyscore(
            key,
            "-inf",
            (datetime.now() - timedelta(days=self.retention_days)).timestamp()
        )

    def record_api_latency(self, endpoint: str, duration: float) -> None:
        """Record API endpoint latency"""
        key = f"{self.metrics_key_prefix}api_latency:{endpoint}"
        timestamp = datetime.now().timestamp()
        self.redis_client.zadd(key, {f"{timestamp}:{duration}": timestamp})
        self.redis_client.zremrangebyscore(
            key,
            "-inf",
            (datetime.now() - timedelta(days=self.retention_days)).timestamp()
        )

    def get_processing_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get video processing metrics for the specified period"""
        cutoff = datetime.now() - timedelta(days=days)
        processing_times_key = f"{self.metrics_key_prefix}processing_times"
        
        # Get recent processing times
        times = []
        for item in self.redis_client.zrangebyscore(
            processing_times_key,
            cutoff.timestamp(),
            "+inf"
        ):
            _, duration = item.decode().split(":")
            times.append(float(duration))

        # Calculate success rate
        success_count = 0
        failure_count = 0
        for i in range(days):
            date_key = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            outcomes = self.redis_client.hgetall(f"{self.metrics_key_prefix}outcomes:{date_key}")
            success_count += int(outcomes.get(b"success", 0))
            failure_count += int(outcomes.get(b"failure", 0))

        total_count = success_count + failure_count

        return {
            "total_videos_processed": total_count,
            "success_rate": (success_count / total_count * 100) if total_count > 0 else 0,
            "average_processing_time": mean(times) if times else 0,
            "median_processing_time": median(times) if times else 0,
            "min_processing_time": min(times) if times else 0,
            "max_processing_time": max(times) if times else 0,
            "processing_time_samples": len(times)
        }

    def get_api_metrics(self, days: int = 7) -> Dict[str, Dict[str, float]]:
        """Get API performance metrics for the specified period"""
        cutoff = datetime.now() - timedelta(days=days)
        metrics = {}

        # Get all API latency keys
        keys = self.redis_client.keys(f"{self.metrics_key_prefix}api_latency:*")
        for key in keys:
            endpoint = key.decode().split(":")[-1]
            latencies = []
            
            # Get latencies for this endpoint
            for item in self.redis_client.zrangebyscore(
                key,
                cutoff.timestamp(),
                "+inf"
            ):
                _, duration = item.decode().split(":")
                latencies.append(float(duration))

            if latencies:
                metrics[endpoint] = {
                    "average_latency": mean(latencies),
                    "median_latency": median(latencies),
                    "p95_latency": sorted(latencies)[int(len(latencies) * 0.95)],
                    "min_latency": min(latencies),
                    "max_latency": max(latencies),
                    "sample_count": len(latencies)
                }

        return metrics

    def get_storage_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get storage usage metrics"""
        cutoff = datetime.now() - timedelta(days=days)
        sizes = []
        
        # Get upload sizes for the period
        upload_sizes_key = f"{self.metrics_key_prefix}upload_sizes"
        for item in self.redis_client.zrangebyscore(
            upload_sizes_key,
            cutoff.timestamp(),
            "+inf"
        ):
            _, size = item.decode().split(":")
            sizes.append(int(size))

        return {
            "total_uploads": len(sizes),
            "total_storage_used": sum(sizes),
            "average_file_size": mean(sizes) if sizes else 0,
            "median_file_size": median(sizes) if sizes else 0,
            "max_file_size": max(sizes) if sizes else 0,
            "min_file_size": min(sizes) if sizes else 0
        }

    async def collect_daily_metrics(self) -> Dict[str, Any]:
        """Collect all metrics for daily report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "processing_metrics": self.get_processing_metrics(days=1),
            "api_metrics": self.get_api_metrics(days=1),
            "storage_metrics": self.get_storage_metrics(days=1)
        }