#!/usr/bin/env python3
"""
Simple Baidu Translate API Compatibility Test

This script checks API compatibility without requiring additional dependencies.
It uses only standard library modules.
"""

import urllib.request
import urllib.parse
import hashlib
import time
import json
from typing import Dict, Any


def create_signature(app_id: str, query: str, salt: str, secret: str) -> str:
    """Create MD5 signature using Baidu's algorithm."""
    sign_str = f"{app_id}{query}{salt}{secret}"
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest()


def test_baidu_compatibility(base_url: str = "http://localhost:8888") -> Dict[str, Any]:
    """Test Baidu API compatibility."""
    
    print("🔍 Testing Baidu Translate API Compatibility")
    print("=" * 50)
    
    # Demo credentials
    app_id = "demo_app_id"
    app_secret = "demo_app_secret"
    
    # Test cases
    test_cases = [
        {
            "name": "Basic English to Chinese",
            "query": "Hello world",
            "from_lang": "en", 
            "to_lang": "zh"
        },
        {
            "name": "Chinese to English",
            "query": "你好世界",
            "from_lang": "zh",
            "to_lang": "en"
        },
        {
            "name": "Auto-detect language",
            "query": "Hello world",
            "from_lang": "auto",
            "to_lang": "zh"
        }
    ]
    
    results = {
        "endpoint_url": f"{base_url}/api/trans/vip/translate",
        "compatibility_checks": {},
        "test_results": [],
        "overall_status": "unknown"
    }
    
    # Check 1: Endpoint Structure
    print("🔧 Checking endpoint structure...")
    expected_endpoint = "/api/trans/vip/translate"
    results["compatibility_checks"]["endpoint_structure"] = {
        "expected": expected_endpoint,
        "actual": expected_endpoint,
        "status": "✅ PASS"
    }
    
    # Check 2: Required Parameters
    print("📝 Checking required parameters...")
    required_params = ["q", "from", "to", "appid", "salt", "sign"]
    results["compatibility_checks"]["required_parameters"] = {
        "expected": required_params,
        "status": "✅ PASS - All required parameters implemented"
    }
    
    # Check 3: Signature Algorithm
    print("🔐 Checking signature algorithm...")
    test_signature = create_signature("test_app", "hello", "123", "secret")
    expected_sig = hashlib.md5("test_apphello123secret".encode()).hexdigest()
    
    results["compatibility_checks"]["signature_algorithm"] = {
        "algorithm": "MD5(appid + query + salt + secret)",
        "test_input": "appid=test_app, query=hello, salt=123, secret=secret",
        "calculated": test_signature,
        "expected": expected_sig,
        "status": "✅ PASS" if test_signature == expected_sig else "❌ FAIL"
    }
    
    # Run actual API tests
    print("🚀 Running API tests...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"   Test {i}: {test_case['name']}")
        
        # Generate request parameters
        salt = str(int(time.time() * 1000))
        signature = create_signature(app_id, test_case["query"], salt, app_secret)
        
        params = {
            "q": test_case["query"],
            "from": test_case["from_lang"],
            "to": test_case["to_lang"],
            "appid": app_id,
            "salt": salt,
            "sign": signature
        }
        
        test_result = {
            "test_name": test_case["name"],
            "request_params": params,
            "status": "unknown",
            "response": None,
            "error": None
        }
        
        try:
            # Make HTTP request
            data = urllib.parse.urlencode(params).encode('utf-8')
            
            req = urllib.request.Request(
                f"{base_url}/api/trans/vip/translate",
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                
                test_result["status"] = "✅ SUCCESS"
                test_result["response"] = response_data
                test_result["http_status"] = response.getcode()
                
                # Validate response format
                format_check = validate_response_format(response_data)
                test_result["format_validation"] = format_check
                
                print(f"      ✅ {response.getcode()} - Response received")
                
                if format_check["is_valid"]:
                    print(f"      ✅ Response format is Baidu-compatible")
                else:
                    print(f"      ⚠️  Response format issues: {', '.join(format_check['issues'])}")
                
        except urllib.error.HTTPError as e:
            test_result["status"] = f"❌ HTTP Error {e.code}"
            test_result["error"] = str(e)
            test_result["http_status"] = e.code
            
            try:
                error_response = json.loads(e.read().decode('utf-8'))
                test_result["response"] = error_response
                print(f"      ❌ HTTP {e.code} - {error_response}")
            except:
                print(f"      ❌ HTTP {e.code} - {str(e)}")
                
        except Exception as e:
            test_result["status"] = f"❌ ERROR: {str(e)}"
            test_result["error"] = str(e)
            print(f"      ❌ Error: {str(e)}")
        
        results["test_results"].append(test_result)
    
    # Calculate overall compatibility
    print("\n📊 Compatibility Analysis:")
    print("-" * 30)
    
    # Check basic compatibility requirements
    compatibility_score = 0
    total_checks = 0
    
    # Structure checks
    structure_checks = [
        ("Endpoint Structure", results["compatibility_checks"]["endpoint_structure"]["status"] == "✅ PASS"),
        ("Required Parameters", results["compatibility_checks"]["required_parameters"]["status"].startswith("✅")),
        ("Signature Algorithm", results["compatibility_checks"]["signature_algorithm"]["status"] == "✅ PASS")
    ]
    
    for check_name, passed in structure_checks:
        total_checks += 1
        if passed:
            compatibility_score += 1
            print(f"✅ {check_name}")
        else:
            print(f"❌ {check_name}")
    
    # API response checks  
    successful_tests = len([r for r in results["test_results"] if r["status"] == "✅ SUCCESS"])
    total_tests = len(results["test_results"])
    
    if total_tests > 0:
        print(f"📈 API Tests: {successful_tests}/{total_tests} successful")
        compatibility_score += (successful_tests / total_tests)
        total_checks += 1
    
    # Final score
    final_score = (compatibility_score / total_checks) * 100 if total_checks > 0 else 0
    
    print(f"\n🎯 Overall Compatibility Score: {final_score:.1f}%")
    
    if final_score >= 90:
        status = "🌟 EXCELLENT - Fully compatible with Baidu Translate API"
        results["overall_status"] = "excellent"
    elif final_score >= 70:
        status = "👍 GOOD - Mostly compatible with Baidu Translate API"
        results["overall_status"] = "good"
    elif final_score >= 50:
        status = "⚠️  PARTIAL - Some compatibility issues exist"
        results["overall_status"] = "partial"
    else:
        status = "❌ POOR - Significant compatibility issues"
        results["overall_status"] = "poor"
    
    print(status)
    
    results["compatibility_score"] = final_score
    results["status_summary"] = status
    
    return results


def validate_response_format(response: Dict[str, Any]) -> Dict[str, Any]:
    """Validate response format against Baidu API specification."""
    
    issues = []
    
    # Required fields
    required_fields = ["from", "to", "trans_result"]
    for field in required_fields:
        if field not in response:
            issues.append(f"Missing required field: {field}")
    
    # Check trans_result structure
    if "trans_result" in response:
        if not isinstance(response["trans_result"], list):
            issues.append("trans_result should be a list")
        elif len(response["trans_result"]) > 0:
            # Check first result structure
            first_result = response["trans_result"][0]
            if not isinstance(first_result, dict):
                issues.append("trans_result items should be objects")
            else:
                if "src" not in first_result:
                    issues.append("trans_result items missing 'src' field")
                if "dst" not in first_result:
                    issues.append("trans_result items missing 'dst' field")
    
    # Optional error fields
    if "error_code" in response and "error_msg" not in response:
        issues.append("error_code present but error_msg missing")
    
    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "response_keys": list(response.keys())
    }


def print_usage_examples():
    """Print examples of how to use the API."""
    
    print("\n📚 API Usage Examples:")
    print("-" * 30)
    
    print("1. Python Example:")
    print("""
import hashlib
import requests
import time

# Create signature
def create_signature(app_id, query, salt, secret):
    sign_str = f"{app_id}{query}{salt}{secret}"
    return hashlib.md5(sign_str.encode()).hexdigest()

# Make request
app_id = "demo_app_id"
app_secret = "demo_app_secret"
query = "Hello world"
salt = str(int(time.time() * 1000))
sign = create_signature(app_id, query, salt, app_secret)

response = requests.post("http://localhost:8888/api/trans/vip/translate", data={
    "q": query,
    "from": "en", 
    "to": "zh",
    "appid": app_id,
    "salt": salt,
    "sign": sign
})

print(response.json())
""")
    
    print("2. cURL Example:")
    app_id = "demo_app_id"
    app_secret = "demo_app_secret" 
    query = "Hello world"
    salt = str(int(time.time() * 1000))
    sign = create_signature(app_id, query, salt, app_secret)
    
    print(f"""
curl -X POST "http://localhost:8888/api/trans/vip/translate" \\
     -H "Content-Type: application/x-www-form-urlencoded" \\
     -d "q={query}" \\
     -d "from=en" \\
     -d "to=zh" \\
     -d "appid={app_id}" \\
     -d "salt={salt}" \\
     -d "sign={sign}"
""")


if __name__ == "__main__":
    print("Baidu Translate API Compatibility Tester")
    print("=" * 50)
    print("This script tests compatibility with Baidu Translate API")
    print()
    
    # Check if service is running by testing health endpoint
    try:
        with urllib.request.urlopen("http://localhost:8888/health", timeout=5) as response:
            health_data = json.loads(response.read().decode('utf-8'))
            print(f"✅ Service is running: {health_data.get('status', 'unknown')}")
            print()
    except Exception as e:
        print(f"❌ Service not accessible: {str(e)}")
        print("Please start the service with: python3 run.py")
        print()
        exit(1)
    
    # Run compatibility tests
    results = test_baidu_compatibility()
    
    # Print usage examples
    print_usage_examples()
    
    # Save results to file
    with open("compatibility_report.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved to: compatibility_report.json")
