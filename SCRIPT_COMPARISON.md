# Service Management Scripts Comparison

This document compares the different service management scripts available in the LLM Translation Service project.

## 📊 Script Comparison Table

| Feature | `stop-service.ps1` | `shutdown.ps1` (New) | `shutdown.bat` | `shutdown.sh` |
|---------|-------------------|----------------------|----------------|---------------|
| **Platform** | Windows | Windows | Windows | Unix/Linux/macOS |
| **Translation Service** | ✅ | ✅ | ✅ | ✅ |
| **Ollama Service** | ❌ | ✅ | ✅ | ✅ |
| **ngrok Service** | ✅ | ✅ | ✅ | ✅ |
| **Tailscale Service** | ❌ | ✅ | ✅ | ✅ |
| **Graceful API Shutdown** | ✅ | ✅ | ✅ | ✅ |
| **Force Stop Option** | ✅ | ✅ | ✅ | ✅ |
| **Selective Service Stop** | ✅ | ✅ | ✅ | ✅ |
| **Port Verification** | ❌ | ✅ | ✅ | ✅ |
| **Color Output** | ✅ | ✅ | ❌ | ✅ |
| **Silent Mode** | ❌ | ✅ | ✅ | ✅ |
| **Comprehensive Logging** | ✅ | ✅ | ✅ | ✅ |
| **Cross-Platform** | ❌ | ❌ | ❌ | ✅ |

## 🎯 When to Use Which Script

### Use `stop-service.ps1` when:
- ✅ You only need to stop translation service and ngrok
- ✅ You're using the existing project workflow
- ✅ You want selective service management (ServiceOnly, NgrokOnly)
- ✅ You prefer the established project conventions

### Use `shutdown.ps1` when:
- ✅ You need comprehensive system shutdown including Tailscale
- ✅ You want to stop Ollama services as well
- ✅ You need port verification and detailed status checking
- ✅ You want more granular control over what stays running
- ✅ You prefer silent operation modes

### Use `shutdown.bat` when:
- ✅ You're on older Windows systems
- ✅ You don't have PowerShell permissions
- ✅ You need a simple, dependency-free solution
- ✅ You're automating with basic batch scripting

### Use `shutdown.sh` when:
- ✅ You're on Unix/Linux/macOS systems
- ✅ You need cross-platform compatibility
- ✅ You're integrating with bash-based workflows
- ✅ You want standard Unix tool integration

## 🔄 Migration Guide

### From `stop-service.ps1` to `shutdown.ps1`

#### Basic Usage
```powershell
# Old way
.\stop-service.ps1

# New way (equivalent)
.\shutdown.ps1 -KeepTailscale  # Keeps Tailscale if you don't want to stop it
```

#### Force Stop
```powershell
# Old way
.\stop-service.ps1 -Force

# New way (equivalent)
.\shutdown.ps1 -Force
```

#### Selective Service Management
```powershell
# Old way - Stop only ngrok
.\stop-service.ps1 -NgrokOnly

# New way - Stop everything except ngrok
.\shutdown.ps1 -KeepNgrok

# Old way - Stop only service
.\stop-service.ps1 -ServiceOnly

# New way - Stop everything except ngrok and tailscale
.\shutdown.ps1 -KeepNgrok -KeepTailscale
```

#### Verbose Output
```powershell
# Old way
.\stop-service.ps1 -Verbose

# New way (verbose is default, use -Quiet for silent)
.\shutdown.ps1
# or for silent
.\shutdown.ps1 -Quiet
```

## 🆕 New Features in Shutdown Scripts

### 1. Tailscale Management
- Graceful logout before process termination
- Support for multiple Tailscale processes (client, daemon)
- Option to keep Tailscale running while stopping other services

### 2. Ollama Service Management
- Automatic detection and stopping of Ollama processes
- Port 11434 verification and cleanup

### 3. Enhanced Port Verification
- Comprehensive port status checking
- Verification that ports are actually released
- Detection of services still using target ports

### 4. Cross-Platform Support
- Unified command syntax across platforms
- Platform-specific optimizations
- Consistent behavior regardless of OS

### 5. Silent Operation Mode
- Quiet mode for automation and scripting
- Minimal output for CI/CD integration
- Error-only reporting option

## 🔧 Advanced Usage Examples

### Development Workflow
```powershell
# Quick restart during development (keep network services)
.\shutdown.ps1 -KeepTailscale -KeepNgrok -Quiet
.\start-service.ps1

# Complete clean restart
.\shutdown.ps1 -Force
.\start-service.ps1 -Force
```

### Production Deployment
```powershell
# Graceful production shutdown
.\shutdown.ps1 -Quiet

# Emergency shutdown
.\shutdown.ps1 -Force -Quiet
```

### Testing Environment
```powershell
# Clean slate for testing
.\shutdown.ps1 -Force
# Verify clean state
netstat -ano | findstr ":8000\|:11434\|:4040"
```

### Remote Development
```powershell
# Keep remote access while restarting services
.\shutdown.ps1 -KeepTailscale -KeepNgrok
.\start-service.ps1
```

## 📝 Script Maintenance

Both script families are actively maintained:

- **`stop-service.ps1`** - Part of the core project scripts, focused on translation service management
- **`shutdown.ps1`** - Comprehensive system management, includes network services and modern service management

Choose the one that best fits your workflow and requirements. Both will continue to be supported and updated as the project evolves.
