"""
Service discovery and deployment mode routes.
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
import logging

from src.core.config import get_settings
from src.core.network import NetworkManager, ServiceDiscovery

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/discovery", tags=["Service Discovery"])


@router.get("/info", response_model=Dict[str, Any])
async def get_service_info(settings = Depends(get_settings)):
    """Get service information including deployment mode and network details."""
    network_manager = NetworkManager(settings)
    
    service_info = network_manager.get_service_info()
    service_info.update({
        "endpoints": {
            "health": "/api/health",
            "translate": "/api/trans/vip/translate",
            "demo_translate": "/api/demo/translate",
            "docs": "/docs",
            "openapi": "/openapi.json"
        },
        "deployment": {
            "mode": settings.deployment.mode,
            "network_interface": settings.deployment.network_interface,
            "connection_url": network_manager.get_connection_url(),
            "external_url": network_manager.get_connection_url(prefer_external=True)
        }
    })
    
    return service_info


@router.get("/network", response_model=Dict[str, Any])
async def get_network_info(request: Request, settings = Depends(get_settings)):
    """Get network configuration and client information."""
    network_manager = NetworkManager(settings)
    
    client_ip = getattr(request.client, 'host', '127.0.0.1') if request.client else '127.0.0.1'
    is_trusted = network_manager.is_ip_in_trusted_networks(client_ip)
    
    return {
        "client_ip": client_ip,
        "is_trusted_network": is_trusted,
        "server_ip": network_manager.get_local_ip(settings.deployment.network_interface),
        "deployment_mode": settings.deployment.mode,
        "trusted_networks": settings.deployment.trusted_networks,
        "connection_urls": {
            "local": network_manager.get_connection_url(),
            "external": network_manager.get_connection_url(prefer_external=True)
        }
    }


@router.get("/discover", response_model=List[Dict[str, Any]])
async def discover_services(timeout: float = 5.0):
    """Discover other llmYTranslate services on the network."""
    try:
        services = await ServiceDiscovery.discover_services(timeout)
        return services
    except Exception as e:
        logger.error(f"Service discovery failed: {e}")
        raise HTTPException(status_code=500, detail=f"Service discovery failed: {str(e)}")


@router.get("/config", response_model=Dict[str, Any])
async def get_deployment_config(settings = Depends(get_settings)):
    """Get deployment configuration (non-sensitive information only)."""
    return {
        "deployment": {
            "mode": settings.deployment.mode,
            "service_name": settings.deployment.service_name,
            "network_interface": settings.deployment.network_interface,
            "enable_discovery": settings.deployment.enable_discovery,
            "discovery_port": settings.deployment.discovery_port,
            "external_host": settings.deployment.external_host,
            "external_port": settings.deployment.external_port
        },
        "api": {
            "host": settings.api.host,
            "port": settings.api.port,
            "version": settings.api.version
        },
        "environment": settings.environment,
        "debug": settings.debug
    }


@router.post("/connect-test", response_model=Dict[str, Any])
async def test_connection(target_url: str):
    """Test connection to another llmYTranslate service."""
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test basic connectivity
            async with session.get(f"{target_url}/api/health", timeout=5) as response:
                if response.status != 200:
                    return {
                        "status": "error",
                        "message": f"Health check failed with status {response.status}"
                    }
            
            # Test service discovery
            async with session.get(f"{target_url}/api/discovery/info", timeout=5) as response:
                if response.status == 200:
                    service_info = await response.json()
                    return {
                        "status": "success",
                        "message": "Connection successful",
                        "service_info": service_info
                    }
                else:
                    return {
                        "status": "warning",
                        "message": "Basic connectivity works but service discovery unavailable"
                    }
                    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Connection failed: {str(e)}"
        }
