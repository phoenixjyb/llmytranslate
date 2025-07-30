"""
Connection Pool Manager for Phone Call Mode
Optimizes connections to external services for better performance
"""

import asyncio
import aiohttp
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ServiceType(Enum):
    OLLAMA = "ollama"
    WHISPER = "whisper"
    TTS = "tts"
    EXTERNAL_API = "external_api"

@dataclass
class ConnectionPoolConfig:
    """Configuration for a connection pool"""
    max_connections: int = 10
    max_keepalive: int = 5
    keepalive_timeout: float = 30.0
    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0

class ConnectionPoolManager:
    """Manages connection pools for various services"""
    
    def __init__(self):
        self.pools: Dict[ServiceType, aiohttp.ClientSession] = {}
        self.pool_configs: Dict[ServiceType, ConnectionPoolConfig] = {}
        self.pool_stats: Dict[ServiceType, Dict] = {}
        self.active_connections: Dict[ServiceType, int] = {}
        
        # Initialize default configurations
        self._setup_default_configs()
        
        # Health check settings
        self.last_health_check = {}
        self.health_check_interval = 300  # 5 minutes
        
        logger.info("Connection pool manager initialized")
    
    def _setup_default_configs(self):
        """Set up default connection pool configurations"""
        # Ollama LLM service - high concurrency for phone calls
        self.pool_configs[ServiceType.OLLAMA] = ConnectionPoolConfig(
            max_connections=15,
            max_keepalive=8,
            keepalive_timeout=60.0,
            connect_timeout=5.0,
            read_timeout=60.0,  # LLM can take time
            retry_attempts=2,
            retry_delay=0.5
        )
        
        # Whisper STT service - moderate concurrency
        self.pool_configs[ServiceType.WHISPER] = ConnectionPoolConfig(
            max_connections=10,
            max_keepalive=5,
            keepalive_timeout=30.0,
            connect_timeout=10.0,
            read_timeout=30.0,
            retry_attempts=3,
            retry_delay=1.0
        )
        
        # TTS service - moderate concurrency
        self.pool_configs[ServiceType.TTS] = ConnectionPoolConfig(
            max_connections=8,
            max_keepalive=4,
            keepalive_timeout=30.0,
            connect_timeout=10.0,
            read_timeout=45.0,  # TTS can take time
            retry_attempts=2,
            retry_delay=1.0
        )
        
        # External APIs - conservative settings
        self.pool_configs[ServiceType.EXTERNAL_API] = ConnectionPoolConfig(
            max_connections=5,
            max_keepalive=3,
            keepalive_timeout=30.0,
            connect_timeout=15.0,
            read_timeout=30.0,
            retry_attempts=3,
            retry_delay=2.0
        )
    
    async def get_session(self, service_type: ServiceType) -> aiohttp.ClientSession:
        """Get or create a connection pool session for a service"""
        if service_type not in self.pools:
            await self._create_pool(service_type)
        
        session = self.pools[service_type]
        
        # Check if session is still valid
        if session.closed:
            logger.warning(f"Session for {service_type.value} was closed, recreating...")
            await self._create_pool(service_type)
            session = self.pools[service_type]
        
        return session
    
    async def _create_pool(self, service_type: ServiceType):
        """Create a new connection pool for a service"""
        config = self.pool_configs[service_type]
        
        # Create connection limits
        connector = aiohttp.TCPConnector(
            limit=config.max_connections,
            limit_per_host=config.max_connections,
            keepalive_timeout=config.keepalive_timeout,
            enable_cleanup_closed=True,
            ttl_dns_cache=300,  # DNS cache for 5 minutes
            use_dns_cache=True
        )
        
        # Create timeout configuration
        timeout = aiohttp.ClientTimeout(
            total=config.connect_timeout + config.read_timeout,
            connect=config.connect_timeout,
            sock_read=config.read_timeout
        )
        
        # Create session
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "User-Agent": "LLMyTranslate-PhoneCall/1.0",
                "Connection": "keep-alive"
            }
        )
        
        self.pools[service_type] = session
        self.pool_stats[service_type] = {
            "created_at": datetime.now().isoformat(),
            "requests_made": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
            "average_response_time": 0.0,
            "last_used": None
        }
        self.active_connections[service_type] = 0
        
        logger.info(f"Created connection pool for {service_type.value} with {config.max_connections} max connections")
    
    async def make_request(self, service_type: ServiceType, method: str, url: str, 
                          **kwargs) -> aiohttp.ClientResponse:
        """Make an HTTP request using the appropriate connection pool"""
        config = self.pool_configs[service_type]
        session = await self.get_session(service_type)
        
        start_time = time.time()
        last_exception = None
        
        for attempt in range(config.retry_attempts):
            try:
                self.active_connections[service_type] += 1
                
                async with session.request(method, url, **kwargs) as response:
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    # Update statistics
                    self._update_stats(service_type, response_time, response.status < 400)
                    
                    # Log slow requests
                    if response_time > 10.0:
                        logger.warning(f"Slow request to {service_type.value}: {response_time:.2f}s")
                    
                    return response
                    
            except Exception as e:
                last_exception = e
                self._update_stats(service_type, time.time() - start_time, False)
                
                if attempt < config.retry_attempts - 1:
                    wait_time = config.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Request to {service_type.value} failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All retry attempts failed for {service_type.value}: {e}")
                    raise
            
            finally:
                if service_type in self.active_connections:
                    self.active_connections[service_type] -= 1
        
        # This should never be reached due to the raise above, but just in case
        raise last_exception
    
    def _update_stats(self, service_type: ServiceType, response_time: float, success: bool):
        """Update statistics for a service pool"""
        if service_type not in self.pool_stats:
            return
        
        stats = self.pool_stats[service_type]
        stats["requests_made"] += 1
        stats["last_used"] = datetime.now().isoformat()
        
        if success:
            stats["successful_requests"] += 1
        else:
            stats["failed_requests"] += 1
        
        stats["total_response_time"] += response_time
        stats["average_response_time"] = stats["total_response_time"] / stats["requests_made"]
    
    async def post_json(self, service_type: ServiceType, url: str, data: Dict, 
                       headers: Dict = None) -> aiohttp.ClientResponse:
        """Convenience method for JSON POST requests"""
        default_headers = {"Content-Type": "application/json"}
        if headers:
            default_headers.update(headers)
        
        return await self.make_request(
            service_type=service_type,
            method="POST",
            url=url,
            json=data,
            headers=default_headers
        )
    
    async def get(self, service_type: ServiceType, url: str, 
                 params: Dict = None, headers: Dict = None) -> aiohttp.ClientResponse:
        """Convenience method for GET requests"""
        return await self.make_request(
            service_type=service_type,
            method="GET",
            url=url,
            params=params,
            headers=headers or {}
        )
    
    async def health_check_all_pools(self) -> Dict[ServiceType, Dict]:
        """Perform health checks on all connection pools"""
        health_results = {}
        
        for service_type in self.pools.keys():
            try:
                health_results[service_type] = await self._health_check_pool(service_type)
            except Exception as e:
                health_results[service_type] = {
                    "healthy": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        self.last_health_check = {
            "timestamp": datetime.now().isoformat(),
            "results": health_results
        }
        
        return health_results
    
    async def _health_check_pool(self, service_type: ServiceType) -> Dict:
        """Perform health check on a specific pool"""
        if service_type not in self.pools:
            return {"healthy": False, "error": "Pool not initialized"}
        
        session = self.pools[service_type]
        
        if session.closed:
            return {"healthy": False, "error": "Session is closed"}
        
        # Get connector stats
        connector = session.connector
        stats = {
            "healthy": True,
            "timestamp": datetime.now().isoformat(),
            "active_connections": self.active_connections.get(service_type, 0),
            "pool_size": connector.limit,
            "connections_in_pool": len(connector._conns),
            "stats": self.pool_stats.get(service_type, {})
        }
        
        return stats
    
    def get_pool_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics for all pools"""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "pools": {},
            "total_active_connections": sum(self.active_connections.values()),
            "last_health_check": self.last_health_check
        }
        
        for service_type in ServiceType:
            if service_type in self.pools:
                session = self.pools[service_type]
                connector = session.connector
                
                pool_info = {
                    "service_type": service_type.value,
                    "active": not session.closed,
                    "active_connections": self.active_connections.get(service_type, 0),
                    "max_connections": connector.limit,
                    "connections_in_pool": len(connector._conns) if hasattr(connector, '_conns') else 0,
                    "statistics": self.pool_stats.get(service_type, {}),
                    "config": {
                        "max_connections": self.pool_configs[service_type].max_connections,
                        "keepalive_timeout": self.pool_configs[service_type].keepalive_timeout,
                        "connect_timeout": self.pool_configs[service_type].connect_timeout,
                        "read_timeout": self.pool_configs[service_type].read_timeout
                    }
                }
                stats["pools"][service_type.value] = pool_info
        
        return stats
    
    async def cleanup_idle_connections(self):
        """Clean up idle connections across all pools"""
        cleaned_count = 0
        
        for service_type, session in self.pools.items():
            if not session.closed:
                try:
                    # Force cleanup of idle connections
                    await session.connector.close()
                    cleaned_count += 1
                    logger.info(f"Cleaned up idle connections for {service_type.value}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup connections for {service_type.value}: {e}")
        
        return cleaned_count
    
    async def close_all_pools(self):
        """Close all connection pools"""
        for service_type, session in self.pools.items():
            try:
                await session.close()
                logger.info(f"Closed connection pool for {service_type.value}")
            except Exception as e:
                logger.error(f"Error closing pool for {service_type.value}: {e}")
        
        self.pools.clear()
        self.pool_stats.clear()
        self.active_connections.clear()
    
    def optimize_for_phone_calls(self):
        """Optimize pool configurations specifically for phone call workloads"""
        # Increase connection limits for real-time workloads
        self.pool_configs[ServiceType.OLLAMA].max_connections = 20
        self.pool_configs[ServiceType.OLLAMA].keepalive_timeout = 120.0
        
        # Reduce timeouts for faster failures
        self.pool_configs[ServiceType.WHISPER].connect_timeout = 5.0
        self.pool_configs[ServiceType.TTS].connect_timeout = 5.0
        
        # Increase retry attempts for critical services
        self.pool_configs[ServiceType.OLLAMA].retry_attempts = 1  # Fast fail for real-time
        self.pool_configs[ServiceType.WHISPER].retry_attempts = 2
        
        logger.info("Connection pools optimized for phone call workloads")

# Global instance
connection_pool_manager = ConnectionPoolManager()
