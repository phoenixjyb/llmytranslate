#!/bin/bash
# Android Development Environment Setup (Command Line Only)
# Bash script to setup minimal Android development environment for macOS/Linux

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Command line arguments
SKIP_JAVA=false
SKIP_ANDROID_SDK=false
CHECK_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-java)
            SKIP_JAVA=true
            shift
            ;;
        --skip-android-sdk)
            SKIP_ANDROID_SDK=true
            shift
            ;;
        --check-only)
            CHECK_ONLY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --skip-java         Skip Java installation check"
            echo "  --skip-android-sdk  Skip Android SDK installation check"
            echo "  --check-only        Only check environment, don't show installation instructions"
            echo "  -h, --help          Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}🚀 Android Development Environment Setup${NC}"
echo -e "${CYAN}=======================================${NC}"

if [ "$CHECK_ONLY" = true ]; then
    echo -e "${CYAN}🔍 Environment Check Mode${NC}"
fi

# Function to test Java installation
test_java_installation() {
    echo -e "\n${YELLOW}☕ Checking Java installation...${NC}"
    
    # First check if java is in PATH
    if command -v java >/dev/null 2>&1; then
        JAVA_VERSION=$(java -version 2>&1 | grep "version" | head -n 1)
        echo -e "${GREEN}✅ Java found in PATH: $JAVA_VERSION${NC}"
        
        # Extract major version number
        VERSION_NUM=$(echo "$JAVA_VERSION" | sed -n 's/.*version "\([0-9]*\).*/\1/p')
        
        if [ "$VERSION_NUM" -ge 11 ] 2>/dev/null; then
            echo -e "${GREEN}✅ Java version $VERSION_NUM is suitable for Android development${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  Java version $VERSION_NUM is too old (need 11+)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Java not found in PATH, checking common locations...${NC}"
    fi
    
    # Check macOS Android Studio bundled JDK
    if [[ "$OSTYPE" == "darwin"* ]]; then
        AS_JAVA="/Applications/Android Studio.app/Contents/jbr/Contents/Home/bin/java"
        if [ -f "$AS_JAVA" ]; then
            AS_VERSION=$("$AS_JAVA" -version 2>&1 | grep "version" | head -n 1)
            echo -e "${GREEN}✅ Java found in Android Studio: $AS_VERSION${NC}"
            echo -e "${CYAN}   Location: $AS_JAVA${NC}"
            
            # Check version
            VERSION_NUM=$(echo "$AS_VERSION" | sed -n 's/.*version "\([0-9]*\).*/\1/p')
            if [ "$VERSION_NUM" -ge 11 ] 2>/dev/null; then
                echo -e "${GREEN}✅ Android Studio Java version is suitable for development${NC}"
                return 0
            fi
        fi
    fi
    
    # Check Linux common locations
    if [[ "$OSTYPE" == "linux"* ]]; then
        # Check common Java locations on Linux
        JAVA_LOCATIONS=(
            "/usr/lib/jvm/default-java/bin/java"
            "/usr/lib/jvm/java-11-openjdk-amd64/bin/java"
            "/usr/lib/jvm/java-17-openjdk-amd64/bin/java"
            "/usr/lib/jvm/java-21-openjdk-amd64/bin/java"
        )
        
        for java_path in "${JAVA_LOCATIONS[@]}"; do
            if [ -f "$java_path" ]; then
                JAVA_VERSION=$("$java_path" -version 2>&1 | grep "version" | head -n 1)
                echo -e "${GREEN}✅ Java found: $JAVA_VERSION${NC}"
                echo -e "${CYAN}   Location: $java_path${NC}"
                
                VERSION_NUM=$(echo "$JAVA_VERSION" | sed -n 's/.*version "\([0-9]*\).*/\1/p')
                if [ "$VERSION_NUM" -ge 11 ] 2>/dev/null; then
                    echo -e "${GREEN}✅ Java version is suitable for development${NC}"
                    return 0
                fi
            fi
        done
    fi
    
    echo -e "${RED}❌ No suitable Java installation found${NC}"
    return 1
}

# Function to test Android SDK
test_android_sdk() {
    echo -e "\n${YELLOW}🤖 Checking Android SDK...${NC}"
    
    # Check standard locations for Android SDK
    SDK_LOCATIONS=(
        "$ANDROID_HOME"
        "$HOME/Library/Android/sdk"  # macOS default
        "$HOME/Android/Sdk"          # Linux default
        "/opt/android-sdk"           # Linux alternative
    )
    
    for sdk_path in "${SDK_LOCATIONS[@]}"; do
        if [ -n "$sdk_path" ] && [ -d "$sdk_path" ]; then
            echo -e "${GREEN}✅ Android SDK found: $sdk_path${NC}"
            
            # Check if platform-tools exists
            if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
                ADB_PATH="$sdk_path/platform-tools/adb.exe"
            else
                ADB_PATH="$sdk_path/platform-tools/adb"
            fi
            
            if [ -f "$ADB_PATH" ]; then
                echo -e "${GREEN}✅ ADB found: $ADB_PATH${NC}"
                
                # Set ANDROID_HOME if not already set
                if [ -z "$ANDROID_HOME" ] || [ "$ANDROID_HOME" != "$sdk_path" ]; then
                    echo -e "${CYAN}ℹ️  Setting ANDROID_HOME to: $sdk_path${NC}"
                    export ANDROID_HOME="$sdk_path"
                fi
                
                return 0
            else
                echo -e "${YELLOW}⚠️  ADB not found. Platform tools may not be installed.${NC}"
                echo -e "${GRAY}   SDK Path: $sdk_path${NC}"
                return 1
            fi
        fi
    done
    
    echo -e "${RED}❌ Android SDK not found in standard locations${NC}"
    return 1
}

# Function to show Java installation instructions
show_java_install_instructions() {
    echo -e "\n${CYAN}📋 Java Installation Instructions:${NC}"
    echo -e "${CYAN}===================================${NC}"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "${GREEN}macOS - Option 1: Use Homebrew (Recommended):${NC}"
        echo -e "${GRAY}   brew install openjdk@21${NC}"
        echo -e "${GRAY}   sudo ln -sfn /opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-21.jdk${NC}"
        echo ""
        echo -e "${YELLOW}macOS - Option 2: Use Android Studio's Java:${NC}"
        echo -e "${GRAY}   export JAVA_HOME=\"/Applications/Android Studio.app/Contents/jbr/Contents/Home\"${NC}"
        echo -e "${GRAY}   export PATH=\"\$JAVA_HOME/bin:\$PATH\"${NC}"
        echo ""
        echo -e "${YELLOW}macOS - Option 3: Download Oracle/Adoptium JDK:${NC}"
        echo -e "${BLUE}   https://adoptium.net/temurin/releases/${NC}"
    elif [[ "$OSTYPE" == "linux"* ]]; then
        echo -e "${GREEN}Linux - Package Manager Installation:${NC}"
        echo ""
        echo -e "${YELLOW}Ubuntu/Debian:${NC}"
        echo -e "${GRAY}   sudo apt update${NC}"
        echo -e "${GRAY}   sudo apt install openjdk-21-jdk${NC}"
        echo ""
        echo -e "${YELLOW}CentOS/RHEL/Fedora:${NC}"
        echo -e "${GRAY}   sudo dnf install java-21-openjdk-devel${NC}"
        echo ""
        echo -e "${YELLOW}Arch Linux:${NC}"
        echo -e "${GRAY}   sudo pacman -S jdk-openjdk${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}4. Verify installation:${NC}"
    echo -e "${GRAY}   java -version${NC}"
    echo -e "${GRAY}   javac -version${NC}"
}

# Function to show Android SDK installation instructions
show_android_sdk_instructions() {
    echo -e "\n${CYAN}📋 Android SDK Installation Instructions:${NC}"
    echo -e "${CYAN}=========================================${NC}"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "${GREEN}macOS - Option 1: Use Homebrew (Recommended):${NC}"
        echo -e "${GRAY}   brew install --cask android-commandlinetools${NC}"
        echo ""
        echo -e "${YELLOW}macOS - Option 2: Manual Installation:${NC}"
        echo -e "1. Download Android Command Line Tools from:"
        echo -e "${BLUE}   https://developer.android.com/studio#command-tools${NC}"
        echo ""
        echo -e "2. Extract to: ~/Library/Android/sdk/cmdline-tools/latest/"
        echo ""
        echo -e "3. Set environment variables in ~/.zshrc or ~/.bash_profile:"
        echo -e "${GRAY}   export ANDROID_HOME=\"\$HOME/Library/Android/sdk\"${NC}"
        echo -e "${GRAY}   export PATH=\"\$ANDROID_HOME/cmdline-tools/latest/bin:\$PATH\"${NC}"
        echo -e "${GRAY}   export PATH=\"\$ANDROID_HOME/platform-tools:\$PATH\"${NC}"
    elif [[ "$OSTYPE" == "linux"* ]]; then
        echo -e "${GREEN}Linux Installation:${NC}"
        echo -e "1. Download Android Command Line Tools from:"
        echo -e "${BLUE}   https://developer.android.com/studio#command-tools${NC}"
        echo ""
        echo -e "2. Extract to: ~/Android/Sdk/cmdline-tools/latest/"
        echo -e "${GRAY}   mkdir -p ~/Android/Sdk/cmdline-tools${NC}"
        echo -e "${GRAY}   unzip commandlinetools-linux-*.zip -d ~/Android/Sdk/cmdline-tools/${NC}"
        echo -e "${GRAY}   mv ~/Android/Sdk/cmdline-tools/cmdline-tools ~/Android/Sdk/cmdline-tools/latest${NC}"
        echo ""
        echo -e "3. Set environment variables in ~/.bashrc or ~/.zshrc:"
        echo -e "${GRAY}   export ANDROID_HOME=\"\$HOME/Android/Sdk\"${NC}"
        echo -e "${GRAY}   export PATH=\"\$ANDROID_HOME/cmdline-tools/latest/bin:\$PATH\"${NC}"
        echo -e "${GRAY}   export PATH=\"\$ANDROID_HOME/platform-tools:\$PATH\"${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}4. Install required components:${NC}"
    echo -e "${GRAY}   sdkmanager --licenses${NC}"
    echo -e "${GRAY}   sdkmanager \"platform-tools\" \"platforms;android-34\" \"build-tools;34.0.0\"${NC}"
    echo ""
    echo -e "${YELLOW}5. Verify installation:${NC}"
    echo -e "${GRAY}   adb version${NC}"
}

# Function to show quick start guide
show_quick_start() {
    echo -e "\n${GREEN}🎯 Quick Start Guide:${NC}"
    echo -e "${GREEN}=====================${NC}"
    echo -e "${GRAY}After setup is complete, you can:${NC}"
    echo ""
    echo -e "${YELLOW}1. Build Android APK:${NC}"
    echo -e "${GRAY}   ./build-android.sh build${NC}"
    echo ""
    echo -e "${YELLOW}2. Build and install on device:${NC}"
    echo -e "${GRAY}   ./build-android.sh build --install${NC}"
    echo ""
    echo -e "${YELLOW}3. Check connected devices:${NC}"
    echo -e "${GRAY}   ./build-android.sh devices${NC}"
    echo ""
    echo -e "${YELLOW}4. Start LLMyTranslate server:${NC}"
    echo -e "${GRAY}   ./start-service.sh${NC}"
    echo ""
    echo -e "${GREEN}🔧 Development Tips:${NC}"
    echo -e "${GRAY}• Use 'adb devices' to list connected Android devices${NC}"
    echo -e "${GRAY}• Enable USB debugging on your Android device${NC}"
    echo -e "${GRAY}• Build with --release flag for production APKs${NC}"
}

# Main execution
JAVA_OK=false
SDK_OK=false

# Test Java installation
if [ "$SKIP_JAVA" = false ]; then
    if test_java_installation; then
        JAVA_OK=true
    fi
fi

# Test Android SDK
if [ "$SKIP_ANDROID_SDK" = false ]; then
    if test_android_sdk; then
        SDK_OK=true
    fi
fi

# Show environment status
echo -e "\n${YELLOW}📊 Environment Status:${NC}"
echo -e "${YELLOW}======================${NC}"

if [ "$SKIP_JAVA" = true ]; then
    echo -e "Java JDK:     ${GRAY}⏭️  Skipped${NC}"
else
    if [ "$JAVA_OK" = true ]; then
        echo -e "Java JDK:     ${GREEN}✅ Ready${NC}"
    else
        echo -e "Java JDK:     ${RED}❌ Missing${NC}"
    fi
fi

if [ "$SKIP_ANDROID_SDK" = true ]; then
    echo -e "Android SDK:  ${GRAY}⏭️  Skipped${NC}"
else
    if [ "$SDK_OK" = true ]; then
        echo -e "Android SDK:  ${GREEN}✅ Ready${NC}"
    else
        echo -e "Android SDK:  ${RED}❌ Missing${NC}"
    fi
fi

# Show results and instructions
if [ "$JAVA_OK" = true ] && ([ "$SDK_OK" = true ] || [ "$SKIP_ANDROID_SDK" = true ]); then
    echo -e "\n${GREEN}🎉 Environment is ready for Android development!${NC}"
    show_quick_start
elif [ "$CHECK_ONLY" = false ]; then
    echo -e "\n${YELLOW}🔧 Setup Required${NC}"
    
    if [ "$JAVA_OK" = false ] && [ "$SKIP_JAVA" = false ]; then
        show_java_install_instructions
    fi
    
    if [ "$SDK_OK" = false ] && [ "$SKIP_ANDROID_SDK" = false ]; then
        show_android_sdk_instructions
    fi
    
    show_quick_start
fi

# Exit with appropriate code
if [ "$JAVA_OK" = true ] && ([ "$SDK_OK" = true ] || [ "$SKIP_ANDROID_SDK" = true ]); then
    exit 0
else
    exit 1
fi
