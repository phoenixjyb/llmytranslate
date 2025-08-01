"""
Admin routes for managing API keys and viewing statistics.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ...models.schemas import StatisticsResponse, APIKeyInfo
from ...services.stats_service import stats_service
from ...services.auth_service import auth_service
from ...services.cache_service import cache_service

# Mock logger
class MockLogger:
    def info(self, msg, **kwargs): pass
    def error(self, msg, **kwargs): pass

logger = MockLogger()

router = APIRouter()


# Simple admin authentication (in production, use proper auth)
async def verify_admin_access():
    """Simple admin verification - replace with proper auth in production."""
    # For demo purposes, no authentication required
    # In production, implement proper admin authentication
    return True


@router.get("/stats", response_model=StatisticsResponse, dependencies=[Depends(verify_admin_access)])
async def get_statistics(
    app_id: Optional[str] = Query(None, description="Filter by specific app ID"),
    hours: Optional[int] = Query(24, description="Number of hours to include in statistics")
) -> StatisticsResponse:
    """
    Get comprehensive service statistics.
    """
    try:
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours) if hours else None
        
        # Get statistics
        stats = await stats_service.get_statistics(
            app_id=app_id,
            start_time=start_time,
            end_time=end_time
        )
        
        return StatisticsResponse(**stats)
        
    except Exception as e:
        logger.error("Failed to get statistics", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to retrieve statistics"}
        )


@router.get("/stats/app/{app_id}", dependencies=[Depends(verify_admin_access)])
async def get_app_statistics(app_id: str) -> Dict[str, Any]:
    """
    Get statistics for a specific application.
    """
    try:
        stats = await stats_service.get_app_statistics(app_id)
        
        # Get API key info
        api_key_info = await auth_service.get_api_key(app_id)
        
        return {
            "app_id": app_id,
            "api_key_info": api_key_info.dict() if api_key_info else None,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error("Failed to get app statistics", app_id=app_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to retrieve app statistics"}
        )


@router.get("/api-keys", dependencies=[Depends(verify_admin_access)])
async def list_api_keys() -> Dict[str, Any]:
    """
    List all API keys with their information.
    """
    try:
        api_keys = await auth_service.list_api_keys()
        
        # Convert to list format and hide secrets
        keys_list = []
        for app_id, key_info in api_keys.items():
            key_data = key_info.dict()
            key_data["app_secret"] = "***hidden***"  # Hide secret in listing
            keys_list.append(key_data)
        
        return {
            "total_keys": len(keys_list),
            "api_keys": keys_list
        }
        
    except Exception as e:
        logger.error("Failed to list API keys", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to list API keys"}
        )


@router.post("/api-keys", dependencies=[Depends(verify_admin_access)])
async def create_api_key(api_key_info: APIKeyInfo) -> Dict[str, Any]:
    """
    Create a new API key.
    """
    try:
        success = await auth_service.add_api_key(api_key_info)
        
        if success:
            logger.info("API key created", app_id=api_key_info.app_id)
            return {
                "message": "API key created successfully",
                "app_id": api_key_info.app_id
            }
        else:
            raise HTTPException(
                status_code=400,
                detail={"error": "API key already exists or creation failed"}
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create API key", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to create API key"}
        )


@router.put("/api-keys/{app_id}", dependencies=[Depends(verify_admin_access)])
async def update_api_key(app_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update an existing API key.
    """
    try:
        success = await auth_service.update_api_key(app_id, updates)
        
        if success:
            logger.info("API key updated", app_id=app_id)
            return {
                "message": "API key updated successfully",
                "app_id": app_id
            }
        else:
            raise HTTPException(
                status_code=404,
                detail={"error": "API key not found"}
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update API key", app_id=app_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to update API key"}
        )


@router.delete("/api-keys/{app_id}", dependencies=[Depends(verify_admin_access)])
async def delete_api_key(app_id: str) -> Dict[str, Any]:
    """
    Delete an API key.
    """
    try:
        success = await auth_service.delete_api_key(app_id)
        
        if success:
            logger.info("API key deleted", app_id=app_id)
            return {
                "message": "API key deleted successfully",
                "app_id": app_id
            }
        else:
            raise HTTPException(
                status_code=404,
                detail={"error": "API key not found"}
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete API key", app_id=app_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to delete API key"}
        )


@router.post("/cache/clear", dependencies=[Depends(verify_admin_access)])
async def clear_cache() -> Dict[str, Any]:
    """
    Clear all cached translations.
    """
    try:
        async with cache_service:
            success = await cache_service.clear_cache()
        
        if success:
            logger.info("Cache cleared by admin")
            return {"message": "Cache cleared successfully"}
        else:
            raise HTTPException(
                status_code=500,
                detail={"error": "Failed to clear cache"}
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to clear cache", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to clear cache"}
        )


@router.get("/cache/stats", dependencies=[Depends(verify_admin_access)])
async def get_cache_statistics() -> Dict[str, Any]:
    """
    Get cache statistics and performance metrics.
    """
    try:
        async with cache_service:
            cache_stats = await cache_service.get_cache_stats()
        
        return {
            "cache_statistics": cache_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get cache statistics", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to retrieve cache statistics"}
        )


@router.get("/system/info", dependencies=[Depends(verify_admin_access)])
async def get_system_info() -> Dict[str, Any]:
    """
    Get comprehensive system information.
    """
    try:
        # Get health metrics
        health_metrics = await stats_service.get_health_metrics()
        
        # Get overall statistics
        stats = await stats_service.get_statistics()
        
        # Get cache stats
        async with cache_service:
            cache_stats = await cache_service.get_cache_stats()
        
        # Get API key count
        api_keys = await auth_service.list_api_keys()
        
        return {
            "system_health": health_metrics,
            "usage_statistics": stats,
            "cache_status": cache_stats,
            "api_keys_count": len(api_keys),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get system info", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to retrieve system information"}
        )
