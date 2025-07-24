"""
Health check and system status routes.
"""

from fastapi import APIRouter
from typing import Dict, Any

from ...models.schemas import HealthCheckResponse
from ...services.translation_service import translation_service
from ...services.stats_service import stats_service
from ...services.cache_service import cache_service

# Mock logger
class MockLogger:
    def info(self, msg, **kwargs): pass
    def error(self, msg, **kwargs): pass

logger = MockLogger()

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """
    Comprehensive health check for all services.
    """
    from datetime import datetime
    from ...core.config import get_settings
    settings = get_settings()
    
    try:
        # Get health status from translation service
        health_data = await translation_service.health_check()
        
        return HealthCheckResponse(
            status=health_data["status"],
            timestamp=datetime.utcnow().isoformat(),
            version=settings.api.version,
            services=health_data["services"]
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        
        return HealthCheckResponse(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            version=settings.api.version,
            services={"error": str(e)}
        )


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with performance metrics.
    """
    try:
        # Get health from all services
        translation_health = await translation_service.health_check()
        
        async with cache_service:
            cache_stats = await cache_service.get_cache_stats()
            cache_health = await cache_service.health_check()
        
        health_metrics = await stats_service.get_health_metrics()
        
        return {
            "overall_status": translation_health["status"],
            "timestamp": translation_health["timestamp"],
            "services": {
                "translation": {
                    "status": translation_health["services"].get("translation", "unknown"),
                    "model_info": translation_health.get("model_info", {})
                },
                "ollama": {
                    "status": translation_health["services"].get("ollama", "unknown")
                },
                "cache": {
                    "status": cache_health["status"],
                    "stats": cache_stats
                },
                "statistics": {
                    "status": "healthy",
                    "metrics": health_metrics
                }
            }
        }
        
    except Exception as e:
        logger.error("Detailed health check failed", error=str(e))
        return {
            "overall_status": "unhealthy",
            "error": str(e)
        }


@router.get("/health/live")
async def liveness_probe() -> Dict[str, str]:
    """
    Simple liveness probe for orchestrators like Kubernetes.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe() -> Dict[str, Any]:
    """
    Readiness probe that checks if the service can handle requests.
    """
    try:
        # Quick check of critical services
        health_data = await translation_service.health_check()
        
        if health_data["status"] in ["healthy", "degraded"]:
            return {
                "status": "ready",
                "services_status": health_data["services"]
            }
        else:
            return {
                "status": "not_ready",
                "services_status": health_data["services"]
            }
            
    except Exception as e:
        logger.error("Readiness probe failed", error=str(e))
        return {
            "status": "not_ready",
            "error": str(e)
        }


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Get Prometheus-style metrics for monitoring.
    """
    try:
        # Get statistics from stats service
        stats = await stats_service.get_statistics()
        health_metrics = await stats_service.get_health_metrics()
        
        # Get cache stats
        async with cache_service:
            cache_stats = await cache_service.get_cache_stats()
        
        # Format metrics in a monitoring-friendly way
        metrics = {
            "translation_requests_total": stats["total_requests"],
            "translation_requests_successful_total": stats["successful_requests"],
            "translation_requests_failed_total": stats["failed_requests"],
            "translation_success_rate": stats["success_rate"] / 100,  # Convert to 0-1 scale
            "translation_response_time_avg_seconds": stats["average_response_time"],
            "translation_cache_hit_rate": stats["cache_hit_rate"] / 100,
            "translation_input_tokens_total": stats["total_input_tokens"],
            "translation_output_tokens_total": stats["total_output_tokens"],
            "translation_uptime_seconds": stats["uptime"],
            
            # Cache metrics
            "cache_keys_total": cache_stats.get("total_translation_keys", 0),
            "cache_hits_total": cache_stats.get("total_cache_hits", 0),
            "cache_memory_usage_bytes": cache_stats.get("memory_usage_bytes", 0),
            
            # Health metrics
            "service_uptime_seconds": health_metrics.get("uptime_seconds", 0),
            "recent_requests_5min": health_metrics.get("recent_requests_5min", 0),
            "recent_success_rate_5min": health_metrics.get("recent_success_rate_5min", 0) / 100,
            "recent_response_time_avg_5min_seconds": health_metrics.get("recent_avg_response_time_5min", 0)
        }
        
        return {
            "metrics": metrics,
            "timestamp": health_metrics.get("timestamp", ""),
            "format": "prometheus_compatible"
        }
        
    except Exception as e:
        logger.error("Metrics endpoint failed", error=str(e))
        return {
            "error": str(e),
            "metrics": {}
        }
