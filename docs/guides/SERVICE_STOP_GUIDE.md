# 🛑 Service Stop Procedures

This document describes how to properly stop the LLM Translation Service and related components.

## Quick Stop Commands

### Windows PowerShell
```powershell
# Stop both translation service and ngrok
.\stop-service.ps1

# Stop with detailed output
.\stop-service.ps1 -Verbose

# Force stop all services
.\stop-service.ps1 -Force

# Stop only specific services
.\stop-service.ps1 -NgrokOnly     # Stop only ngrok
.\stop-service.ps1 -ServiceOnly   # Stop only translation service
```

### Direct Script Access
```powershell
# Run the main stop script directly
.\scripts\stop-service.ps1

# All the same parameters work
.\scripts\stop-service.ps1 -Force -Verbose
```

## Stop Methods Used

### Translation Service Stop Process
1. **Port Detection**: Identifies processes using port 8000
2. **Process Identification**: Finds Python processes running translation services
3. **Graceful Shutdown**: Attempts to close processes normally first
4. **Force Termination**: Uses force termination if graceful shutdown fails
5. **Verification**: Tests that the service is no longer responding

### Ngrok Stop Process
1. **Process Detection**: Finds all ngrok processes
2. **Graceful Shutdown**: Attempts to close main window first
3. **Force Termination**: Uses force termination if needed
4. **Verification**: Confirms all ngrok processes are stopped

## Parameters

| Parameter | Description |
|-----------|-------------|
| `-Force` | Skip graceful shutdown, immediately force terminate |
| `-NgrokOnly` | Stop only ngrok tunnel, leave translation service running |
| `-ServiceOnly` | Stop only translation service, leave ngrok running |
| `-Verbose` | Show detailed output of stop process |

## Manual Stop Procedures

If the automated script fails, you can manually stop services:

### Manual Translation Service Stop
```powershell
# Find processes using port 8000
netstat -ano | findstr :8000

# Stop the process (replace PID with actual process ID)
Stop-Process -Id <PID> -Force

# Verify service is stopped
curl http://localhost:8000/api/health
# Should return "connection refused" error
```

### Manual Ngrok Stop
```powershell
# Find ngrok processes
Get-Process -Name "ngrok"

# Stop ngrok processes
Get-Process -Name "ngrok" | Stop-Process -Force

# Verify ngrok is stopped
Get-Process -Name "ngrok" -ErrorAction SilentlyContinue
# Should return no results
```

## Status Verification

After running the stop script, you'll see a status summary:

```
📊 Service Status Check:
  🚇 Ngrok: ✅ Stopped
  🔴 Translation Service: ✅ Stopped
  🏥 Health Check: ✅ Connection refused (service stopped)
```

## Troubleshooting

### Services Won't Stop
- Try using `-Force` parameter
- Check for multiple Python environments running
- Verify you have administrative privileges
- Use Task Manager as last resort

### Port Still in Use
```powershell
# Check what's using port 8000
netstat -ano | findstr :8000

# Kill specific process
taskkill /PID <process_id> /F
```

### Ngrok Tunnel Still Active
```powershell
# Check ngrok web interface
curl http://127.0.0.1:4040/api/tunnels

# Force kill all ngrok processes
taskkill /IM ngrok.exe /F
```

## Integration with Other Scripts

The stop service script is designed to integrate with other project scripts:

```powershell
# Stop services before running setup
.\stop-service.ps1
.\scripts\setup.ps1

# Stop and restart services
.\stop-service.ps1
.\start-service.ps1

# Stop before git operations
.\stop-service.ps1
git pull
.\start-service.ps1
```

## Exit Codes

- `0`: All services stopped successfully
- `1`: Error occurred during stop process

## Best Practices

1. **Always stop services** before system maintenance
2. **Use graceful shutdown** (default) unless services are hung
3. **Verify services are stopped** before proceeding with other tasks
4. **Use verbose mode** for troubleshooting
5. **Check status summary** to confirm successful stop
