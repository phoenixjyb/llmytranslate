#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Configure LLM Translation Service for remote access
    
.DESCRIPTION
    This script helps configure the translation service for remote access by:
    - Setting up external binding (0.0.0.0)
    - Configuring Windows Firewall rules
    - Testing connectivity
    - Providing access information
    
.PARAMETER Port
    Service port (default: 8000)
    
.PARAMETER EnableFirewall
    Create Windows Firewall rule
    
.PARAMETER TestOnly
    Only test current configuration without making changes
    
.EXAMPLE
    .\configure-remote-access.ps1
    Configure service for remote access on default port
    
.EXAMPLE
    .\configure-remote-access.ps1 -Port 8080 -EnableFirewall
    Configure on port 8080 and create firewall rule
    
.EXAMPLE
    .\configure-remote-access.ps1 -TestOnly
    Test current remote access configuration
#>

param(
    [int]$Port = 8000,
    [switch]$EnableFirewall,
    [switch]$TestOnly
)

# Color output functions
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Error { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }
function Write-Warning { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Cyan }
function Write-Step { param($msg) Write-Host "🔄 $msg" -ForegroundColor Blue }

Write-Host @"
╔════════════════════════════════════════════════════════════════════════════════╗
║                         Remote Access Configuration                           ║
║                           LLM Translation Service                             ║
╚════════════════════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Magenta

Write-Info "Configuring remote access for LLM Translation Service"
Write-Info "Target Port: $Port"
Write-Host ""

# Function to get local IP address
function Get-LocalIPAddress {
    try {
        $ip = (Get-NetIPConfiguration | Where-Object {$_.IPv4DefaultGateway -ne $null}).IPv4Address.IPAddress | Select-Object -First 1
        return $ip
    } catch {
        return "Unable to determine"
    }
}

# Function to get public IP address
function Get-PublicIPAddress {
    try {
        $ip = (Invoke-WebRequest -UseBasicParsing "http://ipinfo.io/ip" -TimeoutSec 5).Content.Trim()
        return $ip
    } catch {
        return "Unable to determine"
    }
}

# Function to test if port is listening
function Test-PortListening {
    param([int]$TestPort)
    
    try {
        $listening = Get-NetTCPConnection -LocalPort $TestPort -State Listen -ErrorAction SilentlyContinue
        return $listening.Count -gt 0
    } catch {
        return $false
    }
}

# Function to check firewall rules
function Test-FirewallRule {
    param([int]$TestPort)
    
    try {
        $rule = Get-NetFirewallRule | Where-Object {
            $_.DisplayName -like "*Translation*" -or 
            $_.DisplayName -like "*LLM*" -or
            ($_.LocalPort -eq $TestPort -and $_.Direction -eq "Inbound")
        }
        return $rule.Count -gt 0
    } catch {
        return $false
    }
}

# Test current configuration
function Test-Configuration {
    Write-Step "Testing current configuration..."
    
    $localIP = Get-LocalIPAddress
    $publicIP = Get-PublicIPAddress
    $isListening = Test-PortListening -TestPort $Port
    $hasFirewallRule = Test-FirewallRule -TestPort $Port
    
    Write-Info "Network Information:"
    Write-Host "  Local IP: $localIP" -ForegroundColor Gray
    Write-Host "  Public IP: $publicIP" -ForegroundColor Gray
    Write-Host ""
    
    if ($isListening) {
        Write-Success "Service is listening on port $Port"
    } else {
        Write-Warning "Service is NOT listening on port $Port"
        Write-Info "Make sure the translation service is running"
    }
    
    if ($hasFirewallRule) {
        Write-Success "Windows Firewall rule exists for the service"
    } else {
        Write-Warning "No Windows Firewall rule found"
        Write-Info "Run with -EnableFirewall to create a rule"
    }
    
    # Test local connectivity
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$Port/api/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        Write-Success "Local health check successful"
    } catch {
        Write-Warning "Local health check failed: $($_.Exception.Message)"
    }
    
    Write-Host ""
    Write-Info "Access URLs:"
    Write-Host "  Local: http://localhost:$Port" -ForegroundColor Cyan
    Write-Host "  Local Network: http://$localIP`:$Port" -ForegroundColor Cyan
    Write-Host "  External: http://$publicIP`:$Port (requires port forwarding)" -ForegroundColor Cyan
    Write-Host ""
}

# Configure .env file for remote access
function Set-RemoteConfig {
    Write-Step "Configuring service for remote access..."
    
    $envFile = ".env"
    
    if (Test-Path $envFile) {
        $content = Get-Content $envFile
        $newContent = @()
        $hostSet = $false
        $portSet = $false
        
        foreach ($line in $content) {
            if ($line -match "^API__HOST=") {
                $newContent += "API__HOST=0.0.0.0"
                $hostSet = $true
            } elseif ($line -match "^API__PORT=") {
                $newContent += "API__PORT=$Port"
                $portSet = $true
            } else {
                $newContent += $line
            }
        }
        
        if (-not $hostSet) {
            $newContent += "API__HOST=0.0.0.0"
        }
        if (-not $portSet) {
            $newContent += "API__PORT=$Port"
        }
        
        $newContent | Out-File -FilePath $envFile -Encoding UTF8
        Write-Success "Updated .env file for remote access"
    } else {
        @(
            "# Remote access configuration",
            "ENVIRONMENT=development",
            "DEBUG=true",
            "API__HOST=0.0.0.0",
            "API__PORT=$Port"
        ) | Out-File -FilePath $envFile -Encoding UTF8
        Write-Success "Created .env file for remote access"
    }
}

# Create Windows Firewall rule
function Set-FirewallRule {
    Write-Step "Creating Windows Firewall rule..."
    
    try {
        $ruleName = "LLM Translation Service - Port $Port"
        
        # Remove existing rule if it exists
        Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
        
        # Create new rule
        New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP -LocalPort $Port -Action Allow -ErrorAction Stop
        Write-Success "Created Windows Firewall rule: $ruleName"
    } catch {
        Write-Error "Failed to create firewall rule: $($_.Exception.Message)"
        Write-Info "You may need to run PowerShell as Administrator"
    }
}

# Main execution
try {
    if ($TestOnly) {
        Test-Configuration
    } else {
        # Configure for remote access
        Set-RemoteConfig
        
        if ($EnableFirewall) {
            Set-FirewallRule
        }
        
        Write-Host ""
        Test-Configuration
        
        Write-Host ""
        Write-Warning "Next Steps:"
        Write-Host "1. Restart the translation service to apply new settings" -ForegroundColor Yellow
        Write-Host "2. Configure router port forwarding (if needed for external access)" -ForegroundColor Yellow
        Write-Host "3. Test access from remote computers" -ForegroundColor Yellow
        Write-Host ""
        Write-Info "For detailed setup instructions, see: REMOTE_ACCESS_GUIDE.md"
    }
    
} catch {
    Write-Error "Configuration failed: $_"
    exit 1
} finally {
    Write-Host ""
    Write-Info "Remote access configuration completed at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
}
