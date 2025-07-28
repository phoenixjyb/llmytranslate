# Git Helper Script - Clean Operations Without Credential Warnings
# Usage: .\git_helper.ps1 [push|pull|status|commit "message"]

param(
    [Parameter(Position=0, Mandatory=$true)]
    [ValidateSet("push", "pull", "status", "commit", "add", "log")]
    [string]$Operation,
    
    [Parameter(Position=1)]
    [string]$Message
)

Write-Host "🔧 Git Helper - Clean Operations" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Suppress credential warnings temporarily
$env:GCM_CREDENTIAL_STORE = "dpapi"

switch ($Operation) {
    "status" {
        Write-Host "📊 Checking repository status..." -ForegroundColor Yellow
        git status
    }
    
    "add" {
        Write-Host "➕ Adding all changes..." -ForegroundColor Yellow
        git add -A
        git status --short
    }
    
    "commit" {
        if (-not $Message) {
            Write-Host "❌ Commit message required!" -ForegroundColor Red
            Write-Host "Usage: .\git_helper.ps1 commit 'Your message here'" -ForegroundColor Gray
            exit 1
        }
        Write-Host "💾 Committing changes..." -ForegroundColor Yellow
        git add -A
        git commit -m $Message
    }
    
    "push" {
        Write-Host "⬆️ Pushing to remote repository..." -ForegroundColor Yellow
        Write-Host "📡 Connecting to origin/master..." -ForegroundColor Cyan
        
        $pushResult = git push origin master 2>&1
        
        # Filter out credential warnings but show important messages
        $filteredOutput = $pushResult | Where-Object {
            $_ -notlike "*Unable to persist credentials*" -and
            $_ -notlike "*wincredman*" -and
            $_ -notlike "*See https://aka.ms/gcm/credstores*"
        }
        
        if ($filteredOutput) {
            $filteredOutput | ForEach-Object { Write-Host $_ -ForegroundColor Cyan }
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Push completed successfully!" -ForegroundColor Green
        } else {
            Write-Host "❌ Push failed!" -ForegroundColor Red
        }
    }
    
    "pull" {
        Write-Host "⬇️ Pulling from remote repository..." -ForegroundColor Yellow
        git pull origin master
    }
    
    "log" {
        Write-Host "📜 Recent commit history..." -ForegroundColor Yellow
        git log --oneline -10
    }
}

Write-Host "`n✅ Git operation completed!" -ForegroundColor Green
