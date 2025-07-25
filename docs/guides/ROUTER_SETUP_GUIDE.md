# Router Port Forwarding Guide for LLM Translation Server

## 🌐 Making Your Server Internet-Accessible

This guide helps you configure your router to allow internet access to your Windows translation server.

## 📋 Before You Start

### Information You'll Need:
- **Your PC's Local IP**: Run `ipconfig` to find (e.g., 192.168.1.100)
- **Router Admin Password**: Usually on router label or manual
- **External Port**: Recommend 8080 (or any port 1024-65535)
- **Internal Port**: 8000 (your service port)

### Quick Check:
```powershell
# Find your local IP
ipconfig | findstr "IPv4"

# Find your public IP
curl -s https://ipinfo.io/ip

# Test local access first
curl http://localhost:8000/api/health
```

## 🔧 Router Configuration Steps

### Step 1: Access Router Admin Panel

#### Common Router IPs:
- **Linksys/Cisco**: `192.168.1.1`
- **Netgear**: `192.168.1.1` or `192.168.0.1`
- **TP-Link**: `192.168.0.1` or `tplinkwifi.net`
- **ASUS**: `192.168.1.1` or `router.asus.com`
- **D-Link**: `192.168.0.1` or `192.168.1.1`

#### Access Steps:
1. Open web browser
2. Go to your router's IP address
3. Enter admin username/password
4. Look for "Port Forwarding" or "Virtual Server"

### Step 2: Create Port Forwarding Rule

#### Standard Settings:
```
Service Name: LLM Translation Server
External Port: 8080
Internal IP: [YOUR_PC_IP]  (e.g., 192.168.1.100)
Internal Port: 8000
Protocol: TCP
Enable: Yes/Checked
```

#### Alternative Names (depending on router):
- **Service Type**: Custom
- **External Port Range**: 8080-8080
- **Internal Port Range**: 8000-8000
- **Local IP**: [YOUR_PC_IP]
- **Protocol**: TCP or TCP/UDP

## 🏭 Router-Specific Instructions

### Linksys/Cisco Routers
1. Navigate to **Smart Wi-Fi Tools** → **Port Range Forward**
2. Click "Add a New Single Port Forward"
3. Fill in the details above
4. Click **Save**

### Netgear Routers
1. Go to **Advanced** → **Dynamic DNS/Port Forwarding** → **Port Forwarding**
2. Click **Add Custom Service**
3. Enter service details
4. Click **Apply**

### TP-Link Routers
1. Navigate to **Advanced** → **NAT Forwarding** → **Virtual Servers**
2. Click **Add**
3. Fill in the port forwarding details
4. Click **Save**

### ASUS Routers
1. Go to **Adaptive QoS** → **Traditional QoS** → **Port Forward**
2. Enable "Enable Port Forward"
3. Add new rule with your details
4. Click **Apply**

### D-Link Routers
1. Navigate to **Advanced** → **Port Forwarding**
2. Click **Add**
3. Configure the rule
4. Click **Save Settings**

## 🔍 Testing Your Setup

### Step 1: Internal Test
```powershell
# Test from your PC
curl http://[YOUR_LOCAL_IP]:8080/api/health
# Should return: {"status": "healthy"}
```

### Step 2: External Test
```powershell
# Test from outside (use phone's mobile data or ask friend)
curl http://[YOUR_PUBLIC_IP]:8080/api/health
```

### Step 3: Online Port Checker
Visit online tools:
- **canyouseeme.org**
- **portchecker.co**
- **yougetsignal.com/tools/open-ports/**

Enter your public IP and port 8080 to verify it's open.

## 🛠️ Troubleshooting

### Port Forwarding Not Working?

#### 1. Check Firewall Settings
```powershell
# Verify Windows Firewall rule exists
Get-NetFirewallRule -DisplayName "*LLM Translation*"

# If missing, add rule:
New-NetFirewallRule -DisplayName "LLM Translation Service" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

#### 2. Verify Service is Running
```powershell
# Check if service is listening on port 8000
netstat -an | findstr :8000
# Should show: TCP 0.0.0.0:8000 LISTENING
```

#### 3. Test Local Network First
```powershell
# From another device on same network
curl http://[PC_LOCAL_IP]:8000/api/health
```

#### 4. Check Router Settings
- Verify internal IP is correct
- Ensure rule is enabled
- Try different external port
- Restart router after changes

#### 5. ISP Restrictions
Some ISPs block certain ports or home servers:
- Try alternative ports: 8080, 8090, 9000
- Contact ISP about server hosting policies
- Consider using Cloudflare Tunnel (bypasses ISP blocks)

### Double NAT Issues
If you have router behind another router:
1. Enable **Bridge Mode** on front router, OR
2. Configure port forwarding on both routers

### UPnP Alternative
If manual port forwarding fails:
1. Enable **UPnP** in router settings
2. Use UPnP tools to automatically configure ports

## 🔒 Security Considerations

### Recommended Security Measures:

#### 1. Change Default External Port
```
Instead of: External Port 8000
Use: External Port 8080, 8443, or random high port
```

#### 2. IP Restrictions (if supported)
```
Source IP: Specific IPs or ranges only
Example: 203.0.113.0/24 (your office network)
```

#### 3. Time-Based Rules (if supported)
```
Schedule: Weekdays 9 AM - 5 PM only
```

#### 4. Enable Router Logging
Track access attempts and unusual activity

#### 5. Regular Security Updates
- Keep router firmware updated
- Change admin passwords regularly
- Monitor connected devices

## 📱 Dynamic IP Solutions

### If Your Public IP Changes:

#### Option 1: Dynamic DNS (DDNS)
**NoIP.com Setup:**
1. Create free account at NoIP.com
2. Create hostname: `yourname.ddns.net`
3. Download NoIP DUC client
4. Configure client with your account

**DuckDNS.org Setup:**
1. Login with GitHub/Google
2. Create subdomain: `yourname.duckdns.org`
3. Set up automatic updates

#### Option 2: Cloudflare Tunnel (Advanced)
- No port forwarding needed
- Free SSL certificate included
- Better security and reliability
- Setup guide: [Cloudflare Tunnel Documentation]

## 📊 Monitoring Access

### Router Log Monitoring
Most routers provide access logs showing:
- Source IP addresses
- Timestamps
- Port access attempts
- Data transfer amounts

### Service-Level Monitoring
```powershell
# Check connection logs
Get-Content logs/production.log | Select-String "GET\|POST"

# Monitor active connections
netstat -an | findstr :8000
```

## 🚨 When Things Go Wrong

### Emergency Checklist:
1. **Can't access locally?** → Service issue
2. **Local works, external doesn't?** → Router/firewall issue
3. **Intermittent access?** → Dynamic IP issue
4. **Slow responses?** → Bandwidth/hardware issue
5. **Security alerts?** → Check access logs immediately

### Emergency Shutdown:
```powershell
# Stop the service immediately
taskkill /f /im python.exe

# Disable router port forwarding
# (Access router admin panel)
```

## 📞 Getting Help

### Resources:
- **Router Manual**: Model-specific instructions
- **ISP Support**: Port blocking policies
- **Network Tools**: Online port checkers
- **Community Forums**: Router-specific communities

### Common Error Messages:
- **"Connection refused"** → Service not running
- **"Connection timeout"** → Firewall/router blocking
- **"Host unreachable"** → Network configuration issue

---

**🎯 Success!** Once configured, your translation server will be accessible from anywhere on the internet via `http://[YOUR_PUBLIC_IP]:8080`
