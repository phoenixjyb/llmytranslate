#!/usr/bin/env powershell
# ================================================================================================
# Quick Performance Testing Setup
# Tests the enhanced timing breakdown features
# ================================================================================================

# Load required assemblies for URL encoding
Add-Type -AssemblyName System.Web

Write-Host "🚀 LLM Translation Service - Performance Testing" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if service is running
Write-Host "🔍 Step 1: Checking service status..." -ForegroundColor Yellow

try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Service status: $($healthResponse.status)" -ForegroundColor Green
    
    # Show service details
    if ($healthResponse.services) {
        Write-Host "� Service details:" -ForegroundColor Gray
        foreach ($service in $healthResponse.services.PSObject.Properties) {
            $status = $service.Value
            $icon = if ($status -eq "healthy") { "✅" } else { "⚠️" }
            Write-Host "   $icon $($service.Name): $status" -ForegroundColor Gray
        }
    }
    
    # If service is degraded, continue but warn user
    if ($healthResponse.status -eq "degraded") {
        Write-Host "⚠️  Service is degraded but functional" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "❌ Service not responding. Please check if it's running:" -ForegroundColor Red
    Write-Host "   python run.py" -ForegroundColor Gray
    Write-Host "   or" -ForegroundColor Gray
    Write-Host "   .\start-service.ps1" -ForegroundColor Gray
    exit 1
}

# Step 2: Test basic translation with timing
Write-Host "`n🧪 Step 2: Testing translation with timing breakdown..." -ForegroundColor Yellow

$testCases = @(
    @{
        name = "Simple English to Chinese"
        text = "Hello world"
        from = "en"
        to = "zh"
    },
    @{
        name = "Simple Chinese to English"
        text = "你好世界"
        from = "zh" 
        to = "en"
    },
    @{
        name = "Medium length text"
        text = "Good morning! How are you today? I hope you have a wonderful day."
        from = "en"
        to = "zh"
    }
)

foreach ($test in $testCases) {
    Write-Host "`n📝 Testing: $($test.name)" -ForegroundColor Cyan
    Write-Host "   Text: $($test.text)" -ForegroundColor Gray
    
    try {
        $startTime = Get-Date
        
        # Prepare form data for URL-encoded request
        $bodyString = "q=$([System.Web.HttpUtility]::UrlEncode($test.text))&from=$($test.from)&to=$($test.to)"
        
        # Make request with proper headers
        $headers = @{
            'Content-Type' = 'application/x-www-form-urlencoded'
        }
        
        Write-Host "   🔄 Sending request..." -ForegroundColor Gray
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/demo/translate" -Method Post -Body $bodyString -Headers $headers -TimeoutSec 15
        
        $totalTime = (Get-Date) - $startTime
        
        # Extract results
        if ($response -and $response.response -and $response.response.trans_result) {
            $translation = $response.response.trans_result[0].dst
            
            Write-Host "   ✅ Success!" -ForegroundColor Green
            Write-Host "   📝 Translation: $translation" -ForegroundColor White
            Write-Host "   ⏱️  Total time: $([math]::Round($totalTime.TotalMilliseconds, 1))ms" -ForegroundColor Yellow
            
            # Check for performance data
            if ($response.performance) {
                $performance = $response.performance
                Write-Host "   🔍 Service timing available!" -ForegroundColor Green
                
                if ($performance.total_time_ms) {
                    Write-Host "   � Service time: $($performance.total_time_ms)ms" -ForegroundColor Yellow
                }
                
                if ($performance.timing_breakdown -and $performance.timing_breakdown.steps) {
                    Write-Host "   � Detailed breakdown:" -ForegroundColor Cyan
                    
                    $stepNames = @{
                        'request_validation' = '📋 Validation'
                        'cache_lookup' = '🔍 Cache Check'
                        'llm_inference' = '🤖 LLM Setup'
                        'ollama_connection' = '🔗 Connection'
                        'llm_inference_actual' = '🧠 AI Processing'
                        'llm_response_processing' = '📤 Response'
                        'cache_write' = '💾 Cache Save'
                        'response_formatting' = '🎨 Formatting'
                    }
                    
                    foreach ($step in $performance.timing_breakdown.steps.PSObject.Properties) {
                        $stepName = $step.Name
                        $stepData = $step.Value
                        $displayName = $stepNames[$stepName]
                        if (-not $displayName) { $displayName = $stepName }
                        
                        Write-Host "      $displayName`: $($stepData.duration_ms)ms ($($stepData.percentage)%)" -ForegroundColor Gray
                    }
                } else {
                    Write-Host "   ℹ️  No detailed timing breakdown available" -ForegroundColor Gray
                }
            } else {
                Write-Host "   ℹ️  No performance data returned" -ForegroundColor Gray
                Write-Host "   💡 Enhanced timing may not be enabled" -ForegroundColor Yellow
            }
        } else {
            Write-Host "   ❌ No translation result received" -ForegroundColor Red
            Write-Host "   📄 Response: $($response | ConvertTo-Json -Depth 2)" -ForegroundColor Gray
        }
        
    } catch {
        Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        
        # More detailed error info
        if ($_.Exception.Response) {
            Write-Host "   📊 Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Gray
        }
    }
    
    # Small delay between tests
    Start-Sleep -Seconds 1
}

# Step 3: Open web interface to test visual timing
Write-Host "`n🌐 Step 3: Web interface information..." -ForegroundColor Yellow

$webUrl = "http://localhost:8000/web/"
Write-Host "✅ Web interface available at: $webUrl" -ForegroundColor Green
Write-Host "   💡 Open in browser to test visual timing breakdown!" -ForegroundColor Cyan
Write-Host "   🎯 Look for the timing breakdown section after each translation" -ForegroundColor Gray

# Optional: Try to open browser (but don't fail if it doesn't work)
try {
    $userChoice = Read-Host "`n🤔 Open web interface now? (y/N)"
    if ($userChoice -eq 'y' -or $userChoice -eq 'Y') {
        Start-Process $webUrl -ErrorAction SilentlyContinue
        Write-Host "🌐 Browser opened!" -ForegroundColor Green
    }
} catch {
    Write-Host "ℹ️  Skipping browser open" -ForegroundColor Gray
}

# Step 4: Advanced performance testing (optional)
Write-Host "`n🚀 Step 4: Additional performance options..." -ForegroundColor Yellow

if (Test-Path "test_performance.py") {
    Write-Host "📊 Python performance script available: test_performance.py" -ForegroundColor Green
    Write-Host "   � Run manually: python test_performance.py" -ForegroundColor Gray
} else {
    Write-Host "ℹ️  Advanced Python performance test not found" -ForegroundColor Gray
}

Write-Host "`n🎉 Performance Testing Complete!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host ""
Write-Host "📍 What you can now see:" -ForegroundColor Cyan
Write-Host "   ✅ Detailed timing breakdown for each translation step" -ForegroundColor Gray
Write-Host "   ✅ Separate timing for LLM inference vs other operations" -ForegroundColor Gray
Write-Host "   ✅ Visual performance metrics in the web interface" -ForegroundColor Gray
Write-Host "   ✅ Performance analysis and recommendations" -ForegroundColor Gray
Write-Host ""
Write-Host "🔍 Key Timing Components:" -ForegroundColor Yellow
Write-Host "   🧠 LLM Inference - Time spent in actual AI processing" -ForegroundColor Gray
Write-Host "   🔗 Connection - Time to connect to Ollama service" -ForegroundColor Gray
Write-Host "   🔍 Cache Operations - Time for cache lookup/storage" -ForegroundColor Gray
Write-Host "   📋 Validation - Time for request validation" -ForegroundColor Gray
Write-Host "   🎨 Formatting - Time for response formatting" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 Performance Tips:" -ForegroundColor Yellow
Write-Host "   • LLM inference should be 60-80% of total time (normal)" -ForegroundColor Gray
Write-Host "   • High connection time may indicate network issues" -ForegroundColor Gray
Write-Host "   • Cache hits should be much faster (<100ms)" -ForegroundColor Gray
Write-Host "   • Total time <2s is considered good performance" -ForegroundColor Gray
