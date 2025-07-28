# Add Ollama to Windows PATH (PowerShell version)

Write-Host "Adding Ollama to Windows PATH..." -ForegroundColor Green

$ollamaPath = "C:\Users\yanbo\AppData\Local\Programs\Ollama"

# Get current user PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)

# Check if Ollama is already in PATH
if ($currentPath -like "*$ollamaPath*") {
    Write-Host "Ollama is already in your PATH!" -ForegroundColor Yellow
} else {
    Write-Host "Adding Ollama to your PATH..." -ForegroundColor Yellow
    
    # Add Ollama to user PATH
    $newPath = $currentPath + ";" + $ollamaPath
    [Environment]::SetEnvironmentVariable("Path", $newPath, [EnvironmentVariableTarget]::User)
    
    Write-Host "Done! Ollama has been added to your PATH." -ForegroundColor Green
    Write-Host "Please restart your terminal or PowerShell for changes to take effect." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "After restart, you can use: ollama --version" -ForegroundColor White
}

# Also add to current session
$env:PATH += ";$ollamaPath"
Write-Host "Ollama is now available in this session. Try: ollama --version" -ForegroundColor Green
