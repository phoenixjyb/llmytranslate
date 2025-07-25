# LLM Translation Service - cURL Command Reference

This document contains the working cURL commands for testing the LLM Translation Service endpoints.

## Service Information

**Base URL:** `http://localhost:8000`

## Working cURL Commands

### 1. Root Endpoint - Service Information
```bash
curl http://localhost:8000/
```
**Response:** Service metadata, available endpoints, and connection information

### 2. Health Check
```bash
curl http://localhost:8000/api/health
```
**Response:** Service health status including Ollama, cache, and translation service status

### 3. Demo Translation (Simple Format)
```bash
curl -X POST "http://localhost:8000/api/demo/translate" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "q=Hello world&from=en&to=zh"
```
**Response:** 
```json
{
  "request": {
    "q": "Hello world",
    "from": "en", 
    "to": "zh",
    "appid": "demo_app_id",
    "salt": "17533398509591",
    "sign": "a81d3c079b09cedde0eef258d55eed75"
  },
  "response": {
    "from_lang": "en",
    "to": "zh", 
    "trans_result": [{"src": "Hello world", "dst": "你好世界"}],
    "error_code": "52000",
    "error_msg": "success"
  }
}
```

### 4. Full Baidu API Compatible Translation
```bash
curl -X POST "http://localhost:8000/api/trans/vip/translate" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "q=Good morning&from=en&to=zh&appid=your_app_id&salt=1234567890&sign=your_signature"
```
**Note:** Requires proper MD5 signature calculation. Use the demo endpoint for simple testing.

## Available Endpoints (from service info)

- **Health:** `/api/health`
- **Demo Translation:** `/api/demo/translate` 
- **Full Translation:** `/api/trans/vip/translate`
- **Documentation:** `/docs`
- **Service Discovery:** `/api/discovery/info`

## Testing Multiple Translations

For testing multiple translations quickly:

```bash
# Test 1: Simple greeting
curl -X POST "http://localhost:8000/api/demo/translate" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "q=Hello, how are you?&from=en&to=zh"

# Test 2: Common phrase
curl -X POST "http://localhost:8000/api/demo/translate" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "q=Thank you very much&from=en&to=zh"

# Test 3: Question
curl -X POST "http://localhost:8000/api/demo/translate" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "q=What time is it?&from=en&to=zh"
```

## PowerShell Equivalent Commands

For Windows PowerShell users:

```powershell
# Health check
Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method Get

# Demo translation
$body = @{
    q = "Hello world"
    from = "en" 
    to = "zh"
}
Invoke-RestMethod -Uri "http://localhost:8000/api/demo/translate" -Method Post -Body $body
```

## Notes

1. **Content-Type:** Use `application/x-www-form-urlencoded` for form data
2. **Demo Endpoint:** Simplest for testing, automatically handles authentication
3. **Full API Endpoint:** Requires proper Baidu API signature calculation
4. **Service Status:** Always check `/api/health` first to ensure service is running
5. **Documentation:** Visit `/docs` for interactive API documentation

## Troubleshooting

- **404 Not Found:** Check endpoint path (remember `/api/` prefix)
- **Field Required:** Ensure all required parameters are included
- **Service Unavailable:** Check if service is running on port 8000
- **Invalid Response:** Verify Content-Type header for form submissions

Last updated: July 25, 2025
