# Remote Access Setup Script for LLM Translation Service
# Usage: .\setup_remote_access.ps1 [ngrok|firewall|local]

param(
    [Parameter(Position=0)]
    [ValidateSet("ngrok", "firewall", "local", "info")]
    [string]$Mode = "info"
)

Write-Host "🌐 LLM Translation Service - Remote Access Setup" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Green

switch ($Mode) {
    "info" {
        Write-Host "`n📋 Available setup modes:" -ForegroundColor Yellow
        Write-Host "  local    - Get local network access info" -ForegroundColor Cyan
        Write-Host "  ngrok    - Set up ngrok tunnel for internet access" -ForegroundColor Cyan
        Write-Host "  firewall - Configure Windows Firewall" -ForegroundColor Cyan
        Write-Host "`nUsage: .\setup_remote_access.ps1 [mode]" -ForegroundColor Gray
    }
    
    "local" {
        Write-Host "`n🏠 Local Network Access Setup" -ForegroundColor Yellow
        Write-Host "=" * 30 -ForegroundColor Yellow
        
        # Get local IP addresses
        $ipAddresses = @()
        Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
            $_.IPAddress -notlike "127.*" -and 
            $_.IPAddress -notlike "169.254.*" -and
            $_.PrefixOrigin -eq "Dhcp" -or $_.PrefixOrigin -eq "Manual"
        } | ForEach-Object {
            $ipAddresses += $_.IPAddress
        }
        
        if ($ipAddresses.Count -gt 0) {
            Write-Host "`n✅ Your local IP addresses:" -ForegroundColor Green
            foreach ($ip in $ipAddresses) {
                Write-Host "   http://$ip:8000" -ForegroundColor Cyan
            }
            
            Write-Host "`n📱 Test commands for other devices on your network:" -ForegroundColor Yellow
            $primaryIP = $ipAddresses[0]
            Write-Host "curl http://$primaryIP:8000/api/health" -ForegroundColor Gray
            Write-Host "curl -X POST `"http://$primaryIP:8000/api/demo/translate`" -H `"Content-Type: application/x-www-form-urlencoded`" -d `"q=Hello world&from=en&to=zh`"" -ForegroundColor Gray
        } else {
            Write-Host "❌ No suitable network interfaces found" -ForegroundColor Red
        }
    }
    
    "firewall" {
        Write-Host "`n🛡️ Windows Firewall Configuration" -ForegroundColor Yellow
        Write-Host "=" * 35 -ForegroundColor Yellow
        
        try {
            # Check if rule already exists
            $existingRule = Get-NetFirewallRule -DisplayName "LLM Translation Service" -ErrorAction SilentlyContinue
            
            if ($existingRule) {
                Write-Host "✅ Firewall rule already exists" -ForegroundColor Green
                Write-Host "   Rule: $($existingRule.DisplayName)" -ForegroundColor Cyan
                Write-Host "   Status: $($existingRule.Enabled)" -ForegroundColor Cyan
            } else {
                Write-Host "🔧 Creating firewall rule..." -ForegroundColor Yellow
                New-NetFirewallRule -DisplayName "LLM Translation Service" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
                Write-Host "✅ Firewall rule created successfully!" -ForegroundColor Green
            }
            
            Write-Host "`n📋 Next steps for internet access:" -ForegroundColor Yellow
            Write-Host "1. Configure router port forwarding (External Port: 8000 → Internal Port: 8000)" -ForegroundColor Gray
            Write-Host "2. Find your public IP: (Invoke-WebRequest -UseBasicParsing 'http://ipinfo.io/ip').Content.Trim()" -ForegroundColor Gray
            Write-Host "3. Access externally: http://YOUR_PUBLIC_IP:8000" -ForegroundColor Gray
            
        } catch {
            Write-Host "❌ Failed to configure firewall: $_" -ForegroundColor Red
            Write-Host "💡 Try running as Administrator" -ForegroundColor Yellow
        }
    }
    
    "ngrok" {
        Write-Host "`n🚇 Ngrok Tunnel Setup" -ForegroundColor Yellow
        Write-Host "=" * 25 -ForegroundColor Yellow
        
        # Check if ngrok is installed
        $ngrokPath = Get-Command ngrok -ErrorAction SilentlyContinue
        
        if (-not $ngrokPath) {
            Write-Host "❌ Ngrok not found. Installing..." -ForegroundColor Red
            Write-Host "💡 Installing via Chocolatey..." -ForegroundColor Yellow
            
            # Check if chocolatey is available
            $chocoPath = Get-Command choco -ErrorAction SilentlyContinue
            if ($chocoPath) {
                choco install ngrok -y
            } else {
                Write-Host "❌ Chocolatey not found. Please install ngrok manually:" -ForegroundColor Red
                Write-Host "   1. Download from: https://ngrok.com/download" -ForegroundColor Gray
                Write-Host "   2. Extract to a folder in your PATH" -ForegroundColor Gray
                Write-Host "   3. Run: ngrok authtoken YOUR_TOKEN" -ForegroundColor Gray
                return
            }
        }
        
        Write-Host "✅ Ngrok found!" -ForegroundColor Green
        Write-Host "`n🔧 To create tunnel:" -ForegroundColor Yellow
        Write-Host "1. Make sure translation service is running (port 8000)" -ForegroundColor Gray
        Write-Host "2. Open new terminal and run:" -ForegroundColor Gray
        Write-Host "   ngrok http 8000" -ForegroundColor Cyan
        Write-Host "3. Copy the public URL (e.g., https://abc123.ngrok.io)" -ForegroundColor Gray
        Write-Host "4. Test with:" -ForegroundColor Gray
        Write-Host "   curl https://YOUR_NGROK_URL/api/health" -ForegroundColor Cyan
        
        Write-Host "`n💡 Ngrok will provide both HTTP and HTTPS URLs" -ForegroundColor Yellow
    }
}

Write-Host "`n🔍 Service Status Check:" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method Get -TimeoutSec 5
    Write-Host "✅ Translation service is running on localhost:8000" -ForegroundColor Green
    Write-Host "   Status: $($response.status)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Translation service not responding on localhost:8000" -ForegroundColor Red
    Write-Host "💡 Start the service first: .\start-service.ps1" -ForegroundColor Yellow
}

Write-Host "`n📚 For detailed setup instructions, see:" -ForegroundColor Yellow
Write-Host "   docs/guides/REMOTE_ACCESS_GUIDE.md" -ForegroundColor Cyan
Write-Host "   docs/CURL_COMMANDS.md" -ForegroundColor Cyan
