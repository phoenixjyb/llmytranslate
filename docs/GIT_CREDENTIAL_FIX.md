# 🔧 Git Credential Manager Fix for Windows

## Problem
You may see these warnings when using git:
```
fatal: Unable to persist credentials with the 'wincredman' credential store.
See https://aka.ms/gcm/credstores for more information.
```

## Solution

### Option 1: Use DPAPI Credential Store (Recommended)
```powershell
git config --global credential.credentialStore dpapi
```

### Option 2: Use Cache Credential Store
```powershell
git config --global credential.credentialStore cache
```

### Option 3: Use Our Git Helper Script (Best Experience)
```powershell
# Clean git operations without warnings
.\scripts\git_helper.ps1 status
.\scripts\git_helper.ps1 add
.\scripts\git_helper.ps1 commit "Your commit message"
.\scripts\git_helper.ps1 push
.\scripts\git_helper.ps1 pull
.\scripts\git_helper.ps1 log
```

## Verification
Check your current settings:
```powershell
git config --list | findstr credential
```

Should show:
```
credential.helper=manager
credential.credentialstore=dpapi
```

## Notes
- These warnings don't prevent git from working
- DPAPI is the most reliable credential store on Windows
- The git helper script provides the cleanest experience
- All solutions maintain your existing authentication
