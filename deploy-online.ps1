# ================================================================================================
# LLM Translation Service - Online Deployment Script
# This script configures your translation service for internet access
# ================================================================================================

param(
    [switch]$SkipFirewall,
    [switch]$TestOnly,
    [string]$ExternalPort = "8080",
    [string]$InternalPort = "8000"
)

Write-Host "🌐 LLM Translation Service - Online Deployment Setup" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# Check if running as administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin -and -not $SkipFirewall) {
    Write-Host "⚠️  Administrator privileges required for firewall configuration" -ForegroundColor Yellow
    Write-Host "Please run this script as Administrator or use -SkipFirewall flag" -ForegroundColor Yellow
    exit 1
}

# Step 1: Check prerequisites
Write-Host "`n🔍 Step 1: Checking Prerequisites..." -ForegroundColor Green

# Check if Ollama is running
$ollamaProcess = Get-Process -Name "ollama*" -ErrorAction SilentlyContinue
if ($ollamaProcess) {
    Write-Host "✅ Ollama is running" -ForegroundColor Green
} else {
    Write-Host "❌ Ollama is not running. Please start Ollama first." -ForegroundColor Red
    Write-Host "   Run: ollama serve" -ForegroundColor Yellow
    exit 1
}

# Check if Redis is available
try {
    $redisTest = Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue
    if ($redisTest.TcpTestSucceeded) {
        Write-Host "✅ Redis is running" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Redis is not running - will use in-memory cache" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Redis is not available - will use in-memory cache" -ForegroundColor Yellow
}

# Step 2: Configure Windows Firewall
if (-not $SkipFirewall) {
    Write-Host "`n🔥 Step 2: Configuring Windows Firewall..." -ForegroundColor Green
    
    try {
        # Remove existing rules if they exist
        Remove-NetFirewallRule -DisplayName "LLM Translation Service" -ErrorAction SilentlyContinue
        Remove-NetFirewallRule -DisplayName "LLM Translation Metrics" -ErrorAction SilentlyContinue
        
        # Add firewall rules for the translation service
        New-NetFirewallRule -DisplayName "LLM Translation Service" -Direction Inbound -Protocol TCP -LocalPort $InternalPort -Action Allow -Profile Any
        New-NetFirewallRule -DisplayName "LLM Translation Metrics" -Direction Inbound -Protocol TCP -LocalPort 8001 -Action Allow -Profile Any
        
        Write-Host "✅ Firewall rules configured for ports ${InternalPort} and 8001" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to configure firewall: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "   Please configure firewall manually or run with -SkipFirewall" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n🔥 Step 2: Skipping firewall configuration (as requested)" -ForegroundColor Yellow
}

# Step 3: Get network information
Write-Host "`n🌐 Step 3: Network Configuration Information..." -ForegroundColor Green

# Get local IP addresses
$networkAdapters = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -ne "127.0.0.1" -and $_.AddressState -eq "Preferred" }

Write-Host "📍 Your local IP addresses:" -ForegroundColor Cyan
foreach ($adapter in $networkAdapters) {
    $interfaceAlias = (Get-NetAdapter -InterfaceIndex $adapter.InterfaceIndex).Name
    Write-Host "   • $($adapter.IPAddress) ($interfaceAlias)" -ForegroundColor White
}

# Get public IP (if available)
try {
    $publicIP = (Invoke-WebRequest -Uri "https://api.ipify.org" -UseBasicParsing).Content.Trim()
    Write-Host "🌍 Your public IP address: $publicIP" -ForegroundColor Cyan
} catch {
    Write-Host "⚠️  Could not retrieve public IP address" -ForegroundColor Yellow
}

# Step 4: Display access URLs
Write-Host "`n🔗 Step 4: Service Access Information..." -ForegroundColor Green

Write-Host "📱 Local Network Access URLs:" -ForegroundColor Cyan
foreach ($adapter in $networkAdapters) {
    Write-Host "   • http://$($adapter.IPAddress):${InternalPort}" -ForegroundColor White
    Write-Host "   • http://$($adapter.IPAddress):${InternalPort}/docs (API Documentation)" -ForegroundColor White
}

if ($publicIP) {
    Write-Host "`n🌍 Internet Access URLs (after router configuration):" -ForegroundColor Cyan
    Write-Host "   • http://${publicIP}:${ExternalPort}" -ForegroundColor White
    Write-Host "   • http://${publicIP}:${ExternalPort}/docs" -ForegroundColor White
}

# Step 5: Router configuration instructions
Write-Host "`n🔧 Step 5: Router Port Forwarding Setup..." -ForegroundColor Green
Write-Host "To enable internet access, configure your router:" -ForegroundColor White
Write-Host "1. Open your router admin panel (usually http://192.168.1.1 or http://192.168.0.1)" -ForegroundColor Yellow
Write-Host "2. Navigate to Port Forwarding / Virtual Server / NAT settings" -ForegroundColor Yellow
Write-Host "3. Add a new port forwarding rule:" -ForegroundColor Yellow
Write-Host "   • Service Name: LLM Translation Service" -ForegroundColor White
Write-Host "   • External Port: ${ExternalPort}" -ForegroundColor White
Write-Host "   • Internal IP: $(($networkAdapters | Select-Object -First 1).IPAddress)" -ForegroundColor White
Write-Host "   • Internal Port: ${InternalPort}" -ForegroundColor White
Write-Host "   • Protocol: TCP" -ForegroundColor White
Write-Host "4. Save and apply the settings" -ForegroundColor Yellow

# Step 6: Security recommendations
Write-Host "`n🛡️  Step 6: Security Recommendations..." -ForegroundColor Green
Write-Host "For production deployment, consider:" -ForegroundColor White
Write-Host "• Change the default SECRET_KEY in .env file" -ForegroundColor Yellow
Write-Host "• Set up API key authentication" -ForegroundColor Yellow
Write-Host "• Configure rate limiting" -ForegroundColor Yellow
Write-Host "• Use HTTPS with SSL certificates" -ForegroundColor Yellow
Write-Host "• Monitor access logs regularly" -ForegroundColor Yellow

# Step 7: Test local access (if not test-only mode)
if (-not $TestOnly) {
    Write-Host "`n🧪 Step 7: Testing Local Access..." -ForegroundColor Green
    
    $localIP = ($networkAdapters | Select-Object -First 1).IPAddress
    $testUrl = "http://${localIP}:${InternalPort}"
    
    Write-Host "Testing connection to $testUrl..." -ForegroundColor White
    
    try {
        $response = Invoke-WebRequest -Uri $testUrl -TimeoutSec 10 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Service is accessible on local network!" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Service responded with status code: $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ Could not connect to service. Make sure it's running." -ForegroundColor Red
        Write-Host "   Start the service with: python run.py" -ForegroundColor Yellow
    }
}

Write-Host "`n🎉 Online Deployment Setup Complete!" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Cyan

# Step 8: Display next steps
Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Start the translation service: python run.py" -ForegroundColor White
Write-Host "2. Test local access using the URLs above" -ForegroundColor White
Write-Host "3. Configure router port forwarding for internet access" -ForegroundColor White
Write-Host "4. Test internet access from external devices" -ForegroundColor White
Write-Host "5. Monitor logs and performance" -ForegroundColor White

Write-Host "`n📖 For detailed documentation, see:" -ForegroundColor Cyan
Write-Host "• PRODUCTION_SETUP_GUIDE.md" -ForegroundColor White
Write-Host "• ROUTER_SETUP_GUIDE.md" -ForegroundColor White
Write-Host "• REMOTE_ACCESS_GUIDE.md" -ForegroundColor White
