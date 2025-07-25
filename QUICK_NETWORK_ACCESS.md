# 🌐 Quick Network Access Guide

This guide covers the essential steps to get your LLM Translation Service accessible from different networks.

## ✅ What We've Achieved

Your LLM Translation Service is now successfully configured and running with:

- **✅ Local Access**: `http://localhost:8000`
- **✅ Local Network Access**: `http://[YOUR_LOCAL_IP]:8000` (verified working)
- **✅ API Documentation**: `http://localhost:8000/docs`
- **✅ Network Interface Binding**: Service listens on `0.0.0.0:8000` (all interfaces)
- **✅ Environment Conflict Resolution**: System `ollama` variable handled properly

## 🚀 Quick Start Commands

### Start the Service
```powershell
# Clear conflicting environment variable and start service
Remove-Item Env:\ollama -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe run.py
```

### Test Local Access
```bash
# Test localhost
curl http://localhost:8000/api/health

# Test from local network (replace with your IP)
curl http://192.168.0.108:8000/api/health
```

### Using the Service Manager
```powershell
# Start with enhanced features
.\start-service.ps1 -NetworkInfo

# Check service status
.\service-manager.ps1 -Action status

# Stop service
.\service-manager.ps1 -Action stop
```

## 🌐 Network Access Levels

### 1. ✅ Local Access (Working)
- **URL**: `http://localhost:8000`
- **Use Case**: Testing and development
- **Status**: ✅ Verified working

### 2. ✅ Local Network Access (Working)
- **URL**: `http://[YOUR_LOCAL_IP]:8000` (e.g., `http://192.168.0.108:8000`)
- **Use Case**: Access from other devices on your WiFi/LAN
- **Status**: ✅ Verified working
- **Requirements**: 
  - Windows Firewall rules configured ✅
  - Service bound to `0.0.0.0:8000` ✅

### 3. 🔧 Internet Access (Requires Router Setup)
- **URL**: `http://[YOUR_PUBLIC_IP]:8080` (e.g., `http://137.175.101.243:8080`)
- **Use Case**: Access from anywhere on the internet
- **Status**: 🔧 Requires router port forwarding
- **Next Steps**: See router configuration below

## 🔧 Router Configuration for Internet Access

### Automated Setup
```powershell
.\deploy-online.ps1
```

### Manual Router Setup
1. **Access Router Admin Panel**:
   - URL: `http://192.168.0.1` or `http://192.168.1.1`
   - Login with admin credentials

2. **Configure Port Forwarding**:
   - **Service Name**: LLM Translation Service
   - **External Port**: `8080` (your choice)
   - **Internal IP**: `192.168.0.108` (your computer's IP)
   - **Internal Port**: `8000`
   - **Protocol**: TCP

3. **Save and Apply Settings**

4. **Test Internet Access**:
   ```bash
   # Test from external network (mobile data)
   curl http://137.175.101.243:8080/api/health
   ```

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### 1. Service Won't Start - JSON Parsing Error
**Problem**: `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`
**Solution**: Clear the conflicting `ollama` environment variable:
```powershell
Remove-Item Env:\ollama -ErrorAction SilentlyContinue
```

#### 2. "Invalid host header" Error
**Problem**: Service rejects requests from network IP
**Solution**: Ensure `DEBUG=true` in `.env` file (disables trusted host middleware)

#### 3. Can't Access from Local Network
**Problem**: Connection refused from other devices
**Solutions**:
- Check Windows Firewall: Run `.\deploy-online.ps1` to configure rules
- Verify service is bound to `0.0.0.0:8000` (not `127.0.0.1`)
- Check if antivirus is blocking connections

#### 4. Python Not Found
**Problem**: `Python was not found`
**Solution**: Use virtual environment Python:
```powershell
.\.venv\Scripts\python.exe run.py
```

## 📋 Verification Checklist

Before proceeding to internet access:

- [ ] ✅ Service starts without errors
- [ ] ✅ Local access works: `http://localhost:8000`
- [ ] ✅ Local network access works: `http://[LOCAL_IP]:8000`
- [ ] ✅ Health check returns healthy status
- [ ] ✅ API documentation accessible
- [ ] ✅ Windows Firewall configured
- [ ] 🔧 Router port forwarding configured (for internet access)

## 📖 Additional Resources

- **Full Production Setup**: `docs/PRODUCTION_SETUP_GUIDE.md`
- **Router Configuration**: `docs/ROUTER_SETUP_GUIDE.md`
- **Service Management**: Use `.\service-manager.ps1 -Action status`
- **Network Deployment**: `.\deploy-online.ps1`

## 🎉 Success!

Your LLM Translation Service is now accessible on your local network! Once you configure router port forwarding, it will be accessible from the internet worldwide.

**Current Status**: ✅ Local Network Access Achieved
**Next Step**: Configure router for internet access
