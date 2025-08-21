# LLM Translation Service Manager
# Manages service startup, ngrok tunneling, and token storage

param(
    [Parameter(ParameterSetName='SetToken')]
    [string]$SetToken,
    
    [Parameter(ParameterSetName='Start')]
    [switch]$Start,
    
    [Parameter(ParameterSetName='StartWeb')]
    [switch]$StartWeb,
    
    [Parameter(ParameterSetName='TestNgrok')]
    [switch]$TestNgrok,
    
    [Parameter(ParameterSetName='Stop')]
    [switch]$Stop,
    
    [Parameter(ParameterSetName='Status')]
    [switch]$Status,
    
    [Parameter(ParameterSetName='GetUrl')]
    [switch]$GetUrl,
    
    [Parameter(ParameterSetName='Help')]
    [switch]$Help
)

# Configuration paths
$configDir = Join-Path $env:USERPROFILE ".llmytranslate"
$tokenFile = Join-Path $configDir "ngrok.token"

# Create config directory if it doesn't exist
if (!(Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

function Show-Help {
    Write-Host "🛠️  LLM Translation Service Manager" -ForegroundColor Green
    Write-Host "====================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "USAGE:" -ForegroundColor Yellow
    Write-Host "  .\service-manager.ps1 -SetToken 'your_ngrok_token'"
    Write-Host "  .\service-manager.ps1 -Start        # Start local service only"
    Write-Host "  .\service-manager.ps1 -StartWeb     # Start service + ngrok tunnel"
    Write-Host "  .\service-manager.ps1 -TestNgrok    # Test ngrok with proven method"
    Write-Host "  .\service-manager.ps1 -Stop         # Stop all services"
    Write-Host "  .\service-manager.ps1 -Status       # Check service status"
    Write-Host "  .\service-manager.ps1 -GetUrl       # Get ngrok public URL"
    Write-Host ""
    Write-Host "FIRST TIME SETUP:" -ForegroundColor Yellow
    Write-Host "1. Get your free ngrok token: https://dashboard.ngrok.com/get-started/your-authtoken"
    Write-Host "2. Save it: .\service-manager.ps1 -SetToken 'your_token_here'"
    Write-Host "3. Start web access: .\service-manager.ps1 -StartWeb"
    Write-Host ""
    Write-Host "TOKEN STORAGE:" -ForegroundColor Yellow
    Write-Host "  Stored securely in: $tokenFile"
    Write-Host "  (File is created with restricted permissions)"
}

function Set-NgrokToken {
    param([string]$Token)
    
    if ([string]::IsNullOrWhiteSpace($Token)) {
        Write-Host "❌ Token cannot be empty" -ForegroundColor Red
        return $false
    }
    
    try {
        # Save token to file with restricted permissions
        $Token | Out-File -FilePath $tokenFile -Encoding UTF8 -Force
        
        # Set file permissions (only current user can read)
        $acl = Get-Acl $tokenFile
        $acl.SetAccessRuleProtection($true, $false)
        $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
            [System.Security.Principal.WindowsIdentity]::GetCurrent().Name,
            "FullControl",
            "Allow"
        )
        $acl.SetAccessRule($accessRule)
        Set-Acl -Path $tokenFile -AclObject $acl
        
        Write-Host "✅ Ngrok token saved securely!" -ForegroundColor Green
        Write-Host "📁 Location: $tokenFile" -ForegroundColor Gray
        
        # Configure ngrok with the token
        ngrok config add-authtoken $Token 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Ngrok configured successfully!" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Token saved but ngrok config failed. Please check if ngrok is installed." -ForegroundColor Yellow
        }
        
        return $true
    }
    catch {
        Write-Host "❌ Failed to save token: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Get-SavedToken {
    if (Test-Path $tokenFile) {
        try {
            return (Get-Content $tokenFile -Raw).Trim()
        }
        catch {
            Write-Host "❌ Failed to read saved token: $($_.Exception.Message)" -ForegroundColor Red
            return $null
        }
    }
    return $null
}

function Start-LocalService {
    Write-Host "🚀 Starting Local Translation Service..." -ForegroundColor Green
    
    # Check if service is already running
    $existing = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "ℹ️  Service is already running on port 8000" -ForegroundColor Yellow
        return $true
    }
    
    # Use the proven working start script from eadb89c commit
    if (Test-Path ".\start-service.ps1") {
        Write-Host "🔧 Using proven start script..." -ForegroundColor Gray
        Start-Process PowerShell -ArgumentList "-NoExit", "-Command", "& '.\start-service.ps1'" -WindowStyle Normal
    } else {
        Write-Host "❌ start-service.ps1 not found!" -ForegroundColor Red
        return $false
    }
    
    # Wait for service to start
    $timeout = 30
    $elapsed = 0
    do {
        Start-Sleep -Seconds 1
        $elapsed++
        $connection = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    } while (!$connection -and $elapsed -lt $timeout)
    
    if ($connection) {
        Write-Host "✅ Local service started successfully!" -ForegroundColor Green
        Write-Host "🌐 Available at: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "📚 API docs: http://localhost:8000/docs" -ForegroundColor Cyan
        return $true
    } else {
        Write-Host "❌ Failed to start local service within $timeout seconds" -ForegroundColor Red
        return $false
    }
}

function Start-NgrokTunnel {
    $token = Get-SavedToken
    if (!$token) {
        Write-Host "❌ No saved ngrok token found!" -ForegroundColor Red
        Write-Host "💡 Please run: .\service-manager.ps1 -SetToken 'your_token'" -ForegroundColor Yellow
        return $false
    }
    
    Write-Host "🚇 Starting ngrok tunnel..." -ForegroundColor Green
    
    # Check if ngrok is available
    $ngrokVersion = & ngrok version 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Ngrok not found in PATH" -ForegroundColor Red
        Write-Host "💡 Please install ngrok from Windows Store or ngrok.com" -ForegroundColor Yellow
        return $false
    }
    
    Write-Host "✅ Found: $ngrokVersion" -ForegroundColor Green
    
    # Configure ngrok (in case it wasn't done before)
    ngrok config add-authtoken $token 2>$null
    
    Write-Host "🌐 Starting public tunnel to http://localhost:8000..." -ForegroundColor Cyan
    Write-Host "📋 Ngrok tunnel will show URL when ready" -ForegroundColor Gray
    Write-Host "🔗 Use Ctrl+C in the ngrok window to stop the tunnel" -ForegroundColor Gray
    Write-Host ""
    
    # Use the proven working method from eadb89c - direct ngrok execution
    # This will run in foreground and show the URL immediately
    Start-Process PowerShell -ArgumentList "-NoExit", "-Command", "Write-Host '🚇 Ngrok Tunnel for LLM Translation Service' -ForegroundColor Green; Write-Host 'Service: http://localhost:8000' -ForegroundColor Cyan; Write-Host ''; ngrok http 8000" -WindowStyle Normal
    
    Start-Sleep -Seconds 3
    Write-Host "✅ Ngrok tunnel started!" -ForegroundColor Green
    Write-Host "💡 Check the ngrok window for your public URL" -ForegroundColor Yellow
    
    return $true
}

function Stop-Services {
    Write-Host "🛑 Stopping services..." -ForegroundColor Yellow
    
    # Use the proven working stop script from eadb89c commit
    if (Test-Path ".\scripts\stop-service.ps1") {
        Write-Host "🔧 Using proven stop script..." -ForegroundColor Gray
        & ".\scripts\stop-service.ps1" -Force
    } else {
        # Fallback to manual stop
        Write-Host "🔧 Using manual stop procedure..." -ForegroundColor Gray
        
        # Stop ngrok processes
        $ngrokProcesses = Get-Process -Name "ngrok" -ErrorAction SilentlyContinue
        if ($ngrokProcesses) {
            $ngrokProcesses | Stop-Process -Force
            Write-Host "✅ Stopped ngrok tunnels" -ForegroundColor Green
        }
        
        # Find and stop service processes
        $connections = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
        if ($connections) {
            foreach ($conn in $connections) {
                $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
                if ($process -and $process.ProcessName -ne "Idle") {
                    Stop-Process -Id $process.Id -Force
                    Write-Host "✅ Stopped service process: $($process.ProcessName)" -ForegroundColor Green
                }
            }
        }
    }
    
    Write-Host "✅ All services stopped" -ForegroundColor Green
}

function Get-NgrokUrl {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction Stop
        $httpTunnel = $response.tunnels | Where-Object { $_.config.addr -eq "http://localhost:8000" -and $_.proto -eq "https" }
        if ($httpTunnel) {
            return $httpTunnel.public_url
        }
        return $null
    }
    catch {
        return $null
    }
}

function Show-Status {
    Write-Host "📊 Service Status" -ForegroundColor Green
    Write-Host "=================" -ForegroundColor Cyan
    
    # Check local service
    $localService = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($localService) {
        Write-Host "🟢 Local Service: RUNNING (port 8000)" -ForegroundColor Green
        Write-Host "   🌐 http://localhost:8000" -ForegroundColor Gray
        Write-Host "   📚 http://localhost:8000/docs" -ForegroundColor Gray
    } else {
        Write-Host "🔴 Local Service: STOPPED" -ForegroundColor Red
    }
    
    # Check ngrok
    $ngrokProcesses = Get-Process -Name "ngrok" -ErrorAction SilentlyContinue
    if ($ngrokProcesses) {
        Write-Host "🟢 Ngrok Tunnel: RUNNING ($($ngrokProcesses.Count) process(es))" -ForegroundColor Green
        
        # Try to get the public URL
        $publicUrl = Get-NgrokUrl
        if ($publicUrl) {
            Write-Host "   🌐 Public URL: $publicUrl" -ForegroundColor Cyan
            Write-Host "   📚 Public Docs: $publicUrl/docs" -ForegroundColor Cyan
            Write-Host "   🌍 Web Interface: $publicUrl/web/" -ForegroundColor Cyan
        } else {
            Write-Host "   💡 Check ngrok window or http://localhost:4040 for public URL" -ForegroundColor Gray
        }
    } else {
        Write-Host "🔴 Ngrok Tunnel: STOPPED" -ForegroundColor Red
    }
    
    # Check saved token
    $token = Get-SavedToken
    if ($token) {
        Write-Host "🟢 Ngrok Token: CONFIGURED" -ForegroundColor Green
    } else {
        Write-Host "🔴 Ngrok Token: NOT CONFIGURED" -ForegroundColor Red
        Write-Host "   💡 Run: .\service-manager.ps1 -SetToken 'your_token'" -ForegroundColor Yellow
    }
}

# Main execution logic
switch ($PSCmdlet.ParameterSetName) {
    'SetToken' {
        Set-NgrokToken -Token $SetToken
    }
    'Start' {
        Start-LocalService
    }
    'StartWeb' {
        Write-Host "🌐 Starting Web-Accessible Translation Service" -ForegroundColor Green
        Write-Host "=============================================" -ForegroundColor Cyan
        
        if (Start-LocalService) {
            Start-NgrokTunnel
            Write-Host ""
            Write-Host "🎉 Web access setup complete!" -ForegroundColor Green
            Write-Host "📱 Local: http://localhost:8000" -ForegroundColor Cyan
            Write-Host "🌐 Public: Check ngrok window for URL" -ForegroundColor Cyan
            Write-Host "🛑 To stop: .\service-manager.ps1 -Stop" -ForegroundColor Yellow
        }
    }
    'TestNgrok' {
        Write-Host "🧪 Testing Ngrok with Proven Method (eadb89c)" -ForegroundColor Green
        Write-Host "=============================================" -ForegroundColor Cyan
        
        $token = Get-SavedToken
        if (!$token) {
            Write-Host "❌ No saved ngrok token found!" -ForegroundColor Red
            Write-Host "💡 Please run: .\service-manager.ps1 -SetToken 'your_token'" -ForegroundColor Yellow
        } else {
            Write-Host "🚇 Using the exact working method from eadb89c commit..." -ForegroundColor Yellow
            Write-Host "📋 This method was proven to work with remote access" -ForegroundColor Gray
            Write-Host ""
            
            # Configure ngrok with token
            ngrok config add-authtoken $token
            
            # Run in a separate window so it doesn't hang this script
            Write-Host "🌐 Starting ngrok tunnel in new window..." -ForegroundColor Cyan
            Start-Process PowerShell -ArgumentList "-NoExit", "-Command", "Write-Host '🧪 Ngrok Test (eadb89c method)' -ForegroundColor Green; Write-Host 'Press Ctrl+C to stop' -ForegroundColor Yellow; Write-Host ''; ngrok http 8000" -WindowStyle Normal
            
            Write-Host "✅ Ngrok test started in new window!" -ForegroundColor Green
            Write-Host "💡 Look for the ngrok window to see your public URL" -ForegroundColor Yellow
        }
    }
    'Stop' {
        Stop-Services
    }
    'Status' {
        Show-Status
    }
    'GetUrl' {
        Write-Host "🔗 Getting Ngrok Public URL..." -ForegroundColor Green
        $publicUrl = Get-NgrokUrl
        if ($publicUrl) {
            Write-Host ""
            Write-Host "✅ Your public URL:" -ForegroundColor Green
            Write-Host "   🌐 Service: $publicUrl" -ForegroundColor Cyan
            Write-Host "   📚 API Docs: $publicUrl/docs" -ForegroundColor Cyan
            Write-Host "   🌍 Web Interface: $publicUrl/web/" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "💡 You can share these URLs with anyone!" -ForegroundColor Yellow
        } else {
            Write-Host "❌ Could not retrieve public URL" -ForegroundColor Red
            Write-Host "💡 Make sure ngrok tunnel is running: .\service-manager.ps1 -StartWeb" -ForegroundColor Yellow
            Write-Host "🌐 Or check manually at: http://localhost:4040" -ForegroundColor Gray
        }
    }
    default {
        Show-Help
    }
}
