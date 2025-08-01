"""
Statistics service for tracking API usage and metrics.
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..core.config import get_settings

# Mock logger
class MockLogger:
    def info(self, msg, **kwargs): pass
    def error(self, msg, **kwargs): pass
    def warning(self, msg, **kwargs): pass

logger = MockLogger()


@dataclass
class RequestMetric:
    """In-memory request metric."""
    request_id: str
    app_id: str
    source_language: str
    target_language: str
    input_text_length: int
    output_text_length: int
    input_tokens: int
    output_tokens: int
    response_time: float
    cache_hit: bool
    success: bool
    error_code: Optional[str]
    timestamp: datetime


class StatsService:
    """Statistics service for tracking API usage and performance metrics."""
    
    def __init__(self):
        self.settings = get_settings()
        self.start_time = time.time()
        
        # In-memory storage for demo purposes
        # In production, this should use a proper database
        self.request_metrics: List[RequestMetric] = []
        self.hourly_stats: Dict[str, Dict[str, Any]] = {}
        self.daily_stats: Dict[str, Dict[str, Any]] = {}
        
        # Performance counters
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.cache_hits = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_response_time = 0.0
    
    async def log_request(
        self,
        request_id: str,
        app_id: str,
        source_language: str,
        target_language: str,
        input_text_length: int,
        output_text_length: int,
        input_tokens: int,
        output_tokens: int,
        response_time: float,
        cache_hit: bool,
        success: bool,
        error_code: Optional[str] = None
    ) -> None:
        """Log a request metric."""
        try:
            # Create metric record
            metric = RequestMetric(
                request_id=request_id,
                app_id=app_id,
                source_language=source_language,
                target_language=target_language,
                input_text_length=input_text_length,
                output_text_length=output_text_length,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                response_time=response_time,
                cache_hit=cache_hit,
                success=success,
                error_code=error_code,
                timestamp=datetime.utcnow()
            )
            
            # Store metric
            self.request_metrics.append(metric)
            
            # Update counters
            self.total_requests += 1
            if success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
            
            if cache_hit:
                self.cache_hits += 1
            
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.total_response_time += response_time
            
            # Update hourly and daily stats
            await self._update_time_based_stats(metric)
            
            # Clean old metrics to prevent memory bloat
            await self._cleanup_old_metrics()
            
            logger.info(
                "Request metric logged",
                request_id=request_id,
                app_id=app_id,
                success=success,
                cache_hit=cache_hit,
                response_time=response_time
            )
            
        except Exception as e:
            logger.error("Failed to log request metric", error=str(e))
    
    async def get_statistics(
        self,
        app_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        try:
            # Filter metrics by criteria
            filtered_metrics = self._filter_metrics(app_id, start_time, end_time)
            
            if not filtered_metrics:
                return self._empty_stats()
            
            # Calculate statistics
            total = len(filtered_metrics)
            successful = sum(1 for m in filtered_metrics if m.success)
            failed = total - successful
            cache_hits = sum(1 for m in filtered_metrics if m.cache_hit)
            
            total_input_tokens = sum(m.input_tokens for m in filtered_metrics)
            total_output_tokens = sum(m.output_tokens for m in filtered_metrics)
            total_response_time = sum(m.response_time for m in filtered_metrics)
            
            # Calculate averages
            avg_response_time = total_response_time / total if total > 0 else 0
            avg_input_tokens = total_input_tokens / total if total > 0 else 0
            avg_output_tokens = total_output_tokens / total if total > 0 else 0
            success_rate = (successful / total * 100) if total > 0 else 0
            cache_hit_rate = (cache_hits / total * 100) if total > 0 else 0
            
            return {
                "total_requests": total,
                "successful_requests": successful,
                "failed_requests": failed,
                "success_rate": round(success_rate, 2),
                "average_response_time": round(avg_response_time, 3),
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "average_input_tokens": round(avg_input_tokens, 1),
                "average_output_tokens": round(avg_output_tokens, 1),
                "cache_hit_rate": round(cache_hit_rate, 2),
                "uptime": round(time.time() - self.start_time, 1),
                "language_pairs": self._get_language_pair_stats(filtered_metrics),
                "hourly_breakdown": self._get_hourly_breakdown(filtered_metrics),
                "error_breakdown": self._get_error_breakdown(filtered_metrics)
            }
            
        except Exception as e:
            logger.error("Failed to get statistics", error=str(e))
            return self._empty_stats()
    
    async def get_app_statistics(self, app_id: str) -> Dict[str, Any]:
        """Get statistics for a specific app."""
        return await self.get_statistics(app_id=app_id)
    
    async def get_health_metrics(self) -> Dict[str, Any]:
        """Get health and performance metrics."""
        try:
            recent_metrics = self._filter_metrics(
                start_time=datetime.utcnow() - timedelta(minutes=5)
            )
            
            # Calculate recent performance
            recent_total = len(recent_metrics)
            recent_successful = sum(1 for m in recent_metrics if m.success)
            recent_avg_response = (
                sum(m.response_time for m in recent_metrics) / recent_total
                if recent_total > 0 else 0
            )
            
            return {
                "uptime_seconds": round(time.time() - self.start_time, 1),
                "total_requests_lifetime": self.total_requests,
                "success_rate_lifetime": (
                    (self.successful_requests / self.total_requests * 100)
                    if self.total_requests > 0 else 0
                ),
                "recent_requests_5min": recent_total,
                "recent_success_rate_5min": (
                    (recent_successful / recent_total * 100)
                    if recent_total > 0 else 0
                ),
                "recent_avg_response_time_5min": round(recent_avg_response, 3),
                "cache_hit_rate_lifetime": (
                    (self.cache_hits / self.total_requests * 100)
                    if self.total_requests > 0 else 0
                ),
                "memory_metrics_count": len(self.request_metrics)
            }
            
        except Exception as e:
            logger.error("Failed to get health metrics", error=str(e))
            return {"error": str(e)}
    
    def _filter_metrics(
        self,
        app_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[RequestMetric]:
        """Filter metrics by criteria."""
        filtered = self.request_metrics
        
        if app_id:
            filtered = [m for m in filtered if m.app_id == app_id]
        
        if start_time:
            filtered = [m for m in filtered if m.timestamp >= start_time]
        
        if end_time:
            filtered = [m for m in filtered if m.timestamp <= end_time]
        
        return filtered
    
    def _get_language_pair_stats(self, metrics: List[RequestMetric]) -> Dict[str, int]:
        """Get language pair statistics."""
        pairs = {}
        for metric in metrics:
            pair = f"{metric.source_language}->{metric.target_language}"
            pairs[pair] = pairs.get(pair, 0) + 1
        return pairs
    
    def _get_hourly_breakdown(self, metrics: List[RequestMetric]) -> Dict[str, Dict[str, Any]]:
        """Get hourly breakdown of requests."""
        hourly = {}
        for metric in metrics:
            hour_key = metric.timestamp.strftime("%Y-%m-%d %H:00")
            if hour_key not in hourly:
                hourly[hour_key] = {"total": 0, "successful": 0, "failed": 0}
            
            hourly[hour_key]["total"] += 1
            if metric.success:
                hourly[hour_key]["successful"] += 1
            else:
                hourly[hour_key]["failed"] += 1
        
        return hourly
    
    def _get_error_breakdown(self, metrics: List[RequestMetric]) -> Dict[str, int]:
        """Get error code breakdown."""
        errors = {}
        for metric in metrics:
            if not metric.success and metric.error_code:
                errors[metric.error_code] = errors.get(metric.error_code, 0) + 1
        return errors
    
    async def _update_time_based_stats(self, metric: RequestMetric) -> None:
        """Update hourly and daily statistics."""
        hour_key = metric.timestamp.strftime("%Y-%m-%d %H")
        day_key = metric.timestamp.strftime("%Y-%m-%d")
        
        # Update hourly stats
        if hour_key not in self.hourly_stats:
            self.hourly_stats[hour_key] = {
                "requests": 0,
                "successful": 0,
                "failed": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "response_time": 0.0
            }
        
        self.hourly_stats[hour_key]["requests"] += 1
        if metric.success:
            self.hourly_stats[hour_key]["successful"] += 1
        else:
            self.hourly_stats[hour_key]["failed"] += 1
        self.hourly_stats[hour_key]["input_tokens"] += metric.input_tokens
        self.hourly_stats[hour_key]["output_tokens"] += metric.output_tokens
        self.hourly_stats[hour_key]["response_time"] += metric.response_time
        
        # Update daily stats (similar logic)
        if day_key not in self.daily_stats:
            self.daily_stats[day_key] = {
                "requests": 0,
                "successful": 0,
                "failed": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "response_time": 0.0
            }
        
        self.daily_stats[day_key]["requests"] += 1
        if metric.success:
            self.daily_stats[day_key]["successful"] += 1
        else:
            self.daily_stats[day_key]["failed"] += 1
        self.daily_stats[day_key]["input_tokens"] += metric.input_tokens
        self.daily_stats[day_key]["output_tokens"] += metric.output_tokens
        self.daily_stats[day_key]["response_time"] += metric.response_time
    
    async def _cleanup_old_metrics(self) -> None:
        """Clean up old metrics to prevent memory bloat."""
        # Keep only metrics from the last 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        self.request_metrics = [
            m for m in self.request_metrics
            if m.timestamp >= cutoff_time
        ]
        
        # Clean old hourly stats (keep 7 days)
        cutoff_hour = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d %H")
        self.hourly_stats = {
            k: v for k, v in self.hourly_stats.items()
            if k >= cutoff_hour
        }
        
        # Clean old daily stats (keep 30 days)
        cutoff_day = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        self.daily_stats = {
            k: v for k, v in self.daily_stats.items()
            if k >= cutoff_day
        }
    
    def _empty_stats(self) -> Dict[str, Any]:
        """Return empty statistics structure."""
        return {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "success_rate": 0,
            "average_response_time": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "average_input_tokens": 0,
            "average_output_tokens": 0,
            "cache_hit_rate": 0,
            "uptime": round(time.time() - self.start_time, 1),
            "language_pairs": {},
            "hourly_breakdown": {},
            "error_breakdown": {}
        }


# Global stats service instance
stats_service = StatsService()
