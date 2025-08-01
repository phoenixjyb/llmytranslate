# Cross-Platform Android Development Scripts

## Script Equivalents

| Purpose | Windows (PowerShell) | macOS/Linux (Bash) |
|---------|---------------------|-------------------|
| **Environment Check** | `setup-android-dev.ps1` | `setup-android-dev.sh` |
| **Environment Setup** | `setup-env-android.ps1` | `setup-env-android.sh` |
| **Android Build** | `build-android.ps1` | `build-android.sh` |

## Usage Examples

### Windows (PowerShell)
```powershell
# Check environment
.\setup-android-dev.ps1 -CheckOnly

# Set up environment variables
.\setup-env-android.ps1

# Build Android APK
.\build-android.ps1

# Build and install to device
.\build-android.ps1 -Install
```

### macOS/Linux (Bash)
```bash
# Make scripts executable (first time only)
chmod +x setup-android-dev.sh setup-env-android.sh build-android.sh

# Check environment
./setup-android-dev.sh --check-only

# Set up environment variables
source ./setup-env-android.sh

# Build Android APK
./build-android.sh

# Build and install to device
./build-android.sh --install
```

## Environment Detection

### Windows
- **Java**: Checks system PATH, then Android Studio bundled JDK
  - Location: `D:\Program Files\Android\Android Studio\jbr`
  - Version: OpenJDK 21

### macOS
- **Java**: Checks Homebrew, Android Studio, system Java
  - Homebrew: `/opt/homebrew/opt/openjdk@*/bin/java`
  - Android Studio: `/Applications/Android Studio.app/Contents/jbr/Contents/Home/bin/java`
  - Your system: OpenJDK 24 (detected automatically)

### Linux
- **Java**: Checks package manager installations, common locations
  - Ubuntu/Debian: `/usr/lib/jvm/java-*-openjdk-amd64/bin/java`
  - Fedora/CentOS: Similar OpenJDK locations

## Android SDK Locations

| OS | Standard SDK Location |
|----|----------------------|
| **Windows** | `%LOCALAPPDATA%\Android\Sdk` |
| **macOS** | `~/Library/Android/sdk` |
| **Linux** | `~/Android/Sdk` |

## Key Features

✅ **Cross-platform compatibility**
✅ **Automatic Java version detection** 
✅ **Multiple Java source support** (system, Homebrew, Android Studio)
✅ **Environment variable setup**
✅ **Color-coded output**
✅ **Detailed installation instructions**
✅ **Command-line argument parsing**

## Installation Instructions Per Platform

### macOS Java Installation
```bash
# Option 1: Homebrew (Recommended)
brew install openjdk@21

# Option 2: Use Android Studio's Java
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
export PATH="$JAVA_HOME/bin:$PATH"
```

### Linux Java Installation
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install openjdk-21-jdk

# Fedora/CentOS
sudo dnf install java-21-openjdk-devel

# Arch Linux
sudo pacman -S jdk-openjdk
```

### Android SDK Installation

#### macOS
```bash
# Homebrew (Recommended)
brew install --cask android-commandlinetools

# Manual setup
export ANDROID_HOME="$HOME/Library/Android/sdk"
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"
export PATH="$ANDROID_HOME/platform-tools:$PATH"
```

#### Linux
```bash
# Download command line tools and extract
mkdir -p ~/Android/Sdk/cmdline-tools
# Extract to ~/Android/Sdk/cmdline-tools/latest/

export ANDROID_HOME="$HOME/Android/Sdk"
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"
export PATH="$ANDROID_HOME/platform-tools:$PATH"
```

## Troubleshooting

### Permission Issues (macOS/Linux)
```bash
chmod +x *.sh
```

### Java Version Conflicts
The scripts automatically detect and use the highest suitable Java version found.

### Environment Variables
Use `source ./setup-env-android.sh` on macOS/Linux to ensure environment variables are set in your current shell session.

## Your Current Setup Status

- ✅ **Windows**: OpenJDK 21 (Android Studio) + Android SDK ready
- ✅ **macOS**: OpenJDK 24 (system) - scripts will detect automatically
- ✅ **Cross-platform**: All scripts created and synchronized

You're now ready for cross-platform Android development! 🚀
