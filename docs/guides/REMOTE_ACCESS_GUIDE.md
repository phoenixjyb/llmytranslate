# 🌐 Remote Access Configuration Guide

This guide explains how to access the LLM Translation Service from remote computers on different networks.

## 🏗️ Architecture Overview

```
Remote PC (Different Network) → Internet → Your Network → Translation Service
```

## 🔧 Configuration Methods

### Method 1: Direct Network Exposure (Development/Testing)

#### 1. **Modify Service Binding**

Update your `.env` file to bind to all interfaces:

```properties
# Allow external connections
API__HOST=0.0.0.0
API__PORT=8000
DEBUG=true
```

#### 2. **Start Service with External Binding**

```powershell
# Using startup script
.\start-service.ps1 -Port 8000

# Or manually
.\.venv\Scripts\python.exe run.py
```

#### 3. **Configure Windows Firewall**

```powershell
# Allow inbound connections on port 8000
New-NetFirewallRule -DisplayName "LLM Translation Service" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow

# Or use GUI: Windows Security → Firewall → Allow an app
```

#### 4. **Router Port Forwarding**

Configure your router to forward external requests:
- **External Port**: 8000 (or different for security)
- **Internal IP**: Your PC's local IP (e.g., 192.168.1.100)
- **Internal Port**: 8000
- **Protocol**: TCP

#### 5. **Find Your Public IP**

```powershell
# Get your public IP
(Invoke-WebRequest -UseBasicParsing "http://ipinfo.io/ip").Content.Trim()
```

#### 6. **Access from Remote PC**

```bash
# Replace YOUR_PUBLIC_IP with actual IP
curl http://YOUR_PUBLIC_IP:8000/api/health
```

---

### Method 2: Reverse Proxy with Nginx (Recommended)

#### 1. **Install Nginx** (if not already installed)

```powershell
# Using Chocolatey
choco install nginx

# Or download from https://nginx.org/en/download.html
```

#### 2. **Configure Nginx**

Create/modify `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream translation_service {
        server 127.0.0.1:8000;
    }
    
    server {
        listen 80;
        server_name your-domain.com;  # Or use IP
        
        # Optional: Basic authentication
        # auth_basic "Translation Service";
        # auth_basic_user_file /path/to/.htpasswd;
        
        location / {
            proxy_pass http://translation_service;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # CORS headers for web clients
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
            add_header Access-Control-Allow-Headers "Content-Type, Authorization";
        }
        
        # Health check endpoint
        location /health {
            proxy_pass http://translation_service/api/health;
        }
    }
}
```

#### 3. **Start Services**

```powershell
# Start translation service (localhost only)
.\start-service.ps1

# Start Nginx
nginx
```

#### 4. **Configure Router**

Forward port 80 (HTTP) to your PC's local IP.

---

### Method 3: Cloud Tunneling (Easiest for Testing)

#### Option A: Ngrok (Free tier available)

```powershell
# Install ngrok
choco install ngrok

# Start translation service locally
.\start-service.ps1

# In another terminal, create tunnel
ngrok http 8000
```

Access via the ngrok URL (e.g., `https://abc123.ngrok.io`)

#### Option B: Cloudflare Tunnel (Free)

```powershell
# Install cloudflared
choco install cloudflared

# Start translation service
.\start-service.ps1

# Create tunnel
cloudflared tunnel --url http://localhost:8000
```

#### Option C: VS Code Port Forwarding

If using VS Code with Remote Development:
1. Start the service locally
2. Go to "Ports" tab in VS Code
3. Forward port 8000
4. Set visibility to "Public"

---

### Method 4: VPN Access (Most Secure)

#### 1. **Set up VPN Server**

Options:
- **WireGuard**: Modern, fast VPN
- **OpenVPN**: Traditional, widely supported
- **Windows Built-in VPN**: Basic PPTP/L2TP

#### 2. **Configure Translation Service**

```properties
# .env - bind to VPN interface or all interfaces
API__HOST=0.0.0.0
API__PORT=8000
```

#### 3. **Client Access**

Remote clients connect via VPN, then access service using your local IP:
```bash
curl http://192.168.1.100:8000/api/health
```

---

## 🔒 Security Considerations

### Essential Security Measures

#### 1. **Authentication & Authorization**

Update `.env` to enable authentication:

```properties
# Enable authentication
AUTH__DISABLE_SIGNATURE_VALIDATION=false
AUTH__SECRET_KEY=your-very-secure-random-key-here
AUTH__ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### 2. **Rate Limiting**

```properties
# Configure rate limits
RATE_LIMIT__REQUESTS_PER_MINUTE=60
RATE_LIMIT__REQUESTS_PER_HOUR=1000
RATE_LIMIT__REQUESTS_PER_DAY=10000
```

#### 3. **HTTPS/TLS**

For production, always use HTTPS:

```nginx
server {
    listen 443 ssl;
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # ... rest of config
}
```

#### 4. **Firewall Rules**

```powershell
# Allow only specific IPs (replace with actual IPs)
New-NetFirewallRule -DisplayName "Translation Service - Specific IPs" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -RemoteAddress "203.0.113.0/24"
```

#### 5. **API Keys**

Implement API key authentication for programmatic access.

---

## 📋 Quick Setup Checklist

### For Development/Testing (Method 1):
- [ ] Update `.env` with `API__HOST=0.0.0.0`
- [ ] Configure Windows Firewall
- [ ] Set up router port forwarding
- [ ] Test local access: `http://localhost:8000/api/health`
- [ ] Test remote access: `http://YOUR_PUBLIC_IP:8000/api/health`

### For Production (Method 2):
- [ ] Set up Nginx reverse proxy
- [ ] Configure HTTPS certificates
- [ ] Enable authentication
- [ ] Set up rate limiting
- [ ] Configure proper firewall rules
- [ ] Test security configuration

---

## 🧪 Testing Remote Access

### From Remote PC:

```bash
# Health check
curl http://YOUR_IP_OR_DOMAIN:PORT/api/health

# Translation test
curl -X POST "http://YOUR_IP_OR_DOMAIN:PORT/api/demo/translate" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "q=hello world&from=en&to=zh"

# Check API documentation
# Visit: http://YOUR_IP_OR_DOMAIN:PORT/docs
```

### Expected Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-07-24T14:40:00Z",
  "version": "1.0.0"
}
```

---

## 🐛 Troubleshooting Remote Access

### Common Issues:

1. **Connection Refused**
   - Check if service binds to `0.0.0.0` not `127.0.0.1`
   - Verify Windows Firewall allows the port
   - Confirm router port forwarding is configured

2. **Timeout**
   - Check ISP doesn't block the port
   - Verify router firewall settings
   - Test with different ports (80, 443, 8080)

3. **403 Forbidden**
   - Check authentication settings
   - Verify CORS configuration
   - Review nginx access rules

4. **Service Not Accessible**
   ```powershell
   # Check if service is running and listening
   netstat -an | findstr :8000
   
   # Test local access first
   curl http://localhost:8000/api/health
   ```

### Debug Commands:

```powershell
# Check Windows Firewall rules
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*Translation*"}

# Check open ports
netstat -an | findstr LISTENING

# Test connectivity from local network
Test-NetConnection -ComputerName 192.168.1.100 -Port 8000
```

---

## 🌟 Recommended Approach

**For Development/Testing**: Use **Method 3 (Tunneling)** with ngrok or Cloudflare
**For Production**: Use **Method 2 (Reverse Proxy)** with proper security
**For Team Access**: Use **Method 4 (VPN)** for secure team access

Choose the method that best fits your security requirements and technical setup!
