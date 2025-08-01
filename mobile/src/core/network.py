"""
Network utilities for deployment mode management.
"""

import socket
import ipaddress
import platform
from typing import Optional, List, Dict, Any
import logging
import asyncio
import json
from datetime import datetime

# OS-aware network interface handling
USE_NETIFACES = False
USE_PSUTIL = False

try:
    if platform.system() == "Windows":
        # For Windows, use psutil if available, otherwise fallback to basic socket methods
        try:
            import psutil
            USE_PSUTIL = True
        except ImportError:
            pass
    else:
        # For macOS/Linux, prefer netifaces
        try:
            import netifaces
            USE_NETIFACES = True
        except ImportError:
            try:
                import psutil
                USE_PSUTIL = True
            except ImportError:
                pass
except Exception:
    pass

logger = logging.getLogger(__name__)


class NetworkManager:
    """Handles network configuration and service discovery for different deployment modes."""
    
    def __init__(self, settings):
        self.settings = settings
        
    def get_local_ip(self, interface: str = "auto") -> str:
        """Get the local IP address for the specified interface."""
        try:
            if USE_NETIFACES:
                if interface == "auto":
                    # Try to find the best interface
                    interfaces = netifaces.interfaces()
                    
                    # Prefer ethernet, then wifi, then any other
                    preferred_order = ['eth0', 'ens', 'enp', 'wlan0', 'wlp']
                    
                    for pref in preferred_order:
                        for iface in interfaces:
                            if pref in iface and iface != 'lo':
                                addresses = netifaces.ifaddresses(iface)
                                if netifaces.AF_INET in addresses:
                                    ip = addresses[netifaces.AF_INET][0]['addr']
                                    if not ip.startswith('127.'):
                                        return ip
                    
                    # Fallback: use any non-loopback interface
                    for iface in interfaces:
                        if iface != 'lo':
                            addresses = netifaces.ifaddresses(iface)
                            if netifaces.AF_INET in addresses:
                                ip = addresses[netifaces.AF_INET][0]['addr']
                                if not ip.startswith('127.'):
                                    return ip
                else:
                    # Use specific interface
                    if interface in netifaces.interfaces():
                        addresses = netifaces.ifaddresses(interface)
                        if netifaces.AF_INET in addresses:
                            return addresses[netifaces.AF_INET][0]['addr']
            
            # Fallback for when netifaces is not available
            else:
                # Use basic socket method as fallback
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80))
                    return s.getsockname()[0]
                        
        except Exception as e:
            logger.warning(f"Could not determine local IP: {e}")
            
        # Ultimate fallback
        return "127.0.0.1"
    
    def is_ip_in_trusted_networks(self, ip: str) -> bool:
        """Check if an IP address is in the trusted networks."""
        try:
            client_ip = ipaddress.ip_address(ip)
            for network_str in self.settings.deployment.trusted_networks:
                network = ipaddress.ip_network(network_str, strict=False)
                if client_ip in network:
                    return True
            return False
        except Exception as e:
            logger.warning(f"Error checking trusted networks for {ip}: {e}")
            return False
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information for discovery."""
        local_ip = self.get_local_ip(self.settings.deployment.network_interface)
        
        return {
            "service_name": self.settings.deployment.service_name,
            "mode": self.settings.deployment.mode,
            "host": local_ip,
            "port": self.settings.api.port,
            "external_host": self.settings.deployment.external_host,
            "external_port": self.settings.deployment.external_port,
            "version": self.settings.api.version,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "capabilities": [
                "translation",
                "baidu_api_compatible",
                "bidirectional_zh_en"
            ]
        }
    
    def get_connection_url(self, prefer_external: bool = False) -> str:
        """Get the appropriate connection URL based on deployment mode."""
        if self.settings.deployment.mode == "remote" and prefer_external:
            if self.settings.deployment.external_host and self.settings.deployment.external_port:
                return f"http://{self.settings.deployment.external_host}:{self.settings.deployment.external_port}"
        
        # Use local/internal address
        if self.settings.deployment.mode == "local":
            return f"http://127.0.0.1:{self.settings.api.port}"
        else:
            local_ip = self.get_local_ip(self.settings.deployment.network_interface)
            return f"http://{local_ip}:{self.settings.api.port}"
    
    def is_port_available(self, port: int, host: str = "0.0.0.0") -> bool:
        """Check if a port is available."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((host, port))
                return True
        except OSError:
            return False
    
    async def start_discovery_service(self):
        """Start the service discovery endpoint."""
        if not self.settings.deployment.enable_discovery:
            return
        
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        import uvicorn
        
        discovery_app = FastAPI(title="Service Discovery")
        
        @discovery_app.get("/discover")
        async def discover_service():
            return JSONResponse(self.get_service_info())
        
        @discovery_app.get("/health")
        async def discovery_health():
            return {"status": "ok", "service": "discovery"}
        
        # Run discovery service in background
        config = uvicorn.Config(
            discovery_app,
            host="0.0.0.0",
            port=self.settings.deployment.discovery_port,
            log_level="warning"
        )
        server = uvicorn.Server(config)
        
        logger.info(f"Starting service discovery on port {self.settings.deployment.discovery_port}")
        await server.serve()


class ServiceDiscovery:
    """Client for discovering llmYTranslate services on the network."""
    
    @staticmethod
    async def discover_services(timeout: float = 5.0) -> List[Dict[str, Any]]:
        """Discover llmYTranslate services on the local network."""
        services = []
        
        # Common discovery ports
        discovery_ports = [8889, 8890, 8891]
        
        # Get local network ranges
        local_networks = ServiceDiscovery._get_local_networks()
        
        tasks = []
        for network in local_networks:
            for host_num in range(1, 255):  # Scan common host range
                host = str(network.network_address + host_num)
                for port in discovery_ports:
                    tasks.append(ServiceDiscovery._check_service(host, port, timeout))
        
        # Execute discovery requests
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, dict) and result.get("service_name") == "llm-translation":
                services.append(result)
        
        return services
    
    @staticmethod
    def _get_local_networks():
        """Get local network ranges for discovery."""
        networks = []
        try:
            interfaces = netifaces.interfaces()
            for iface in interfaces:
                if iface != 'lo':  # Skip loopback
                    addresses = netifaces.ifaddresses(iface)
                    if netifaces.AF_INET in addresses:
                        for addr_info in addresses[netifaces.AF_INET]:
                            ip = addr_info.get('addr')
                            netmask = addr_info.get('netmask')
                            if ip and netmask and not ip.startswith('127.'):
                                try:
                                    network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                                    networks.append(network)
                                except Exception:
                                    pass
        except Exception as e:
            logger.warning(f"Error getting local networks: {e}")
        
        return networks
    
    @staticmethod
    async def _check_service(host: str, port: int, timeout: float) -> Optional[Dict[str, Any]]:
        """Check if a service is running at the given host:port."""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(f"http://{host}:{port}/discover") as response:
                    if response.status == 200:
                        data = await response.json()
                        data["discovered_at"] = f"{host}:{port}"
                        return data
        except Exception:
            pass  # Service not found or not responding
        
        return None
