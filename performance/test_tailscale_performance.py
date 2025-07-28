#!/usr/bin/env python3
"""
Tailscale Network Performance Test for LLM Translation Service
Tests the service performance over Tailscale VPN connection.
"""

import asyncio
import aiohttp
import time
import json
import statistics
from typing import List, Dict, Any

class TailscalePerformanceTest:
    def __init__(self, tailscale_ip: str = "100.104.28.77", port: int = 8000):
        self.base_url = f"http://{tailscale_ip}:{port}"
        self.results = []
    
    async def test_health_endpoint(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test health endpoint response time."""
        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}/api/health") as response:
                await response.json()
                end_time = time.time()
                return {
                    "endpoint": "health", 
                    "status": "success",
                    "response_time": end_time - start_time,
                    "status_code": response.status
                }
        except Exception as e:
            end_time = time.time()
            return {
                "endpoint": "health",
                "status": "error", 
                "response_time": end_time - start_time,
                "error": str(e)
            }
    
    async def test_demo_translate(self, session: aiohttp.ClientSession, text: str) -> Dict[str, Any]:
        """Test demo translation endpoint."""
        start_time = time.time()
        try:
            payload = {"q": text}
            async with session.post(
                f"{self.base_url}/api/demo/translate",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                end_time = time.time()
                return {
                    "endpoint": "demo_translate",
                    "status": "success",
                    "response_time": end_time - start_time,
                    "status_code": response.status,
                    "input_length": len(text),
                    "result": result
                }
        except Exception as e:
            end_time = time.time()
            return {
                "endpoint": "demo_translate",
                "status": "error",
                "response_time": end_time - start_time,
                "error": str(e),
                "input_length": len(text)
            }
    
    async def run_concurrent_tests(self, num_concurrent: int = 5) -> List[Dict[str, Any]]:
        """Run concurrent tests to measure performance under load."""
        async with aiohttp.ClientSession() as session:
            # Test basic health checks
            health_tasks = [self.test_health_endpoint(session) for _ in range(num_concurrent)]
            health_results = await asyncio.gather(*health_tasks)
            
            # Test translation with various text lengths
            test_texts = [
                "Hello",
                "Hello world",
                "This is a longer sentence to test translation performance.",
                "This is an even longer paragraph with multiple sentences. It should help us understand how the translation service performs with larger text inputs over the Tailscale network connection.",
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
            ]
            
            translate_tasks = []
            for text in test_texts:
                translate_tasks.append(self.test_demo_translate(session, text))
            
            translate_results = await asyncio.gather(*translate_tasks)
            
            return health_results + translate_results
    
    async def run_performance_suite(self):
        """Run complete performance test suite."""
        print("🚀 Tailscale Network Performance Test")
        print("=" * 50)
        print(f"🔗 Testing service at: {self.base_url}")
        print(f"⏰ Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Test 1: Basic connectivity
        print("📡 Test 1: Basic Connectivity")
        print("-" * 30)
        async with aiohttp.ClientSession() as session:
            result = await self.test_health_endpoint(session)
            if result["status"] == "success":
                print(f"✅ Health check: {result['response_time']:.3f}s")
            else:
                print(f"❌ Health check failed: {result.get('error', 'Unknown error')}")
                return
        
        # Test 2: Concurrent load test  
        print("\n🔥 Test 2: Concurrent Load Test")
        print("-" * 30)
        concurrent_results = await self.run_concurrent_tests(10)
        
        # Analyze results
        successful_tests = [r for r in concurrent_results if r["status"] == "success"]
        failed_tests = [r for r in concurrent_results if r["status"] == "error"]
        
        if successful_tests:
            response_times = [r["response_time"] for r in successful_tests]
            print(f"✅ Successful requests: {len(successful_tests)}")
            print(f"❌ Failed requests: {len(failed_tests)}")
            print(f"📊 Average response time: {statistics.mean(response_times):.3f}s")
            print(f"📊 Median response time: {statistics.median(response_times):.3f}s")
            print(f"📊 Min response time: {min(response_times):.3f}s")
            print(f"📊 Max response time: {max(response_times):.3f}s")
        
        # Test 3: Translation accuracy test
        print("\n🔤 Test 3: Translation Tests")
        print("-" * 30)
        translation_tests = [r for r in concurrent_results if r["endpoint"] == "demo_translate"]
        for test in translation_tests:
            if test["status"] == "success":
                print(f"✅ Text length {test['input_length']:3d}: {test['response_time']:.3f}s")
            else:
                print(f"❌ Text length {test['input_length']:3d}: {test.get('error', 'Failed')}")
        
        # Save results
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        results_file = f"tailscale_performance_results_{timestamp}.json"
        
        summary = {
            "test_timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "service_url": self.base_url,
            "total_tests": len(concurrent_results),
            "successful_tests": len(successful_tests), 
            "failed_tests": len(failed_tests),
            "detailed_results": concurrent_results
        }
        
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        print(f"🎯 Overall success rate: {len(successful_tests)/len(concurrent_results)*100:.1f}%")

async def main():
    """Main test execution."""
    tester = TailscalePerformanceTest()
    await tester.run_performance_suite()

if __name__ == "__main__":
    asyncio.run(main())
