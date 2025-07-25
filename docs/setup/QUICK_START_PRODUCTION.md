# Quick Start Guide for Internet-Accessible Translation Server

## 🚀 One-Click Production Setup

### Option 1: Automated Setup (Recommended)
```powershell
# Run as Administrator
.\production-setup.ps1 -EnableHTTPS -InstallNginx
```

### Option 2: Manual Setup Steps

#### 1. 🔧 Network Configuration
```powershell
# Check your local IP
ipconfig | findstr "IPv4"

# Your router settings needed:
# External Port: 8080 → Internal IP: [YOUR_IP] → Internal Port: 8000
```

#### 2. 🚀 Start Production Service
```powershell
.\start-production.ps1
```

#### 3. 🌐 Access Your Server
- **Local Network**: `http://[YOUR_LOCAL_IP]:8080`
- **Internet**: `http://[YOUR_PUBLIC_IP]:8080` (after port forwarding)
- **API Docs**: Add `/docs` to any URL above

## 📱 Client Access Examples

### Python Client
```python
import requests

# Replace with your server's IP/domain
server_url = "http://YOUR_SERVER_IP:8080"

response = requests.post(f"{server_url}/api/translate", 
    json={
        "text": "Hello, world!",
        "target_language": "Spanish",
        "api_key": "your-api-key"
    }
)
print(response.json())
```

### JavaScript Client
```javascript
const serverUrl = "http://YOUR_SERVER_IP:8080";

fetch(`${serverUrl}/api/translate`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        text: "Hello, world!",
        target_language: "Spanish",
        api_key: "your-api-key"
    })
})
.then(response => response.json())
.then(data => console.log(data));
```

### cURL Command
```bash
curl -X POST "http://YOUR_SERVER_IP:8080/api/translate" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Hello, world!",
       "target_language": "Spanish", 
       "api_key": "your-api-key"
     }'
```

## 🔒 Security Checklist

### ✅ Before Going Live:
- [ ] Set strong API keys
- [ ] Configure router port forwarding
- [ ] Test from external network
- [ ] Enable HTTPS (recommended)
- [ ] Set up monitoring
- [ ] Configure backups

### 🛡️ Security Features Included:
- Rate limiting (30 requests/minute per IP)
- Request size limits (1MB max)
- IP filtering capabilities
- Security headers
- Access logging
- Health monitoring

## 🌍 Dynamic DNS Setup (Optional)

### Free DDNS Services:
1. **NoIP.com**
   - Create account → Add hostname → Install DUC client
   - Your URL: `http://yourname.ddns.net:8080`

2. **DuckDNS.org**
   - Simple setup with token
   - Your URL: `http://yourname.duckdns.org:8080`

3. **Cloudflare Tunnel** (Advanced)
   - No port forwarding needed
   - Free SSL included
   - Better security

## 📊 Monitoring Your Server

### Health Check
```powershell
.\monitor-health.ps1
```

### Continuous Monitoring
```powershell
.\monitor-health.ps1 -Continuous
```

### Check Logs
```powershell
Get-Content logs/production.log -Tail 50 -Wait
```

## 🛠️ Troubleshooting

### Common Issues:

1. **Can't access from internet**
   - Check router port forwarding
   - Verify Windows Firewall allows port 8000
   - Test with local IP first

2. **Service not responding**
   - Check if Ollama is running: `ollama list`
   - Restart service: `.\start-production.ps1`
   - Check logs for errors

3. **High resource usage**
   - Monitor CPU/Memory in Task Manager
   - Consider smaller Ollama model
   - Adjust rate limits

## 📈 Performance Optimization

### For High Traffic:
```powershell
# Use more workers
$env:API_WORKERS = "8"

# Increase connection limits  
$env:MAX_CONCURRENT_REQUESTS = "200"

# Enable caching
$env:CACHE_ENABLED = "true"
```

### Hardware Recommendations:
- **Light usage**: 8GB RAM, 4 cores
- **Medium usage**: 16GB RAM, 8 cores  
- **Heavy usage**: 32GB+ RAM, 16+ cores

## 🌐 Advanced Features

### Geographic Restrictions
```env
GEO_BLOCKING_ENABLED=true
ALLOWED_COUNTRIES=["US", "CA", "GB"]
```

### IP Whitelisting
```env
ALLOWED_IPS=["192.168.1.0/24", "10.0.0.0/8"]
```

### Custom Domain with HTTPS
1. Get domain name
2. Point A record to your public IP
3. Get SSL certificate (Let's Encrypt)
4. Configure nginx for HTTPS

## 📞 Support & Resources

### Getting Help:
- Check logs: `logs/production.log`
- Test health: `http://localhost:8000/api/health`
- API docs: `http://localhost:8000/docs`

### Community:
- Report issues on GitHub
- Check documentation
- Join discussions

---

**🎉 Congratulations!** Your Windows PC is now a powerful translation server accessible from anywhere on the internet!
