#!/usr/bin/env python3
"""
LLM Translation Service Discovery Client

This utility helps discover and connect to llmYTranslate services on the network.
Can be used by systemDesign project to automatically find translation services.
"""

import asyncio
import aiohttp
import json
import sys
import argparse
from typing import List, Dict, Any, Optional
import time


class TranslationServiceClient:
    """Client for discovering and connecting to llmYTranslate services."""
    
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
    
    async def discover_services(self) -> List[Dict[str, Any]]:
        """Discover available translation services on the network."""
        # Common service ports and endpoints
        discovery_endpoints = [
            "http://127.0.0.1:8888/api/discovery/info",  # Local default
            "http://localhost:8888/api/discovery/info",   # Local alias
        ]
        
        # Try to discover on local network (basic scan)
        local_ips = self._get_local_network_ips()
        for ip in local_ips[:20]:  # Limit scan range
            for port in [8888, 8000, 8080]:
                discovery_endpoints.append(f"http://{ip}:{port}/api/discovery/info")
        
        services = []
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            tasks = [self._check_service_endpoint(session, endpoint) for endpoint in discovery_endpoints]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, dict):
                    service_name = result.get("service_name", "")
                    if service_name in ["llm-translation-local", "llm-translation-remote"] or "llm-translation" in service_name:
                        services.append(result)
        
        return services
    
    async def _check_service_endpoint(self, session: aiohttp.ClientSession, endpoint: str) -> Optional[Dict[str, Any]]:
        """Check if a service is available at the given endpoint."""
        try:
            async with session.get(endpoint) as response:
                if response.status == 200:
                    data = await response.json()
                    data["discovered_endpoint"] = endpoint
                    return data
        except Exception:
            pass  # Service not available
        return None
    
    def _get_local_network_ips(self) -> List[str]:
        """Get a list of IPs to scan on the local network."""
        import socket
        import ipaddress
        
        ips = []
        try:
            # Get local IP
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            # Generate network range
            network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
            ips = [str(ip) for ip in network.hosts()][:50]  # Limit to 50 IPs
            
        except Exception:
            # Fallback to common local ranges
            for subnet in ["192.168.1", "192.168.0", "10.0.0"]:
                ips.extend([f"{subnet}.{i}" for i in range(1, 21)])
        
        return ips
    
    async def test_service(self, service_url: str) -> Dict[str, Any]:
        """Test connectivity to a specific service."""
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            try:
                # Test health endpoint
                async with session.get(f"{service_url}/api/health") as response:
                    if response.status != 200:
                        return {"status": "error", "message": f"Health check failed: {response.status}"}
                
                # Test translation endpoint
                test_data = {
                    "q": "Hello",
                    "from": "en", 
                    "to": "zh",
                    "appid": "demo",
                    "salt": "123",
                    "sign": "dummy"
                }
                
                async with session.post(f"{service_url}/api/trans/vip/translate", data=test_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "status": "success",
                            "message": "Service is working correctly",
                            "test_translation": result
                        }
                    else:
                        return {"status": "warning", "message": f"Translation test failed: {response.status}"}
                        
            except Exception as e:
                return {"status": "error", "message": f"Connection failed: {str(e)}"}
    
    async def get_best_service(self) -> Optional[Dict[str, Any]]:
        """Find the best available translation service."""
        services = await self.discover_services()
        
        if not services:
            return None
        
        # Prefer local services, then remote
        local_services = [s for s in services if s.get("mode") == "local"]
        if local_services:
            return local_services[0]
        
        return services[0] if services else None


async def main():
    parser = argparse.ArgumentParser(description="LLM Translation Service Discovery")
    parser.add_argument("--discover", action="store_true", help="Discover available services")
    parser.add_argument("--test", type=str, help="Test a specific service URL")
    parser.add_argument("--best", action="store_true", help="Find the best available service")
    parser.add_argument("--timeout", type=float, default=5.0, help="Connection timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    args = parser.parse_args()
    
    client = TranslationServiceClient(timeout=args.timeout)
    
    if args.discover:
        print("Discovering translation services...")
        services = await client.discover_services()
        
        if args.json:
            print(json.dumps(services, indent=2))
        else:
            if not services:
                print("No translation services found.")
                sys.exit(1)
            
            print(f"Found {len(services)} service(s):")
            for i, service in enumerate(services, 1):
                print(f"\n{i}. {service.get('service_name', 'Unknown')}")
                print(f"   Mode: {service.get('mode', 'Unknown')}")
                print(f"   URL: {service.get('deployment', {}).get('connection_url', 'Unknown')}")
                print(f"   Version: {service.get('version', 'Unknown')}")
                print(f"   Status: {service.get('status', 'Unknown')}")
                if service.get('discovered_endpoint'):
                    print(f"   Discovered at: {service['discovered_endpoint']}")
    
    elif args.test:
        print(f"Testing service at {args.test}...")
        result = await client.test_service(args.test)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Status: {result['status']}")
            print(f"Message: {result['message']}")
            if result.get('test_translation'):
                print("Test translation successful!")
    
    elif args.best:
        print("Finding best available service...")
        service = await client.get_best_service()
        
        if args.json:
            print(json.dumps(service, indent=2))
        else:
            if not service:
                print("No translation services available.")
                sys.exit(1)
            
            print("Best available service:")
            print(f"Name: {service.get('service_name', 'Unknown')}")
            print(f"Mode: {service.get('mode', 'Unknown')}")
            print(f"URL: {service.get('deployment', {}).get('connection_url', 'Unknown')}")
            print(f"Version: {service.get('version', 'Unknown')}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
