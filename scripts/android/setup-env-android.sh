#!/bin/bash
# Set up Android development environment using existing installations
# Bash script to configure environment variables for macOS/Linux

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

echo -e "${CYAN}🔧 Setting up Android Development Environment${NC}"
echo -e "${CYAN}=============================================${NC}"

# Detect OS
OS_TYPE="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macOS"
elif [[ "$OSTYPE" == "linux"* ]]; then
    OS_TYPE="Linux"
fi

echo -e "${GRAY}Detected OS: $OS_TYPE${NC}"

# Java paths for different OS
if [ "$OS_TYPE" = "macOS" ]; then
    # macOS paths
    JAVA_LOCATIONS=(
        "/opt/homebrew/opt/openjdk@21/bin/java"  # Homebrew OpenJDK 21
        "/opt/homebrew/opt/openjdk@24/bin/java"  # Homebrew OpenJDK 24
        "/opt/homebrew/opt/openjdk/bin/java"     # Homebrew default
        "/Applications/Android Studio.app/Contents/jbr/Contents/Home/bin/java"  # Android Studio
        "/System/Library/Frameworks/JavaVM.framework/Versions/Current/Commands/java"  # System Java
    )
    JAVA_HOME_PATHS=(
        "/opt/homebrew/opt/openjdk@21"
        "/opt/homebrew/opt/openjdk@24"
        "/opt/homebrew/opt/openjdk"
        "/Applications/Android Studio.app/Contents/jbr/Contents/Home"
        "/System/Library/Frameworks/JavaVM.framework/Versions/Current"
    )
    ANDROID_SDK_LOCATIONS=(
        "$HOME/Library/Android/sdk"
        "/opt/android-sdk"
    )
elif [ "$OS_TYPE" = "Linux" ]; then
    # Linux paths
    JAVA_LOCATIONS=(
        "/usr/lib/jvm/java-21-openjdk-amd64/bin/java"
        "/usr/lib/jvm/java-24-openjdk-amd64/bin/java"
        "/usr/lib/jvm/java-17-openjdk-amd64/bin/java"
        "/usr/lib/jvm/default-java/bin/java"
        "/opt/jdk/bin/java"
    )
    JAVA_HOME_PATHS=(
        "/usr/lib/jvm/java-21-openjdk-amd64"
        "/usr/lib/jvm/java-24-openjdk-amd64"
        "/usr/lib/jvm/java-17-openjdk-amd64"
        "/usr/lib/jvm/default-java"
        "/opt/jdk"
    )
    ANDROID_SDK_LOCATIONS=(
        "$HOME/Android/Sdk"
        "/opt/android-sdk"
    )
fi

# Find Java installation
JAVA_FOUND=false
JAVA_PATH=""
JAVA_HOME_PATH=""

for i in "${!JAVA_LOCATIONS[@]}"; do
    java_path="${JAVA_LOCATIONS[$i]}"
    java_home_path="${JAVA_HOME_PATHS[$i]}"
    
    if [ -f "$java_path" ]; then
        # Test if Java works and get version
        if JAVA_VERSION=$("$java_path" -version 2>&1 | grep "version" | head -n 1); then
            echo -e "${GREEN}✅ Found Java at: $java_path${NC}"
            echo -e "${GREEN}   Version: $JAVA_VERSION${NC}"
            
            # Check if it's suitable version (11+)
            VERSION_NUM=$(echo "$JAVA_VERSION" | sed -n 's/.*version "\([0-9]*\).*/\1/p')
            if [ "$VERSION_NUM" -ge 11 ] 2>/dev/null; then
                echo -e "${GREEN}✅ Java version $VERSION_NUM is suitable for Android development${NC}"
                
                JAVA_FOUND=true
                JAVA_PATH="$java_path"
                JAVA_HOME_PATH="$java_home_path"
                
                # Set environment variables for current session
                export JAVA_HOME="$java_home_path"
                export PATH="$(dirname "$java_path"):$PATH"
                echo -e "${GREEN}✅ Set JAVA_HOME to: $JAVA_HOME${NC}"
                break
            else
                echo -e "${YELLOW}⚠️  Java version $VERSION_NUM is too old (need 11+)${NC}"
            fi
        fi
    fi
done

if [ "$JAVA_FOUND" = false ]; then
    echo -e "${RED}❌ No suitable Java installation found${NC}"
    echo -e "${YELLOW}💡 Install Java using:${NC}"
    if [ "$OS_TYPE" = "macOS" ]; then
        echo -e "${GRAY}   brew install openjdk@21${NC}"
    elif [ "$OS_TYPE" = "Linux" ]; then
        echo -e "${GRAY}   sudo apt install openjdk-21-jdk  # Ubuntu/Debian${NC}"
        echo -e "${GRAY}   sudo dnf install java-21-openjdk-devel  # Fedora${NC}"
    fi
    exit 1
fi

# Find Android SDK
SDK_FOUND=false
SDK_PATH=""

for sdk_path in "${ANDROID_SDK_LOCATIONS[@]}"; do
    if [ -d "$sdk_path" ]; then
        echo -e "${GREEN}✅ Found Android SDK at: $sdk_path${NC}"
        
        # Check for platform-tools
        adb_path="$sdk_path/platform-tools/adb"
        if [ -f "$adb_path" ]; then
            echo -e "${GREEN}✅ ADB found: $adb_path${NC}"
            
            SDK_FOUND=true
            SDK_PATH="$sdk_path"
            
            # Set environment variables for current session
            export ANDROID_HOME="$sdk_path"
            export PATH="$sdk_path/platform-tools:$PATH"
            export PATH="$sdk_path/cmdline-tools/latest/bin:$PATH"
            echo -e "${GREEN}✅ Set ANDROID_HOME to: $ANDROID_HOME${NC}"
            break
        else
            echo -e "${YELLOW}⚠️  ADB not found in: $sdk_path${NC}"
        fi
    fi
done

if [ "$SDK_FOUND" = false ]; then
    echo -e "${YELLOW}⚠️  Android SDK not found in standard locations${NC}"
    echo -e "${YELLOW}💡 You can still build APKs, but won't be able to install to devices${NC}"
    if [ "$OS_TYPE" = "macOS" ]; then
        echo -e "${GRAY}   Install with: brew install --cask android-commandlinetools${NC}"
    elif [ "$OS_TYPE" = "Linux" ]; then
        echo -e "${GRAY}   Download from: https://developer.android.com/studio#command-tools${NC}"
    fi
fi

echo -e "\n${GREEN}🎯 Environment Setup Complete!${NC}"
echo -e "${GREEN}==============================${NC}"

# Verify installations
echo -e "\n${YELLOW}📋 Verification:${NC}"

# Test Java
if command -v java >/dev/null 2>&1; then
    JAVA_VERSION=$(java -version 2>&1 | grep "version" | head -n 1)
    echo -e "${GREEN}✅ Java: $JAVA_VERSION${NC}"
else
    echo -e "${RED}❌ Java verification failed${NC}"
fi

# Test ADB
if command -v adb >/dev/null 2>&1; then
    ADB_VERSION=$(adb version 2>&1 | grep "Android Debug Bridge" | head -n 1)
    echo -e "${GREEN}✅ ADB: $ADB_VERSION${NC}"
else
    echo -e "${YELLOW}⚠️  ADB not available (platform-tools may not be installed)${NC}"
fi

echo -e "\n${CYAN}💡 To make these changes permanent, add to your shell profile:${NC}"
if [ "$OS_TYPE" = "macOS" ]; then
    SHELL_PROFILE="~/.zshrc"
else
    SHELL_PROFILE="~/.bashrc"
fi

echo -e "${GRAY}   echo 'export JAVA_HOME=\"$JAVA_HOME_PATH\"' >> $SHELL_PROFILE${NC}"
echo -e "${GRAY}   echo 'export ANDROID_HOME=\"$SDK_PATH\"' >> $SHELL_PROFILE${NC}"
echo -e "${GRAY}   echo 'export PATH=\"\$JAVA_HOME/bin:\$ANDROID_HOME/platform-tools:\$ANDROID_HOME/cmdline-tools/latest/bin:\$PATH\"' >> $SHELL_PROFILE${NC}"

echo -e "\n${GREEN}🚀 Ready to build Android apps!${NC}"
echo -e "${CYAN}   Try: ./build-android.sh${NC}"
