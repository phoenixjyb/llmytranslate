# LLMyTranslate Remote Access Setup Guide

This guide helps you set up remote access to your LLMyTranslate service so clients can connect from other machines.

## Quick Start

### 1. Choose Your Access Method
```bash
./scripts/setup_remote_access_unified.sh
```

This will show you all available options.

### 2. Set Up Remote Access
```bash
# For private VPN access (recommended)
./scripts/setup_remote_access_unified.sh tailscale

# For public internet access  
./scripts/setup_remote_access_unified.sh ngrok

# For local network only
./scripts/setup_remote_access_unified.sh local
```

### 3. Start Your Service
```bash
python run.py
```

### 4. Share Connection Details
Give clients the service URL from step 2 to configure their connection.

## Access Methods Comparison

| Method | Security | Ease of Setup | Persistence | Best For |
|--------|----------|---------------|-------------|----------|
| **Tailscale** | 🔒 Private VPN | Medium | ✅ Stable IPs | Regular development |
| **ngrok** | 🌍 Public tunnel | Easy | ❌ URLs change | Quick sharing/demos |
| **Local** | 🏠 Network only | Very easy | ✅ Stable | Same network |

## Detailed Setup Instructions

### Tailscale Setup (Recommended)

**Advantages:**
- ✅ Secure encrypted VPN
- ✅ Stable IP addresses
- ✅ Works across networks
- ✅ Free for personal use

**Setup:**
```bash
./scripts/setup_remote_access_unified.sh tailscale
```

**Client Configuration:**
Clients need to:
1. Install Tailscale on their machine
2. Join the same Tailscale network
3. Use the Tailscale IP provided by the setup script

### ngrok Setup (Public Access)

**Advantages:**
- ✅ No client installation needed
- ✅ Public internet access
- ✅ Great for demos

**Limitations:**
- ❌ URL changes on restart
- ❌ Connection limits on free plan

**Setup:**
```bash
./scripts/setup_remote_access_unified.sh ngrok
```

**Client Configuration:**
Clients can use the ngrok URL directly (e.g., `https://abc123.ngrok.io`)

### Local Network Setup

**Advantages:**
- ✅ Simple setup
- ✅ Fast connections
- ✅ No external dependencies

**Limitations:**
- ❌ Same network only

**Setup:**
```bash
./scripts/setup_remote_access_unified.sh local
```

**Client Configuration:**
Clients use your local IP address (e.g., `http://192.168.1.100:8888`)

## Firewall Configuration

### macOS
```bash
# Allow incoming connections on port 8888
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add $(which python3)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp $(which python3)
```

### Linux (ufw)
```bash
sudo ufw allow 8888
```

### Windows
```powershell
# Run as Administrator
New-NetFirewallRule -DisplayName "LLMyTranslate" -Direction Inbound -Port 8888 -Protocol TCP -Action Allow
```

## Client Integration

Once you've set up remote access, clients (like the systemDesign project) can connect using:

```bash
# In the client project
./tools/scripts/configure_remote_service.sh
```

## Troubleshooting

### Service Not Reachable
1. Check if service is running: `curl http://localhost:8888/health`
2. Verify firewall settings
3. For Tailscale: Check `tailscale status`
4. For ngrok: Check `curl http://localhost:4040/api/tunnels`

### Connection Issues
1. Test local access first
2. Check network connectivity
3. Verify client configuration
4. Review service logs

### Performance Issues
1. Use Tailscale for best performance
2. Check network latency
3. Consider running service closer to clients

## Security Best Practices

1. **Use Tailscale** for production environments
2. **Limit ngrok usage** to demos and development
3. **Enable authentication** in production
4. **Monitor access logs** regularly
5. **Use HTTPS** in production (automatic with ngrok)

## Advanced Configuration

### Custom Domain (ngrok)
```bash
./scripts/setup_ngrok_enhanced.sh 8888 --domain your-domain.ngrok.io
```

### Multiple Clients
- Tailscale: All clients join the same network
- ngrok: Share the same tunnel URL
- Local: Ensure all clients are on the same network

### Load Balancing
For high-traffic scenarios, consider:
- Multiple service instances
- Load balancer (nginx, haproxy)
- Container orchestration (Docker Compose, Kubernetes)

## Integration Examples

### systemDesign Project
```bash
# Client-side configuration
cd /path/to/systemDesign
./tools/scripts/choose_access_method.sh
```

### Custom Applications
```bash
# Set environment variable
export LLM_SERVICE_URL="http://tailscale-ip:8888"

# Use in your application
curl -X POST "$LLM_SERVICE_URL/api/trans/vip/translate" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "q=Hello&from=en&to=zh&appid=demo&salt=123&sign=dummy"
```

## Scripts Reference

- `setup_remote_access_unified.sh` - Main setup script
- `setup_tailscale.sh` - Tailscale-specific setup
- `setup_ngrok_enhanced.sh` - Enhanced ngrok setup
- `stop_ngrok.sh` - Stop ngrok tunnels

## Support

For issues:
1. Check the troubleshooting section above
2. Review service logs
3. Test with local access first
4. Check network connectivity

