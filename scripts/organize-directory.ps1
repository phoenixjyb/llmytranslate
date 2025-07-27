# ================================================================================================
# Directory Organization Script - LLM Translation Service
# This script organizes the project directory structure for better maintainability
# ================================================================================================

Write-Host "🗂️  LLM Translation Service - Directory Organization" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# Create organized directory structure
$directories = @{
    "scripts" = "All automation and utility scripts"
    "config" = "Configuration files and templates"
    "docs" = "Documentation and guides"
    "src" = "Source code"
    "tests" = "Test files and test data"
    "web" = "Web interface files"
    "logs" = "Log files (if not exists)"
    "cache" = "Cache directory (if not exists)"
    "docker" = "Docker configuration files"
    "performance" = "Performance testing and results"
}

Write-Host "`n📁 Ensuring directory structure..." -ForegroundColor Yellow

foreach ($dir in $directories.Keys) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  ✅ Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "  ℹ️  Exists: $dir" -ForegroundColor Gray
    }
}

# Create performance directory for test results
if (-not (Test-Path "performance")) {
    New-Item -ItemType Directory -Path "performance" -Force | Out-Null
    Write-Host "  ✅ Created: performance" -ForegroundColor Green
}

Write-Host "`n🔄 Organizing files..." -ForegroundColor Yellow

# Move performance test files to performance directory
$performanceFiles = @(
    "test-performance.ps1",
    "test_performance.py",
    "test_performance_comparison.py", 
    "test_timing_direct.py",
    "test_optimized_service.py",
    "ollama_direct_results.json",
    "optimized_service_results.json"
)

foreach ($file in $performanceFiles) {
    if (Test-Path $file) {
        Move-Item $file "performance\" -Force
        Write-Host "  📊 Moved to performance/: $file" -ForegroundColor Cyan
    }
}

# Move configuration files to config directory (if not already there)
$configFiles = @(
    ".env.example",
    ".env.remote", 
    "nginx.conf"
)

foreach ($file in $configFiles) {
    if ((Test-Path $file) -and (-not (Test-Path "config\$file"))) {
        Copy-Item $file "config\" -Force
        Write-Host "  ⚙️  Copied to config/: $file" -ForegroundColor Blue
    }
}

# Move Docker files to docker directory (if not already there)
$dockerFiles = @(
    "docker-compose.yml",
    "docker-compose.remote.yml",
    "Dockerfile"
)

foreach ($file in $dockerFiles) {
    if ((Test-Path $file) -and (-not (Test-Path "docker\$file"))) {
        Copy-Item $file "docker\" -Force
        Write-Host "  🐳 Copied to docker/: $file" -ForegroundColor Blue
    }
}

# Clean up test files from root
$testFiles = @(
    "test_ollama.json",
    "test_ollama_connectivity.py",
    "test_ollama_direct.py"
)

foreach ($file in $testFiles) {
    if (Test-Path $file) {
        if (-not (Test-Path "tests\$file")) {
            Move-Item $file "tests\" -Force
            Write-Host "  🧪 Moved to tests/: $file" -ForegroundColor Magenta
        } else {
            Remove-Item $file -Force
            Write-Host "  🗑️  Removed duplicate: $file" -ForegroundColor Yellow
        }
    }
}

# Clean up old/unused files
$oldFiles = @(
    "translation_server.py",
    "discover_service.py",
    "validate.py"
)

foreach ($file in $oldFiles) {
    if (Test-Path $file) {
        # Move to tests or remove if duplicate
        if (-not (Test-Path "tests\$file")) {
            Move-Item $file "tests\" -Force
            Write-Host "  📦 Moved to tests/: $file" -ForegroundColor Gray
        } else {
            Remove-Item $file -Force
            Write-Host "  🗑️  Removed duplicate: $file" -ForegroundColor Yellow
        }
    }
}

Write-Host "`n📋 Creating directory documentation..." -ForegroundColor Yellow

# Create README files for each directory
$directoryDocs = @{
    "scripts/README.md" = @"
# Scripts Directory

This directory contains all automation and utility scripts for the LLM Translation Service.

## PowerShell Scripts (.ps1)
- **start-service.ps1** - Main service startup with full functionality
- **stop-service.ps1** - Graceful service shutdown
- **setup.ps1** - Initial project setup for Windows
- **service-manager.ps1** - Service lifecycle management
- **production-setup.ps1** - Production deployment configuration
- **deploy-online.ps1** - Internet deployment setup
- **setup_ngrok.ps1** - ngrok tunnel configuration
- **setup_remote_access.ps1** - Remote access configuration
- **git_helper.ps1** - Clean git operations
- **test_endpoints.ps1** - API endpoint testing

## Shell Scripts (.sh)
- **start-service.sh** - Main service startup (Unix/Linux/macOS)
- **stop-service.sh** - Graceful service shutdown (Unix/Linux/macOS)
- **setup.sh** - Initial project setup (Unix/Linux/macOS)
- **service-manager.sh** - Service lifecycle management (Unix/Linux/macOS)
- **production-setup.sh** - Production deployment (Unix/Linux/macOS)
- **deploy-online.sh** - Internet deployment setup (Unix/Linux/macOS)
- **setup_ngrok.sh** - ngrok tunnel configuration (Unix/Linux/macOS)
- **setup_remote_access.sh** - Remote access configuration (Unix/Linux/macOS)
- **git_helper.sh** - Clean git operations (Unix/Linux/macOS)
- **test_endpoints.sh** - API endpoint testing (Unix/Linux/macOS)

## Batch Scripts (.bat)
- **setup.bat** - Basic Windows setup
- **start-service.bat** - Simple Windows service start

All shell scripts provide feature parity with their PowerShell counterparts.
"@

    "performance/README.md" = @"
# Performance Directory

This directory contains performance testing scripts and results.

## Performance Test Scripts
- **test-performance.ps1** - PowerShell performance testing
- **test_performance.py** - Python performance testing
- **test_performance_comparison.py** - Service comparison testing
- **test_timing_direct.py** - Direct timing measurements
- **test_optimized_service.py** - Optimized service testing

## Results Files
- **ollama_direct_results.json** - Direct Ollama performance results
- **optimized_service_results.json** - Optimized service performance results

Run performance tests to benchmark translation speed and service responsiveness.
"@

    "config/README.md" = @"
# Configuration Directory

This directory contains configuration files and templates.

## Environment Files
- **.env.example** - Template for environment variables
- **.env.remote** - Remote deployment configuration
- **nginx.conf** - nginx reverse proxy configuration

## Usage
1. Copy .env.example to .env in project root
2. Modify .env with your specific settings
3. Use nginx.conf for production reverse proxy setup
"@

    "docker/README.md" = @"
# Docker Directory

This directory contains Docker configuration files.

## Docker Files
- **Dockerfile** - Main container image definition
- **docker-compose.yml** - Local development setup
- **docker-compose.remote.yml** - Remote deployment setup

## Usage
```bash
# Local development
docker-compose up

# Remote deployment
docker-compose -f docker-compose.remote.yml up
```
"@
}

foreach ($docFile in $directoryDocs.Keys) {
    $content = $directoryDocs[$docFile]
    $content | Out-File -FilePath $docFile -Encoding UTF8 -Force
    Write-Host "  📝 Created: $docFile" -ForegroundColor Green
}

Write-Host "`n✅ Directory organization complete!" -ForegroundColor Green
Write-Host "`n📊 Final directory structure:" -ForegroundColor Cyan

# Display organized structure
$structure = @"
llmytranslate/
├── 📁 scripts/          # All automation scripts
├── 📁 src/              # Source code
├── 📁 tests/            # Test files
├── 📁 docs/             # Documentation
├── 📁 config/           # Configuration templates
├── 📁 web/              # Web interface
├── 📁 docker/           # Docker configuration
├── 📁 performance/      # Performance tests & results
├── 📁 logs/             # Service logs
├── 📁 cache/            # Cache storage
├── 📄 run.py            # Main service entry point
├── 📄 requirements.txt  # Python dependencies
├── 📄 .env              # Environment configuration
└── 📄 README.md         # Project documentation
"@

Write-Host $structure -ForegroundColor White

Write-Host "`n🎯 Key benefits of this organization:" -ForegroundColor Yellow
Write-Host "  • All scripts centralized in scripts/ directory" -ForegroundColor White
Write-Host "  • Performance tests isolated in performance/ directory" -ForegroundColor White
Write-Host "  • Configuration files organized in config/ directory" -ForegroundColor White
Write-Host "  • Docker files organized in docker/ directory" -ForegroundColor White
Write-Host "  • Clear separation of concerns" -ForegroundColor White
Write-Host "  • Easy navigation and maintenance" -ForegroundColor White
