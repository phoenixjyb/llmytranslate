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

## Remote Access from Outside Networks

### Quick Setup for External Access

#### Option 1: Simple Network Access (Local Network)
If you want to access from other devices on your local network:

1. **Find your local IP:**
```bash
ipconfig | findstr IPv4
```

2. **Access from other devices on same network:**
```bash
# Replace 192.168.1.100 with your actual local IP
curl http://192.168.1.100:8000/api/health
curl -X POST "http://192.168.1.100:8000/api/demo/translate" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "q=Hello world&from=en&to=zh"
```

#### Option 2: Internet Access (Using Ngrok - Easiest)

1. **Install ngrok:**
```powershell
# Using Chocolatey
choco install ngrok

# Or download from https://ngrok.com/
```

2. **Start your translation service locally**
3. **Create public tunnel:**
```powershell
ngrok http 8000
```

4. **Use the ngrok URL (example):**
```bash
# Ngrok will provide a URL like: https://abc123.ngrok.io
curl https://abc123.ngrok.io/api/health
curl -X POST "https://abc123.ngrok.io/api/demo/translate" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "q=Hello world&from=en&to=zh"
```

#### Option 3: Permanent VPN Access (Using ZeroTier - Most Secure)

1. **Install ZeroTier:**
```powershell
# Using Chocolatey
choco install zerotier-one

# Or download from https://www.zerotier.com/download/
```

2. **Create network at:** https://my.zerotier.com/
3. **Join network on this computer:**
```powershell
zerotier-cli join YOUR_NETWORK_ID
```

4. **Authorize device in ZeroTier Central**
5. **Install ZeroTier on remote devices and join same network**
6. **Access using ZeroTier IP:**
```bash
# Use the ZeroTier IP assigned to your computer
curl http://172.28.1.100:8000/api/health
curl -X POST "http://172.28.1.100:8000/api/demo/translate" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "q=Hello world&from=en&to=zh"
```

#### Option 4: Port Forwarding (Permanent Solution)

1. **Configure Windows Firewall:**
```powershell
New-NetFirewallRule -DisplayName "LLM Translation Service" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

2. **Set up router port forwarding:**
   - External Port: 8000
   - Internal IP: Your PC's local IP
   - Internal Port: 8000

3. **Find your public IP:**
```powershell
(Invoke-WebRequest -UseBasicParsing "http://ipinfo.io/ip").Content.Trim()
```

4. **Access from anywhere:**
```bash
# Replace YOUR_PUBLIC_IP with your actual public IP
curl http://YOUR_PUBLIC_IP:8000/api/health
```

**⚠️ Security Note:** For production use, consider adding authentication, HTTPS, and restricting access to trusted IPs.

### 🔍 **Comparison: Ngrok vs ZeroTier vs Port Forwarding**

| Method | Ease of Setup | Security | Permanence | Cost |
|--------|---------------|----------|------------|------|
| **Ngrok** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | Free tier limited |
| **ZeroTier** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Free up to 25 devices |
| **Port Forward** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | Free |

**Recommendations:**
- **Quick demos/testing:** Use Ngrok
- **Permanent secure access:** Use ZeroTier  
- **Public production service:** Use Port Forwarding + Nginx

For detailed configuration options, see: `docs/guides/REMOTE_ACCESS_GUIDE.md`

## Troubleshooting

- **404 Not Found:** Check endpoint path (remember `/api/` prefix)
- **Field Required:** Ensure all required parameters are included
- **Service Unavailable:** Check if service is running on port 8000
- **Invalid Response:** Verify Content-Type header for form submissions
- **Connection Refused (Remote):** Check firewall settings and port forwarding
- **Timeout (Remote):** Verify your public IP and ensure router port forwarding is correct

Last updated: July 25, 2025
