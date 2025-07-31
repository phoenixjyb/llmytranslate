# ================================================================================================
# LLM Translation Service - Phase 4 Service Status Dashboard
# Shows the status of all 4 Phase 4 service components with card-based display
# ================================================================================================

param(
    [switch]$Continuous,
    [int]$RefreshInterval = 5,
    [switch]$Detailed
)

# Service component endpoints for health checks
$ServiceComponents = @{
    "OptimizedLLM" = @{
        Name = "Optimized LLM Service"
        Icon = "🧠"
        Endpoint = "http://localhost:8000/api/llm/health"
        Description = "AI model optimization and routing"
    }
    "PerformanceMonitor" = @{
        Name = "Performance Monitor"
        Icon = "📊"
        Endpoint = "http://localhost:8000/api/performance/status"
        Description = "Real-time performance tracking"
    }
    "QualityMonitor" = @{
        Name = "Quality Monitor" 
        Icon = "✅"
        Endpoint = "http://localhost:8000/api/quality/status"
        Description = "Service quality assessment"
    }
    "ConnectionPool" = @{
        Name = "Connection Pool Manager"
        Icon = "🔗"
        Endpoint = "http://localhost:8000/api/connections/status"
        Description = "Connection pooling and optimization"
    }
}

function Get-ServiceComponentStatus {
    param([hashtable]$Component)
    
    try {
        $response = Invoke-RestMethod -Uri $Component.Endpoint -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($response) {
            return @{
                Status = "Healthy"
                Color = "Green"
                Symbol = "✅"
                Details = $response
            }
        }
    } catch {
        # Check if main service is running
        try {
            $mainHealth = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($mainHealth) {
                return @{
                    Status = "Partial"
                    Color = "Yellow"
                    Symbol = "⚠️"
                    Details = "Main service running, component endpoint unavailable"
                }
            }
        } catch {
            # Main service not running
        }
    }
    
    return @{
        Status = "Offline"
        Color = "Red"
        Symbol = "❌"
        Details = "Service not responding"
    }
}

function Show-ServiceDashboard {
    Clear-Host
    
    Write-Host "🚀 LLM Translation Service - Phase 4 Dashboard" -ForegroundColor Cyan
    Write-Host "=================================================" -ForegroundColor Cyan
    Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
    Write-Host ""
    
    # Check main service first
    $mainServiceStatus = "❌ Offline"
    $mainServiceColor = "Red"
    try {
        $mainHealth = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($mainHealth) {
            $mainServiceStatus = "✅ Online"
            $mainServiceColor = "Green"
        }
    } catch {
        # Service offline
    }
    
    Write-Host "🏠 Main Service Status: " -NoNewline -ForegroundColor White
    Write-Host $mainServiceStatus -ForegroundColor $mainServiceColor
    Write-Host ""
    
    # Display service components in card format
    $cardWidth = 50
    $componentsPerRow = 2
    $componentKeys = $ServiceComponents.Keys | Sort-Object
    
    for ($i = 0; $i -lt $componentKeys.Count; $i += $componentsPerRow) {
        $row = $componentKeys[$i..($i + $componentsPerRow - 1)]
        
        # Card headers
        foreach ($key in $row) {
            $component = $ServiceComponents[$key]
            Write-Host ("┌" + ("─" * ($cardWidth - 2)) + "┐") -NoNewline -ForegroundColor DarkGray
            if ($row.IndexOf($key) -lt ($row.Count - 1)) {
                Write-Host "  " -NoNewline
            }
        }
        Write-Host ""
        
        # Card titles
        foreach ($key in $row) {
            $component = $ServiceComponents[$key]
            $title = "$($component.Icon) $($component.Name)"
            $padding = [Math]::Max(0, $cardWidth - $title.Length - 2)
            $leftPad = [Math]::Floor($padding / 2)
            $rightPad = $padding - $leftPad
            
            Write-Host ("│" + (" " * $leftPad) + $title + (" " * $rightPad) + "│") -NoNewline -ForegroundColor White
            if ($row.IndexOf($key) -lt ($row.Count - 1)) {
                Write-Host "  " -NoNewline
            }
        }
        Write-Host ""
        
        # Card status line
        foreach ($key in $row) {
            $component = $ServiceComponents[$key]
            $status = Get-ServiceComponentStatus -Component $component
            
            $statusLine = "$($status.Symbol) $($status.Status)"
            $padding = [Math]::Max(0, $cardWidth - $statusLine.Length - 2)
            $leftPad = [Math]::Floor($padding / 2)
            $rightPad = $padding - $leftPad
            
            Write-Host ("│" + (" " * $leftPad)) -NoNewline -ForegroundColor DarkGray
            Write-Host $statusLine -NoNewline -ForegroundColor $status.Color
            Write-Host ((" " * $rightPad) + "│") -NoNewline -ForegroundColor DarkGray
            if ($row.IndexOf($key) -lt ($row.Count - 1)) {
                Write-Host "  " -NoNewline
            }
        }
        Write-Host ""
        
        # Card description
        foreach ($key in $row) {
            $component = $ServiceComponents[$key]
            $desc = $component.Description
            $padding = [Math]::Max(0, $cardWidth - $desc.Length - 2)
            $leftPad = [Math]::Floor($padding / 2)
            $rightPad = $padding - $leftPad
            
            Write-Host ("│" + (" " * $leftPad) + $desc + (" " * $rightPad) + "│") -NoNewline -ForegroundColor Gray
            if ($row.IndexOf($key) -lt ($row.Count - 1)) {
                Write-Host "  " -NoNewline
            }
        }
        Write-Host ""
        
        # Card details (if detailed mode)
        if ($Detailed) {
            foreach ($key in $row) {
                $component = $ServiceComponents[$key]
                $status = Get-ServiceComponentStatus -Component $component
                $details = if ($status.Details -is [string]) { $status.Details } else { "Ready" }
                if ($details.Length -gt ($cardWidth - 4)) {
                    $details = $details.Substring(0, $cardWidth - 7) + "..."
                }
                $padding = [Math]::Max(0, $cardWidth - $details.Length - 2)
                $rightPad = $padding
                
                Write-Host ("│ " + $details + (" " * $rightPad) + "│") -NoNewline -ForegroundColor DarkCyan
                if ($row.IndexOf($key) -lt ($row.Count - 1)) {
                    Write-Host "  " -NoNewline
                }
            }
            Write-Host ""
        }
        
        # Card footers
        foreach ($key in $row) {
            $component = $ServiceComponents[$key]
            Write-Host ("└" + ("─" * ($cardWidth - 2)) + "┘") -NoNewline -ForegroundColor DarkGray
            if ($row.IndexOf($key) -lt ($row.Count - 1)) {
                Write-Host "  " -NoNewline
            }
        }
        Write-Host ""
        Write-Host ""
    }
    
    # Overall system health
    $healthyCount = 0
    foreach ($key in $componentKeys) {
        $status = Get-ServiceComponentStatus -Component $ServiceComponents[$key]
        if ($status.Status -eq "Healthy") {
            $healthyCount++
        }
    }
    
    $overallHealth = switch ($healthyCount) {
        4 { @{ Status = "Excellent"; Color = "Green"; Icon = "🟢" } }
        3 { @{ Status = "Good"; Color = "Yellow"; Icon = "🟡" } }
        { $_ -ge 1 } { @{ Status = "Degraded"; Color = "Red"; Icon = "🟠" } }
        default { @{ Status = "Critical"; Color = "Red"; Icon = "🔴" } }
    }
    
    Write-Host "🎯 Overall System Health: " -NoNewline -ForegroundColor White
    Write-Host "$($overallHealth.Icon) $($overallHealth.Status) " -NoNewline -ForegroundColor $overallHealth.Color
    Write-Host "($healthyCount/4 components healthy)" -ForegroundColor Gray
    
    # Show management commands
    Write-Host ""
    Write-Host "🛠️  Management Commands:" -ForegroundColor Cyan
    Write-Host "   .\start-service.ps1          # Start all services" -ForegroundColor White
    Write-Host "   .\stop-service.ps1           # Stop all services" -ForegroundColor White
    Write-Host "   .\scripts\service-status.ps1 -Continuous  # Continuous monitoring" -ForegroundColor White
    Write-Host "   .\scripts\service-status.ps1 -Detailed    # Detailed view" -ForegroundColor White
}

# Main execution
try {
    if ($Continuous) {
        Write-Host "🔄 Starting continuous monitoring (Ctrl+C to stop)..." -ForegroundColor Yellow
        Write-Host "Refresh interval: $RefreshInterval seconds" -ForegroundColor Gray
        Write-Host ""
        
        while ($true) {
            Show-ServiceDashboard
            Write-Host ""
            Write-Host "Next refresh in $RefreshInterval seconds... (Ctrl+C to stop)" -ForegroundColor DarkGray
            Start-Sleep -Seconds $RefreshInterval
        }
    } else {
        Show-ServiceDashboard
    }
} catch [System.Management.Automation.PipelineStoppedException] {
    Write-Host "`n👋 Monitoring stopped by user" -ForegroundColor Yellow
} catch {
    Write-Host "`n❌ Error in service status monitoring: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
