#!/usr/bin/env python3
"""
Test script to verify Baidu Translate API compatibility.

This script tests various aspects of the API to ensure it's fully compatible
with the Baidu Translate API specification.
"""

import hashlib
import time
import json
import asyncio
import aiohttp
from typing import Dict, Any

# Baidu API specification reference
BAIDU_API_SPEC = {
    "endpoint": "/api/trans/vip/translate",
    "method": "POST",
    "content_type": "application/x-www-form-urlencoded",
    "required_params": ["q", "from", "to", "appid", "salt", "sign"],
    "signature_algorithm": "MD5(appid + query + salt + secret)",
    "response_format": {
        "from": "source_language_code",
        "to": "target_language_code", 
        "trans_result": [{"src": "source_text", "dst": "translated_text"}],
        "error_code": "optional_error_code",
        "error_msg": "optional_error_message"
    }
}

class BaiduCompatibilityTester:
    """Test suite for Baidu Translate API compatibility."""
    
    def __init__(self, base_url: str = "http://localhost:8888"):
        self.base_url = base_url
        self.demo_app_id = "demo_app_id"
        self.demo_app_secret = "demo_app_secret"
        
    def create_signature(self, app_id: str, query: str, salt: str, secret: str) -> str:
        """Create MD5 signature using Baidu's algorithm."""
        sign_str = f"{app_id}{query}{salt}{secret}"
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest()
    
    def generate_request_params(self, query: str, from_lang: str = "en", to_lang: str = "zh") -> Dict[str, str]:
        """Generate request parameters with proper signature."""
        salt = str(int(time.time() * 1000))
        signature = self.create_signature(self.demo_app_id, query, salt, self.demo_app_secret)
        
        return {
            "q": query,
            "from": from_lang,
            "to": to_lang,
            "appid": self.demo_app_id,
            "salt": salt,
            "sign": signature
        }
    
    async def test_endpoint_accessibility(self) -> Dict[str, Any]:
        """Test if the translation endpoint is accessible."""
        print("🔍 Testing endpoint accessibility...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test with valid request
                params = self.generate_request_params("Hello world")
                
                async with session.post(
                    f"{self.base_url}/api/trans/vip/translate",
                    data=params
                ) as response:
                    status = response.status
                    content = await response.text()
                    
                    return {
                        "test": "endpoint_accessibility",
                        "success": status in [200, 400, 401],  # Any response is good
                        "status_code": status,
                        "response_preview": content[:200],
                        "details": "Endpoint is accessible" if status in [200, 400, 401] else "Endpoint not accessible"
                    }
                    
        except Exception as e:
            return {
                "test": "endpoint_accessibility", 
                "success": False,
                "error": str(e),
                "details": "Could not reach the endpoint"
            }
    
    async def test_signature_validation(self) -> Dict[str, Any]:
        """Test signature validation mechanism."""
        print("🔐 Testing signature validation...")
        
        results = []
        
        # Test 1: Valid signature
        try:
            async with aiohttp.ClientSession() as session:
                params = self.generate_request_params("Test message")
                
                async with session.post(
                    f"{self.base_url}/api/trans/vip/translate",
                    data=params
                ) as response:
                    response_data = await response.json()
                    
                    results.append({
                        "test": "valid_signature",
                        "success": response.status == 200 and not response_data.get("error_code"),
                        "status_code": response.status,
                        "response": response_data
                    })
        except Exception as e:
            results.append({
                "test": "valid_signature",
                "success": False,
                "error": str(e)
            })
        
        # Test 2: Invalid signature
        try:
            async with aiohttp.ClientSession() as session:
                params = self.generate_request_params("Test message")
                params["sign"] = "invalid_signature"  # Corrupt signature
                
                async with session.post(
                    f"{self.base_url}/api/trans/vip/translate",
                    data=params
                ) as response:
                    response_data = await response.json()
                    
                    results.append({
                        "test": "invalid_signature",
                        "success": response_data.get("error_code") == "INVALID_SIGNATURE",
                        "status_code": response.status,
                        "response": response_data,
                        "expected_error": "INVALID_SIGNATURE"
                    })
        except Exception as e:
            results.append({
                "test": "invalid_signature", 
                "success": False,
                "error": str(e)
            })
        
        return {
            "test": "signature_validation",
            "success": all(r["success"] for r in results),
            "subtests": results
        }
    
    async def test_parameter_validation(self) -> Dict[str, Any]:
        """Test parameter validation (required params, language codes, etc.)."""
        print("📝 Testing parameter validation...")
        
        results = []
        
        # Test missing required parameters
        missing_param_tests = [
            ("missing_q", {"from": "en", "to": "zh", "appid": self.demo_app_id, "salt": "123", "sign": "test"}),
            ("missing_from", {"q": "test", "to": "zh", "appid": self.demo_app_id, "salt": "123", "sign": "test"}),
            ("missing_to", {"q": "test", "from": "en", "appid": self.demo_app_id, "salt": "123", "sign": "test"}),
            ("missing_appid", {"q": "test", "from": "en", "to": "zh", "salt": "123", "sign": "test"}),
            ("missing_salt", {"q": "test", "from": "en", "to": "zh", "appid": self.demo_app_id, "sign": "test"}),
            ("missing_sign", {"q": "test", "from": "en", "to": "zh", "appid": self.demo_app_id, "salt": "123"})
        ]
        
        for test_name, params in missing_param_tests:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/api/trans/vip/translate",
                        data=params
                    ) as response:
                        status = response.status
                        
                        results.append({
                            "test": test_name,
                            "success": status == 422,  # FastAPI validation error
                            "status_code": status,
                            "expected": "422 (validation error)"
                        })
            except Exception as e:
                results.append({
                    "test": test_name,
                    "success": False,
                    "error": str(e)
                })
        
        # Test invalid language codes
        try:
            params = self.generate_request_params("test", from_lang="invalid", to_lang="zh")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/trans/vip/translate",
                    data=params
                ) as response:
                    response_data = await response.json()
                    
                    results.append({
                        "test": "invalid_language_code",
                        "success": response_data.get("error_code") is not None,
                        "status_code": response.status,
                        "response": response_data
                    })
        except Exception as e:
            results.append({
                "test": "invalid_language_code",
                "success": False,
                "error": str(e)
            })
        
        return {
            "test": "parameter_validation",
            "success": all(r["success"] for r in results),
            "subtests": results
        }
    
    async def test_response_format(self) -> Dict[str, Any]:
        """Test response format compatibility with Baidu API."""
        print("📋 Testing response format compatibility...")
        
        try:
            async with aiohttp.ClientSession() as session:
                params = self.generate_request_params("Hello world", "en", "zh")
                
                async with session.post(
                    f"{self.base_url}/api/trans/vip/translate",
                    data=params
                ) as response:
                    response_data = await response.json()
                    
                    # Check required fields
                    required_fields = ["from", "to", "trans_result"]
                    field_checks = {}
                    
                    for field in required_fields:
                        field_checks[field] = field in response_data
                    
                    # Check trans_result structure
                    trans_result_valid = False
                    if "trans_result" in response_data and isinstance(response_data["trans_result"], list):
                        if len(response_data["trans_result"]) == 0:
                            # Empty result is OK for errors
                            trans_result_valid = True
                        elif len(response_data["trans_result"]) > 0:
                            # Check first result structure
                            first_result = response_data["trans_result"][0]
                            trans_result_valid = "src" in first_result and "dst" in first_result
                    
                    return {
                        "test": "response_format",
                        "success": all(field_checks.values()) and trans_result_valid,
                        "status_code": response.status,
                        "response": response_data,
                        "field_checks": field_checks,
                        "trans_result_valid": trans_result_valid,
                        "baidu_compatible": True if all(field_checks.values()) and trans_result_valid else False
                    }
                    
        except Exception as e:
            return {
                "test": "response_format",
                "success": False,
                "error": str(e)
            }
    
    async def test_language_support(self) -> Dict[str, Any]:
        """Test supported language pairs."""
        print("🌍 Testing language support...")
        
        language_tests = [
            ("en_to_zh", "en", "zh", "Hello world"),
            ("zh_to_en", "zh", "en", "你好世界"),
            ("auto_detect", "auto", "zh", "Hello world")
        ]
        
        results = []
        
        for test_name, from_lang, to_lang, text in language_tests:
            try:
                async with aiohttp.ClientSession() as session:
                    params = self.generate_request_params(text, from_lang, to_lang)
                    
                    async with session.post(
                        f"{self.base_url}/api/trans/vip/translate",
                        data=params
                    ) as response:
                        response_data = await response.json()
                        
                        results.append({
                            "test": test_name,
                            "success": response.status == 200,
                            "status_code": response.status,
                            "response": response_data,
                            "language_pair": f"{from_lang} -> {to_lang}"
                        })
                        
            except Exception as e:
                results.append({
                    "test": test_name,
                    "success": False,
                    "error": str(e),
                    "language_pair": f"{from_lang} -> {to_lang}"
                })
        
        return {
            "test": "language_support",
            "success": all(r["success"] for r in results),
            "subtests": results
        }
    
    async def test_health_endpoint(self) -> Dict[str, Any]:
        """Test health check endpoint."""
        print("🩺 Testing health endpoint...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    response_data = await response.json()
                    
                    return {
                        "test": "health_endpoint",
                        "success": response.status == 200,
                        "status_code": response.status,
                        "response": response_data
                    }
                    
        except Exception as e:
            return {
                "test": "health_endpoint",
                "success": False,
                "error": str(e)
            }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all compatibility tests."""
        print("🚀 Starting Baidu Translate API Compatibility Tests")
        print("=" * 60)
        
        tests = [
            self.test_endpoint_accessibility(),
            self.test_health_endpoint(),
            self.test_signature_validation(),
            self.test_parameter_validation(), 
            self.test_response_format(),
            self.test_language_support()
        ]
        
        results = []
        for test_coro in tests:
            result = await test_coro
            results.append(result)
            
            # Print test result
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} {result['test']}")
            if not result["success"] and "error" in result:
                print(f"    Error: {result['error']}")
        
        print("=" * 60)
        
        # Overall compatibility score
        passed_tests = sum(1 for r in results if r["success"])
        total_tests = len(results)
        compatibility_score = (passed_tests / total_tests) * 100
        
        print(f"🎯 Compatibility Score: {compatibility_score:.1f}% ({passed_tests}/{total_tests} tests passed)")
        
        if compatibility_score >= 90:
            print("🌟 EXCELLENT: API is highly compatible with Baidu Translate API")
        elif compatibility_score >= 70:
            print("👍 GOOD: API is mostly compatible with Baidu Translate API")
        elif compatibility_score >= 50:
            print("⚠️  PARTIAL: API has some compatibility issues")
        else:
            print("❌ POOR: API has significant compatibility issues")
        
        return {
            "compatibility_score": compatibility_score,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "results": results,
            "baidu_spec_reference": BAIDU_API_SPEC
        }


async def main():
    """Main test runner."""
    tester = BaiduCompatibilityTester()
    
    print("Baidu Translate API Compatibility Test Suite")
    print("=" * 60)
    print("Testing API compatibility with Baidu Translate API specification")
    print("Service URL: http://localhost:8888")
    print()
    
    # Run all tests
    results = await tester.run_all_tests()
    
    # Save results to file
    with open("baidu_compatibility_report.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: baidu_compatibility_report.json")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
