"""
Phase 4 Service Status API Routes
Provides health and status endpoints for the 4 main Phase 4 service components
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ...services.optimized_llm_service import optimized_llm_service
from ...services.performance_monitor import performance_monitor
from ...services.quality_monitor import quality_monitor
from ...services.connection_pool_manager import connection_pool_manager

router = APIRouter(prefix="/api", tags=["Phase 4 Status"])

@router.get("/llm/health")
async def get_llm_service_health():
    """Get health status of the Optimized LLM Service."""
    try:
        # Check if service is responsive
        start_time = time.time()
        
        # Test basic service functionality
        test_result = await optimized_llm_service.get_service_stats()
        response_time = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "service": "Optimized LLM Service",
            "timestamp": datetime.now().isoformat(),
            "response_time_ms": round(response_time, 2),
            "stats": test_result,
            "capabilities": {
                "model_optimization": True,
                "adaptive_routing": True,
                "quality_monitoring": True,
                "performance_tracking": True
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "Optimized LLM Service",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "details": "Service not responding or misconfigured"
            }
        )

@router.get("/performance/status")
async def get_performance_monitor_status():
    """Get status of the Performance Monitor service."""
    try:
        # Get current performance metrics
        metrics = performance_monitor.get_current_metrics()
        
        # Get system health indicators
        health_indicators = {
            "active_sessions": len(performance_monitor.active_sessions),
            "total_interactions": performance_monitor.get_total_interactions(),
            "average_response_time": performance_monitor.get_average_response_time(),
            "error_rate": performance_monitor.get_error_rate()
        }
        
        return {
            "status": "healthy",
            "service": "Performance Monitor",
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "health_indicators": health_indicators,
            "capabilities": {
                "real_time_monitoring": True,
                "metric_aggregation": True,
                "performance_analytics": True,
                "alerting": True
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "Performance Monitor",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "details": "Performance monitoring service not available"
            }
        )

@router.get("/quality/status")
async def get_quality_monitor_status():
    """Get status of the Quality Monitor service."""
    try:
        # Get quality assessment data
        quality_metrics = quality_monitor.get_quality_summary()
        
        # Get quality trends
        quality_health = {
            "current_quality_level": quality_monitor.get_current_quality_level().value,
            "quality_trend": quality_monitor.get_quality_trend(),
            "total_assessments": quality_monitor.get_total_assessments(),
            "quality_distribution": quality_monitor.get_quality_distribution()
        }
        
        return {
            "status": "healthy",
            "service": "Quality Monitor",
            "timestamp": datetime.now().isoformat(),
            "quality_metrics": quality_metrics,
            "quality_health": quality_health,
            "capabilities": {
                "quality_assessment": True,
                "trend_analysis": True,
                "quality_scoring": True,
                "adaptive_quality": True
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "Quality Monitor",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "details": "Quality monitoring service not available"
            }
        )

@router.get("/connections/status")
async def get_connection_pool_status():
    """Get status of the Connection Pool Manager."""
    try:
        # Get connection pool statistics
        pool_stats = connection_pool_manager.get_pool_statistics()
        
        # Get connection health
        connection_health = {
            "total_pools": connection_pool_manager.get_total_pools(),
            "active_connections": connection_pool_manager.get_active_connections(),
            "available_connections": connection_pool_manager.get_available_connections(),
            "connection_efficiency": connection_pool_manager.get_efficiency_ratio()
        }
        
        return {
            "status": "healthy",
            "service": "Connection Pool Manager",
            "timestamp": datetime.now().isoformat(),
            "pool_statistics": pool_stats,
            "connection_health": connection_health,
            "capabilities": {
                "connection_pooling": True,
                "load_balancing": True,
                "connection_optimization": True,
                "resource_management": True
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "Connection Pool Manager", 
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "details": "Connection pool management service not available"
            }
        )

@router.get("/phase4/overview")
async def get_phase4_overview():
    """Get overall status of all Phase 4 service components."""
    try:
        # Gather status from all components
        components = {}
        overall_healthy = True
        
        # Check each component
        component_checks = [
            ("llm", get_llm_service_health),
            ("performance", get_performance_monitor_status),
            ("quality", get_quality_monitor_status),
            ("connections", get_connection_pool_status)
        ]
        
        for component_name, check_func in component_checks:
            try:
                result = await check_func()
                if isinstance(result, JSONResponse):
                    components[component_name] = {
                        "status": "unhealthy",
                        "details": "Service check failed"
                    }
                    overall_healthy = False
                else:
                    components[component_name] = {
                        "status": result.get("status", "unknown"),
                        "service": result.get("service", "Unknown"),
                        "capabilities": result.get("capabilities", {})
                    }
                    if result.get("status") != "healthy":
                        overall_healthy = False
            except Exception as e:
                components[component_name] = {
                    "status": "error",
                    "error": str(e)
                }
                overall_healthy = False
        
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "phase": "Phase 4",
            "timestamp": datetime.now().isoformat(),
            "overall_health": overall_healthy,
            "components": components,
            "summary": {
                "total_components": len(components),
                "healthy_components": sum(1 for c in components.values() if c.get("status") == "healthy"),
                "degraded_components": sum(1 for c in components.values() if c.get("status") != "healthy")
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "phase": "Phase 4",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "details": "Failed to gather Phase 4 component status"
            }
        )
