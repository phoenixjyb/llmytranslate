# 🚀 Service Management Scripts

This document provides a comprehensive guide to starting and stopping the LLM Translation Service.

## 🟢 Starting Services

### Quick Start
```powershell
# Start translation service and auto-configure
.\start-service.ps1

# Start with specific options
.\start-service.ps1 -Production    # Production mode
.\start-service.ps1 -Debug         # Debug mode
.\start-service.ps1 -Force         # Force start (ignore conflicts)
```

### Ngrok Tunnel Setup
```powershell
# Setup ngrok with auth token (first time)
.\scripts\setup_ngrok.ps1 YOUR_AUTH_TOKEN

# Start ngrok tunnel (after service is running)
ngrok http 8000
```

## 🛑 Stopping Services

### Quick Stop
```powershell
# Stop both translation service and ngrok
.\stop-service.ps1

# Stop with detailed output
.\stop-service.ps1 -Verbose

# Force stop all services (if graceful shutdown fails)
.\stop-service.ps1 -Force
```

### Selective Stop
```powershell
# Stop only ngrok tunnel
.\stop-service.ps1 -NgrokOnly

# Stop only translation service
.\stop-service.ps1 -ServiceOnly
```

## 📋 Complete Workflow Examples

### Development Workflow
```powershell
# 1. Start services
.\start-service.ps1

# 2. Start ngrok for remote access
ngrok http 8000

# 3. Do your work...

# 4. Stop everything when done
.\stop-service.ps1
```

### Production Workflow
```powershell
# 1. Setup production environment
.\scripts\production-setup.ps1

# 2. Start in production mode
.\start-service.ps1 -Production

# 3. Setup remote access if needed
.\scripts\configure-remote-access.ps1

# 4. Graceful shutdown when needed
.\stop-service.ps1
```

### Troubleshooting Workflow
```powershell
# 1. Stop all services
.\stop-service.ps1 -Force

# 2. Validate environment
python validate.py

# 3. Restart services
.\start-service.ps1 -Debug -Verbose
```

## 🔍 Service Status Checking

### Health Check
```powershell
# Check if service is running
curl http://localhost:8000/api/health

# Check detailed service status
python validate.py

# Check running processes
Get-Process python, ngrok -ErrorAction SilentlyContinue
```

### Port Usage Check
```powershell
# Check what's using port 8000
netstat -ano | findstr :8000

# Check ngrok web interface
curl http://127.0.0.1:4040/api/tunnels
```

## 🚨 Emergency Procedures

### Force Kill Everything
```powershell
# Nuclear option - stop all related processes
Get-Process python, ngrok -ErrorAction SilentlyContinue | Stop-Process -Force

# Kill specific port usage
$portProcess = netstat -ano | Select-String ":8000.*LISTENING"
if ($portProcess) {
    $pid = ($portProcess.Line -split '\s+')[-1]
    Stop-Process -Id $pid -Force
}
```

### Service Recovery
```powershell
# 1. Complete stop
.\stop-service.ps1 -Force

# 2. Clean restart
.\start-service.ps1 -Force

# 3. Verify everything is working
python validate.py
curl http://localhost:8000/api/health
```

## 📖 Script Locations

- **Start Service**: `.\start-service.ps1` → `.\scripts\start-service.ps1`
- **Stop Service**: `.\stop-service.ps1` → `.\scripts\stop-service.ps1`
- **Ngrok Setup**: `.\scripts\setup_ngrok.ps1`
- **Production Setup**: `.\scripts\production-setup.ps1`
- **Service Manager**: `.\scripts\service-manager.ps1`

## 💡 Best Practices

1. **Always use stop script** before shutting down or restarting
2. **Use verbose mode** when troubleshooting: `-Verbose`
3. **Check service status** before starting new instances
4. **Use force mode sparingly** - only when graceful shutdown fails
5. **Keep ngrok auth token secure** and don't commit it to git

## 🔧 Advanced Usage

### Custom Service Management
```powershell
# Using the service manager script
.\scripts\service-manager.ps1

# Environment-specific commands
.\scripts\start-service.ps1 -Debug
.\scripts\stop-service.ps1 -Force
```

### Integration with CI/CD
```powershell
# Pre-deployment stop
.\stop-service.ps1 -Force

# Post-deployment start
.\start-service.ps1 -Production

# Health verification
if (!(curl http://localhost:8000/api/health)) {
    Write-Error "Service failed to start"
    exit 1
}
```