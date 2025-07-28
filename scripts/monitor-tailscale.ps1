#!/usr/bin/env powershell
<#
.SYNOPSIS
Monitor and restart Tailscale if it becomes unresponsive.

.DESCRIPTION
This script checks if Tailscale is responding and restarts it if needed.
Run this periodically or when you notice connectivity issues.
#>

param(
    [switch]$Force,
    [switch]$Verbose
)

$TailscalePath = "C:\Program Files\Tailscale\tailscale.exe"

function Write-Log {
    param($Message, $Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "WARNING" { "Yellow" }
        "SUCCESS" { "Green" }
        default { "White" }
    }
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
}

function Test-TailscaleHealth {
    try {
        $result = & $TailscalePath status 2>&1
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
        Write-Log "Tailscale status command failed: $result" "ERROR"
        return $false
    }
    catch {
        Write-Log "Failed to run Tailscale status: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Restart-TailscaleService {
    Write-Log "Restarting Tailscale service..." "WARNING"
    
    try {
        # Stop the service
        Stop-Service -Name "Tailscale" -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
        
        # Kill any remaining processes
        taskkill /F /IM tailscaled.exe /T 2>$null
        Start-Sleep -Seconds 2
        
        # Start the service
        Start-Service -Name "Tailscale"
        Start-Sleep -Seconds 10
        
        Write-Log "Tailscale service restarted successfully" "SUCCESS"
        return $true
    }
    catch {
        Write-Log "Failed to restart Tailscale service: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Show-TailscaleStatus {
    try {
        Write-Log "Current Tailscale status:" "INFO"
        & $TailscalePath status
    }
    catch {
        Write-Log "Could not get Tailscale status" "ERROR"
    }
}

# Main script
Write-Log "Tailscale Monitor Starting..." "INFO"

if ($Force) {
    Write-Log "Force restart requested" "WARNING"
    Restart-TailscaleService
    Show-TailscaleStatus
    exit 0
}

$isHealthy = Test-TailscaleHealth

if ($isHealthy) {
    Write-Log "Tailscale is healthy" "SUCCESS"
    if ($Verbose) {
        Show-TailscaleStatus
    }
} else {
    Write-Log "Tailscale is not responding, attempting restart..." "WARNING"
    $restarted = Restart-TailscaleService
    
    if ($restarted) {
        Start-Sleep -Seconds 5
        $isHealthyAfterRestart = Test-TailscaleHealth
        
        if ($isHealthyAfterRestart) {
            Write-Log "Tailscale successfully restored!" "SUCCESS"
            Show-TailscaleStatus
        } else {
            Write-Log "Tailscale restart failed - manual intervention required" "ERROR"
            exit 1
        }
    } else {
        Write-Log "Failed to restart Tailscale service" "ERROR"
        exit 1
    }
}

Write-Log "Tailscale Monitor Complete" "INFO"
